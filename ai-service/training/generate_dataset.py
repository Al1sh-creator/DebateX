"""
DebateX — Synthetic Debate Dataset Generator
=============================================
Generates prompt→argument pairs for fine-tuning flan-t5-base.

For each topic × stance × persona × strategy combination, a structured
debate argument is produced and saved as JSONL.

Run:
    python training/generate_dataset.py
Output:
    training/debate_dataset.jsonl  (~700-900 lines)
"""

import json
import random
import os
from pathlib import Path

# ── Topics (50 fun + serious) ────────────────────────────────

TOPICS = [
    # Fun / Weird
    "Dogs are better pets than cats",
    "Pineapple belongs on pizza",
    "Ninjas are cooler than pirates",
    "Morning people are better than night owls",
    "Cats are better companions than dogs",
    "Coffee is better than tea",
    "Summer is better than winter",
    "Marvel is better than DC",
    "Books are better than movies",
    "Mountains are better than beaches",
    "Android phones are better than iPhones",
    "Introverts make better leaders than extroverts",
    "Chocolate ice cream is better than vanilla",
    "Working from home is better than working in an office",
    "Video games are a legitimate sport",
    "Social media does more harm than good",
    "Zoos should be banned",
    "Space exploration is more important than ocean exploration",
    "Math is more important than art in school",
    "Fast food is an acceptable everyday meal",
    "Aliens definitely exist somewhere in the universe",
    "Time travel would do more harm than good",
    "Robots will eventually replace all human jobs",
    "Living in a city is better than living in the countryside",
    "Online friendships are as real as offline ones",
    "E-books are better than physical books",
    "Homework should be abolished in schools",
    "Streaming services have killed cinema",
    "Renewable energy should completely replace fossil fuels immediately",
    "Universal basic income should be implemented globally",
    # Serious / Debate-classic
    "Artificial intelligence poses an existential risk to humanity",
    "Social media platforms should be held legally responsible for their content",
    "Capital punishment should be abolished worldwide",
    "Genetic engineering of humans should be permitted",
    "Nuclear energy is essential for a sustainable future",
    "Privacy is more important than national security",
    "Climate change is the most urgent crisis of our time",
    "Voting should be compulsory in democracies",
    "Immigration benefits host countries more than it costs them",
    "The internet has done more good than harm to society",
    "Higher education should be free for all",
    "Corporations are more powerful than governments",
    "Animal testing for medical research is justified",
    "Cryptocurrency will replace traditional banking",
    "The global minimum wage should be standardized",
    "Standardized testing is an unfair measure of intelligence",
    "Social safety nets reduce overall economic productivity",
    "Freedom of speech should have limits",
    "Colonization of Mars is a moral imperative",
    "Veganism is the most ethical dietary choice",
]

PERSONAS = ["PHILOSOPHER", "SCIENTIST", "POLITICIAN", "COMEDIAN", "LAWYER", "HISTORIAN"]
STRATEGIES = [
    "LOGICAL_ARGUMENT",
    "EMOTIONAL_APPEAL",
    "STATISTICAL_EVIDENCE",
    "REBUTTAL_ATTACK",
    "DEFENSIVE_CLARIFICATION",
]
STANCES = ["PRO", "CON"]

# ── Argument template banks ──────────────────────────────────

