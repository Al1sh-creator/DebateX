package com.debatex.controller;

import com.debatex.dto.Dtos.*;
import com.debatex.service.AgentService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/agents")
@RequiredArgsConstructor
public class AgentController {

    private final AgentService agentService;

    @PostMapping
    public ResponseEntity<AgentResponse> createAgent(
            @Valid @RequestBody CreateAgentRequest request,
            Authentication auth) {
        return ResponseEntity.ok(agentService.createAgent(request, auth.getName()));
    }

    @GetMapping
    public ResponseEntity<List<AgentResponse>> getMyAgents(Authentication auth) {
        return ResponseEntity.ok(agentService.getUserAgents(auth.getName()));
    }

    @GetMapping("/{id}")
    public ResponseEntity<AgentResponse> getAgent(@PathVariable Long id) {
        return ResponseEntity.ok(agentService.getAgent(id));
    }

    @GetMapping("/leaderboard")
    public ResponseEntity<List<RankingResponse>> getLeaderboard() {
        return ResponseEntity.ok(agentService.getLeaderboard());
    }
}
