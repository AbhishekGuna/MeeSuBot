import os
from dotenv import load_dotenv

load_dotenv()

# Discord
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
COMMAND_PREFIX = "!"

# Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-2.5-flash"

# Database
DATABASE_URL = os.getenv("DATABASE_URL")

# File constraints
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB
DISCORD_MESSAGE_LIMIT = 2000
SUMMARY_CHARACTER_LIMIT = 2000

# Supported file types
SUPPORTED_FILE_TYPES = {".mp3", ".mp4", ".wav", ".txt"}

HISTORY_LIMIT = 5