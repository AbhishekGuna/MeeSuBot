import discord
from discord.ext import commands
import time
import json
from config import DISCORD_MESSAGE_LIMIT, GEMINI_MODEL
from utils import get_ai_client, validate_file, process_file_content

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

            summary_response = self.client.models.generate_content(
                model=GEMINI_MODEL,
                contents=f"""You are an expert meeting analyst. Analyze the following meeting transcript and extract structured information.

                Return your response as a valid JSON object with exactly these keys:

                {{
                "tldr": "2-3 sentence plain-English summary of the entire meeting",
                "key_decisions": [
                    "Decision 1 that was made",
                    "Decision 2 that was made"
                ],
                "action_items": [
                    {{
                    "task": "What needs to be done",
                    "owner": "Person's name or 'Unassigned' if not mentioned",
                    "deadline": "Deadline if mentioned or null"
                    }}
                ],
                "open_questions": [
                    "Question that was raised but not resolved"
                ],
                "meeting_sentiment": "positive | neutral | negative",
                "topics_discussed": ["topic1", "topic2"]
                }}

                Rules:
                - Be concise. tldr must be under 60 words.
                - Only include action items explicitly mentioned. Do not invent tasks.
                - If no decisions were made, return an empty array for key_decisions.
                - If no open questions, return an empty array.
                - owner must be a name from the transcript, not a role.
                - Return ONLY the JSON object. No explanation, no markdown, no code fences.

                TRANSCRIPT:
                {text}"""
            )

            result = json.loads(summary_response.text)

            # --- build embed ---
            embed = discord.Embed(
                title="📋 Meeting Summary",
                description=result["tldr"],
                color=discord.Color.blurple()
            )
            embed.add_field(
                name="✅ Decisions made",
                value="\n".join(f"• {d}" for d in result["key_decisions"]) or "None recorded",
                inline=False
            )
            embed.add_field(
                name="📌 Action items",
                value="\n".join(
                    f"• **{a['owner']}** — {a['task']}" +
                    (f" *(by {a['deadline']})*" if a["deadline"] else "")
                    for a in result["action_items"]
                ) or "None assigned",
                inline=False
            )
            embed.add_field(
                name="❓ Open questions",
                value="\n".join(f"• {q}" for q in result["open_questions"]) or "None",
                inline=False
            )
            embed.set_footer(text=f"Mood: {result['meeting_sentiment']} · Topics: {', '.join(result['topics_discussed'])}")


            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"An error occurred while processing the file: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Summarize(bot))
    cogs_list.append("summarize")