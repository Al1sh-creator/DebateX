package com.debatex.controller;

import com.debatex.dto.Dtos.*;
import com.debatex.service.DebateService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/debates")
@RequiredArgsConstructor
public class DebateController {

    private final DebateService debateService;

    @PostMapping
    public ResponseEntity<DebateResponse> startDebate(
            @Valid @RequestBody StartDebateRequest request,
            Authentication auth) {
        return ResponseEntity.ok(debateService.createAndRunDebate(request, auth.getName()));
    }

    @GetMapping
    public ResponseEntity<List<DebateResponse>> getMyDebates(Authentication auth) {
        return ResponseEntity.ok(debateService.getUserDebates(auth.getName()));
    }

    @GetMapping("/{id}")
    public ResponseEntity<DebateResponse> getDebate(@PathVariable Long id) {
        return ResponseEntity.ok(debateService.getDebate(id));
    }

    @GetMapping("/{id}/rounds")
    public ResponseEntity<List<RoundResponse>> getDebateRounds(@PathVariable Long id) {
        return ResponseEntity.ok(debateService.getDebateRounds(id));
    }

    @GetMapping("/{id}/scores")
    public ResponseEntity<List<ScoreResponse>> getDebateScores(@PathVariable Long id) {
        return ResponseEntity.ok(debateService.getDebateScores(id));
    }

    @GetMapping("/{id}/summary")
    public ResponseEntity<DebateSummaryResponse> getDebateSummary(@PathVariable Long id) {
        return ResponseEntity.ok(debateService.getDebateSummary(id));
    }
}
