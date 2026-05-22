from google import genai
from config import GEMINI_API_KEY, GEMINI_MODEL

client = genai.Client(api_key=GEMINI_API_KEY)


async def get_ai_response(text):

    response =  client.models.generate_content(
        model=GEMINI_MODEL,
        contents=text
    )
    return response.text

def get_ai_client():
    return client
