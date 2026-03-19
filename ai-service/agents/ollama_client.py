"""
DebateX — Ollama Local API Client
=================================
Handles interaction with a locally running Ollama instance.
"""

import httpx
import json
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config
OLLAMA_BASE_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_GENERATE_URL = f"{OLLAMA_BASE_URL}/api/generate"
OLLAMA_CHAT_URL = f"{OLLAMA_BASE_URL}/api/chat"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

async def generate_ollama(prompt: str, system_instruction: str = None, max_tokens: int = 500) -> str:
    """
    Generate a response using the local Ollama Chat API.
    
    Args:
        prompt: The user prompt.
        system_instruction: Optional system instruction.
        max_tokens: Maximum tokens to generate.
        
    Returns:
        str: The generated argument, or None if failed.
    """
    messages = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
    
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "num_predict": max_tokens,
            "temperature": 0.7,
            "top_p": 0.9,
        }
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(OLLAMA_CHAT_URL, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                # Extract content from chat response structure
                message = data.get("message", {})
                return message.get("content", "").strip()
            else:
                logger.warning(f"Ollama error: {response.status_code} - {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Failed to connect to Ollama at {OLLAMA_CHAT_URL}: {e}")
        return None

def is_ollama_available() -> bool:
    """Check if Ollama is running locally."""
    import socket
    from urllib.parse import urlparse
    
    try:
        url = urlparse(OLLAMA_BASE_URL)
        host = url.hostname or "localhost"
        port = url.port or 11434
        
        # Check connectivity
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except:
        return False
