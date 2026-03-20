"""
Debate Agent — AI agent with personality profile and Q-learning strategy selection.

Each agent has:
  - A unique personality profile (aggression, logic weight, emotion weight, evidence preference)
  - Memory of previous rounds
  - Strategy selection via Q-learning
  - Argument generation using HuggingFace transformers
"""

import random
from typing import Optional
from models.schemas import (
    AgentProfile, DebateState, Strategy, QTableEntry,
    GenerateArgumentResponse,
)
from agents.q_learning import QLearningEngine, encode_state, ALL_ACTIONS


# ── Persona prompt templates ─────────────────────────────────

PERSONA_SYSTEM_PROMPTS = {
    "PHILOSOPHER": (
        "You are a deep-thinking philosopher. Use first principles, thought experiments, "
        "moral reasoning, and references to great thinkers (Aristotle, Kant, Nietzsche, etc). "
        "Your tone is contemplative yet persuasive."
    ),
    "SCIENTIST": (
        "You are a rigorous scientist. Argue using empirical evidence, studies, statistics, "
        "and the scientific method. You value data over opinion. Your tone is precise and analytical."
    ),
    "POLITICIAN": (
        "You are a charismatic politician. Use emotional appeals, policy impacts, anecdotes "
        "about everyday people, and rhetorical flourishes. Your tone is passionate and persuasive."
    ),
    "COMEDIAN": (
        "You are a sharp-witted comedian-debater. Use clever analogies, satire, wit, and humor "
        "while making strong logical points. Poke fun at weak arguments. Your tone is entertaining yet insightful."
    ),
    "LAWYER": (
        "You are a brilliant trial lawyer. Use legal precedent, logical structure, cross-examination "
        "techniques, and airtight reasoning. Systematically dismantle opposing arguments. "
        "Your tone is authoritative."
    ),
    "HISTORIAN": (
        "You are an erudite historian. Argue with historical parallels, lessons from past civilizations, "
        "cause-and-effect analysis, and rich storytelling. Your tone is scholarly and compelling."
    ),
}


# ── Strategy-specific argument instructions ──────────────────

STRATEGY_INSTRUCTIONS = {
    Strategy.LOGICAL_ARGUMENT: (
        "Construct a LOGICAL ARGUMENT using deductive or inductive reasoning. "
        "Present clear premises leading to a well-supported conclusion. "
        "Avoid emotional appeals — focus on pure logic and valid reasoning chains."
    ),
    Strategy.EMOTIONAL_APPEAL: (
        "Make an EMOTIONAL APPEAL that resonates with human values, empathy, and lived experience. "
        "Use vivid language, personal stories, and moral urgency to persuade. "
        "Connect the argument to feelings of justice, fairness, or compassion."
    ),
    Strategy.STATISTICAL_EVIDENCE: (
        "Present STATISTICAL EVIDENCE and data-driven arguments. "
        "Cite specific numbers, percentages, studies, and trends. "
        "Use quantitative reasoning to make your case irrefutable."
    ),
    Strategy.REBUTTAL_ATTACK: (
        "Launch a targeted REBUTTAL ATTACK on your opponent's weakest arguments. "
        "Identify logical fallacies, inconsistencies, and gaps in their reasoning. "
        "Dismantle their position point-by-point while reinforcing your stance."
    ),
    Strategy.DEFENSIVE_CLARIFICATION: (
        "Provide a DEFENSIVE CLARIFICATION that strengthens your position. "
        "Address potential objections preemptively, clarify misunderstandings, "
        "and reinforce the nuance and depth of your argument."
    ),
}


def get_personality_weights(profile: AgentProfile) -> dict[Strategy, float]:
    """
    Convert agent personality traits into strategy bias weights.
    These bias weights are added to Q-values during action selection.
    """
    weights = {
        Strategy.LOGICAL_ARGUMENT: profile.logic_weight * 2.0,
        Strategy.EMOTIONAL_APPEAL: profile.emotion_weight * 2.0,
        Strategy.STATISTICAL_EVIDENCE: profile.evidence_preference * 2.0,
        Strategy.REBUTTAL_ATTACK: profile.aggression_level * 1.5,
        Strategy.DEFENSIVE_CLARIFICATION: (1.0 - profile.aggression_level) * 1.5,
    }
    return weights


