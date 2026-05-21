import discord
from discord.ext import commands

cogs_list = []

class Utilities(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name='ping', description='Check the bot\'s latency')
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"Pong! {latency}ms")
        
async def setup(bot):
    await bot.add_cog(Utilities(bot))
    cogs_list.append("utilities")