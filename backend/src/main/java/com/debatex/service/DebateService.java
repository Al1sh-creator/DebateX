package com.debatex.service;

import com.debatex.dto.Dtos.*;
import com.debatex.model.*;
import com.debatex.repository.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;

import java.time.LocalDateTime;
import java.util.*;

@Slf4j
@Service
@RequiredArgsConstructor
public class DebateService {

        private final DebateRepository debateRepository;
        private final AgentRepository agentRepository;
        private final RoundRepository roundRepository;
        private final ScoreRepository scoreRepository;
        private final AgentQTableRepository qTableRepository;
        private final UserRepository userRepository;
        private final RankingService rankingService;
        private final SimpMessagingTemplate messagingTemplate;

        @Value("${app.ai-service.url}")
        private String aiServiceUrl;

        public DebateResponse createAndRunDebate(StartDebateRequest request, String username) {
                User user = userRepository.findByUsername(username)
                                .orElseThrow(() -> new RuntimeException("User not found"));

                Agent agentA = agentRepository.findById(request.getAgentAId())
                                .orElseThrow(() -> new RuntimeException("Agent A not found"));
                Agent agentB = agentRepository.findById(request.getAgentBId())
                                .orElseThrow(() -> new RuntimeException("Agent B not found"));

                int numRounds = request.getNumRounds() != null ? request.getNumRounds() : 3;

                Debate debate = Debate.builder()
                                .topic(request.getTopic())
                                .agentA(agentA)
                                .agentB(agentB)
                                .numRounds(numRounds)
                                .createdBy(user)
                                .status(Debate.Status.IN_PROGRESS)
                                .startedAt(LocalDateTime.now())
                                .build();

                debate = debateRepository.save(debate);

                // Run the debate asynchronously
                final Debate savedDebate = debate;
                new Thread(() -> runDebate(savedDebate, agentA, agentB)).start();

                return toDebateResponse(debate);
        }

