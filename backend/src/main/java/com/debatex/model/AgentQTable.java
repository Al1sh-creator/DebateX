package com.debatex.model;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "agent_q_table")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class AgentQTable {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "agent_id", nullable = false)
    private Agent agent;

    @Column(name = "state_key", nullable = false)
    private String stateKey;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private Round.Strategy action;

    @Column(name = "q_value", nullable = false)
    @Builder.Default
    private Double qValue = 0.0;

    @Column(name = "visit_count", nullable = false)
    @Builder.Default
    private Integer visitCount = 0;

    @Column(name = "last_updated")
    @Builder.Default
    private LocalDateTime lastUpdated = LocalDateTime.now();

    @PreUpdate
    public void onUpdate() {
        this.lastUpdated = LocalDateTime.now();
    }
}
