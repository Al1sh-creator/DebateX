package com.debatex.repository;

import com.debatex.model.Ranking;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.Optional;

public interface RankingRepository extends JpaRepository<Ranking, Long> {
    Optional<Ranking> findByAgentId(Long agentId);

    List<Ranking> findAllByOrderByEloRatingDesc();
}
