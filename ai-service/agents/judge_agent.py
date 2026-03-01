"""
Judge Agent for DebateX.

Evaluates debate arguments on 6 dimensions:
  1. Logical consistency
  2. Semantic relevance (embedding similarity to topic)
  3. Argument coherence
  4. Emotional tone impact
  5. Fallacy detection penalty
  6. Evidence usage strength

Uses NLP modules for scoring and produces structured JSON output.
"""

from models.schemas import (
    JudgeRoundRequest, JudgeRoundResponse, DimensionScores,
)
from nlp.embeddings import compute_topic_relevance, compute_similarity
from nlp.sentiment import compute_emotional_impact, analyze_sentiment
from nlp.fallacy_detector import compute_fallacy_penalty, get_fallacy_summary


# ── Scoring Weights for Final Score ──────────────────────────

SCORE_WEIGHTS = {
    "logical_consistency": 0.20,
    "semantic_relevance": 0.20,
    "argument_coherence": 0.20,
    "emotional_tone_impact": 0.15,
    "evidence_strength": 0.15,
    "fallacy_penalty": 0.10,  # This is subtracted
}


def compute_logical_consistency(argument: str) -> float:
    """
    Evaluate logical consistency of an argument (0-10 scale).

    Checks for:
    - Structural markers (premises, conclusions)
    - Causal reasoning indicators
    - Logical connectives usage
    - Contradiction indicators (penalized)
    """
    text_lower = argument.lower()
    score = 5.0  # Base score

    # Positive indicators — structured reasoning
    logic_markers = [
        "therefore", "thus", "hence", "consequently", "because",
        "since", "given that", "it follows", "we can conclude",
        "if...then", "firstly", "secondly", "moreover", "furthermore",
        "in addition", "for example", "for instance", "specifically",
        "this demonstrates", "this shows", "the evidence suggests",
    ]
    marker_count = sum(1 for m in logic_markers if m in text_lower)
    score += min(3.0, marker_count * 0.6)

    # Positive — paragraph structure (indicates organized thinking)
    paragraphs = [p.strip() for p in argument.split("\n\n") if p.strip()]
    if len(paragraphs) >= 2:
        score += 0.5
    if len(paragraphs) >= 3:
        score += 0.5

    # Negative — contradiction indicators
    contradiction_markers = [
        "however, i also think the opposite",
        "but then again, maybe not",
        "i'm not sure",
        "this contradicts",
    ]
    for marker in contradiction_markers:
        if marker in text_lower:
            score -= 1.0

    # Negative — too short (likely underdeveloped argument)
    word_count = len(argument.split())
    if word_count < 30:
        score -= 2.0
    elif word_count < 60:
        score -= 1.0

    return round(max(0, min(10, score)), 2)


def compute_argument_coherence(argument: str) -> float:
    """
    Evaluate coherence — how well sentences connect to each other (0-10 scale).

    Uses sentence-level similarity to measure how well the argument flows.
    """
    sentences = [s.strip() for s in argument.replace("\n", ". ").split(". ") if len(s.strip()) > 10]

    if len(sentences) < 2:
        return 5.0  # Can't evaluate coherence of a single sentence

    # Compute average similarity between consecutive sentences
    similarities = []
    for i in range(len(sentences) - 1):
        sim = compute_similarity(sentences[i], sentences[i + 1])
        similarities.append(sim)

    avg_similarity = sum(similarities) / len(similarities) if similarities else 0.5

    # Map to 0-10 scale
    # Coherent arguments: high inter-sentence similarity (0.3-0.8)
    # Too high (>0.9) = repetitive, too low (<0.1) = incoherent
    if avg_similarity > 0.9:
        score = 7.0  # Slightly penalize for repetition
    elif avg_similarity > 0.6:
        score = 9.0 + (avg_similarity - 0.6) * 3
    elif avg_similarity > 0.3:
        score = 6.0 + (avg_similarity - 0.3) * 10
    else:
        score = max(2.0, avg_similarity * 20)

    return round(min(10, score), 2)


