import json
import logging
from fastapi import HTTPException
from google.genai import types
from google.genai.errors import APIError
from database.schemas import TodoCreate
from llm.config import LLM_MODEL, llm_client

logger = logging.getLogger(__name__)


async def _call_gemini(
    system_prompt: str, 
    user_prompt: str, 
    max_tokens: int = 500,
    response_mime_type: str | None = None,
    response_schema: any = None
) -> str:
    """
    Central gateway function for all Gemini API communications.
    """
    try:
        response = await llm_client.aio.models.generate_content(
            model=LLM_MODEL,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=max_tokens,
                # New parameters added here:
                response_mime_type=response_mime_type,
                response_schema=response_schema,
            ),
        )
        return response.text.strip() if response.text else ""

    except APIError as e:
        logger.error(f"Google Gemini API error: {e}")
        # Handle specific error status codes (e.g., rate limits)
        if getattr(e, "code", None) == 429:
            raise HTTPException(
                status_code=429,
                detail="The AI service is busy right now. Please try again in a moment.",
            )
        raise HTTPException(
            status_code=502,
            detail=f"The AI service returned an error: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Unexpected error communicating with Gemini API: {e}")
        raise HTTPException(
            status_code=500,
            detail="An internal server error occurred while contacting the AI service.",
        )


async def parse_natural_language_todo(text: str) -> TodoCreate:
    """
    Converts unstructured user text into a structured TodoCreate Pydantic model.
    """
    system_prompt = "You convert a user's freeform sentence into a to-do item."

    raw = await _call_gemini(
        system_prompt, 
        text, 
        max_tokens=200,
        response_mime_type="application/json",
        response_schema=TodoCreate
    )

    # 1. Handle empty responses (can happen if blocked by safety filters)
    if not raw:
        logger.error("AI returned an empty string.")
        raise HTTPException(status_code=502, detail="The AI service returned an unexpected format.")

    # 2. The Markdown Safety Net
    # Strips fences if the model ignored the JSON constraint and wrapped the output
    raw = raw.strip()
    if raw.startswith("```json"):
        raw = raw[7:]
    elif raw.startswith("```"):
        raw = raw[3:]
    if raw.endswith("```"):
        raw = raw[:-3]
    raw = raw.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # 💡 DEBUGGING TIP: If it fails again, check your FastAPI terminal! 
        # This logger will print the EXACT string the AI returned.
        logger.error(f"Model did not return valid JSON. Raw output: {raw!r}")
        raise HTTPException(
            status_code=502, detail="The AI service returned an unexpected format."
        )

    try:
        return TodoCreate(**data)
    except Exception as e:
        logger.error(f"Model JSON didn't match the TodoCreate schema: {data!r} ({e})")
        raise HTTPException(
            status_code=502, detail="The AI service returned data in an unexpected shape."
        )

    
async def generate_description(title: str) -> str:
    """
    Generates a task description based on a given task title.
    """
    system_prompt = (
        "You write a single short, practical to-do description (one "
        "sentence, 25 words or fewer) based on a task title. Respond with "
        "ONLY the description text - no quotes, no preamble, no labels."
    )
    return await _call_gemini(system_prompt, title, max_tokens=100)


async def summarize_todos(todos: list[dict]) -> str:
    """
    Generates a natural-language summary from a list of to-do items.
    """
    if not todos:
        return "You have no active to-dos right now."

    lines = "\n".join(
        f"- {todo['title']}: {todo['description'] or 'no description'}" for todo in todos
    )
    system_prompt = (
        "You are a concise assistant summarizing someone's to-do list. "
        "Write a short 2-4 sentence summary that groups related tasks and "
        "calls out anything that sounds urgent or time-sensitive. Do not "
        "just repeat the list back item by item."
    )
    return await _call_gemini(system_prompt, lines, max_tokens=300)