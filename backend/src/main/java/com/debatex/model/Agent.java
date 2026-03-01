package com.debatex.model;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "agents")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Agent {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @Column(nullable = false, length = 100)
    private String name;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private Persona persona;

    @Column(name = "aggression_level", nullable = false)
    @Builder.Default
    private Float aggressionLevel = 0.5f;

    @Column(name = "logic_weight", nullable = false)
    @Builder.Default
    private Float logicWeight = 0.5f;

    @Column(name = "emotion_weight", nullable = false)
    @Builder.Default
    private Float emotionWeight = 0.3f;

    @Column(name = "evidence_preference", nullable = false)
    @Builder.Default
    private Float evidencePreference = 0.5f;

    @Column(name = "total_debates", nullable = false)
    @Builder.Default
    private Integer totalDebates = 0;

    @Column(nullable = false)
    @Builder.Default
    private Integer wins = 0;

    @Column(nullable = false)
    @Builder.Default
    private Integer losses = 0;

    @Column(nullable = false)
    @Builder.Default
    private Integer draws = 0;

    @Column(name = "elo_rating", nullable = false)
    @Builder.Default
    private Integer eloRating = 1200;

    @Column(name = "created_at")
    @Builder.Default
    private LocalDateTime createdAt = LocalDateTime.now();

    @Column(name = "updated_at")
    @Builder.Default
    private LocalDateTime updatedAt = LocalDateTime.now();

    public enum Persona {
        PHILOSOPHER, SCIENTIST, POLITICIAN, COMEDIAN, LAWYER, HISTORIAN
    }

    @PreUpdate
    public void onUpdate() {
        this.updatedAt = LocalDateTime.now();
    }
}
