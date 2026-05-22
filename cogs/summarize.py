import discord
from discord.ext import commands
import time
from config import DISCORD_MESSAGE_LIMIT
from utils import get_ai_response,get_ai_client, validate_file, process_file_content

cogs_list = ["summarize"]

class Summarize(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = get_ai_client()

    @commands.hybrid_command(name="summarize", description="Summarize text or transcribe audio/video files.")
    async def summarize(self, ctx:commands.Context, file:discord.Attachment):

        is_valid, error_msg = validate_file(file.filename, file.size)
        if not is_valid:
            await ctx.send(error_msg, ephemeral=True)
            return
        
        await ctx.defer()

        try:
            file_content = await file.read()
            text = await process_file_content(file.filename, file_content, self.client)

            summary_response = await get_ai_response(f"Summarize the following content:\n\n{text}")
            summary = summary_response or "No summary returned."

            if len(summary) > DISCORD_MESSAGE_LIMIT:
                summary = summary[:DISCORD_MESSAGE_LIMIT - 50] + "\n\n[Content truncated due to length.]"

            await ctx.send(summary)
        except Exception as e:
            await ctx.send(f"An error occurred while processing the file: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Summarize(bot))
    cogs_list.append("summarize")