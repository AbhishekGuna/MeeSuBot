"""
Search cog — /search command

Lets users find past meeting summaries using PostgreSQL full-text search.

Usage
-----
/search query:"budget approval"
/search query:"roadmap" topic:"marketing"

Options
-------
query  (required) — free-text phrase to search across tldr, topics,
                    key_decisions, and action_items
topic  (optional) — additional topic filter (ILIKE match)
limit  (optional) — max results to return (1–20, default 10)
"""

import discord
from discord import app_commands
from discord.ext import commands

from db.summaries import search_summaries
from models import SummaryRecord

# --------------------------------------------------------------------- #
# Helpers                                                                #
# --------------------------------------------------------------------- #

SENTIMENT_EMOJI = {
    "positive": "😊",
    "neutral": "😐",
    "negative": "😟",
}

_HIGHLIGHT_COLOR = discord.Color.from_rgb(88, 101, 242)   # Discord blurple-ish


def _build_search_embed(
    record: SummaryRecord,
    page: int,
    total: int,
    query: str,
    topic: str | None,
) -> discord.Embed:
    """Build a rich embed for one search result."""
    sentiment_icon = SENTIMENT_EMOJI.get(record.sentiment, "😐")
    timestamp_str = record.created_at.strftime("%d %b %Y, %H:%M UTC")

    # Surface which fields matched
    matched_topics = (
        ", ".join(t for t in record.topics if query.lower() in t.lower())
        or (", ".join(record.topics) if record.topics else "—")
    )

    embed = discord.Embed(
        title=f"🔍 Search Result — {record.filename}",
        description=record.tldr,
        color=_HIGHLIGHT_COLOR,
        timestamp=record.created_at,
    )

    # --- Key decisions ---
    decisions_value = (
        "\n".join(f"• {d}" for d in record.key_decisions)
        if record.key_decisions
        else "None recorded"
    )
    embed.add_field(name="✅ Key Decisions", value=decisions_value, inline=False)

    # --- Action items ---
    if record.action_items:
        action_lines = []
        for item in record.action_items:
            line = f"• **{item.get('owner', 'Unassigned')}** — {item.get('task', '')}"
            if item.get("deadline"):
                line += f" *(by {item['deadline']})*"
            action_lines.append(line)
        actions_value = "\n".join(action_lines)
    else:
        actions_value = "None assigned"
    embed.add_field(name="📌 Action Items", value=actions_value, inline=False)

    # --- Open questions ---
    questions_value = (
        "\n".join(f"• {q}" for q in record.open_questions)
        if record.open_questions
        else "None"
    )
    embed.add_field(name="❓ Open Questions", value=questions_value, inline=False)

    # --- Topics & Mood (inline) ---
    embed.add_field(name="🏷️ Topics", value=matched_topics, inline=True)
    embed.add_field(
        name="🎭 Mood",
        value=f"{sentiment_icon} {record.sentiment.capitalize()}",
        inline=True,
    )

    # Construct footer
    filter_info = f" · topic filter: \"{topic}\"" if topic else ""
    embed.set_footer(
        text=(
            f"Result {page}/{total} · query: \"{query}\"{filter_info}"
            f" · {timestamp_str}"
        )
    )
    return embed


# --------------------------------------------------------------------- #
# Paginator View                                                         #
# --------------------------------------------------------------------- #

class SearchPaginator(discord.ui.View):
    """
    Interactive pagination view for /search results.

    Only the command invoker can navigate; times out after 120 s.
    """

    def __init__(
        self,
        records: list[SummaryRecord],
        author_id: int,
        query: str,
        topic: str | None,
    ):
        super().__init__(timeout=120)
        self.records = records
        self.author_id = author_id
        self.query = query
        self.topic = topic
        self.page = 0  # 0-based
        self.message: discord.Message | None = None
        self._refresh_buttons()

    # ---- internal helpers ------------------------------------------- #

    def _refresh_buttons(self) -> None:
        self.prev_button.disabled = self.page == 0
        self.next_button.disabled = self.page == len(self.records) - 1

    def _current_embed(self) -> discord.Embed:
        return _build_search_embed(
            self.records[self.page],
            self.page + 1,
            len(self.records),
            self.query,
            self.topic,
        )

    async def _guard(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "⚠️ Only the person who ran `/search` can navigate these pages.",
                ephemeral=True,
            )
            return False
        return True

    # ---- buttons ---------------------------------------------------- #

    @discord.ui.button(
        label="◀ Prev",
        style=discord.ButtonStyle.secondary,
        custom_id="search_prev",
        disabled=True,
    )
    async def prev_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if not await self._guard(interaction):
            return
        self.page -= 1
        self._refresh_buttons()
        await interaction.response.edit_message(embed=self._current_embed(), view=self)

    @discord.ui.button(
        label="Next ▶",
        style=discord.ButtonStyle.secondary,
        custom_id="search_next",
    )
    async def next_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if not await self._guard(interaction):
            return
        self.page += 1
        self._refresh_buttons()
        await interaction.response.edit_message(embed=self._current_embed(), view=self)

    # ---- timeout ---------------------------------------------------- #

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True  # type: ignore[attr-defined]
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass


# --------------------------------------------------------------------- #
# Cog                                                                    #
# --------------------------------------------------------------------- #

class Search(commands.Cog):
    """Cog that provides the /search slash command."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(
        name="search",
        description="Search past meeting summaries by keyword, topic, or action item.",
    )
    @app_commands.describe(
        query="Keyword or phrase to search for (e.g. 'budget approval')",
        topic="Optional: filter results to a specific topic (e.g. 'marketing')",
        limit="Max results to return (1–20, default 10)",
    )
    async def search(
        self,
        ctx: commands.Context,
        query: str,
        topic: str | None = None,
        limit: app_commands.Range[int, 1, 20] = 10,
    ):
        """
        Full-text search over this server's meeting summaries.

        Uses PostgreSQL ``plainto_tsquery`` to match across the summary,
        topics, decisions, and action items fields, ranked by relevance.
        """
        if ctx.guild is None:
            await ctx.send(
                "⚠️ This command can only be used inside a server.", ephemeral=True
            )
            return

        await ctx.defer(ephemeral=False)

        records = await search_summaries(
            ctx.guild.id,
            query,
            topic=topic,
            limit=limit,
        )

        if not records:
            tip = f" Try broadening your query or removing the topic filter." if topic else ""
            embed = discord.Embed(
                title="🔍 No Results Found",
                description=(
                    f"No meeting summaries matched **\"{query}\"**"
                    + (f" with topic **\"{topic}\"**" if topic else "")
                    + f".{tip}"
                ),
                color=discord.Color.orange(),
            )
            await ctx.send(embed=embed)
            return

        # Single result — skip pagination
        if len(records) == 1:
            embed = _build_search_embed(records[0], 1, 1, query, topic)
            await ctx.send(embed=embed)
            return

        view = SearchPaginator(records, author_id=ctx.author.id, query=query, topic=topic)
        message = await ctx.send(embed=view._current_embed(), view=view)
        view.message = message


async def setup(bot: commands.Bot):
    await bot.add_cog(Search(bot))
