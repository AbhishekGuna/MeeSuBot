import mimetypes
from config import SUPPORTED_FILE_TYPES, MAX_FILE_SIZE , GEMINI_MODEL
from google.genai import types
import asyncio

def validate_file(filename: str, file_size: int) -> tuple[bool, str]:
     # Check file type
    if not any(filename.endswith(ext) for ext in SUPPORTED_FILE_TYPES):
        return False, "Unsupported file type. Please upload an audio file (.mp3, .mp4, .wav) or a text file (.txt)."
    
    # Check file size
    if file_size > MAX_FILE_SIZE:
        return False, f"File size exceeds the limit of {MAX_FILE_SIZE} bytes."

    return True, "File is valid."


async def process_file_content(filename: str,file_content: bytes,client) -> str:

    # Text files
    if filename.endswith(".txt"):
        return file_content.decode("utf-8", errors="ignore")

    # Audio/video files
    if filename.endswith((".mp3", ".mp4", ".wav", ".m4a")):
        try:
            mime_type, _ = mimetypes.guess_type(filename)

            # fallback if mimetype detection fails
            if mime_type is None:
                mime_type = "audio/mpeg"

            response = await asyncio.to_thread(
                client.models.generate_content,
                model=GEMINI_MODEL,
                contents=[
                    types.Part.from_bytes(
                        data=file_content,
                        mime_type=mime_type
                    ),
                    "Transcribe this audio accurately."
                ]
            )

            return response.text or "No transcription returned."

        except Exception as e:
            return f"An error occurred during transcription: {e}"

    return "Unsupported file type."