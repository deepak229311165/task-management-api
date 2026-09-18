import json
import logging
from fastapi import HTTPException
from openai import AsyncOpenAI, APIError, APIResponse
from database.schemas import TodoCreate, TodoList
from llm.config import LLM_MODEL, llm_client
from datetime import datetime, timezone
from typing import Optional 
from zoneinfo import ZoneInfo

USER_TIMEZONE = "Asia/Kolkata"

logger = logging.getLogger(__name__)

SYSTEM_PARSER_PROMPT = """
you are a strict data extraction engine for a task management app
TASK: extract structured to do items from the text inside <user_input> tags
RULES: 
1: TITLE: create clear, concise and action oriented titles (1-10 words). capitalize appropriately
if the user mentions 2 or more tasks then you have to create different tasks for that.
tasks can be differentiated by day or timing or actions.
if the user provides input in hindi or other languages convert it into english and return the title 
2: DESCRIPTION: provide a 1 sentence summary of any extra context, time or details. if multiple tasks then mention them all 
if no extra context exists generate a short logical description 
3: DUE_DATE: if the user mentions any specific date or time (e.g. "tomorrow at 5pm", "on Friday", "in 2 hours", "11 AM"), 
resolve it into an absolute ISO 8601 datetime **in UTC**, and return it in the "due_date" field.
All bare times mentioned by the user (e.g. "1:30 PM", "tomorrow at 5pm") are in the user's LOCAL timezone, 
given in <user_timezone>. Convert them to UTC before returning. 
Use <current_datetime> (already in UTC) as your reference point for resolving relative dates/times.
If no date or time is mentioned, leave "due_date" null.4: STRICT EXTRACTION: rely only on the details provided by the user text. do not invent unrelated appointments or tasks. 
"""


async def _call_openai(
    system_prompt: str, 
    user_prompt: str, 
    max_tokens: int = 500,
    response_format: type | dict | None = None
) -> str:
    """
    Central gateway function for all Openai API communications.
    llm_client should be an instance of openai.AsyncOpenAI
    """
    try:
        kwargs = { 
            "model": LLM_MODEL,
            "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            "max_tokens": max_tokens,
    
        }
        if response_format:
            kwargs["response_format"] = response_format
        response = await llm_client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""

    except APIError as e:
        logger.error(f"OpenAI API error: {e}")
        # Handle specific error status codes (e.g., rate limits)
        if getattr(e, "status_code", None) == 429:
            raise HTTPException(
                status_code=429,
                detail="The AI service is busy right now. Please try again in a moment.",
            )
        raise HTTPException(
            status_code=502,
            detail=f"The AI service returned an error: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Unexpected error communicating with OpenAI API: {e}")
        raise HTTPException(
            status_code=500,
            detail="An internal server error occurred while contacting the AI service.",
        )


async def parse_natural_language_todo(text: str, current_time: Optional[datetime]= None) -> list[TodoCreate]:
    """
    Converts unstructured user text into a structured TodoCreate Pydantic model 
    using OpenAI native structured outputs.
    """
    now_str = datetime.now(timezone.utc).isoformat()
    clean_text = text.strip() if text else ""
    if not clean_text or clean_text.lower() == "string":
        raise HTTPException(
            status_code=400, detail="input cannot be empty. please enter a valid task"
        )
    if current_time is None:
        current_time = datetime.now(timezone.utc)

    try:
        response = await llm_client.beta.chat.completions.parse(
            model = LLM_MODEL,
            messages=[
                { 
                "role": "system",
                "content": SYSTEM_PARSER_PROMPT
            },
            {"role": "user", "content": f"<current_datetime>{now_str}</current_datetime>"f"\n<user_timezone>\n{USER_TIMEZONE}\n</user_timezone>"f"<user_input>\n{clean_text}\n</user_input>"},
            ],
            response_format=TodoList,
            max_tokens=300, 
        )

        parsed_data = response.choices[0].message.parsed
        if not parsed_data or not parsed_data.tasks:
            raise HTTPException(
                status_code=502,
                detail="the AI service failed to parse the task output"
            )
        return parsed_data.tasks

    except APIError as e:
        logger.error(f"openai api error: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"the AI service returned an error: {str(e)}",
        )
    
    except Exception as e:
        logger.error(f"error parsing data with OpenAI: {e}")
        raise HTTPException(
            status_code=500,
            detail="an inner error occurred while contacting the AI service",
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
    return await _call_openai(system_prompt, title, max_tokens=200)


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
        "Write  sentence summary that groups related tasks and "
        "calls out anything that sounds urgent or time-sensitive. Do not "
        "just repeat the list back item by item."
    )
    return await _call_openai(system_prompt, lines, max_tokens=300)