def compute_evidence_strength(argument: str) -> float:
    """
    Evaluate evidence usage in an argument (0-10 scale).

    Checks for:
    - Statistical references (numbers, percentages)
    - Citation indicators
    - Concrete examples
    - Data-driven language
    """
    import re
    text_lower = argument.lower()
    score = 3.0  # Base score

    # Statistical references
    numbers = re.findall(r'\d+(?:\.\d+)?%?\b', argument)
    score += min(2.0, len(numbers) * 0.5)

    # Citation language
    citation_markers = [
        "according to", "research shows", "studies indicate",
        "data suggests", "evidence demonstrates", "survey found",
        "published in", "researchers found", "analysis reveals",
        "statistics show", "report indicates", "findings suggest",
        "experiments prove", "meta-analysis", "peer-reviewed",
    ]
    citation_count = sum(1 for m in citation_markers if m in text_lower)
    score += min(2.5, citation_count * 0.8)

    # Concrete examples
    example_markers = [
        "for example", "for instance", "such as", "consider the case",
        "take the example", "as demonstrated by", "as seen in",
        "specifically", "in particular", "a clear example",
    ]
    example_count = sum(1 for m in example_markers if m in text_lower)
    score += min(1.5, example_count * 0.5)

    # Data-driven vocabulary
    data_words = [
        "percent", "ratio", "trend", "correlation", "significant",
        "increase", "decrease", "majority", "minority", "proportion",
    ]
    data_count = sum(1 for w in data_words if w in text_lower)
    score += min(1.0, data_count * 0.25)

    return round(max(0, min(10, score)), 2)


