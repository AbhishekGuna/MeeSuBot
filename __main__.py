import discord
import os
import asyncio
import discord.ext.commands as commands
from config import DISCORD_TOKEN, COMMAND_PREFIX
from db.connection import connect_db, close_db
from db.summaries import init_db

class MeeSuBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(command_prefix=COMMAND_PREFIX, intents=intents)

    async def setup_hook(self):

        cogs_dir = os.path.join(os.path.dirname(__file__), "cogs")

        for filename in os.listdir(cogs_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                cog_name = filename[:-3]
                try:
                    await self.load_extension(f"cogs.{cog_name}")
                    print(f"Loaded cog: {cog_name}")
                except Exception as e:
                    print(f"Failed to load cog {cog_name}: {e}")


        try:
            await connect_db()
            await init_db()
        except Exception as e:
            print(f"Failed to connect to the database: {e}")
            await self.close()
            return

    async def on_ready(self):
        try:
            await self.tree.sync()
        except Exception as e:
            print(f"Failed to sync application tree: {e}")
            return
        print(f'Logged in as {self.user} (ID: {self.user.id})')

    async def close(self):
        await close_db()
        await super().close()

async def main():
    bot = MeeSuBot()
    try:
        await bot.start(DISCORD_TOKEN)
    finally:
        await bot.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped manually.")