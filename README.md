---
title: CodeReviewEnv
emoji: 🔍
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
tags:
  - openenv
---

# CodeReviewEnv 🔍

> A real-world OpenEnv environment where AI agents perform Python code review
> detecting bugs, classifying them, and generating fixes.
> Simulates tasks that professional software engineers do every day.

---

## Why Code Review?

Code review is one of the most cognitively demanding tasks in software engineering.
It requires understanding program logic, identifying subtle errors, and reasoning about
correctness — making it an ideal benchmark for AI agent capability.

---

## Tasks

| # | Task ID | Difficulty | What the Agent Does |
|---|---|---|---|
| 1 | `bug_detection` | Easy | Detect if a bug exists + find its line number |
| 2 | `bug_classification` | Medium | Classify bug type + severity level |
| 3 | `code_fix` | Hard | Generate fully corrected Python code |

---

## Bug Categories Covered

10 hand-crafted Python snippets spanning all major bug categories:

- **Security** — shell injection via shell=True
- **Infinite loops** — missing loop increment
- **Off-by-one** — binary search, slicing errors
- **Scope bugs** — late binding closures
- **Mutation bugs** — mutable default arguments
- **Recursion bugs** — missing base case decrement
- **Type errors** — uncast input() values
- **Logic errors** — wrong operators, empty input guards
- **Style bugs** — == None vs is None

---

## Observation Space
```json
{
  "code_snippet": "def calculate_average(numbers):\n    ...",
  "language": "python",
  "task_description": "Examine the code and detect if a bug exists...",
  "task_id": "bug_detection",
  "step_number": 1,
  "max_steps": 5
}
```

---

## Action Space

**bug_detection:**
```json
{"has_bug": true, "line_number": 7}
```

**bug_classification:**
```json
{
  "bug_type": "logic",
  "severity": "high",
  "line_number": 7,
  "explanation": "Division by zero when the input list is empty."
}
```

**code_fix:**
```json
{
  "fixed_code": "def calculate_average(numbers):\n    if not numbers:\n        return 0\n    ...",
  "explanation": "Added an empty-list guard before dividing."
}
```

---

## Reward Function

| Component | Task | Weight |
|---|---|---|
| Correct has_bug | detection | 0.5 |
| Correct line number +/-1 | detection | 0.5 |
| Correct bug_type | classification | 0.4 |
| Correct severity | classification | 0.3 |
| Correct line number | classification | 0.2 |
| Has explanation | classification | 0.1 |
| Valid Python syntax | fix | 0.2 |
| Structurally similar | fix | 0.1 |
| Matches expected fix | fix | 0.4 |
| Runs without error | fix | 0.2 |
| Has explanation | fix | 0.1 |

- Step penalty: -0.02 per step
- First-try bonus: +0.1 for perfect score on step 1
- Garbage penalty: -0.3 for empty/invalid responses

---

## Baseline Scores

Evaluated using Qwen2.5-Coder-1.5B-Instruct — fully local, no API key required.
Apple M1 MPS backend. Seed=42, 3 snippets per task.

| Task | Difficulty | Score |
|---|---|---|
| bug_detection | Easy | 0.000 |
| bug_classification | Medium | 0.387 |
| code_fix | Hard | 0.767 |
| Overall | | 0.385 |

> Low detection score shows the environment correctly challenges weak models.
> Stronger models score significantly higher on the same tasks.

---

## Setup & Usage

### Local
```bash
git clone https://github.com/Farhan487/codereview-env
cd codereview-env
pip install -r requirements.txt
python server.py
```

### Docker
```bash
docker build -t codereview-env .
docker run -p 7860:7860 codereview-env
```

### Python API
```python
from env import CodeReviewEnv, Action

env = CodeReviewEnv(task_id="bug_detection", seed=42)
obs = env.reset()

action = Action(response={"has_bug": True, "line_number": 4})
obs, reward, done, info = env.step(action)

print(f"Score: {info['score']}, Reward: {reward}")
```

### Run Baseline (OpenAI)
```bash
export OPENAI_API_KEY=sk-...
python baseline.py --model gpt-4o-mini --snippets 5
```

### Run Baseline (Local - no API key needed)
```bash
pip install torch transformers accelerate
python hf_baseline.py --model Qwen/Qwen2.5-Coder-1.5B-Instruct --snippets 5
```

---

## HTTP API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Health check |
| `/reset` | POST | Start new episode |
| `/step` | POST | Submit agent action |
| `/state` | GET | Get current env state |
| `/tasks` | GET | List available tasks |

Interactive docs at `/docs`.

---

## File Structure
```
codereview-env/
├── env.py                   # Core environment (step/reset/state)
├── tasks.py                 # 3 task definitions + graders
├── dataset.py               # 10 buggy Python snippets
├── reward.py                # Shaped reward function
├── server.py                # FastAPI HTTP server
├── baseline.py              # OpenAI baseline script
├── hf_baseline.py           # Local HF baseline (no API key)
├── hf_baseline_results.json # Real baseline scores
├── openenv.yaml             # OpenEnv spec metadata
├── Dockerfile
├── requirements.txt
└── README.md
```