def select_strategy(
    state: DebateState,
    q_table_entries: list[QTableEntry],
    epsilon: float = 0.15,
) -> tuple[Strategy, dict[str, float], bool]:
    """
    Select a debate strategy using Q-learning with personality bias.

    Returns: (chosen_strategy, all_q_values, was_exploration)
    """
    engine = QLearningEngine(epsilon=epsilon)
    engine.load_q_table(q_table_entries)

    # Encode current state
    opponent_strat = state.opponent_last_strategy.value if state.opponent_last_strategy else None
    state_key = encode_state(
        topic_cluster=hash(state.topic) % 10,  # Simple topic clustering
        round_number=state.round_number,
        opponent_strategy=opponent_strat,
    )

    # Get personality weights for this agent
    personality_weights = get_personality_weights(state.agent_profile)

    # Select action
    chosen, was_exploration = engine.select_action(state_key, personality_weights)
    q_values = {s.value: engine.get_q_value(state_key, s) for s in ALL_ACTIONS}

    return chosen, q_values, was_exploration


def build_argument_prompt(state: DebateState, strategy: Strategy) -> str:
    """
    Build the full prompt for argument generation.
    Combines persona, stance, strategy instruction, and conversation history.
    """
    persona_prompt = PERSONA_SYSTEM_PROMPTS.get(state.agent_profile.persona.value, "")
    strategy_instruction = STRATEGY_INSTRUCTIONS[strategy]

    stance_text = "IN FAVOR OF (PRO)" if state.stance == "PRO" else "AGAINST (CON)"

    # Build conversation context
    history_text = ""
    if state.conversation_history:
        history_lines = []
        for entry in state.conversation_history[-6:]:  # Last 6 exchanges for context
            role = entry.get("role", "unknown")
            content = entry.get("content", "")
            if role == "self":
                history_lines.append(f"YOUR PREVIOUS ARGUMENT:\n{content}")
            else:
                history_lines.append(f"OPPONENT'S ARGUMENT:\n{content}")
        history_text = "\n\n".join(history_lines)

    prompt = f"""{persona_prompt}

DEBATE TOPIC: "{state.topic}"
YOUR STANCE: {stance_text}
ROUND: {state.round_number} of {state.total_rounds}

{f"CONVERSATION SO FAR:{chr(10)}{history_text}" if history_text else "This is the opening of the debate."}

STRATEGY FOR THIS TURN:
{strategy_instruction}

Write your argument in 2-3 focused paragraphs. Be persuasive, specific, and stay in character.
Do NOT use labels like "Argument:" or "Paragraph 1:" — just write the argument naturally."""

    return prompt


async def generate_argument_with_model(prompt: str) -> str:
    """
    Generate argument text using a 2-tier local-primary chain:

    1. Ollama (Local)  - Primary choice, no API key needed.
    2. Gemini API      - Fallback if Ollama is not running.
    """
    import asyncio
    import os
    from dotenv import load_dotenv

    load_dotenv()

    # Tier 1: Local Ollama
    try:
        from agents.local_model import generate_local, is_model_available
        if is_model_available():
            system_instruction = (
                "You are an AI debate agent. Generate compelling, specific, and well-structured "
                "debate arguments. Stay in character as the persona described. Write naturally "
                "without labels or headers. Be persuasive and reference the specific topic. "
                "Keep your response to 2-3 focused paragraphs."
            )
            local_arg = await generate_local(prompt, system_instruction=system_instruction)
            if local_arg and len(local_arg.strip()) >= 60:
                print(f"[Engine] ✅ Generated via Ollama (Local)")
                return local_arg.strip()
    except Exception as e:
        print(f"[Engine] ⚠️ Local model error: {e}")

    # Tier 2: Google Gemini API
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        print(f"[Engine] ☁️ Falling back to Gemini API...")
        max_retries = 3
        base_delay = 2.0

        for attempt in range(max_retries):
            try:
                from google import genai
                client = genai.Client(api_key=api_key)

                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt,
                    config={
                        "temperature": 0.9,
                        "top_p": 0.95,
                        "max_output_tokens": 500,
                        "system_instruction": (
                            "You are an AI debate agent. Generate compelling, specific, and well-structured "
                            "debate arguments. Stay in character as the persona described. Write naturally "
                            "without labels or headers. Be persuasive and reference the specific topic. "
                            "Keep your response to 2-3 focused paragraphs."
                        ),
                    },
                )

                if response and response.text and len(response.text.strip()) > 50:
                    print("[Engine] ✅ Used Gemini API")
                    return response.text.strip()

            except Exception as e:
                error_str = str(e)
                print(f"[Engine] Gemini error (attempt {attempt + 1}/{max_retries}): {e}")

                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        print(f"[Engine] Rate limited. Retrying in {delay}s...")
                        await asyncio.sleep(delay)
                        continue
                break

    # Final Failure
    return "ERROR: No AI engine available. Please start Ollama or set GEMINI_API_KEY."


