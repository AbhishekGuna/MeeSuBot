import discord
from discord.ext import commands
from config import DISCORD_MESSAGE_LIMIT
from utils import get_ai_response

cogs_list = []

class AskGemini(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name='askgemini', help='Ask a question to Gemini AI')
    async def ask_gemini(self, ctx:commands.Context, *, question: str):
        # thinking
        await ctx.defer()

        try:
            response = await get_ai_response(question)
            if len(response) > DISCORD_MESSAGE_LIMIT:
                response = response[:DISCORD_MESSAGE_LIMIT - 3] + "..."
            await ctx.send(response)
        except Exception as e:
            await ctx.send(f"An error occurred while processing your request: {e}")


async def setup(bot):
    await bot.add_cog(AskGemini(bot))
    cogs_list.append("askgemini")