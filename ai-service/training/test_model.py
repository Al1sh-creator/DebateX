"""
DebateX — Local Model Quick Test
==================================
Tests the fine-tuned debate model with fun topics.

Run AFTER training:
    python training/test_model.py
"""

import sys
from pathlib import Path

# Add parent so we can import agents/
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.local_model import generate_local, is_model_available

TEST_CASES = [
    {
        "prompt": (
            "You are a philosopher debater. "
            'DEBATE TOPIC: "Dogs are better pets than cats". '
            "YOUR STANCE: IN FAVOR OF (PRO). "
            "ROUND: 1 of 3. "
            "STRATEGY: LOGICAL ARGUMENT. "
            "Generate a persuasive 2-3 paragraph debate argument."
        ),
        "label": "Dogs vs Cats | PHILOSOPHER | PRO | LOGICAL",
    },
    {
        "prompt": (
            "You are a comedian debater. "
            'DEBATE TOPIC: "Pineapple belongs on pizza". '
            "YOUR STANCE: AGAINST (CON). "
            "ROUND: 2 of 3. "
            "STRATEGY: EMOTIONAL APPEAL. "
            "Generate a persuasive 2-3 paragraph debate argument."
        ),
        "label": "Pineapple Pizza | COMEDIAN | CON | EMOTIONAL",
    },
    {
        "prompt": (
            "You are a scientist debater. "
            'DEBATE TOPIC: "Ninjas are cooler than pirates". '
            "YOUR STANCE: IN FAVOR OF (PRO). "
            "ROUND: 1 of 3. "
            "STRATEGY: STATISTICAL EVIDENCE. "
            "Generate a persuasive 2-3 paragraph debate argument."
        ),
        "label": "Ninjas vs Pirates | SCIENTIST | PRO | STATS",
    },
    {
        "prompt": (
            "You are a lawyer debater. "
            'DEBATE TOPIC: "Artificial intelligence poses an existential risk to humanity". '
            "YOUR STANCE: IN FAVOR OF (PRO). "
            "ROUND: 3 of 3. "
            "STRATEGY: REBUTTAL ATTACK. "
            "Generate a persuasive 2-3 paragraph debate argument."
        ),
        "label": "AI Risk | LAWYER | PRO | REBUTTAL",
    },
]


def main():
    print("🧪 DebateX Local Model Test\n")

    if not is_model_available():
        print("❌ Model not found. Run: python training/train.py first.")
        return

    print("Loading model...\n")

    for i, case in enumerate(TEST_CASES, 1):
        print(f"{'='*60}")
        print(f"Test {i}: {case['label']}")
        print(f"{'='*60}")

        result = generate_local(case["prompt"])

        if result:
            print(result)
        else:
            print("⚠️  No output generated (model returned None or too short)")

        print()


if __name__ == "__main__":
    main()