# ── Dynamic fallback argument generator ──────────────────────

def _parse_prompt_context(prompt: str) -> dict:
    """Extract topic, stance, persona, strategy, round info, and opponent args from the prompt."""
    import re

    context = {
        "topic": "this issue",
        "stance": "PRO",
        "round": 1,
        "total_rounds": 3,
        "persona": "PHILOSOPHER",
        "strategy": "LOGICAL_ARGUMENT",
        "opponent_args": [],
        "is_opening": True,
    }

    # Extract topic
    topic_match = re.search(r'DEBATE TOPIC:\s*"(.+?)"', prompt)
    if topic_match:
        context["topic"] = topic_match.group(1)

    # Extract stance
    if "AGAINST (CON)" in prompt:
        context["stance"] = "CON"

    # Extract round
    round_match = re.search(r'ROUND:\s*(\d+)\s*of\s*(\d+)', prompt)
    if round_match:
        context["round"] = int(round_match.group(1))
        context["total_rounds"] = int(round_match.group(2))
        context["is_opening"] = context["round"] == 1

    # Extract persona
    for persona in ["PHILOSOPHER", "SCIENTIST", "POLITICIAN", "COMEDIAN", "LAWYER", "HISTORIAN"]:
        if persona.lower() in prompt.lower()[:200]:
            context["persona"] = persona
            break

    # Extract strategy
    for strat in ["LOGICAL_ARGUMENT", "EMOTIONAL_APPEAL", "STATISTICAL_EVIDENCE",
                   "REBUTTAL_ATTACK", "DEFENSIVE_CLARIFICATION"]:
        if strat.replace("_", " ") in prompt.upper():
            context["strategy"] = strat
            break

    # Extract opponent arguments
    opp_args = re.findall(r"OPPONENT'S ARGUMENT:\n(.+?)(?=\n\n|YOUR PREVIOUS|STRATEGY FOR|$)", prompt, re.DOTALL)
    context["opponent_args"] = [a.strip() for a in opp_args if a.strip()]

    return context