        private void runDebate(Debate debate, Agent agentA, Agent agentB) {
                try {
                        WebClient client = WebClient.create(aiServiceUrl);
                        List<Map<String, Object>> conversationHistory = new ArrayList<>();
                        int totalScoreA = 0, totalScoreB = 0;

                        for (int round = 1; round <= debate.getNumRounds(); round++) {
                                // Broadcast round start
                                broadcastEvent(debate.getId(), "round_start", Map.of(
                                                "round", round, "total", debate.getNumRounds()));
                                Thread.sleep(1500); // Let users see the round banner

                                // Get Agent A's Q-table entries
                                List<AgentQTable> qTableA = qTableRepository.findByAgentId(agentA.getId());
                                String opponentLastStrategy = conversationHistory.isEmpty() ? null
                                                : (String) conversationHistory.get(conversationHistory.size() - 1)
                                                                .getOrDefault("strategy",
                                                                                null);

                                // ── Agent A generates argument ──
                                broadcastEvent(debate.getId(), "typing_start", Map.of(
                                                "bot", "A", "round", round, "name", agentA.getName()));

                                Map<String, Object> stateA = buildAgentState(
                                                debate.getTopic(), round, debate.getNumRounds(),
                                                agentA, agentB, "PRO", conversationHistory, opponentLastStrategy);

                                Map<String, Object> argResponseA = callAiService(client, "/generate-argument",
                                                Map.of("state", stateA, "q_table", convertQTable(qTableA)));

                                String argumentA = (String) argResponseA.getOrDefault("argument",
                                                "Agent A could not generate an argument.");
                                String strategyA = (String) argResponseA.getOrDefault("chosen_strategy",
                                                "LOGICAL_ARGUMENT");

                                broadcastEvent(debate.getId(), "turn_complete", Map.of(
                                                "bot", "A", "content", argumentA, "strategy", strategyA,
                                                "round", round, "persona", agentA.getPersona().name()));

                                conversationHistory.add(
                                                Map.of("role", "agentA", "content", argumentA, "strategy", strategyA));

                                Thread.sleep(1500); // Let users read Agent A's argument

                                // ── Agent B generates argument ──
                                broadcastEvent(debate.getId(), "typing_start", Map.of(
                                                "bot", "B", "round", round, "name", agentB.getName()));

                                List<AgentQTable> qTableB = qTableRepository.findByAgentId(agentB.getId());

                                Map<String, Object> stateB = buildAgentState(
                                                debate.getTopic(), round, debate.getNumRounds(),
                                                agentB, agentA, "CON", conversationHistory, strategyA);

                                Map<String, Object> argResponseB = callAiService(client, "/generate-argument",
                                                Map.of("state", stateB, "q_table", convertQTable(qTableB)));

                                String argumentB = (String) argResponseB.getOrDefault("argument",
                                                "Agent B could not generate an argument.");
                                String strategyB = (String) argResponseB.getOrDefault("chosen_strategy",
                                                "LOGICAL_ARGUMENT");

                                broadcastEvent(debate.getId(), "turn_complete", Map.of(
                                                "bot", "B", "content", argumentB, "strategy", strategyB,
                                                "round", round, "persona", agentB.getPersona().name()));

                                conversationHistory.add(
                                                Map.of("role", "agentB", "content", argumentB, "strategy", strategyB));

                                Thread.sleep(1500); // Let users read Agent B's argument

                                // ── Save Round ──
                                Round.Strategy roundStratA = Round.Strategy.valueOf(strategyA);
                                Round.Strategy roundStratB = Round.Strategy.valueOf(strategyB);

                                Round debateRound = Round.builder()
                                                .debate(debate)
                                                .roundNumber(round)
                                                .agentAArgument(argumentA)
                                                .agentBArgument(argumentB)
                                                .agentAStrategy(roundStratA)
                                                .agentBStrategy(roundStratB)
                                                .build();

                                debateRound = roundRepository.save(debateRound);

                                // ── Judge the round ──
                                broadcastEvent(debate.getId(), "judging", Map.of("round", round));
                                Thread.sleep(1500); // Build anticipation for judging

                                Map<String, Object> judgeRequest = Map.of(
                                                "topic", debate.getTopic(),
                                                "round_number", round,
                                                "agent_a_argument", argumentA,
                                                "agent_b_argument", argumentB,
                                                "agent_a_strategy", strategyA,
                                                "agent_b_strategy", strategyB,
                                                "agent_a_profile", buildProfile(agentA),
                                                "agent_b_profile", buildProfile(agentB));

                                Map<String, Object> judgeResponse = callAiService(client, "/judge-round", judgeRequest);

                                // Save scores
                                Map<String, Object> scoresA = (Map<String, Object>) judgeResponse.getOrDefault(
                                                "agent_a_scores",
                                                Map.of());
                                Map<String, Object> scoresB = (Map<String, Object>) judgeResponse.getOrDefault(
                                                "agent_b_scores",
                                                Map.of());

                                Score scoreA = saveScore(debateRound, debate, agentA, scoresA,
                                                (String) judgeResponse.getOrDefault("feedback_a", ""));
                                Score scoreB = saveScore(debateRound, debate, agentB, scoresB,
                                                (String) judgeResponse.getOrDefault("feedback_b", ""));

                                totalScoreA += scoreA.getTotalScore().intValue();
                                totalScoreB += scoreB.getTotalScore().intValue();

                                broadcastEvent(debate.getId(), "round_scored", Map.of(
                                                "round", round,
                                                "agent_a_scores", scoresA,
                                                "agent_b_scores", scoresB,
                                                "agent_a_total", scoreA.getTotalScore(),
                                                "agent_b_total", scoreB.getTotalScore(),
                                                "feedback_a", judgeResponse.getOrDefault("feedback_a", ""),
                                                "feedback_b", judgeResponse.getOrDefault("feedback_b", ""),
                                                "analysis", judgeResponse.getOrDefault("analysis", "")));

                                Thread.sleep(2000); // Let users read the judge's evaluation
                        }

                        // ── Determine Winner ──
                        String winner;
                        boolean isDraw = false;
                        Agent winnerAgent = null;

                        if (totalScoreA > totalScoreB) {
                                winner = "A";
                                winnerAgent = agentA;
                                agentA.setWins(agentA.getWins() + 1);
                                agentB.setLosses(agentB.getLosses() + 1);
                        } else if (totalScoreB > totalScoreA) {
                                winner = "B";
                                winnerAgent = agentB;
                                agentB.setWins(agentB.getWins() + 1);
                                agentA.setLosses(agentA.getLosses() + 1);
                        } else {
                                winner = "TIE";
                                isDraw = true;
                                agentA.setDraws(agentA.getDraws() + 1);
                                agentB.setDraws(agentB.getDraws() + 1);
                        }

                        agentA.setTotalDebates(agentA.getTotalDebates() + 1);
                        agentB.setTotalDebates(agentB.getTotalDebates() + 1);
                        agentRepository.save(agentA);
                        agentRepository.save(agentB);

                        // Update ELO ratings
                        rankingService.updateElo(agentA, agentB, winner, debate);

                        // Finalize debate
                        debate.setStatus(Debate.Status.COMPLETED);
                        debate.setWinnerAgent(winnerAgent);
                        debate.setIsDraw(isDraw);
                        debate.setTotalScoreA(totalScoreA);
                        debate.setTotalScoreB(totalScoreB);
                        debate.setFinalVerdict(String.format(
                                        "After %d rounds, %s wins with a score of %d to %d!",
                                        debate.getNumRounds(),
                                        winner.equals("TIE") ? "It's a tie" : "Agent " + winner,
                                        Math.max(totalScoreA, totalScoreB),
                                        Math.min(totalScoreA, totalScoreB)));
                        debate.setCompletedAt(LocalDateTime.now());
                        debateRepository.save(debate);

                        broadcastEvent(debate.getId(), "debate_end", Map.of(
                                        "winner", winner,
                                        "totalScoreA", totalScoreA,
                                        "totalScoreB", totalScoreB,
                                        "finalVerdict", debate.getFinalVerdict()));

                } catch (Exception e) {
                        log.error("Debate execution failed", e);
                        debate.setStatus(Debate.Status.CANCELLED);
                        debate.setFinalVerdict("Debate failed: " + e.getMessage());
                        debateRepository.save(debate);
                        broadcastEvent(debate.getId(), "error", Map.of("message", e.getMessage()));
                }
        }