def judge_round(request: JudgeRoundRequest) -> JudgeRoundResponse:
    """
    Judge a debate round by evaluating both agents' arguments.

    Returns detailed scores on 6 dimensions for each agent,
    along with analysis and per-agent feedback.
    """
    # ── Score Agent A ────────────────────────────────────────
    a_logical = compute_logical_consistency(request.agent_a_argument)
    a_relevance = compute_topic_relevance(request.agent_a_argument, request.topic)
    a_coherence = compute_argument_coherence(request.agent_a_argument)
    a_emotional = compute_emotional_impact(request.agent_a_argument)
    a_fallacy = compute_fallacy_penalty(request.agent_a_argument)
    a_evidence = compute_evidence_strength(request.agent_a_argument)

    a_total = round(
        a_logical * SCORE_WEIGHTS["logical_consistency"] +
        a_relevance * SCORE_WEIGHTS["semantic_relevance"] +
        a_coherence * SCORE_WEIGHTS["argument_coherence"] +
        a_emotional * SCORE_WEIGHTS["emotional_tone_impact"] +
        a_evidence * SCORE_WEIGHTS["evidence_strength"] -
        a_fallacy * SCORE_WEIGHTS["fallacy_penalty"],
        2
    ) * 10  # Scale to ~0-100 range

    # ── Score Agent B ────────────────────────────────────────
    b_logical = compute_logical_consistency(request.agent_b_argument)
    b_relevance = compute_topic_relevance(request.agent_b_argument, request.topic)
    b_coherence = compute_argument_coherence(request.agent_b_argument)
    b_emotional = compute_emotional_impact(request.agent_b_argument)
    b_fallacy = compute_fallacy_penalty(request.agent_b_argument)
    b_evidence = compute_evidence_strength(request.agent_b_argument)

    b_total = round(
        b_logical * SCORE_WEIGHTS["logical_consistency"] +
        b_relevance * SCORE_WEIGHTS["semantic_relevance"] +
        b_coherence * SCORE_WEIGHTS["argument_coherence"] +
        b_emotional * SCORE_WEIGHTS["emotional_tone_impact"] +
        b_evidence * SCORE_WEIGHTS["evidence_strength"] -
        b_fallacy * SCORE_WEIGHTS["fallacy_penalty"],
        2
    ) * 10

    # ── Build Scores ─────────────────────────────────────────
    agent_a_scores = DimensionScores(
        logical_consistency=a_logical,
        semantic_relevance=a_relevance,
        argument_coherence=a_coherence,
        emotional_tone_impact=a_emotional,
        fallacy_penalty=a_fallacy,
        evidence_strength=a_evidence,
        total_score=round(a_total, 2),
    )
    agent_b_scores = DimensionScores(
        logical_consistency=b_logical,
        semantic_relevance=b_relevance,
        argument_coherence=b_coherence,
        emotional_tone_impact=b_emotional,
        fallacy_penalty=b_fallacy,
        evidence_strength=b_evidence,
        total_score=round(b_total, 2),
    )

    # ── Analysis ─────────────────────────────────────────────
    leader = "Agent A" if a_total > b_total else "Agent B" if b_total > a_total else "Neither (tied)"
    margin = abs(a_total - b_total)

    analysis = (
        f"Round {request.round_number} Analysis: {leader} leads by {margin:.1f} points. "
        f"Agent A ({request.agent_a_profile.persona.value}) used {request.agent_a_strategy.value} strategy "
        f"with logical score {a_logical}/10 and evidence score {a_evidence}/10. "
        f"Agent B ({request.agent_b_profile.persona.value}) used {request.agent_b_strategy.value} strategy "
        f"with logical score {b_logical}/10 and evidence score {b_evidence}/10."
    )

    # ── Per-Agent Feedback ───────────────────────────────────
    a_fallacies = get_fallacy_summary(request.agent_a_argument)
    b_fallacies = get_fallacy_summary(request.agent_b_argument)

    feedback_a = (
        f"Strengths: {'logical structure' if a_logical > 6 else 'emotional impact' if a_emotional > 6 else 'topic relevance'}. "
        f"Weaknesses: {'evidence usage could be stronger' if a_evidence < 5 else 'coherence needs work' if a_coherence < 5 else 'minor areas for improvement'}. "
        f"Fallacies: {a_fallacies}"
    )
    feedback_b = (
        f"Strengths: {'logical structure' if b_logical > 6 else 'emotional impact' if b_emotional > 6 else 'topic relevance'}. "
        f"Weaknesses: {'evidence usage could be stronger' if b_evidence < 5 else 'coherence needs work' if b_coherence < 5 else 'minor areas for improvement'}. "
        f"Fallacies: {b_fallacies}"
    )

    return JudgeRoundResponse(
        agent_a_scores=agent_a_scores,
        agent_b_scores=agent_b_scores,
        analysis=analysis,
        feedback_a=feedback_a,
        feedback_b=feedback_b,
    )


# ── Example Output ───────────────────────────────────────────

EXAMPLE_JUDGE_OUTPUT = {
    "agent_a_scores": {
        "logical_consistency": 7.8,
        "semantic_relevance": 8.2,
        "argument_coherence": 7.5,
        "emotional_tone_impact": 6.1,
        "fallacy_penalty": 0.8,
        "evidence_strength": 6.5,
        "total_score": 72.4
    },
    "agent_b_scores": {
        "logical_consistency": 6.5,
        "semantic_relevance": 7.9,
        "argument_coherence": 8.1,
        "emotional_tone_impact": 8.4,
        "fallacy_penalty": 1.2,
        "evidence_strength": 5.8,
        "total_score": 68.9
    },
    "analysis": "Round 1 Analysis: Agent A leads by 3.5 points. Agent A (PHILOSOPHER) used LOGICAL_ARGUMENT strategy with strong reasoning chains. Agent B (POLITICIAN) used EMOTIONAL_APPEAL with compelling but less evidence-backed claims.",
    "feedback_a": "Strengths: logical structure. Weaknesses: minor areas for improvement. Fallacies: No significant logical fallacies detected.",
    "feedback_b": "Strengths: emotional impact. Weaknesses: evidence usage could be stronger. Fallacies: • Appeal to Emotion (40% confidence): Using excessive emotional manipulation instead of logical reasoning."
}
