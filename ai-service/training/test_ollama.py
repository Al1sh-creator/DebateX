"""
DebateX — Ollama Connectivity Test
===================================
Tests if Ollama is running and can generate a simple response.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.ollama_client import generate_ollama, is_ollama_available

async def main():
    print("🔍 Testing Ollama Connectivity...")
    
    if not is_ollama_available():
        print("❌ Ollama is NOT running on http://localhost:11434")
        print("   Please download it from https://ollama.com and run it.")
        print("   Then run: ollama pull llama3")
        return

    print("✅ Ollama is running!")
    
    test_prompt = "You are a philosopher. DEBATE TOPIC: 'Dogs are better than cats'. Generate a short opening statement."
    print(f"\n🚀 Sending test prompt to Ollama...")
    print(f"   Prompt: {test_prompt}")
    
    result = await generate_ollama(test_prompt, max_tokens=200)
    
    if result:
        print("\n✨ Ollama Response:")
        print("-" * 50)
        print(result)
        print("-" * 50)
        print("\n🎯 Local AI integration is working perfectly!")
    else:
        print("\n❌ Ollama generated no response.")
        print("   Did you pull the model? Try: ollama pull llama3")

if __name__ == "__main__":
    asyncio.run(main())
