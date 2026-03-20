package com.debatex.dto;

import com.debatex.model.Agent;
import jakarta.validation.constraints.*;
import lombok.*;

public class Dtos {

    // ── Auth DTOs ──────────────────────────────────────────────

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class RegisterRequest {
        @NotBlank
        @Size(min = 3, max = 50)
        private String username;
        @NotBlank
        @Email
        private String email;
        @NotBlank
        @Size(min = 6, max = 100)
        private String password;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class LoginRequest {
        @NotBlank
        private String username;
        @NotBlank
        private String password;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class AuthResponse {
        private String token;
        private String username;
        private String role;
        private Long userId;
    }

    // ── Agent DTOs ─────────────────────────────────────────────

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class CreateAgentRequest {
        @NotBlank
        @Size(min = 2, max = 100)
        private String name;
        @NotNull
        private Agent.Persona persona;
        private Float aggressionLevel;
        private Float logicWeight;
        private Float emotionWeight;
        private Float evidencePreference;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class AgentResponse {
        private Long id;
        private String name;
        private String persona;
        private Float aggressionLevel;
        private Float logicWeight;
        private Float emotionWeight;
        private Float evidencePreference;
        private Integer totalDebates;
        private Integer wins;
        private Integer losses;
        private Integer draws;
        private Integer eloRating;
    }

    // ── Debate DTOs ────────────────────────────────────────────

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class StartDebateRequest {
        @NotBlank
        @Size(min = 5, max = 500)
        private String topic;
        @NotNull
        private Long agentAId;
        @NotNull
        private Long agentBId;
        private Integer numRounds;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class DebateResponse {
        private Long id;
        private String topic;
        private AgentResponse agentA;
        private AgentResponse agentB;
        private Integer numRounds;
        private String status;
        private String winner;
        private Boolean isDraw;
        private Integer totalScoreA;
        private Integer totalScoreB;
        private String finalVerdict;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class RoundResponse {
        private Integer roundNumber;
        private String agentAArgument;
        private String agentBArgument;
        private String agentAStrategy;
        private String agentBStrategy;
        private Float agentASentiment;
        private Float agentBSentiment;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class ScoreResponse {
        private Integer roundNumber;
        private String agentName;
        private Float logicalConsistency;
        private Float semanticRelevance;
        private Float argumentCoherence;
        private Float emotionalToneImpact;
        private Float fallacyPenalty;
        private Float evidenceStrength;
        private Float totalScore;
        private String feedback;
    }

    // ── Analytics DTOs ─────────────────────────────────────────

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class RankingResponse {
        private Integer rank;
        private String agentName;
        private String persona;
        private Integer eloRating;
        private Integer totalDebates;
        private Float winRate;
        private Float avgScore;
        private String bestStrategy;
        private String ownerUsername;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class AnalyticsResponse {
        private Integer totalDebates;
        private Integer totalAgents;
        private Integer totalUsers;
        private java.util.List<RankingResponse> topAgents;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class DebateSummaryResponse {
        private java.util.List<String> summaryA;
        private java.util.List<String> summaryB;
    }
}
