package com.debatex.dto;

import com.debatex.model.Agent;
import jakarta.validation.constraints.*;
import lombok.*;

// ── Auth DTOs ──────────────────────────────────────────────

@Data
@NoArgsConstructor
@AllArgsConstructor
public class RegisterRequest {
    @NotBlank
    @Size(min = 3, max = 50)
    String username;
    @NotBlank
    @Email
    String email;
    @NotBlank
    @Size(min = 6, max = 100)
    String password;
}

@Data
@NoArgsConstructor
@AllArgsConstructor
class LoginRequest {
    @NotBlank
    String username;
    @NotBlank
    String password;
}

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
class AuthResponse {
    String token;
    String username;
    String role;
    Long userId;
}

// ── Agent DTOs ─────────────────────────────────────────────

@Data
@NoArgsConstructor
@AllArgsConstructor
class CreateAgentRequest {
    @NotBlank
    @Size(min = 2, max = 100)
    String name;
    @NotNull
    Agent.Persona persona;
    Float aggressionLevel;
    Float logicWeight;
    Float emotionWeight;
    Float evidencePreference;
}

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
class AgentResponse {
    Long id;
    String name;
    String persona;
    Float aggressionLevel;
    Float logicWeight;
    Float emotionWeight;
    Float evidencePreference;
    Integer totalDebates;
    Integer wins;
    Integer losses;
    Integer draws;
    Integer eloRating;
}

// ── Debate DTOs ────────────────────────────────────────────

@Data
@NoArgsConstructor
@AllArgsConstructor
class StartDebateRequest {
    @NotBlank
    @Size(min = 5, max = 500)
    String topic;
    @NotNull
    Long agentAId;
    @NotNull
    Long agentBId;
    Integer numRounds;
}

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
class DebateResponse {
    Long id;
    String topic;
    AgentResponse agentA;
    AgentResponse agentB;
    Integer numRounds;
    String status;
    String winner;
    Boolean isDraw;
    Integer totalScoreA;
    Integer totalScoreB;
    String finalVerdict;
}

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
class RoundResponse {
    Integer roundNumber;
    String agentAArgument;
    String agentBArgument;
    String agentAStrategy;
    String agentBStrategy;
    Float agentASentiment;
    Float agentBSentiment;
}

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
class ScoreResponse {
    Integer roundNumber;
    String agentName;
    Float logicalConsistency;
    Float semanticRelevance;
    Float argumentCoherence;
    Float emotionalToneImpact;
    Float fallacyPenalty;
    Float evidenceStrength;
    Float totalScore;
    String feedback;
}

// ── Analytics DTOs ─────────────────────────────────────────

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
class RankingResponse {
    Integer rank;
    String agentName;
    String persona;
    Integer eloRating;
    Integer totalDebates;
    Float winRate;
    Float avgScore;
    String bestStrategy;
    String ownerUsername;
}

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
class AnalyticsResponse {
    Integer totalDebates;
    Integer totalAgents;
    Integer totalUsers;
    java.util.List<RankingResponse> topAgents;
}
