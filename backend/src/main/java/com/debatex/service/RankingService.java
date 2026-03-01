package com.debatex.service;

import com.debatex.model.*;
import com.debatex.repository.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

@Slf4j
@Service
@RequiredArgsConstructor
public class RankingService {

    private final RankingRepository rankingRepository;
    private final AgentRepository agentRepository;
    private final ScoreRepository scoreRepository;

    private static final int K_FACTOR = 32;
    private static final int INITIAL_ELO = 1200;

    /**
     * Update ELO ratings after a debate.
     *
     * Formula:
     * Expected(A) = 1 / (1 + 10^((R_B - R_A) / 400))
     * R_A_new = R_A + K × (S_A − Expected(A))
     *
     * S = 1.0 for win, 0.5 for tie, 0.0 for loss
     */
    public void updateElo(Agent agentA, Agent agentB, String winner, Debate debate) {
        int ratingA = agentA.getEloRating();
        int ratingB = agentB.getEloRating();

        double expectedA = 1.0 / (1.0 + Math.pow(10, (ratingB - ratingA) / 400.0));
        double expectedB = 1.0 / (1.0 + Math.pow(10, (ratingA - ratingB) / 400.0));

        double scoreA, scoreB;
        switch (winner) {
            case "A" -> {
                scoreA = 1.0;
                scoreB = 0.0;
            }
            case "B" -> {
                scoreA = 0.0;
                scoreB = 1.0;
            }
            default -> {
                scoreA = 0.5;
                scoreB = 0.5;
            }
        }

        int newRatingA = (int) Math.round(ratingA + K_FACTOR * (scoreA - expectedA));
        int newRatingB = (int) Math.round(ratingB + K_FACTOR * (scoreB - expectedB));

        // Update agent ELO
        agentA.setEloRating(newRatingA);
        agentB.setEloRating(newRatingB);
        agentRepository.save(agentA);
        agentRepository.save(agentB);

        // Update rankings
        updateRanking(agentA);
        updateRanking(agentB);

        // Recalculate rank positions
        recalculatePositions();

        log.info("ELO updated: {} ({} → {}), {} ({} → {})",
                agentA.getName(), ratingA, newRatingA,
                agentB.getName(), ratingB, newRatingB);
    }

    private void updateRanking(Agent agent) {
        Ranking ranking = rankingRepository.findByAgentId(agent.getId())
                .orElse(Ranking.builder()
                        .agent(agent)
                        .eloRating(INITIAL_ELO)
                        .build());

        ranking.setEloRating(agent.getEloRating());
        ranking.setTotalDebates(agent.getTotalDebates());

        float winRate = agent.getTotalDebates() > 0
                ? (float) agent.getWins() / agent.getTotalDebates() * 100
                : 0f;
        ranking.setWinRate(winRate);

        Float avgScore = scoreRepository.findAverageScoreByAgentId(agent.getId());
        ranking.setAvgScore(avgScore != null ? avgScore : 0f);

        rankingRepository.save(ranking);
    }

    private void recalculatePositions() {
        var rankings = rankingRepository.findAllByOrderByEloRatingDesc();
        for (int i = 0; i < rankings.size(); i++) {
            rankings.get(i).setRankPosition(i + 1);
        }
        rankingRepository.saveAll(rankings);
    }
}
