# CodeReviewEnv 🔍

An OpenEnv-compliant environment where an AI agent performs **real Python code review** — detecting bugs, classifying them by type and severity, and generating corrected code.

This simulates a task that professional software engineers do every day, making it a meaningful benchmark for AI agent capability.

---

## Environment Description

The agent receives Python code snippets containing intentional, realistic bugs. The bugs span a range of categories: logic errors, off-by-one mistakes, type errors, security vulnerabilities, and more.

The environment exposes 3 tasks of increasing difficulty:

| Task ID | Difficulty | What the Agent Does |
|---|---|---|
| `bug_detection` | Easy | Identify if a bug exists and its line number |
| `bug_classification` | Medium | Classify bug type + severity |
| `code_fix` | Hard | Generate corrected code |

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

The action is a JSON `response` object. Schema depends on the task:

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

Rewards provide **partial progress signals** across the full trajectory — not just binary end-of-episode scores.

| Component | Task | Weight |
|---|---|---|
| Correct has_bug | detection | 0.5 |
| Correct line number (±1) | detection | 0.5 |
| Correct bug_type | classification | 0.4 |
| Correct severity | classification | 0.3 |
| Correct line number | classification | 0.2 |
| Has explanation | classification | 0.1 |
| Valid Python syntax | fix | 0.2 |
| Structurally similar | fix | 0.1 |
| Matches expected fix | fix | 0.4 |
| Runs without error | fix | 0.2 |
| Has explanation | fix | 0.1 |

Additional shaping:
- **Step penalty**: -0.02 per step (efficiency incentive)
- **First-try bonus**: +0.1 for perfect score on step 1
- **Garbage penalty**: -0.3 for empty/invalid responses

---

## Setup & Usage

### Local

```bash
git clone <repo>
cd codereview-env
pip install -r requirements.txt
```

**Run the server:**
```bash
python server.py
# API at http://localhost:7860
```

**Run baseline:**
```bash
export OPENAI_API_KEY=sk-...
python baseline.py --model gpt-4o-mini --snippets 5
```

### Docker

```bash
docker build -t codereview-env .
docker run -p 7860:7860 -e OPENAI_API_KEY=sk-... codereview-env
```

### Python API

```python
from env import CodeReviewEnv, Action

env = CodeReviewEnv(task_id="bug_detection", seed=42)
obs = env.reset()

action = Action(response={"has_bug": True, "line_number": 7})
obs, reward, done, info = env.step(action)

print(f"Score: {info['score']}, Reward: {reward}")
```

---

## Baseline Scores

Evaluated on `gpt-4o-mini` with 5 snippets per task, temperature=0, seed=42:

| Task | Difficulty | Avg Score |
|---|---|---|
| bug_detection | Easy | ~0.82 |
| bug_classification | Medium | ~0.61 |
| code_fix | Hard | ~0.44 |

---

## Dataset

The environment includes 10 hand-crafted Python snippets covering:
- Logic errors (division by zero, infinite loops, wrong operators)
- Off-by-one errors (binary search, slicing)
- Type errors (uncast input)
- Security vulnerabilities (shell injection)
- Scope/closure bugs (late binding lambdas)
- Mutable default arguments
- Recursion bugs

Each snippet includes: bug location, type, severity, expected fix, and test cases.

---

## HTTP API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Health check |
| `/reset` | POST | Start new episode |
| `/step` | POST | Submit agent action |
| `/state` | GET | Get current env state |
| `/tasks` | GET | List available tasks |

---

## File Structure

```
codereview-env/
├── env.py           # Main environment (step/reset/state)
├── tasks.py         # 3 task definitions + graders
├── dataset.py       # Buggy Python snippets
├── reward.py        # Shaped reward function
├── server.py        # FastAPI HTTP server
├── baseline.py      # OpenAI baseline inference script
├── openenv.yaml     # OpenEnv spec metadata
├── Dockerfile
├── requirements.txt
└── README.md
```
