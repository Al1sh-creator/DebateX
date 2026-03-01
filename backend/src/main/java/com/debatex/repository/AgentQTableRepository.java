package com.debatex.repository;

import com.debatex.model.AgentQTable;
import com.debatex.model.Round;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.Optional;

public interface AgentQTableRepository extends JpaRepository<AgentQTable, Long> {
    List<AgentQTable> findByAgentId(Long agentId);

    Optional<AgentQTable> findByAgentIdAndStateKeyAndAction(Long agentId, String stateKey, Round.Strategy action);
}
