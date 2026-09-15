from anthropic import AsyncAnthropic
from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-3.6-flash")

llm_client = genai.Client(api_key=GEMINI_API_KEY)