PERSONA_INTROS = {
    "PHILOSOPHER": [
        "From a philosophical standpoint, we must examine the foundational premises at play here.",
        "Aristotle himself recognized that true wisdom begins by questioning assumptions — and on this topic, the assumptions of my opponents are deeply flawed.",
        "Through a Kantian lens, the categorical imperative demands we consider the universal implications of this position.",
        "Plato's allegory of the cave reminds us that appearances can deceive — and nowhere is this truer than in this debate.",
        "At the heart of this question lies a fundamental tension between individual freedom and collective good.",
    ],
    "SCIENTIST": [
        "The peer-reviewed literature on this subject is unambiguous — and it supports my position conclusively.",
        "Science thrives on evidence, not opinion — and the evidence strongly supports the stance I am about to articulate.",
        "When we apply the scientific method rigorously to this question, the data tells a compelling story.",
        "Meta-analyses spanning decades of research consistently demonstrate a clear pattern on this question.",
        "The empirical record here is not a matter of interpretation — it is a matter of measurable, reproducible fact.",
    ],
    "POLITICIAN": [
        "I've spoken to real people — families, workers, students — and they all feel this issue in their daily lives.",
        "The voters I represent didn't send me here to ignore the elephant in the room — and on this topic, the elephant is enormous.",
        "This is not an abstract debate. Behind every statistic is a human being whose life is affected by this decision.",
        "Policy without empathy is engineering without ethics — and today, I argue for the humane path forward.",
        "Let me be direct: the people on the other side of this argument have never had to live with its consequences.",
    ],
    "COMEDIAN": [
        "Okay, let's be honest here — if you squint at this argument from the other side, it gets pretty absurd, pretty fast.",
        "Look, I don't want to be the person who makes everyone laugh while making an airtight logical point, but here we are.",
        "This debate reminded me of a joke — except the punchline is how wrong the other side is.",
        "I'll give credit where it's due: opposing this position takes a special kind of commitment to being incorrect.",
        "Imagine explaining this situation to someone from 200 years ago. They'd think we'd lost the plot — and they'd be right about that, at least.",
    ],
    "LAWYER": [
        "Let the record reflect that the evidence on this matter is overwhelming and uncontested.",
        "I submit to this court of public opinion: the opposing argument fails on three separate grounds — precedent, logic, and consequence.",
        "A case built on assumption is a case built on sand. My argument, by contrast, rests on firm documentary evidence.",
        "Burden of proof rests with those who challenge the status quo — and the other side has conspicuously failed to meet it.",
        "The facts, when examined in their totality rather than selectively, lead to one and only one conclusion.",
    ],
    "HISTORIAN": [
        "History does not repeat itself — but it rhymes with remarkable precision, and the echoes here are unmistakable.",
        "Every civilization that has ignored this lesson has paid a steep price. We would do well to learn from their mistakes.",
        "From ancient Rome to the Industrial Revolution, humanity has faced this crossroads before — and the outcomes speak for themselves.",
        "The long arc of history bends toward the position I am defending today.",
        "Those who forget history are doomed to repeat it — and this debate is a case study in selective historical memory.",
    ],
}

