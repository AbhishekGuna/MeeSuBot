# MeeSuBot

A Discord bot that intelligently summarizes meeting transcripts and audio/video files using Google's Gemini AI. Perfect for teams who want to capture key decisions, action items, and meeting sentiment without manual note-taking.

## Features

🎙️ **Multi-format Support**
- Transcribe and summarize audio files (MP3, WAV, MP4)
- Process text transcripts directly
- Supports files up to 25MB

📊 **Intelligent Meeting Analysis**
- **TL;DR**: Concise 2-3 sentence summary
- **Key Decisions**: Extract all decisions made
- **Action Items**: Track tasks with owners and deadlines
- **Open Questions**: Capture unresolved discussions
- **Meeting Sentiment**: Analyze overall tone (positive/neutral/negative)
- **Topics Discussed**: Automatically tag conversation themes

💾 **Meeting History**
- Store summaries in a PostgreSQL database
- Browse last 5 summaries with `/history` command
- Interactive pagination through historical records

🤖 **AI Assistant**
- Ask general questions to Gemini AI via Discord
- Contextual responses right in your channel

⏱️ **System Health**
- Check bot latency with `/ping` command

## Commands

| Command | Description | Usage |
|---------|-------------|-------|
| `/summarize <file>` | Summarize a meeting transcript or audio/video file | `/summarize @meeting_transcript.txt` |
| `/history` | View the last 5 meeting summaries in your server | `/history` |
| `/askgemini <question>` | Ask the Gemini AI a question | `/askgemini How do I implement OAuth?` |
| `/ping` | Check bot latency | `/ping` |

## Requirements

- Python 3.12+
- Discord Bot Token
- Google Gemini API Key
- PostgreSQL database

## Setup

### 1. Clone the Repository
```bash
git clone https://github.com/AbhishekGuna/MeeSuBot.git
cd MeeSuBot
```

### 2. Create Virtual Environment
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the project root:

```env
# Discord Configuration
DISCORD_TOKEN=your_discord_bot_token_here

# Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/meesubot
```

**Getting Your Tokens:**
- **Discord Token**: Create a bot at [Discord Developer Portal](https://discord.com/developers/applications)
- **Gemini API Key**: Get it from [Google AI Studio](https://aistudio.google.com/apikey)
- **PostgreSQL**: Set up a local or cloud PostgreSQL instance

### 5. Initialize Database
The bot automatically initializes the database schema on first startup.

### 6. Run the Bot
```bash
python -m __main__
```

The bot will log in and sync commands with your Discord server.

## Project Structure

```
MeeSuBot/
├── __main__.py              # Bot entry point and initialization
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (create this)
├── config/
│   ├── __init__.py
│   └── config.py            # Configuration constants
├── cogs/                    # Discord command modules
│   ├── summarize.py         # Meeting summarization
│   ├── askgemini.py         # AI question answering
│   ├── history.py           # Summary history retrieval
│   └── utilities.py         # Utility commands (ping)
├── db/
│   ├── connection.py        # Database connection management
│   └── summaries.py         # Database operations for summaries
├── models/
│   ├── __init__.py
│   └── summary.py           # SummaryRecord data model
└── utils/
    ├── ai_service.py        # Gemini API integration
    └── file_handler.py      # File processing and validation
```

## Configuration

Key settings in `config/config.py`:

- `MAX_FILE_SIZE`: 25MB (maximum uploadable file size)
- `DISCORD_MESSAGE_LIMIT`: 2000 characters (Discord API limit)
- `SUMMARY_CHARACTER_LIMIT`: 2000 characters
- `SUPPORTED_FILE_TYPES`: `.mp3`, `.mp4`, `.wav`, `.txt`
- `HISTORY_LIMIT`: 5 (last N summaries to display)
- `GEMINI_MODEL`: `gemini-2.5-flash` (configured model)
- `COMMAND_PREFIX`: `!` (for prefix commands)

## Database Schema

The bot uses PostgreSQL with the following key table:

- **summaries**: Stores meeting summaries with:
  - Guild ID, Channel ID, User ID
  - Filename and processing timestamp
  - Structured summary data (decisions, actions, questions, sentiment, topics)

## How It Works

### Summarization Flow
1. User uploads a file to Discord with `/summarize`
2. Bot validates file type and size
3. Audio files are transcribed using Gemini's audio processing
4. Text is sent to Gemini with a structured prompt
5. AI returns JSON with meeting analysis
6. Results are formatted into an embeded Discord message
7. Summary is saved to PostgreSQL database

### History Retrieval
1. User runs `/history` command
2. Bot fetches last 5 summaries from database
3. Creates paginated embeds with navigation buttons
4. Users can navigate between summaries with ◀/▶ buttons
5. View times out after 120 seconds of inactivity

## Development

### Adding a New Command
1. Create a new file in `cogs/` (e.g., `cogs/mycommand.py`)
2. Define a command class extending `commands.Cog`
3. Add `@commands.hybrid_command()` decorator
4. Implement the command logic
5. Add setup function for the cog
6. Bot automatically loads all cogs on startup

### Example Command
```python
from discord.ext import commands

class MyCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.hybrid_command(name="mycommand", description="My custom command")
    async def my_command(self, ctx: commands.Context):
        await ctx.send("Hello!")

async def setup(bot):
    await bot.add_cog(MyCommand(bot))
```

## Dependencies

Key packages used:
- **discord.py 2.7.1**: Discord bot framework
- **google-genai 2.5.0**: Gemini AI API client
- **asyncpg 0.31.0**: Async PostgreSQL driver
- **python-dotenv 1.2.2**: Environment variable management
- **pydantic 2.13.4**: Data validation

See `requirements.txt` for complete list.

## Troubleshooting

### Bot doesn't respond
- Verify Discord token is correct
- Check bot has necessary permissions in your server
- Ensure bot has "Message Content Intent" enabled

### Summarization fails
- Check Gemini API key is valid
- Verify file is in a supported format
- Ensure file is under 25MB
- Check file isn't corrupted

### Database errors
- Verify PostgreSQL is running
- Check DATABASE_URL format is correct
- Ensure database exists and user has permissions

### Commands don't sync
- Restart the bot to resync commands
- Check bot has "application.commands" scope

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests
- Improve documentation

## Contact & Support

For issues, questions, or suggestions, please open an issue on the [GitHub repository](https://github.com/AbhishekGuna/MeeSuBot).

---

**Built with ❤️ using discord.py and Google Gemini AI**
