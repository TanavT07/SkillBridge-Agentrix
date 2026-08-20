import json
import logging
import os
from typing import Any, Dict, Optional, Type
from pydantic import BaseModel
from openai import AsyncOpenAI
from dotenv import load_dotenv  # Add this import

# Tell Python to load the secrets from the .env file
load_dotenv()

logger = logging.getLogger("skillbridge.agents.llm_client")

# Initialize OpenAI async client to use Gemini via compatibility bridge
# Requires GEMINI_API_KEY set in environment or .env
_api_key = os.getenv("GEMINI_API_KEY", "dummy_key_to_allow_import")
client = AsyncOpenAI(
    api_key=_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

async def call_llm(
    system_prompt: str,
    user_prompt: str,
    schema: Optional[Type[BaseModel]] = None,
    model: str = "gemini-3.6-flash",
    temperature: float = 0.2,
) -> Dict[str, Any]:
    """
    Call the LLM with a system prompt and user prompt, enforcing JSON output.
    
    Args:
        system_prompt: Instructions for the LLM.
        user_prompt: The input data or task description.
        schema: Optional Pydantic model to validate the JSON response against.
        model: Model name to use (defaults to gemini-2.5-flash).
        temperature: Controls randomness (lower is more deterministic).
        
    Returns:
        A dictionary containing the parsed JSON response.
        
    Raises:
        Exception: If the API call fails or the output cannot be parsed/validated.
    """
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content
        if not content:
            raise ValueError("LLM returned empty response")

        # Parse JSON
        parsed_data = json.loads(content)

        # Validate against schema if provided
        if schema:
            validated_data = schema(**parsed_data)
            return validated_data.model_dump()
        
        return parsed_data

    except Exception as e:
        logger.error(f"Error calling LLM or parsing response: {e}")
        raise
