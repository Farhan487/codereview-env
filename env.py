"""
CodeReviewEnv - OpenEnv compliant environment for AI code review tasks.
"""

import json
import random
from typing import Any
from pydantic import BaseModel
from dataset import BUGGY_SNIPPETS
from tasks import BugDetectionTask, BugClassificationTask, CodeFixTask
from reward import RewardCalculator


# ── Typed Models (OpenEnv spec) ──────────────────────────────────────────────

class Observation(BaseModel):
    code_snippet: str
    language: str
    task_description: str
    task_id: str
    step_number: int
    max_steps: int


class Action(BaseModel):
    # For detection: {"has_bug": true/false, "line_number": int or null}
    # For classification: {"bug_type": str, "severity": str, "line_number": int}
    # For fix: {"fixed_code": str, "explanation": str}
    response: dict


class Reward(BaseModel):
    value: float
    breakdown: dict
    done: bool
    info: dict


# ── Main Environment ──────────────────────────────────────────────────────────

class CodeReviewEnv:
    """
    OpenEnv-compliant Code Review Environment.

    An AI agent receives buggy Python code and must:
    - Task 1 (Easy):   Detect if there's a bug and find its line number
    - Task 2 (Medium): Classify the bug type and severity
    - Task 3 (Hard):   Generate a corrected version of the code
    """

    TASKS = {
        "bug_detection": BugDetectionTask,
        "bug_classification": BugClassificationTask,
        "code_fix": CodeFixTask,
    }

    def __init__(self, task_id: str = "bug_detection", seed: int = 42):
        if task_id not in self.TASKS:
            raise ValueError(f"task_id must be one of {list(self.TASKS.keys())}")
        self.task_id = task_id
        self.seed = seed
        self._rng = random.Random(seed)
        self.task = self.TASKS[task_id]()
        self.reward_calc = RewardCalculator()
        self._current_snippet = None
        self._step_num = 0
        self._max_steps = 5
        self._done = False
        self._cumulative_reward = 0.0
        self._history = []

    # ── OpenEnv API ───────────────────────────────────────────────────────────

    def reset(self) -> Observation:
        """Reset environment and return initial observation."""
        self._step_num = 0
        self._done = False
        self._cumulative_reward = 0.0
        self._history = []
        self._current_snippet = self._rng.choice(BUGGY_SNIPPETS)
        return self._make_observation()

    def step(self, action: Action) -> tuple[Observation, float, bool, dict]:
        """
        Process agent action and return (observation, reward, done, info).
        """
        if self._done:
            raise RuntimeError("Episode is done. Call reset() to start a new one.")

        self._step_num += 1

        # Grade the action
        score, breakdown = self.task.grade(action.response, self._current_snippet)

        # Compute reward with partial progress signals
        reward = self.reward_calc.compute(
            score=score,
            breakdown=breakdown,
            step_num=self._step_num,
            max_steps=self._max_steps,
        )

        self._cumulative_reward += reward
        self._history.append({"step": self._step_num, "action": action.response, "reward": reward})

        # Episode ends if agent solved it or hit max steps
        self._done = score >= 1.0 or self._step_num >= self._max_steps

        obs = self._make_observation()
        info = {
            "score": max(0.01, min(0.99, score)),
            "breakdown": breakdown,
            "cumulative_reward": self._cumulative_reward,
            "steps_taken": self._step_num,
        }

        return obs, reward, self._done, info

    def state(self) -> dict:
        """Return full current state of the environment."""
        return {
            "task_id": self.task_id,
            "step_number": self._step_num,
            "max_steps": self._max_steps,
            "done": self._done,
            "cumulative_reward": self._cumulative_reward,
            "current_snippet_id": self._current_snippet["id"] if self._current_snippet else None,
            "history": self._history,
        }

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _make_observation(self) -> Observation:
        snippet = self._current_snippet or {}
        return Observation(
            code_snippet=snippet.get("code", ""),
            language=snippet.get("language", "python"),
            task_description=self.task.description,
            task_id=self.task_id,
            step_number=self._step_num,
            max_steps=self._max_steps,
        )
