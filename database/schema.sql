-- ============================================================
-- DebateX Database Schema
-- Compatible with MySQL 8.0+ and TiDB Cloud
-- ============================================================

CREATE DATABASE IF NOT EXISTS debatex;
USE debatex;

-- ============================================================
-- USERS TABLE
-- ============================================================
CREATE TABLE users (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    username        VARCHAR(50)  NOT NULL UNIQUE,
    email           VARCHAR(100) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    role            ENUM('USER', 'ADMIN') NOT NULL DEFAULT 'USER',
    elo_rating      INT NOT NULL DEFAULT 1200,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_users_username (username),
    INDEX idx_users_email (email)
);

-- ============================================================
-- AGENTS TABLE
-- ============================================================
CREATE TABLE agents (
    id                  BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id             BIGINT NOT NULL,
    name                VARCHAR(100) NOT NULL,
    persona             ENUM('PHILOSOPHER', 'SCIENTIST', 'POLITICIAN', 'COMEDIAN', 'LAWYER', 'HISTORIAN') NOT NULL,
    aggression_level    FLOAT NOT NULL DEFAULT 0.5 CHECK (aggression_level BETWEEN 0 AND 1),
    logic_weight        FLOAT NOT NULL DEFAULT 0.5 CHECK (logic_weight BETWEEN 0 AND 1),
    emotion_weight      FLOAT NOT NULL DEFAULT 0.3 CHECK (emotion_weight BETWEEN 0 AND 1),
    evidence_preference FLOAT NOT NULL DEFAULT 0.5 CHECK (evidence_preference BETWEEN 0 AND 1),
    total_debates       INT NOT NULL DEFAULT 0,
    wins                INT NOT NULL DEFAULT 0,
    losses              INT NOT NULL DEFAULT 0,
    draws               INT NOT NULL DEFAULT 0,
    elo_rating          INT NOT NULL DEFAULT 1200,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_agents_user (user_id),
    INDEX idx_agents_elo (elo_rating DESC)
);