STRATEGY_BODIES = {
    "LOGICAL_ARGUMENT": [
        lambda topic, stance: (
            f"The logical case {'for' if stance == 'PRO' else 'against'} '{topic}' is straightforward when examined clearly. "
            f"Premise one: decisions should be made based on their measurable outcomes. "
            f"Premise two: the outcomes associated with this position are demonstrably {'positive' if stance == 'PRO' else 'negative'}. "
            f"Therefore, the {'adoption' if stance == 'PRO' else 'rejection'} of this position is rationally justified. "
            f"Any attempt to argue otherwise requires rejecting one of these well-established premises — a burden my opponent has not yet met."
        ),
        lambda topic, stance: (
            f"Let us reason carefully. The core question is whether '{topic}' {'benefits' if stance == 'PRO' else 'harms'} those it affects. "
            f"A logical analysis reveals that it {'does' if stance == 'PRO' else 'does not'}, for three reasons: "
            f"first, the causal mechanism is clear and well-understood; "
            f"second, comparable situations have produced consistent results; "
            f"third, the alternatives are demonstrably {'inferior' if stance == 'PRO' else 'superior'}. "
            f"Sound reasoning, not wishful thinking, must guide our position."
        ),
    ],
    "EMOTIONAL_APPEAL": [
        lambda topic, stance: (
            f"We must ask ourselves: what kind of world are we building? "
            f"When it comes to '{topic}', the human stakes could not be higher. "
            f"Real people — with families, fears, and dreams — are affected by this question every single day. "
            f"To {'support' if stance == 'PRO' else 'oppose'} this is to {'stand with' if stance == 'PRO' else 'turn our backs on'} those who need our collective wisdom most. "
            f"The moral weight of this moment demands that we choose the path of {'courage and progress' if stance == 'PRO' else 'caution and compassion'}."
        ),
        lambda topic, stance: (
            f"Imagine the person most affected by this debate. They're not here to argue abstractly — they live with this reality. "
            f"For them, '{topic}' is not a philosophical exercise; it is their daily experience. "
            f"When we {'embrace' if stance == 'PRO' else 'resist'} this position, we are sending a message about our values as a society. "
            f"Let that message be one of {'empathy, progress, and shared humanity' if stance == 'PRO' else 'wisdom, restraint, and genuine care'}."
        ),
    ],
    "STATISTICAL_EVIDENCE": [
        lambda topic, stance: (
            f"The data on '{topic}' is clear and consistent across multiple independent studies. "
            f"Research spanning over a decade shows that this position is {'supported' if stance == 'PRO' else 'undermined'} by the quantitative evidence. "
            f"Surveys consistently show 60-75% of experts align with the {'PRO' if stance == 'PRO' else 'CON'} position. "
            f"Longitudinal studies demonstrate {'positive' if stance == 'PRO' else 'negative'} trends in key metrics over time. "
            f"When the evidence is this consistent, dismissing it requires extraordinary justification."
        ),
        lambda topic, stance: (
            f"Numbers do not lie. When we examine '{topic}' through a quantitative lens: "
            f"meta-analyses of over 50 peer-reviewed studies find statistically significant {'support for' if stance == 'PRO' else 'evidence against'} this position (p < 0.01). "
            f"The effect size is not marginal — it is substantial, with a Cohen's d of approximately 0.7. "
            f"Furthermore, cross-cultural data from 30+ countries shows consistent results, ruling out regional bias. "
            f"This is science, not speculation."
        ),
    ],
    "REBUTTAL_ATTACK": [
        lambda topic, stance: (
            f"My opponent's argument on '{topic}' rests on a fundamental logical fallacy — the straw man. "
            f"They have characterized the {'PRO' if stance == 'PRO' else 'CON'} position as extreme when it is, in fact, moderate and evidence-based. "
            f"Furthermore, their central claim involves a classic correlation-causation error. "
            f"When we strip away the rhetorical misdirection, their argument collapses into unsupported assertion. "
            f"The burden of proof has not been met, and I invite the audience to notice what questions my opponent carefully avoided answering."
        ),
        lambda topic, stance: (
            f"Let me address the weaknesses in my opponent's case directly. "
            f"First, their argument about '{topic}' cherry-picks data while ignoring the broader empirical picture. "
            f"Second, the analogy they relied upon breaks down on close examination — the cases are not comparable. "
            f"Third, their most dramatic claim is sourced from a single study that has not been replicated. "
            f"A position built on selective evidence, flawed analogies, and unreplicated data is not a position — it is a hope dressed up as an argument."
        ),
    ],
    "DEFENSIVE_CLARIFICATION": [
        lambda topic, stance: (
            f"I want to clarify what the {'PRO' if stance == 'PRO' else 'CON'} position on '{topic}' actually entails — because my opponent has mischaracterized it. "
            f"We are not claiming {'the extreme position they suggest' if stance == 'PRO' else 'blind opposition to all nuance'}. "
            f"Rather, our argument is carefully bounded: we {'support' if stance == 'PRO' else 'challenge'} this proposition with full awareness of its complexities, trade-offs, and limits. "
            f"A nuanced position that acknowledges complexity is stronger, not weaker, than an overconfident claim. "
            f"My opponent's apparent dismissal of nuance says more about their approach than mine."
        ),
        lambda topic, stance: (
            f"Before proceeding, I must address a misconception that has crept into this debate. "
            f"Supporters of the {'PRO' if stance == 'PRO' else 'CON'} side on '{topic}' do not ignore the counterarguments — we have grappled with them seriously. "
            f"Our position has been stress-tested against the strongest objections and has emerged stronger, not weaker. "
            f"When critics raise concerns about edge cases, we welcome that — it refines, rather than refutes, our core argument. "
            f"A position that grows stronger under scrutiny is a position worth defending."
        ),
    ],
}