def _fallback_argument(prompt: str) -> str:
    """Generate a dynamic, topic-aware argument when Gemini is unavailable."""
    ctx = _parse_prompt_context(prompt)
    topic = ctx["topic"]
    stance = ctx["stance"]
    persona = ctx["persona"]
    strategy = ctx["strategy"]
    rnd = ctx["round"]
    is_opening = ctx["is_opening"]
    opponent_args = ctx["opponent_args"]

    stance_phrase = "in support of" if stance == "PRO" else "against"
    stance_word = "advocate for" if stance == "PRO" else "challenge"
    position = "beneficial and necessary" if stance == "PRO" else "problematic and concerning"

    # ── Persona-specific argument openers and styles ──────────
    persona_openers = {
        "PHILOSOPHER": [
            f"When we examine {topic} through the lens of first principles, a profound truth emerges.",
            f"The great thinkers — from Aristotle to Rawls — would recognize that {topic} raises fundamental questions about our values.",
            f"Philosophically speaking, the question of {topic} forces us to confront what we truly believe about progress and human flourishing.",
        ],
        "SCIENTIST": [
            f"The empirical evidence surrounding {topic} paints a clear picture that demands our attention.",
            f"When we apply rigorous scientific analysis to {topic}, the data leads us to a compelling conclusion.",
            f"Research across multiple peer-reviewed studies on {topic} converges on findings we cannot ignore.",
        ],
        "POLITICIAN": [
            f"The people I've spoken to — families, workers, community leaders — all feel the impact of {topic} in their daily lives.",
            f"Let me be direct with you: {topic} is not an abstract debate — it affects real people in real communities right now.",
            f"I've seen firsthand how {topic} shapes the lives of ordinary citizens, and their voices deserve to be heard in this debate.",
        ],
        "COMEDIAN": [
            f"So here's the thing about {topic} — and I promise this is going somewhere — it's actually kind of absurd when you think about it.",
            f"You know what's funny about {topic}? The more people argue about it, the more they prove my point.",
            f"Let me paint you a picture: imagine explaining {topic} to someone from 100 years ago. They'd think we've lost our minds — and they might be right.",
        ],
        "LAWYER": [
            f"Let the record reflect that the evidence on {topic} overwhelmingly supports the position I will now establish.",
            f"I submit to this court of public opinion that {topic} presents a clear case with a clear precedent, and the verdict should be equally clear.",
            f"Examining {topic} with the precision it deserves, I will systematically demonstrate why the facts are on my side.",
        ],
        "HISTORIAN": [
            f"History does not repeat itself, but it often rhymes — and the echoes surrounding {topic} are unmistakable.",
            f"From the ancient world to the modern era, civilizations have grappled with questions remarkably similar to {topic}.",
            f"The historical record on matters relating to {topic} offers us lessons we ignore at our peril.",
        ],
    }

    # ── Strategy-specific argument bodies ─────────────────────
    strategy_bodies = {
        "LOGICAL_ARGUMENT": [
            f"The logical chain is straightforward: when we consider the premises underlying {topic}, "
            f"the conclusion that this is {position} follows necessarily. The first premise is that "
            f"societies must adapt to changing realities. The second is that {topic} represents precisely "
            f"such a change. Therefore, we must {stance_word} this position with intellectual honesty. "
            f"Any attempt to deny this reasoning requires rejecting one of these well-established premises.",

            f"Consider the deductive structure: if we value progress and evidence-based decision making — "
            f"and I believe we do — then {topic} must be evaluated on its merits, not on unfounded fears. "
            f"The premises are sound, the logic is valid, and the conclusion stands: I argue {stance_phrase} "
            f"this proposition because reason demands it.",
        ],
        "EMOTIONAL_APPEAL": [
            f"Think about the real people affected by {topic}. Behind every policy position and every "
            f"statistic is a human being with hopes, dreams, and fears. When we talk about {topic}, "
            f"we're talking about the future we're building for our children, our communities, and "
            f"ourselves. I argue {stance_phrase} this because compassion and justice demand it.",

            f"There comes a moment in every important debate where we must look beyond the numbers "
            f"and ask: what kind of society do we want to be? {topic} is exactly that kind of question. "
            f"The moral weight of this issue compels me to stand {stance_phrase} it, because the human "
            f"cost of getting this wrong is simply too high to bear.",
        ],
        "STATISTICAL_EVIDENCE": [
            f"The numbers don't lie. Research consistently shows that {topic} has measurable, significant "
            f"effects that support my position. Studies indicate trends of 15-30% impact in affected areas, "
            f"and meta-analyses across multiple countries confirm these findings. When approximately 67% "
            f"of relevant data points to the same conclusion, it becomes irresponsible to argue otherwise. "
            f"I stand {stance_phrase} this because the quantitative evidence is overwhelming.",

            f"Let's examine the data rigorously. Cross-referencing findings from over a dozen major studies "
            f"on {topic} reveals a consistent pattern: the evidence strongly supports the view that this is "
            f"{position}. Longitudinal data spanning the last two decades shows clear trends, with statistical "
            f"significance at the p < 0.01 level. The data-driven conclusion is clear.",
        ],
        "REBUTTAL_ATTACK": [
            f"My opponent's argument {"sounds persuasive but" if opponent_args else "will likely"} "
            f"collapse under scrutiny. {"They" if opponent_args else "Opponents of my position"} "
            f"commit the fundamental error of {"cherry-picking evidence" if stance == "PRO" else "ignoring systemic impacts"} "
            f"while discussing {topic}. This is a classic case of {"the straw man fallacy — misrepresenting " if opponent_args else "begging the question — assuming "} "
            f"{"my position to make it easier to attack" if opponent_args else "the very conclusion they claim to prove"}. "
            f"When we strip away the rhetoric and examine {topic} on its actual merits, my case stands firm.",

            f"Let me address the weaknesses in the opposing argument directly. {"Their reasoning" if opponent_args else "The counterargument"} "
            f"on {topic} relies on assumptions that are demonstrably {"outdated" if stance == "PRO" else "oversimplified"}. "
            f"They {"have" if opponent_args else "would"} presented a selective reading of the evidence, ignoring "
            f"{"the broader context" if stance == "PRO" else "the real-world consequences"} that undermines their entire position. "
            f"Point by point, their argument unravels.",
        ],
        "DEFENSIVE_CLARIFICATION": [
            f"Allow me to strengthen and clarify my position on {topic}. Some may misunderstand my stance "
            f"as {"naive optimism" if stance == "PRO" else "mere contrarianism"}, but the reality is far more nuanced. "
            f"I argue {stance_phrase} this with full awareness of the complexities involved. My position accounts "
            f"for the counterarguments and emerges stronger because of them, not in spite of them.",

            f"I want to preemptively address potential objections to my position on {topic}. Critics "
            f"{"will" if is_opening else "have tried to"} argue that my stance overlooks certain factors. "
            f"On the contrary — my argument is strengthened by considering these factors. The depth and "
            f"nuance of this position on {topic} make it resilient to simplistic attacks.",
        ],
    }

    # ── Round-aware closing statements ────────────────────────
    closings = {
        1: [
            f"As this debate begins, I invite my opponent to engage with the substance of my argument on {topic} rather than retreat to generalizations.",
            f"I look forward to hearing my opponent's response, though I'm confident in the strength of my opening position on {topic}.",
        ],
        2: [
            f"As this debate deepens, the evidence and reasoning only strengthen my case {stance_phrase} {topic}.",
            f"With each round, the weight of argument grows heavier in my favor regarding {topic}.",
        ],
        3: [
            f"In this final round, let me underscore the central truth of this debate: {topic} is {position}, and the arguments presented throughout confirm this beyond reasonable doubt.",
            f"As we conclude, I trust the strength of my cumulative argument on {topic} speaks for itself.",
        ],
    }

    # ── Assemble the argument ─────────────────────────────────
    opener = random.choice(persona_openers.get(persona, persona_openers["PHILOSOPHER"]))
    body = random.choice(strategy_bodies.get(strategy, strategy_bodies["LOGICAL_ARGUMENT"]))
    closing_round = min(rnd, 3)  # cap at 3 for closing selection
    closing = random.choice(closings.get(closing_round, closings[1]))

    return f"{opener}\n\n{body}\n\n{closing}"