-- ============================================================
-- DEBATES TABLE
-- ============================================================
CREATE TABLE debates (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    topic           VARCHAR(500) NOT NULL,
    agent_a_id      BIGINT NOT NULL,
    agent_b_id      BIGINT NOT NULL,
    num_rounds      INT NOT NULL DEFAULT 3,
    status          ENUM('PENDING', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED') NOT NULL DEFAULT 'PENDING',
    winner_agent_id BIGINT NULL,
    is_draw         BOOLEAN NOT NULL DEFAULT FALSE,
    total_score_a   INT DEFAULT 0,
    total_score_b   INT DEFAULT 0,
    final_verdict   TEXT NULL,
    created_by      BIGINT NOT NULL,
    started_at      TIMESTAMP NULL,
    completed_at    TIMESTAMP NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_a_id) REFERENCES agents(id) ON DELETE CASCADE,
    FOREIGN KEY (agent_b_id) REFERENCES agents(id) ON DELETE CASCADE,
    FOREIGN KEY (winner_agent_id) REFERENCES agents(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_debates_status (status),
    INDEX idx_debates_agents (agent_a_id, agent_b_id),
    INDEX idx_debates_created (created_at DESC)
);

-- ============================================================
-- ROUNDS TABLE
-- ============================================================
CREATE TABLE rounds (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    debate_id       BIGINT NOT NULL,
    round_number    INT NOT NULL,
    agent_a_argument TEXT NOT NULL,
    agent_b_argument TEXT NOT NULL,
    agent_a_strategy ENUM('LOGICAL_ARGUMENT', 'EMOTIONAL_APPEAL', 'STATISTICAL_EVIDENCE', 'REBUTTAL_ATTACK', 'DEFENSIVE_CLARIFICATION') NOT NULL,
    agent_b_strategy ENUM('LOGICAL_ARGUMENT', 'EMOTIONAL_APPEAL', 'STATISTICAL_EVIDENCE', 'REBUTTAL_ATTACK', 'DEFENSIVE_CLARIFICATION') NOT NULL,
    agent_a_sentiment FLOAT DEFAULT 0,
    agent_b_sentiment FLOAT DEFAULT 0,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (debate_id) REFERENCES debates(id) ON DELETE CASCADE,
    UNIQUE KEY uk_debate_round (debate_id, round_number),
    INDEX idx_rounds_debate (debate_id)
);

-- ============================================================
-- SCORES TABLE
-- ============================================================
CREATE TABLE scores (
    id                      BIGINT AUTO_INCREMENT PRIMARY KEY,
    round_id                BIGINT NOT NULL,
    debate_id               BIGINT NOT NULL,
    agent_id                BIGINT NOT NULL,
    logical_consistency     FLOAT NOT NULL CHECK (logical_consistency BETWEEN 0 AND 10),
    semantic_relevance      FLOAT NOT NULL CHECK (semantic_relevance BETWEEN 0 AND 10),
    argument_coherence      FLOAT NOT NULL CHECK (argument_coherence BETWEEN 0 AND 10),
    emotional_tone_impact   FLOAT NOT NULL CHECK (emotional_tone_impact BETWEEN 0 AND 10),
    fallacy_penalty         FLOAT NOT NULL DEFAULT 0 CHECK (fallacy_penalty BETWEEN 0 AND 5),
    evidence_strength       FLOAT NOT NULL CHECK (evidence_strength BETWEEN 0 AND 10),
    total_score             FLOAT NOT NULL,
    feedback                TEXT NULL,
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (round_id) REFERENCES rounds(id) ON DELETE CASCADE,
    FOREIGN KEY (debate_id) REFERENCES debates(id) ON DELETE CASCADE,
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
    INDEX idx_scores_debate (debate_id),
    INDEX idx_scores_agent (agent_id)
);

-- ============================================================
-- AGENT Q-TABLE
-- ============================================================
CREATE TABLE agent_q_table (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    agent_id        BIGINT NOT NULL,
    state_key       VARCHAR(255) NOT NULL COMMENT 'Encoded state: topic_cluster|round_num|opponent_strategy',
    action          ENUM('LOGICAL_ARGUMENT', 'EMOTIONAL_APPEAL', 'STATISTICAL_EVIDENCE', 'REBUTTAL_ATTACK', 'DEFENSIVE_CLARIFICATION') NOT NULL,
    q_value         DOUBLE NOT NULL DEFAULT 0.0,
    visit_count     INT NOT NULL DEFAULT 0,
    last_updated    TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
    UNIQUE KEY uk_agent_state_action (agent_id, state_key, action),
    INDEX idx_qtable_agent (agent_id),
    INDEX idx_qtable_lookup (agent_id, state_key)
);

-- ============================================================
-- RANKINGS TABLE
-- ============================================================
CREATE TABLE rankings (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    agent_id        BIGINT NOT NULL,
    elo_rating      INT NOT NULL DEFAULT 1200,
    rank_position   INT NULL,
    total_debates   INT NOT NULL DEFAULT 0,
    win_rate        FLOAT NOT NULL DEFAULT 0.0,
    avg_score       FLOAT NOT NULL DEFAULT 0.0,
    best_strategy   ENUM('LOGICAL_ARGUMENT', 'EMOTIONAL_APPEAL', 'STATISTICAL_EVIDENCE', 'REBUTTAL_ATTACK', 'DEFENSIVE_CLARIFICATION') NULL,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
    UNIQUE KEY uk_ranking_agent (agent_id),
    INDEX idx_rankings_elo (elo_rating DESC),
    INDEX idx_rankings_position (rank_position)
);

-- ============================================================
-- ELO HISTORY TABLE (for analytics)
-- ============================================================
CREATE TABLE elo_history (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    agent_id        BIGINT NOT NULL,
    debate_id       BIGINT NOT NULL,
    elo_before      INT NOT NULL,
    elo_after       INT NOT NULL,
    elo_change      INT NOT NULL,
    recorded_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
    FOREIGN KEY (debate_id) REFERENCES debates(id) ON DELETE CASCADE,
    INDEX idx_elo_history_agent (agent_id),
    INDEX idx_elo_history_time (recorded_at)
);
