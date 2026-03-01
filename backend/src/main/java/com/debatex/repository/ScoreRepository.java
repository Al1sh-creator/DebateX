package com.debatex.repository;

import com.debatex.model.Score;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import java.util.List;

public interface ScoreRepository extends JpaRepository<Score, Long> {
    List<Score> findByDebateId(Long debateId);

    List<Score> findByAgentId(Long agentId);

    @Query("SELECT AVG(s.totalScore) FROM Score s WHERE s.agent.id = :agentId")
    Float findAverageScoreByAgentId(Long agentId);
}
