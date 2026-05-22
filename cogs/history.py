"""
History cog — /history command
Shows the last 5 meeting summaries recorded in this server as paginated embeds.
Navigation is handled by a discord.ui.View with ◀ Prev / Next ▶ buttons.
"""

import discord
from discord.ext import commands
from db.summaries import get_guild_summaries
from models import SummaryRecord
from config import HISTORY_LIMIT

# --------------------------------------------------------------------- #
# Helpers                                                                #
# --------------------------------------------------------------------- #

SENTIMENT_EMOJI = {
    "positive": "😊",
    "neutral": "😐",
    "negative": "😟",
}



def _build_embed(record: SummaryRecord, page: int, total: int) -> discord.Embed:

    sentiment_icon = SENTIMENT_EMOJI.get(record.sentiment, "😐")
    timestamp_str = record.created_at.strftime("%d %b %Y, %H:%M UTC")

    embed = discord.Embed(
        title=f"📋 Meeting Summary — {record.filename}",
        description=record.tldr,
        color=discord.Color.blurple(),
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

    # --- Topics (inline) ---
    topics_value = ", ".join(record.topics) if record.topics else "—"
    embed.add_field(name="🏷️ Topics", value=topics_value, inline=True)

    # --- Mood (inline) ---
    embed.add_field(
        name="🎭 Mood",
        value=f"{sentiment_icon} {record.sentiment.capitalize()}",
        inline=True,
    )

    embed.set_footer(text=f"Summary {page}/{total} · Recorded on {timestamp_str}")
    return embed


# --------------------------------------------------------------------- #
# Paginator View                                                         #
# --------------------------------------------------------------------- #

class HistoryPaginator(discord.ui.View):
    """
    Interactive pagination view for the /history command.

    Buttons auto-disable at the boundary pages and the whole view
    times out after 120 seconds of inactivity.
    """

    def __init__(self, records: list[SummaryRecord], author_id: int):
        super().__init__(timeout=120)
        self.records = records
        self.author_id = author_id
        self.page = 0  # 0-based index

        self._refresh_buttons()

    # ---- internal helpers ------------------------------------------- #

    def _refresh_buttons(self) -> None:
        """Enable/disable nav buttons based on current page."""
        self.prev_button.disabled = self.page == 0
        self.next_button.disabled = self.page == len(self.records) - 1

    def _current_embed(self) -> discord.Embed:
        return _build_embed(self.records[self.page], self.page + 1, len(self.records))

    async def _guard(self, interaction: discord.Interaction) -> bool:
        """Only the command invoker may paginate."""
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "⚠️ Only the person who ran `/history` can navigate these pages.",
                ephemeral=True,
            )
            return False
        return True

    # ---- buttons ---------------------------------------------------- #

    @discord.ui.button(label="◀ Prev", style=discord.ButtonStyle.secondary, custom_id="history_prev", disabled=True)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._guard(interaction):
            return
        self.page -= 1
        self._refresh_buttons()
        await interaction.response.edit_message(embed=self._current_embed(), view=self)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.secondary, custom_id="history_next")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._guard(interaction):
            return
        self.page += 1
        self._refresh_buttons()
        await interaction.response.edit_message(embed=self._current_embed(), view=self)

    # ---- timeout ---------------------------------------------------- #

    async def on_timeout(self):
        """Disable all buttons when the view expires."""
        for item in self.children:
            item.disabled = True  # type: ignore[attr-defined]
        # We cannot edit the message here without a reference; the cog
        # stores it on the view so we can update it.
        if hasattr(self, "message") and self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass


# --------------------------------------------------------------------- #
# Cog                                                                    #
# --------------------------------------------------------------------- #

class History(commands.Cog):
    """Cog that provides the /history slash command."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(
        name="history",
        description="Show the last 5 meeting summaries recorded in this server.",
    )
    async def history(self, ctx: commands.Context):
        """
        Fetch the most recent HISTORY_LIMIT summaries for the current guild
        and present them as interactive paginated embeds.
        """
        if ctx.guild is None:
            await ctx.send(
                "⚠️ This command can only be used inside a server.", ephemeral=True
            )
            return

        await ctx.defer(ephemeral=False)

        records = await get_guild_summaries(ctx.guild.id, limit=HISTORY_LIMIT)

        if not records:
            embed = discord.Embed(
                title="📋 Meeting History",
                description="No summaries have been recorded in this server yet.\nUse `/summarize` to create the first one!",
                color=discord.Color.orange(),
            )
            await ctx.send(embed=embed)
            return

        # Single summary — no pagination needed
        if len(records) == 1:
            print(f"Only one summary found, sending embed without pagination. {len(records)} record(s) retrieved.")
            embed = _build_embed(records[0], 1, 1)
            await ctx.send(embed=embed)
            print("Displayed single summary, no pagination needed.")
            return

        view = HistoryPaginator(records, author_id=ctx.author.id)
        message = await ctx.send(embed=view._current_embed(), view=view)
        # Store reference so on_timeout can disable buttons
        view.message = message


async def setup(bot: commands.Bot):
    await bot.add_cog(History(bot))