CLOSINGS = [
    lambda topic, stance: f"In conclusion, the case for {'supporting' if stance == 'PRO' else 'opposing'} '{topic}' is robust, evidence-backed, and morally sound.",
    lambda topic, stance: f"The arguments speak clearly: on '{topic}', the {'PRO' if stance == 'PRO' else 'CON'} position is the only defensible one.",
    lambda topic, stance: f"I rest my case. The {'evidence' if random.random() > 0.5 else 'logic'} on '{topic}' is unambiguous — and I trust the audience can see that.",
    lambda topic, stance: f"On '{topic}', the burden of proof has been met. The {'PRO' if stance == 'PRO' else 'CON'} position stands.",
]


def build_prompt(topic: str, stance: str, persona: str, strategy: str, round_num: int = 1) -> str:
    stance_text = "IN FAVOR OF (PRO)" if stance == "PRO" else "AGAINST (CON)"
    return (
        f"You are a {persona.lower()} debater. "
        f"DEBATE TOPIC: \"{topic}\". "
        f"YOUR STANCE: {stance_text}. "
        f"ROUND: {round_num} of 3. "
        f"STRATEGY: {strategy.replace('_', ' ')}. "
        f"Generate a persuasive 2-3 paragraph debate argument."
    )


def build_argument(topic: str, stance: str, persona: str, strategy: str) -> str:
    intro = random.choice(PERSONA_INTROS[persona])
    body_fn = random.choice(STRATEGY_BODIES[strategy])
    body = body_fn(topic, stance)
    closing_fn = random.choice(CLOSINGS)
    closing = closing_fn(topic, stance)
    return f"{intro}\n\n{body}\n\n{closing}"


def generate_dataset(output_path: str, samples_per_combo: int = 1) -> int:
    records = []
    for topic in TOPICS:
        for stance in STANCES:
            for persona in PERSONAS:
                for strategy in STRATEGIES:
                    for _ in range(samples_per_combo):
                        round_num = random.randint(1, 3)
                        prompt = build_prompt(topic, stance, persona, strategy, round_num)
                        argument = build_argument(topic, stance, persona, strategy)
                        records.append({
                            "prompt": prompt,
                            "completion": argument,
                            "metadata": {
                                "topic": topic,
                                "stance": stance,
                                "persona": persona,
                                "strategy": strategy,
                                "round": round_num,
                            }
                        })

    random.shuffle(records)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return len(records)


if __name__ == "__main__":
    script_dir = Path(__file__).parent
    output_path = str(script_dir / "debate_dataset.jsonl")

    print("🎯 Generating DebateX training dataset...")
    print(f"   Topics: {len(TOPICS)}")
    print(f"   Personas: {len(PERSONAS)}")
    print(f"   Strategies: {len(STRATEGIES)}")
    print(f"   Stances: {len(STANCES)}")
    print(f"   Total combos: {len(TOPICS) * len(PERSONAS) * len(STRATEGIES) * len(STANCES)}")

    count = generate_dataset(output_path)

    print(f"\n✅ Generated {count} training samples → {output_path}")
    print("\n📋 Sample (first record):")
    with open(output_path, "r", encoding="utf-8") as f:
        sample = json.loads(f.readline())
        print(f"  TOPIC: {sample['metadata']['topic']}")
        print(f"  PERSONA: {sample['metadata']['persona']} | STANCE: {sample['metadata']['stance']} | STRATEGY: {sample['metadata']['strategy']}")
        print(f"  PROMPT: {sample['prompt'][:100]}...")
        print(f"  ARGUMENT: {sample['completion'][:200]}...")
