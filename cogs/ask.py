"""
/ask command — RAG-lite Q&A over stored meeting summaries.

Flow
----
1. Fetch the N most recent summaries for the guild from the DB.
2. Serialise each summary into a plain-text context chunk.
3. Ask Gemini to answer the user's question using only that context.
4. Return the answer in a rich Discord embed.

The context is intentionally capped (CONTEXT_MEETINGS_LIMIT) to keep
token usage bounded.  If no summaries exist the command tells the user
gracefully instead of hallucinating.
"""

import textwrap

import discord
from discord.ext import commands

from config import GEMINI_MODEL
from db.summaries import get_guild_summaries
from models.summary import SummaryRecord
from utils import get_ai_client

# How many past summaries to pull as context
CONTEXT_MEETINGS_LIMIT = 5
# Hard cap on the answer shown in Discord (characters)
ANSWER_HARD_CAP = 1900


def _build_context(records: list[SummaryRecord]) -> str:
    """
    Serialise a list of SummaryRecord objects into a readable text block
    that the LLM can use as grounding context.
    """
    chunks: list[str] = []
    for i, r in enumerate(records, start=1):
        decisions = "\n  ".join(f"- {d}" for d in r.key_decisions) or "  None recorded"
        items = (
            "\n  ".join(
                f"- {a['owner']}: {a['task']}"
                + (f" (by {a['deadline']})" if a.get("deadline") else "")
                for a in r.action_items
            )
            or "  None assigned"
        )
        questions = "\n  ".join(f"- {q}" for q in r.open_questions) or "  None"
        topics = ", ".join(r.topics) or "unspecified"
        date = r.created_at.strftime("%Y-%m-%d")

        chunk = textwrap.dedent(f"""\
            === Meeting {i} | {date} | file: {r.filename} ===
            Summary: {r.tldr}
            Sentiment: {r.sentiment}
            Topics: {topics}
            Key Decisions:
              {decisions}
            Action Items:
              {items}
            Open Questions:
              {questions}
        """)
        chunks.append(chunk)

    return "\n".join(chunks)


_SYSTEM_PROMPT = """\
You are a helpful meeting assistant.  You have access to a set of recent \
meeting summaries from this team.  Answer the user's question **strictly \
using the information provided in the meeting context below**.

Rules:
- Be concise and factual.
- If the answer cannot be determined from the context, say so clearly — \
  do NOT invent information.
- Do not repeat the context back verbatim; synthesise a natural answer.
- Keep the answer under 400 words.
"""


class Ask(commands.Cog):
    """RAG-lite Q&A over stored meeting summaries."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.client = get_ai_client()

    # ------------------------------------------------------------------ #
    # Command                                                              #
    # ------------------------------------------------------------------ #

    @commands.hybrid_command(
        name="ask",
        description="Ask a question answered from your stored meeting transcripts.",
    )
    async def ask(self, ctx: commands.Context, *, question: str) -> None:
        """
        Usage: /ask <question>

        The bot retrieves the most recent meeting summaries for this server
        and uses them as grounding context to answer the question.
        """
        await ctx.defer()

        # 1. Fetch context from DB
        try:
            records = await get_guild_summaries(
                ctx.guild.id, limit=CONTEXT_MEETINGS_LIMIT
            )
        except Exception as exc:
            await ctx.send(
                embed=_error_embed(f"Failed to load meeting data: {exc}"),
                ephemeral=True,
            )
            return

        if not records:
            await ctx.send(
                embed=_no_data_embed(),
                ephemeral=True,
            )
            return

        context_text = _build_context(records)

        # 2. Build the prompt
        prompt = (
            f"{_SYSTEM_PROMPT}\n\n"
            f"--- MEETING CONTEXT ---\n{context_text}\n"
            f"--- END OF CONTEXT ---\n\n"
            f"Question: {question}"
        )

        # 3. Ask the model (native async — no thread overhead)
        try:
            response = await self.client.aio.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
            )
        except Exception as exc:
            await ctx.send(
                embed=_error_embed(f"AI request failed: {exc}"),
                ephemeral=True,
            )
            return

        answer = (response.text or "").strip()

        # 4. Truncate if necessary
        if len(answer) > ANSWER_HARD_CAP:
            answer = answer[: ANSWER_HARD_CAP - 3] + "…"

        # 5. Build and send the embed
        embed = _answer_embed(question=question, answer=answer, num_meetings=len(records))
        await ctx.send(embed=embed)


# ------------------------------------------------------------------ #
# Embed helpers                                                        #
# ------------------------------------------------------------------ #

def _answer_embed(*, question: str, answer: str, num_meetings: int) -> discord.Embed:
    embed = discord.Embed(
        title="🔍 Meeting Q&A",
        color=discord.Color.from_rgb(88, 101, 242),  # Discord blurple-ish
    )
    # Trim question for display if very long
    display_q = question if len(question) <= 200 else question[:197] + "…"
    embed.add_field(name="❓ Question", value=display_q, inline=False)
    embed.add_field(name="💬 Answer", value=answer, inline=False)
    embed.set_footer(
        text=f"Context: {num_meetings} most recent meeting{'s' if num_meetings != 1 else ''}"
    )
    return embed


def _no_data_embed() -> discord.Embed:
    return discord.Embed(
        title="📭 No Meeting Data",
        description=(
            "There are no stored meeting summaries for this server yet.\n"
            "Use `/summarize` to process a transcript first."
        ),
        color=discord.Color.orange(),
    )


def _error_embed(detail: str) -> discord.Embed:
    return discord.Embed(
        title="⚠️ Error",
        description=detail,
        color=discord.Color.red(),
    )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Ask(bot))
