import discord
import os
import asyncio
import discord.ext as commands
from config import DISCORD_TOKEN, COMMAND_PREFIX
from .db import connect_db, close_db

class MeeSuBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(command_prefix=COMMAND_PREFIX, intents=intents)

    async def setup_hook(self):
        try:
            await connect_db()
        except Exception as e:
            print(f"Failed to connect to the database: {e}")
            await self.close()
            return

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')

    async def close(self):
        await close_db()
        await super().close()

async def main():
    bot = MeeSuBot()
    await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())