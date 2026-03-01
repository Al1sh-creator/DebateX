package com.debatex.model;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "debates")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Debate {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 500)
    private String topic;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "agent_a_id", nullable = false)
    private Agent agentA;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "agent_b_id", nullable = false)
    private Agent agentB;

    @Column(name = "num_rounds", nullable = false)
    @Builder.Default
    private Integer numRounds = 3;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    @Builder.Default
    private Status status = Status.PENDING;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "winner_agent_id")
    private Agent winnerAgent;

    @Column(name = "is_draw", nullable = false)
    @Builder.Default
    private Boolean isDraw = false;

    @Column(name = "total_score_a")
    @Builder.Default
    private Integer totalScoreA = 0;

    @Column(name = "total_score_b")
    @Builder.Default
    private Integer totalScoreB = 0;

    @Column(name = "final_verdict", columnDefinition = "TEXT")
    private String finalVerdict;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "created_by", nullable = false)
    private User createdBy;

    @Column(name = "started_at")
    private LocalDateTime startedAt;

    @Column(name = "completed_at")
    private LocalDateTime completedAt;

    @Column(name = "created_at")
    @Builder.Default
    private LocalDateTime createdAt = LocalDateTime.now();

    public enum Status {
        PENDING, IN_PROGRESS, COMPLETED, CANCELLED
    }
}
