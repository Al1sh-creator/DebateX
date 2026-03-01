"""
Q-Learning Engine for DebateX Agents.

Implements tabular Q-learning with epsilon-greedy exploration.
Each agent maintains its own Q-table mapping (state, action) → value.

State encoding:  topic_cluster | round_number | opponent_strategy
Actions:         5 debate strategies
Reward:          Weighted composite of judge scores
"""

import numpy as np
import random
from typing import Optional
from models.schemas import Strategy, QTableEntry, RewardSignal


# ── All possible actions ─────────────────────────────────────

ALL_ACTIONS = list(Strategy)


# ── Q-Learning Hyperparameters ───────────────────────────────

DEFAULT_LEARNING_RATE = 0.1      # α — how fast the agent learns
DEFAULT_DISCOUNT_FACTOR = 0.95   # γ — importance of future rewards
DEFAULT_EPSILON = 0.3            # ε — exploration rate
EPSILON_DECAY = 0.995            # Decay factor per debate
EPSILON_MIN = 0.05               # Minimum exploration rate


class QLearningEngine:
    """
    Tabular Q-learning engine for debate strategy selection.

    The Q-table maps (state_key, action) → q_value.
    State keys encode: topic cluster, round number, and opponent's last strategy.
    """

    def __init__(
        self,
        learning_rate: float = DEFAULT_LEARNING_RATE,
        discount_factor: float = DEFAULT_DISCOUNT_FACTOR,
        epsilon: float = DEFAULT_EPSILON,
    ):
        self.alpha = learning_rate
        self.gamma = discount_factor
        self.epsilon = epsilon
        self.q_table: dict[tuple[str, Strategy], float] = {}
        self.visit_counts: dict[tuple[str, Strategy], int] = {}

    def load_q_table(self, entries: list[QTableEntry]):
        """Load Q-table from database entries."""
        self.q_table.clear()
        self.visit_counts.clear()
        for entry in entries:
            key = (entry.state_key, entry.action)
            self.q_table[key] = entry.q_value
            self.visit_counts[key] = entry.visit_count

    def export_q_table(self, agent_id: int) -> list[QTableEntry]:
        """Export Q-table as database-ready entries."""
        entries = []
        for (state_key, action), q_value in self.q_table.items():
            entries.append(QTableEntry(
                agent_id=agent_id,
                state_key=state_key,
                action=action,
                q_value=q_value,
                visit_count=self.visit_counts.get((state_key, action), 0),
            ))
        return entries

    def get_q_value(self, state_key: str, action: Strategy) -> float:
        """Get Q-value for a state-action pair. Returns 0 if unseen."""
        return self.q_table.get((state_key, action), 0.0)

    def get_all_q_values(self, state_key: str) -> dict[Strategy, float]:
        """Get Q-values for all actions in a given state."""
        return {action: self.get_q_value(state_key, action) for action in ALL_ACTIONS}

    def select_action(
        self,
        state_key: str,
        personality_weights: Optional[dict[Strategy, float]] = None,
    ) -> tuple[Strategy, bool]:
        """
        Select an action using epsilon-greedy policy with personality bias.

        Returns: (chosen_action, was_exploration)
        """
        # Exploration: random action
        if random.random() < self.epsilon:
            chosen = random.choice(ALL_ACTIONS)
            return chosen, True

        # Exploitation: choose best Q-value, with personality bias
        q_values = self.get_all_q_values(state_key)

        # Apply personality weights as additive bias
        if personality_weights:
            for action in ALL_ACTIONS:
                q_values[action] += personality_weights.get(action, 0.0)

        # Pick action with highest combined value (break ties randomly)
        max_q = max(q_values.values())
        best_actions = [a for a, q in q_values.items() if abs(q - max_q) < 1e-9]
        chosen = random.choice(best_actions)

        return chosen, False

    def update(
        self,
        state_key: str,
        action: Strategy,
        reward: float,
        next_state_key: str,
    ) -> float:
        """
        Perform Q-learning update:
        Q(s,a) ← Q(s,a) + α [r + γ · max_a' Q(s',a') - Q(s,a)]

        Returns the new Q-value.
        """
        current_q = self.get_q_value(state_key, action)

        # Max Q-value for next state
        next_q_values = self.get_all_q_values(next_state_key)
        max_next_q = max(next_q_values.values()) if next_q_values else 0.0

        # Bellman update
        new_q = current_q + self.alpha * (reward + self.gamma * max_next_q - current_q)

        # Store
        key = (state_key, action)
        self.q_table[key] = new_q
        self.visit_counts[key] = self.visit_counts.get(key, 0) + 1

        return new_q

    def decay_epsilon(self):
        """Decay exploration rate after each debate."""
        self.epsilon = max(EPSILON_MIN, self.epsilon * EPSILON_DECAY)


def compute_reward(reward_signal: RewardSignal) -> float:
    """
    Compute composite reward from judge evaluation.

    Weights:
      - Judge score:      30%
      - Relevance:        25%
      - Coherence:        25%
      - Sentiment impact: 20%
    """
    return (
        0.30 * reward_signal.judge_score +
        0.25 * reward_signal.relevance_score +
        0.25 * reward_signal.coherence_score +
        0.20 * reward_signal.sentiment_impact
    )


def encode_state(topic_cluster: int, round_number: int, opponent_strategy: Optional[str] = None) -> str:
    """
    Encode debate state as a string key for Q-table lookup.

    Format: "cluster_{X}|round_{Y}|opp_{Z}"
    """
    opp = opponent_strategy or "NONE"
    return f"cluster_{topic_cluster}|round_{round_number}|opp_{opp}"
