"""
DebateX — Prove the AI Works with Any Topic
===========================================
Simulates pulling a wild, unscripted topic from the database
and having the AI generate a debate argument for it.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.debate_agent import build_argument_prompt, generate_argument_with_model
from models.schemas import DebateState, AgentProfile, Persona, Strategy
import asyncio

async def test_random_topic():
    # 1. Imagine we queried: SELECT topic FROM debates ORDER BY RAND() LIMIT 1
    # Let's use a completely weird, unscripted topic to prove dynamic generation works.
    db_topic_statement = "Time travel would actually just cause everyone to get stuck in traffic."
    
    print("=" * 60)
    print(f"📥 Querying database for a random topic...")
    print(f"🎯 TOPIC FROM DB : \"{db_topic_statement}\"")
    print("=" * 60)

    # 2. Build our agent profile
    agent = AgentProfile(
        agent_id=1,
        name="Dr. Paradox",
        persona=Persona.SCIENTIST,
        aggression_level=0.7,
        logic_weight=0.9,
        emotion_weight=0.1,
        evidence_preference=0.8
    )

    opponent = AgentProfile(
        agent_id=2, 
        name="Marty",
        persona=Persona.COMEDIAN,
        aggression_level=0.5, logic_weight=0.5, emotion_weight=0.5, evidence_preference=0.5
    )

    # 3. Create the debate state
    state = DebateState(
        topic=db_topic_statement,
        round_number=1,
        total_rounds=3,
        agent_profile=agent,
        opponent_profile=opponent,
        stance="PRO"
    )

    # 4. We want a rigorous scientific argument for this ridiculous premise
    strategy = Strategy.LOGICAL_ARGUMENT

    print(f"🤖 AGENT        : {agent.name} (Persona: {agent.persona.value})")
    print(f"⚔️  STANCE       : PRO")
    print(f"🧠 STRATEGY     : {strategy.value}")
    print("=" * 60)
    print("Generating argument via DebateX AI Pipeline...\n")

    # 5. Generate!
    prompt = build_argument_prompt(state, strategy)
    argument = await generate_argument_with_model(prompt)

    print("🎙️ ARGUMENT GENERATED:")
    print("-" * 60)
    print(argument)
    print("-" * 60)

if __name__ == "__main__":
    asyncio.run(test_random_topic())
