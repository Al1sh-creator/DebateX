"""Pydantic schemas for the DebateX AI Service."""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


# ── Enums ────────────────────────────────────────────────────

class Persona(str, Enum):
    PHILOSOPHER = "PHILOSOPHER"
    SCIENTIST = "SCIENTIST"
    POLITICIAN = "POLITICIAN"
    COMEDIAN = "COMEDIAN"
    LAWYER = "LAWYER"
    HISTORIAN = "HISTORIAN"


class Strategy(str, Enum):
    LOGICAL_ARGUMENT = "LOGICAL_ARGUMENT"
    EMOTIONAL_APPEAL = "EMOTIONAL_APPEAL"
    STATISTICAL_EVIDENCE = "STATISTICAL_EVIDENCE"
    REBUTTAL_ATTACK = "REBUTTAL_ATTACK"
    DEFENSIVE_CLARIFICATION = "DEFENSIVE_CLARIFICATION"


# ── Agent Profile ────────────────────────────────────────────

class AgentProfile(BaseModel):
    agent_id: int
    name: str
    persona: Persona
    aggression_level: float = Field(0.5, ge=0, le=1)
    logic_weight: float = Field(0.5, ge=0, le=1)
    emotion_weight: float = Field(0.3, ge=0, le=1)
    evidence_preference: float = Field(0.5, ge=0, le=1)


# ── Q-Learning ───────────────────────────────────────────────

class QTableEntry(BaseModel):
    agent_id: int
    state_key: str
    action: Strategy
    q_value: float = 0.0
    visit_count: int = 0


class QTableBatch(BaseModel):
    entries: list[QTableEntry]


# ── Debate State ─────────────────────────────────────────────

class DebateState(BaseModel):
    topic: str
    round_number: int
    total_rounds: int
    agent_profile: AgentProfile
    opponent_profile: AgentProfile
    stance: str  # "PRO" or "CON"
    conversation_history: list[dict] = []
    opponent_last_strategy: Optional[Strategy] = None


# ── Argument Generation ──────────────────────────────────────

class GenerateArgumentRequest(BaseModel):
    state: DebateState
    q_table: list[QTableEntry] = []


class GenerateArgumentResponse(BaseModel):
    argument: str
    chosen_strategy: Strategy
    strategy_reasoning: str


# ── Judge Scoring ────────────────────────────────────────────

class JudgeRoundRequest(BaseModel):
    topic: str
    round_number: int
    agent_a_argument: str
    agent_b_argument: str
    agent_a_strategy: Strategy
    agent_b_strategy: Strategy
    agent_a_profile: AgentProfile
    agent_b_profile: AgentProfile


class DimensionScores(BaseModel):
    logical_consistency: float = Field(..., ge=0, le=10)
    semantic_relevance: float = Field(..., ge=0, le=10)
    argument_coherence: float = Field(..., ge=0, le=10)
    emotional_tone_impact: float = Field(..., ge=0, le=10)
    fallacy_penalty: float = Field(0, ge=0, le=5)
    evidence_strength: float = Field(..., ge=0, le=10)
    total_score: float


class JudgeRoundResponse(BaseModel):
    agent_a_scores: DimensionScores
    agent_b_scores: DimensionScores
    analysis: str
    feedback_a: str
    feedback_b: str


# ── Q-Table Update ───────────────────────────────────────────

class RewardSignal(BaseModel):
    judge_score: float
    relevance_score: float
    coherence_score: float
    sentiment_impact: float


class UpdateQTableRequest(BaseModel):
    agent_id: int
    state_key: str
    action: Strategy
    reward: RewardSignal
    next_state_key: str
    q_table: list[QTableEntry] = []
    learning_rate: float = 0.1
    discount_factor: float = 0.95


class UpdateQTableResponse(BaseModel):
    updated_entry: QTableEntry
    reward_value: float


# ── Strategy Query ───────────────────────────────────────────

class GetStrategyRequest(BaseModel):
    agent_id: int
    state_key: str
    agent_profile: AgentProfile
    q_table: list[QTableEntry] = []
    epsilon: float = 0.15


class GetStrategyResponse(BaseModel):
    chosen_strategy: Strategy
    q_values: dict[str, float]
    was_exploration: bool