        // ── Helper methods ──

        private Map<String, Object> buildAgentState(String topic, int round, int totalRounds,
                        Agent agent, Agent opponent, String stance,
                        List<Map<String, Object>> history, String opponentLastStrategy) {
                Map<String, Object> state = new HashMap<>();
                state.put("topic", topic);
                state.put("round_number", round);
                state.put("total_rounds", totalRounds);
                state.put("agent_profile", buildProfile(agent));
                state.put("opponent_profile", buildProfile(opponent));
                state.put("stance", stance);
                state.put("conversation_history", history);
                state.put("opponent_last_strategy", opponentLastStrategy);
                return state;
        }

        private Map<String, Object> buildProfile(Agent agent) {
                Map<String, Object> profile = new HashMap<>();
                profile.put("agent_id", agent.getId());
                profile.put("name", agent.getName());
                profile.put("persona", agent.getPersona().name());
                profile.put("aggression_level", agent.getAggressionLevel());
                profile.put("logic_weight", agent.getLogicWeight());
                profile.put("emotion_weight", agent.getEmotionWeight());
                profile.put("evidence_preference", agent.getEvidencePreference());
                return profile;
        }

        private List<Map<String, Object>> convertQTable(List<AgentQTable> entries) {
                return entries.stream().map(e -> {
                        Map<String, Object> m = new HashMap<>();
                        m.put("agent_id", e.getAgent().getId());
                        m.put("state_key", e.getStateKey());
                        m.put("action", e.getAction().name());
                        m.put("q_value", e.getQValue());
                        m.put("visit_count", e.getVisitCount());
                        return m;
                }).toList();
        }

        @SuppressWarnings("unchecked")
        private Map<String, Object> callAiService(WebClient client, String endpoint, Map<String, Object> body) {
                try {
                        return client.post()
                                        .uri(endpoint)
                                        .bodyValue(body)
                                        .retrieve()
                                        .bodyToMono(Map.class)
                                        .block();
                } catch (Exception e) {
                        log.error("AI service call failed: {}", endpoint, e);
                        return Map.of("error", e.getMessage());
                }
        }

        private Score saveScore(Round round, Debate debate, Agent agent,
                        Map<String, Object> scores, String feedback) {
                Score score = Score.builder()
                                .round(round)
                                .debate(debate)
                                .agent(agent)
                                .logicalConsistency(toFloat(scores.get("logical_consistency")))
                                .semanticRelevance(toFloat(scores.get("semantic_relevance")))
                                .argumentCoherence(toFloat(scores.get("argument_coherence")))
                                .emotionalToneImpact(toFloat(scores.get("emotional_tone_impact")))
                                .fallacyPenalty(toFloat(scores.get("fallacy_penalty")))
                                .evidenceStrength(toFloat(scores.get("evidence_strength")))
                                .totalScore(toFloat(scores.get("total_score")))
                                .feedback(feedback)
                                .build();
                return scoreRepository.save(score);
        }

