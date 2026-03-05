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
    Generate argument text using Google Gemini API.

    Uses Gemini 2.0 Flash for fast, high-quality debate argument generation.
    Falls back to template-based generation if API is unavailable.
    """
    try:
        import os
        from dotenv import load_dotenv
        from google import genai

        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            return _fallback_argument(prompt)

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
            return response.text.strip()
        else:
            return _fallback_argument(prompt)

    except Exception as e:
        print(f"Gemini API error: {e}")
        return _fallback_argument(prompt)


def _fallback_argument(prompt: str) -> str:
    """Generate a template-based argument when the model is unavailable."""
    templates = {
        "LOGICAL_ARGUMENT": [
            "From a logical standpoint, we must consider the fundamental premises at play. "
            "The evidence clearly demonstrates a causal relationship that cannot be ignored. "
            "When we trace the chain of reasoning to its conclusion, the position I defend "
            "stands on solid logical ground.",

            "Let us examine this through the lens of deductive reasoning. If we accept the "
            "established premises — and the evidence strongly suggests we should — then the "
            "conclusion follows necessarily. My opponent's position contains a critical flaw "
            "in its logical structure.",
        ],
        "EMOTIONAL_APPEAL": [
            "Consider the real human impact of this issue. Behind every statistic is a "
            "person, a family, a community affected by these decisions. We cannot afford "
            "to remain indifferent when the consequences touch the lives of millions.",

            "I ask you to look beyond the cold calculations and see the human story. "
            "Throughout history, progress has been driven not just by logic, but by our "
            "collective sense of justice and compassion. This debate is no different.",
        ],
        "STATISTICAL_EVIDENCE": [
            "The data speaks clearly: research across multiple studies shows significant "
            "trends supporting this position. When we examine the quantitative evidence — "
            "the percentages, the longitudinal data, the meta-analyses — the conclusion "
            "becomes difficult to dispute.",

            "Statistical analysis reveals patterns that demand our attention. Cross-referencing "
            "data from multiple credible sources, we find consistent evidence pointing in "
            "one direction. Numbers don't lie, and these numbers support my stance.",
        ],
        "REBUTTAL_ATTACK": [
            "My opponent's argument, while superficially appealing, falls apart under scrutiny. "
            "They've committed several logical fallacies and ignored crucial counterevidence. "
            "Allow me to address their weakest points systematically.",

            "I must point out the fundamental weaknesses in my opponent's reasoning. "
            "Their argument relies on assumptions that are demonstrably false, and their "
            "evidence has been selectively presented to support a predetermined conclusion.",
        ],
        "DEFENSIVE_CLARIFICATION": [
            "Let me clarify and strengthen my position against potential objections. "
            "The nuance of this issue requires careful consideration, and I want to ensure "
            "my argument is understood in its full depth and complexity.",

            "I'd like to preemptively address what I anticipate my opponent might argue. "
            "My position is not as simple as it might appear — there are layers of reasoning "
            "that, when understood together, create an unassailable case.",
        ],
    }

    for strategy, args in templates.items():
        if strategy in prompt:
            return random.choice(args)

    return random.choice([arg for args in templates.values() for arg in args])
