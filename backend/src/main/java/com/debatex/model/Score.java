package com.debatex.model;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "scores")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Score {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "round_id", nullable = false)
    private Round round;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "debate_id", nullable = false)
    private Debate debate;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "agent_id", nullable = false)
    private Agent agent;

    @Column(name = "logical_consistency", nullable = false)
    private Float logicalConsistency;

    @Column(name = "semantic_relevance", nullable = false)
    private Float semanticRelevance;

    @Column(name = "argument_coherence", nullable = false)
    private Float argumentCoherence;

    @Column(name = "emotional_tone_impact", nullable = false)
    private Float emotionalToneImpact;

    @Column(name = "fallacy_penalty", nullable = false)
    @Builder.Default
    private Float fallacyPenalty = 0f;

    @Column(name = "evidence_strength", nullable = false)
    private Float evidenceStrength;

    @Column(name = "total_score", nullable = false)
    private Float totalScore;

    @Column(columnDefinition = "TEXT")
    private String feedback;

    @Column(name = "created_at")
    @Builder.Default
    private LocalDateTime createdAt = LocalDateTime.now();
}
