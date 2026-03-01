package com.debatex.model;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "rounds")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Round {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "debate_id", nullable = false)
    private Debate debate;

    @Column(name = "round_number", nullable = false)
    private Integer roundNumber;

    @Column(name = "agent_a_argument", nullable = false, columnDefinition = "TEXT")
    private String agentAArgument;

    @Column(name = "agent_b_argument", nullable = false, columnDefinition = "TEXT")
    private String agentBArgument;

    @Enumerated(EnumType.STRING)
    @Column(name = "agent_a_strategy", nullable = false)
    private Strategy agentAStrategy;

    @Enumerated(EnumType.STRING)
    @Column(name = "agent_b_strategy", nullable = false)
    private Strategy agentBStrategy;

    @Column(name = "agent_a_sentiment")
    @Builder.Default
    private Float agentASentiment = 0f;

    @Column(name = "agent_b_sentiment")
    @Builder.Default
    private Float agentBSentiment = 0f;

    @Column(name = "created_at")
    @Builder.Default
    private LocalDateTime createdAt = LocalDateTime.now();

    public enum Strategy {
        LOGICAL_ARGUMENT, EMOTIONAL_APPEAL, STATISTICAL_EVIDENCE,
        REBUTTAL_ATTACK, DEFENSIVE_CLARIFICATION
    }
}
