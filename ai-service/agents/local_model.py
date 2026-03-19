"""
DebateX — Local Model Bridge
============================
Redirects local generation requests to Ollama.
"""

from typing import Optional
from .ollama_client import generate_ollama, is_ollama_available

async def generate_local(prompt: str, system_instruction: str = None, max_new_tokens: int = 500) -> Optional[str]:
    """
    Generate a debate argument using the local Ollama engine.

    Returns:
        str: Generated argument text, or None if Ollama is unavailable.
    """
    if not is_ollama_available():
        return None

    return await generate_ollama(prompt, system_instruction=system_instruction, max_tokens=max_new_tokens)

def is_model_available() -> bool:
    """Check if the local model engine is available."""
    return is_ollama_available()
