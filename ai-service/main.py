"""
DebateX AI Service — FastAPI Application

Endpoints:
  POST /generate-argument   → Generate a debate argument with Q-learning strategy
  POST /judge-round          → Judge a debate round (6-dimension scoring)
  POST /update-q-table       → Update Q-values after receiving rewards
  POST /get-strategy         → Get optimal strategy for a given state
  GET  /health               → Health check
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models.schemas import (
    GenerateArgumentRequest, GenerateArgumentResponse,
    JudgeRoundRequest, JudgeRoundResponse,
    UpdateQTableRequest, UpdateQTableResponse,
    GetStrategyRequest, GetStrategyResponse,
    QTableEntry,
)
from agents.debate_agent import (
    select_strategy, build_argument_prompt,
    generate_argument_with_model, _fallback_argument,
)
from agents.judge_agent import judge_round
from agents.q_learning import QLearningEngine, compute_reward, encode_state
from warmup import warmup_nlp


# ── FastAPI App ──────────────────────────────────────────────

app = FastAPI(
    title="DebateX AI Service",
    description="Multi-agent debate AI with Q-learning and NLP scoring",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Warm up NLP models on startup."""
    import asyncio
    # Run warmup in a thread to not block the event loop
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, warmup_nlp)


# ── Endpoints ────────────────────────────────────────────────

@app.post("/generate-argument", response_model=GenerateArgumentResponse)
async def generate_argument_endpoint(request: GenerateArgumentRequest):
    """
    Generate a debate argument.

    1. Selects strategy via Q-learning (epsilon-greedy + personality bias)
    2. Builds a prompt based on persona, stance, history, and strategy
    3. Generates the argument text
    """
    try:
        # Step 1: Select strategy
        strategy, q_values, was_exploration = select_strategy(
            state=request.state,
            q_table_entries=request.q_table,
            epsilon=0.15,
        )

        # Step 2: Build the prompt
        prompt = build_argument_prompt(request.state, strategy)

        # Step 3: Generate argument
        argument = await generate_argument_with_model(prompt)

        reasoning = (
            f"{'Explored randomly' if was_exploration else 'Exploited best Q-value'}. "
            f"Q-values: {', '.join(f'{k}: {v:.2f}' for k, v in q_values.items())}. "
            f"Personality bias applied: aggression={request.state.agent_profile.aggression_level}, "
            f"logic={request.state.agent_profile.logic_weight}."
        )

        return GenerateArgumentResponse(
            argument=argument,
            chosen_strategy=strategy,
            strategy_reasoning=reasoning,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Argument generation failed: {str(e)}")


@app.post("/judge-round", response_model=JudgeRoundResponse)
async def judge_round_endpoint(request: JudgeRoundRequest):
    """
    Judge a debate round.

    Evaluates both arguments on 6 NLP dimensions:
    logical consistency, semantic relevance, argument coherence,
    emotional tone impact, fallacy penalty, evidence strength.
    """
    try:
        return judge_round(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Judging failed: {str(e)}")


@app.post("/update-q-table", response_model=UpdateQTableResponse)
async def update_q_table_endpoint(request: UpdateQTableRequest):
    """
    Update Q-values after receiving reward signal.

    Uses Bellman equation: Q(s,a) ← Q(s,a) + α[r + γ·max Q(s',a') - Q(s,a)]
    """
    try:
        engine = QLearningEngine(
            learning_rate=request.learning_rate,
            discount_factor=request.discount_factor,
        )
        engine.load_q_table(request.q_table)

        # Compute composite reward
        reward_value = compute_reward(request.reward)

        # Perform Q-learning update
        new_q = engine.update(
            state_key=request.state_key,
            action=request.action,
            reward=reward_value,
            next_state_key=request.next_state_key,
        )

        updated_entry = QTableEntry(
            agent_id=request.agent_id,
            state_key=request.state_key,
            action=request.action,
            q_value=new_q,
            visit_count=engine.visit_counts.get((request.state_key, request.action), 1),
        )

        return UpdateQTableResponse(
            updated_entry=updated_entry,
            reward_value=round(reward_value, 4),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Q-table update failed: {str(e)}")


@app.post("/get-strategy", response_model=GetStrategyResponse)
async def get_strategy_endpoint(request: GetStrategyRequest):
    """
    Get the optimal strategy for a given state without generating an argument.
    Useful for strategy preview and analytics.
    """
    try:
        from agents.debate_agent import get_personality_weights

        engine = QLearningEngine(epsilon=request.epsilon)
        engine.load_q_table(request.q_table)

        personality_weights = get_personality_weights(request.agent_profile)
        chosen, was_exploration = engine.select_action(request.state_key, personality_weights)
        q_values = {s.value: engine.get_q_value(request.state_key, s) for s in engine.q_table if s[0] == request.state_key}

        # If no entries found, return base Q-values
        if not q_values:
            from models.schemas import Strategy
            q_values = {s.value: 0.0 for s in Strategy}

        return GetStrategyResponse(
            chosen_strategy=chosen,
            q_values=q_values,
            was_exploration=was_exploration,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Strategy selection failed: {str(e)}")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "debatex-ai-service", "version": "1.0.0"}


# ── Run ──────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