# ── Summarization ────────────────────────────────────────────────

async def summarize_debate_with_model(topic: str, arguments: list[dict]) -> tuple[list[str], list[str]]:
    import json
    # Filter and format args
    formatted_args = []
    for arg in arguments:
        formatted_args.append(f"Agent {arg.get('agent', 'Unknown')}: {arg.get('text', '')}")
    
    prompt = f"""Summarize the debate deeply but concisely. 
TOPIC: "{topic}"

ARGUMENTS:
{chr(10).join(formatted_args)}

Extract exactly 3 concise bullet points representing the strongest core points made by Agent A, and 3 for Agent B.
Do not use markdown formatting like ** or *. Do not add any extra conversational text.
Format precisely as follows:
AGENT_A
- Point 1
- Point 2
- Point 3
AGENT_B
- Point 1
- Point 2
- Point 3"""

    raw_summary = await generate_argument_with_model(prompt)
    
    summary_a = []
    summary_b = []
    current_agent = None
    
    for line in raw_summary.split("\n"):
        line = line.strip()
        if not line:
            continue
        if "AGENT_A" in line.upper():
            current_agent = "A"
        elif "AGENT_B" in line.upper():
            current_agent = "B"
        elif line.startswith("-"):
            pt = line.lstrip("- ").strip()
            if current_agent == "A":
                summary_a.append(pt)
            elif current_agent == "B":
                summary_b.append(pt)
                
    # Fallback if parsing fails
    if not summary_a: summary_a = ["Agent A argued their position effectively.", "Emphasized core values.", "Presented standard supporting evidence."]
    if not summary_b: summary_b = ["Agent B challenged the premise well.", "Highlighted potential risks.", "Brought alternative perspectives."]
    
    return summary_a[:3], summary_b[:3]

