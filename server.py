"""
FastAPI server exposing CodeReviewEnv via HTTP for Hugging Face Spaces.
Implements the OpenEnv HTTP interface: /reset, /step, /state, /health
"""

import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from env import CodeReviewEnv, Action

app = FastAPI(
    title="CodeReviewEnv",
    description="OpenEnv-compliant Python Code Review Environment",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store (single session for simplicity)
_envs: dict[str, CodeReviewEnv] = {}


class ResetRequest(BaseModel):
    task_id: str = "bug_detection"
    seed: int = 42
    session_id: str = "default"
    
    model_config = {"extra": "allow"}


class StepRequest(BaseModel):
    response: dict
    session_id: str = "default"


@app.get("/health")
def health():
    return {"status": "ok", "env": "CodeReviewEnv", "version": "1.0.0"}


@app.post("/reset")
def reset(req: ResetRequest = None):
    if req is None:
        req = ResetRequest()
    env = CodeReviewEnv(task_id=req.task_id, seed=req.seed)
    obs = env.reset()
    _envs[req.session_id] = env
    return {
        "observation": obs.model_dump(),
        "session_id": req.session_id,
    }


@app.post("/step")
def step(req: StepRequest):
    env = _envs.get(req.session_id)
    if env is None:
        raise HTTPException(status_code=404, detail="Session not found. Call /reset first.")

    action = Action(response=req.response)
    obs, reward, done, info = env.step(action)

    # Clamp score strictly between 0 and 1
    if "score" in info:
        info["score"] = max(0.01, min(0.99, float(info["score"])))
    reward = max(0.01, min(0.99, float(reward)))
    return {
        "observation": obs.model_dump(),
        "reward": reward,
        "done": done,
        "info": info,
    }


@app.get("/state")
def state(session_id: str = "default"):
    env = _envs.get(session_id)
    if env is None:
        raise HTTPException(status_code=404, detail="Session not found. Call /reset first.")
    return env.state()


@app.get("/tasks")
def list_tasks():
    return {
        "tasks": [
            {"id": "bug_detection", "difficulty": "easy"},
            {"id": "bug_classification", "difficulty": "medium"},
            {"id": "code_fix", "difficulty": "hard"},
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
