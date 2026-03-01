package com.debatex.repository;

import com.debatex.model.Debate;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface DebateRepository extends JpaRepository<Debate, Long> {
    List<Debate> findByCreatedByIdOrderByCreatedAtDesc(Long userId);

    List<Debate> findByStatusOrderByCreatedAtDesc(Debate.Status status);

    List<Debate> findAllByOrderByCreatedAtDesc();
}