        private Float toFloat(Object value) {
                if (value == null)
                        return 0f;
                if (value instanceof Number n)
                        return n.floatValue();
                try {
                        return Float.parseFloat(value.toString());
                } catch (Exception e) {
                        return 0f;
                }
        }

        private void broadcastEvent(Long debateId, String eventType, Map<String, Object> data) {
                Map<String, Object> event = new HashMap<>(data);
                event.put("event", eventType);
                messagingTemplate.convertAndSend("/topic/debate/" + debateId, event);
        }

        public DebateResponse getDebate(Long id) {
                Debate debate = debateRepository.findById(id)
                                .orElseThrow(() -> new RuntimeException("Debate not found"));
                return toDebateResponse(debate);
        }

        public List<DebateResponse> getUserDebates(String username) {
                User user = userRepository.findByUsername(username)
                                .orElseThrow(() -> new RuntimeException("User not found"));
                return debateRepository.findByCreatedByIdOrderByCreatedAtDesc(user.getId())
                                .stream().map(this::toDebateResponse).toList();
        }

        public List<RoundResponse> getDebateRounds(Long debateId) {
                return roundRepository.findByDebateIdOrderByRoundNumber(debateId)
                                .stream().map(r -> RoundResponse.builder()
                                                .roundNumber(r.getRoundNumber())
                                                .agentAArgument(r.getAgentAArgument())
                                                .agentBArgument(r.getAgentBArgument())
                                                .agentAStrategy(r.getAgentAStrategy().name())
                                                .agentBStrategy(r.getAgentBStrategy().name())
                                                .agentASentiment(r.getAgentASentiment())
                                                .agentBSentiment(r.getAgentBSentiment())
                                                .build())
                                .toList();
        }

        public List<ScoreResponse> getDebateScores(Long debateId) {
                return scoreRepository.findByDebateId(debateId)
                                .stream().map(s -> ScoreResponse.builder()
                                                .roundNumber(s.getRound().getRoundNumber())
                                                .agentName(s.getAgent().getName())
                                                .logicalConsistency(s.getLogicalConsistency())
                                                .semanticRelevance(s.getSemanticRelevance())
                                                .argumentCoherence(s.getArgumentCoherence())
                                                .emotionalToneImpact(s.getEmotionalToneImpact())
                                                .fallacyPenalty(s.getFallacyPenalty())
                                                .evidenceStrength(s.getEvidenceStrength())
                                                .totalScore(s.getTotalScore())
                                                .feedback(s.getFeedback())
                                                .build())
                                .toList();
        }

        @SuppressWarnings("unchecked")
        public DebateSummaryResponse getDebateSummary(Long debateId) {
                Debate debate = debateRepository.findById(debateId)
                                .orElseThrow(() -> new RuntimeException("Debate not found"));

                List<Round> rounds = roundRepository.findByDebateIdOrderByRoundNumber(debateId);
                List<Map<String, Object>> arguments = new ArrayList<>();

                for (Round r : rounds) {
                        arguments.add(Map.of("agent", "A", "text", r.getAgentAArgument()));
                        arguments.add(Map.of("agent", "B", "text", r.getAgentBArgument()));
                }

                WebClient client = WebClient.create(aiServiceUrl);
                Map<String, Object> request = Map.of(
                                "topic", debate.getTopic(),
                                "arguments", arguments
                );

                Map<String, Object> response = callAiService(client, "/summarize-debate", request);

                List<String> summaryA = (List<String>) response.getOrDefault("summary_a", List.of("No summary available."));
                List<String> summaryB = (List<String>) response.getOrDefault("summary_b", List.of("No summary available."));

                return DebateSummaryResponse.builder()
                                .summaryA(summaryA)
                                .summaryB(summaryB)
                                .build();
        }

        private DebateResponse toDebateResponse(Debate d) {

                return DebateResponse.builder()
                                .id(d.getId())
                                .topic(d.getTopic())
                                .agentA(toAgentResponse(d.getAgentA()))
                                .agentB(toAgentResponse(d.getAgentB()))
                                .numRounds(d.getNumRounds())
                                .status(d.getStatus().name())
                                .winner(d.getWinnerAgent() != null ? d.getWinnerAgent().getName()
                                                : (d.getIsDraw() ? "TIE" : null))
                                .isDraw(d.getIsDraw())
                                .totalScoreA(d.getTotalScoreA())
                                .totalScoreB(d.getTotalScoreB())
                                .finalVerdict(d.getFinalVerdict())
                                .build();
        }

        private AgentResponse toAgentResponse(Agent a) {
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
