package com.debatex.repository;

import com.debatex.model.Agent;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface AgentRepository extends JpaRepository<Agent, Long> {
    List<Agent> findByUserId(Long userId);

    List<Agent> findAllByOrderByEloRatingDesc();
}
