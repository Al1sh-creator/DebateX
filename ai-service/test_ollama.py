import asyncio
import httpx
import os
import sys

# Add the parent directory to sys.path to import agents
sys.path.append(os.getcwd())

from agents.ollama_client import generate_ollama, is_ollama_available

async def test_ollama():
    print("Checking Ollama availability...")
    available = is_ollama_available()
    print(f"Ollama available: {available}")
    
    if available:
        print("Testing generation...")
        prompt = "Explain why debates are important in 2 sentences."
        system = "You are a helpful assistant."
        response = await generate_ollama(prompt, system_instruction=system)
        print(f"Response: {response}")
    else:
        print("Ollama is not running. Please start it to test local generation.")

if __name__ == "__main__":
    asyncio.run(test_ollama())
