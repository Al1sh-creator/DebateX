package com.debatex.model;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "rankings")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Ranking {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "agent_id", nullable = false, unique = true)
    private Agent agent;

    @Column(name = "elo_rating", nullable = false)
    @Builder.Default
    private Integer eloRating = 1200;

    @Column(name = "rank_position")
    private Integer rankPosition;

    @Column(name = "total_debates", nullable = false)
    @Builder.Default
    private Integer totalDebates = 0;

    @Column(name = "win_rate", nullable = false)
    @Builder.Default
    private Float winRate = 0f;

    @Column(name = "avg_score", nullable = false)
    @Builder.Default
    private Float avgScore = 0f;

    @Enumerated(EnumType.STRING)
    @Column(name = "best_strategy")
    private Round.Strategy bestStrategy;

    @Column(name = "updated_at")
    @Builder.Default
    private LocalDateTime updatedAt = LocalDateTime.now();

    @PreUpdate
    public void onUpdate() {
        this.updatedAt = LocalDateTime.now();
    }
}
