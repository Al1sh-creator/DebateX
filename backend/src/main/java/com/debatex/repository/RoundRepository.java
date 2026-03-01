package com.debatex.repository;

import com.debatex.model.Round;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface RoundRepository extends JpaRepository<Round, Long> {
    List<Round> findByDebateIdOrderByRoundNumber(Long debateId);
}
