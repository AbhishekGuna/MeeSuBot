"""
Stats cog — /stats command

Shows aggregate statistics for the current server:
  • Total meetings summarized
  • Total hours of audio/video processed (based on estimated durations)
  • Breakdown by sentiment
"""

import discord
from discord.ext import commands
from db.summaries import get_guild_stats, get_guild_summaries


def _format_duration(total_seconds: float) -> str:
    """Convert seconds into a human-readable string like '3 h 24 min'."""
    total_seconds = int(total_seconds)
    hours, remainder = divmod(total_seconds, 3600)
    minutes = remainder // 60
    if hours > 0 and minutes > 0:
        return f"{hours} h {minutes} min"
    if hours > 0:
        return f"{hours} h"
    if minutes > 0:
        return f"{minutes} min"
    return f"{total_seconds} sec"


def _sentiment_bar(counts: dict[str, int], total: int) -> str:
    """Render a compact emoji bar showing the sentiment distribution."""
    if total == 0:
        return "—"
    icons = {"positive": "🟢", "neutral": "🟡", "negative": "🔴"}
    parts = []
    for sentiment, icon in icons.items():
        n = counts.get(sentiment, 0)
        if n:
            parts.append(f"{icon} {sentiment.capitalize()} **{n}**")
    return "  ·  ".join(parts) if parts else "—"


# --------------------------------------------------------------------- #
# Cog                                                                    #
# --------------------------------------------------------------------- #

class Stats(commands.Cog):
    """Cog that provides the /stats slash command."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(
        name="stats",
        description="Show total meetings summarized and hours of audio processed in this server.",
    )
    async def stats(self, ctx: commands.Context):
        """
        Fetch aggregate statistics for the current guild and display them
        as a rich Discord embed.
        """
        if ctx.guild is None:
            await ctx.send(
                "⚠️ This command can only be used inside a server.", ephemeral=True
            )
            return

        await ctx.defer(ephemeral=False)

        # Parallel fetch: aggregate stats + recent records for sentiment breakdown
        stats = await get_guild_stats(ctx.guild.id)
        records = await get_guild_summaries(ctx.guild.id, limit=1000)

        total_meetings = stats["total_meetings"]
        total_seconds = stats["total_seconds"]
        timed_meetings = stats["timed_meetings"]

        # ---- No data yet ------------------------------------------------
        if total_meetings == 0:
            embed = discord.Embed(
                title="📊 Server Stats",
                description=(
                    "No meetings have been summarized in this server yet.\n"
                    "Use `/summarize` to get started!"
                ),
                color=discord.Color.orange(),
            )
            await ctx.send(embed=embed)
            return

        # ---- Sentiment breakdown ----------------------------------------
        sentiment_counts: dict[str, int] = {}
        for r in records:
            sentiment_counts[r.sentiment] = sentiment_counts.get(r.sentiment, 0) + 1

        # ---- Build embed ------------------------------------------------
        embed = discord.Embed(
            title=f"📊 {ctx.guild.name} — Meeting Stats",
            color=discord.Color.blurple(),
        )

        # Total meetings
        embed.add_field(
            name="🗂️ Total Meetings Summarized",
            value=f"**{total_meetings}**",
            inline=True,
        )

        # Audio processed
        if timed_meetings > 0:
            duration_str = _format_duration(total_seconds)
            audio_value = f"**{duration_str}**\n_{timed_meetings} of {total_meetings} meetings timed_"
        else:
            audio_value = "_Duration data not yet available._\n_New summaries will be tracked automatically._"

        embed.add_field(
            name="🎙️ Audio Processed",
            value=audio_value,
            inline=True,
        )

        # Blank spacer to force next field onto a new row
        embed.add_field(name="\u200b", value="\u200b", inline=True)

        # Sentiment breakdown
        embed.add_field(
            name="🎭 Meeting Mood Breakdown",
            value=_sentiment_bar(sentiment_counts, total_meetings),
            inline=False,
        )

        embed.set_footer(text=f"Stats for {ctx.guild.name} · Use /history to browse past meetings")
        embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Stats(bot))
