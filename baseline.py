"""
Baseline inference script for CodeReviewEnv.

Uses the OpenAI API client to run a model against all 3 tasks
and produces reproducible baseline scores.

Usage:
    export OPENAI_API_KEY=your_key_here
    python baseline.py

    # Or with a custom model:
    python baseline.py --model gpt-4o-mini --snippets 5
"""

import os
import json
import argparse
import time
from openai import OpenAI
from env import CodeReviewEnv, Action
from dataset import BUGGY_SNIPPETS


TASK_SYSTEM_PROMPTS = {
    "bug_detection": (
        "You are an expert Python code reviewer. "
        "When given a code snippet, detect if it has a bug and identify the line number.\n"
        "Always respond with ONLY valid JSON. No markdown, no explanation outside JSON.\n"
        'Format: {"has_bug": true/false, "line_number": <int or null>}'
    ),
    "bug_classification": (
        "You are an expert Python code reviewer. "
        "Classify the bug in the code snippet.\n"
        "Bug types: logic, off_by_one, type, security, style, performance\n"
        "Severities: low, medium, high, critical\n"
        "Always respond with ONLY valid JSON. No markdown, no explanation outside JSON.\n"
        'Format: {"bug_type": "<type>", "severity": "<severity>", '
        '"line_number": <int>, "explanation": "<string>"}'
    ),
    "code_fix": (
        "You are an expert Python code reviewer and debugger. "
        "Find and fix the bug in the code snippet.\n"
        "Always respond with ONLY valid JSON. No markdown, no explanation outside JSON.\n"
        'Format: {"fixed_code": "<corrected python code as single string>", '
        '"explanation": "<what was wrong and what you changed>"}'
    ),
}


def run_agent_on_task(client: OpenAI, model: str, task_id: str, n_snippets: int, seed: int = 42) -> dict:
    """Run the agent on a single task and return results."""
    env = CodeReviewEnv(task_id=task_id, seed=seed)
    system_prompt = TASK_SYSTEM_PROMPTS[task_id]

    results = []
    total_score = 0.0

    for i, snippet in enumerate(BUGGY_SNIPPETS[:n_snippets]):
        obs = env.reset()
        # Override with specific snippet for reproducibility
        env._current_snippet = snippet

        obs = env._make_observation()
        user_message = (
            f"Task: {obs.task_description}\n\n"
            f"Code snippet:\n```python\n{obs.code_snippet}\n```"
        )

        # Call the model
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.0,  # Deterministic for reproducibility
                max_tokens=512,
            )
            raw_text = response.choices[0].message.content.strip()

            # Strip markdown fences if present
            if raw_text.startswith("```"):
                raw_text = raw_text.split("```")[1]
                if raw_text.startswith("json"):
                    raw_text = raw_text[4:]
                raw_text = raw_text.strip()

            agent_response = json.loads(raw_text)
        except json.JSONDecodeError as e:
            print(f"  [!] JSON parse error on snippet {snippet['id']}: {e}")
            agent_response = {}
        except Exception as e:
            print(f"  [!] API error on snippet {snippet['id']}: {e}")
            agent_response = {}

        # Step the environment
        action = Action(response=agent_response)
        obs, reward, done, info = env.step(action)

        score = info["score"]
        total_score += score
        results.append({
            "snippet_id": snippet["id"],
            "score": score,
            "reward": reward,
            "breakdown": info["breakdown"],
            "agent_response": agent_response,
        })

        print(f"  Snippet {snippet['id']:20s} | score={score:.2f} | reward={reward:.4f}")
        time.sleep(0.3)  # Rate limit courtesy

    avg_score = total_score / len(results) if results else 0.0
    return {
        "task_id": task_id,
        "model": model,
        "n_snippets": len(results),
        "average_score": round(avg_score, 4),
        "results": results,
    }


def main():
    parser = argparse.ArgumentParser(description="CodeReviewEnv Baseline")
    parser.add_argument("--model", default="gpt-4o-mini", help="OpenAI model name")
    parser.add_argument("--snippets", type=int, default=5, help="Number of snippets per task")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output", default="baseline_results.json", help="Output file path")
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENAI_API_KEY environment variable not set.")

    client = OpenAI(api_key=api_key)

    print(f"\n{'='*60}")
    print(f"  CodeReviewEnv Baseline")
    print(f"  Model: {args.model} | Snippets per task: {args.snippets}")
    print(f"{'='*60}\n")

    all_results = {}
    task_ids = ["bug_detection", "bug_classification", "code_fix"]

    for task_id in task_ids:
        print(f"\n[Task] {task_id}")
        print("-" * 40)
        task_results = run_agent_on_task(
            client=client,
            model=args.model,
            task_id=task_id,
            n_snippets=args.snippets,
            seed=args.seed,
        )
        all_results[task_id] = task_results
        print(f"  => Average Score: {task_results['average_score']:.4f}")

    # Summary
    print(f"\n{'='*60}")
    print("  BASELINE SUMMARY")
    print(f"{'='*60}")
    overall = 0.0
    for task_id, res in all_results.items():
        difficulty = {"bug_detection": "easy", "bug_classification": "medium", "code_fix": "hard"}[task_id]
        print(f"  {task_id:30s} [{difficulty:6s}]  score={res['average_score']:.4f}")
        overall += res["average_score"]
    print(f"\n  Overall Average: {overall / len(task_ids):.4f}")
    print(f"{'='*60}\n")

    # Save results
    with open(args.output, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"Results saved to {args.output}")


if __name__ == "__main__":
    main()
