package com.debatex.service;

import com.debatex.dto.Dtos.*;
import com.debatex.model.*;
import com.debatex.repository.*;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@RequiredArgsConstructor
public class AgentService {

    private final AgentRepository agentRepository;
    private final UserRepository userRepository;
    private final RankingRepository rankingRepository;

    public AgentResponse createAgent(CreateAgentRequest request, String username) {
        User user = userRepository.findByUsername(username)
                .orElseThrow(() -> new RuntimeException("User not found"));

        Agent agent = Agent.builder()
                .user(user)
                .name(request.getName())
                .persona(request.getPersona())
                .aggressionLevel(request.getAggressionLevel() != null ? request.getAggressionLevel() : 0.5f)
                .logicWeight(request.getLogicWeight() != null ? request.getLogicWeight() : 0.5f)
                .emotionWeight(request.getEmotionWeight() != null ? request.getEmotionWeight() : 0.3f)
                .evidencePreference(request.getEvidencePreference() != null ? request.getEvidencePreference() : 0.5f)
                .build();

        agent = agentRepository.save(agent);

        Ranking ranking = Ranking.builder().agent(agent).build();
        rankingRepository.save(ranking);

        return toResponse(agent);
    }

    public List<AgentResponse> getUserAgents(String username) {
        User user = userRepository.findByUsername(username)
                .orElseThrow(() -> new RuntimeException("User not found"));
        return agentRepository.findByUserId(user.getId())
                .stream().map(this::toResponse).toList();
    }

    public AgentResponse getAgent(Long id) {
        return toResponse(agentRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Agent not found")));
    }

    public List<RankingResponse> getLeaderboard() {
        return rankingRepository.findAllByOrderByEloRatingDesc()
                .stream().map(r -> RankingResponse.builder()
                        .rank(r.getRankPosition())
                        .agentName(r.getAgent().getName())
                        .persona(r.getAgent().getPersona().name())
                        .eloRating(r.getEloRating())
                        .totalDebates(r.getTotalDebates())
                        .winRate(r.getWinRate())
                        .avgScore(r.getAvgScore())
                        .bestStrategy(r.getBestStrategy() != null ? r.getBestStrategy().name() : null)
                        .ownerUsername(r.getAgent().getUser().getUsername())
                        .build())
                .toList();
    }

    private AgentResponse toResponse(Agent a) {
        return AgentResponse.builder()
                .id(a.getId())
                .name(a.getName())
                .persona(a.getPersona().name())
                .aggressionLevel(a.getAggressionLevel())
                .logicWeight(a.getLogicWeight())
                .emotionWeight(a.getEmotionWeight())
                .evidencePreference(a.getEvidencePreference())
                .totalDebates(a.getTotalDebates())
                .wins(a.getWins())
                .losses(a.getLosses())
                .draws(a.getDraws())
                .eloRating(a.getEloRating())
                .build();
    }
}
