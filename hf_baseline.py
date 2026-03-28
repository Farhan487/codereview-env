"""
Baseline inference script for CodeReviewEnv using Hugging Face & PyTorch.

Specifically adapted to run on an M1 MacBook Air (8GB RAM) using the `mps` backend
and a small (1.5B) but capable programming model: Qwen/Qwen2.5-Coder-1.5B-Instruct

Usage:
    python hf_baseline.py
    
    # Or with a custom Hugging Face model:
    python hf_baseline.py --model Qwen/Qwen2.5-Coder-1.5B-Instruct --snippets 5
"""

import os
import json
import argparse
import time
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from env import CodeReviewEnv, Action
from dataset import BUGGY_SNIPPETS


TASK_SYSTEM_PROMPTS = {
    "bug_detection": (
        "You are an expert Python code reviewer. Analyze the code carefully.\n"
        "Most snippets contain bugs.\n"
        "Return ONLY valid JSON. No markdown. No explanation.\n"
        'Format: {"has_bug": true/false, "line_number": <int or null>}'
    ),
    "bug_classification": (
        "You are an expert Python code reviewer. Analyze the code carefully.\n"
        "Classify the bug in the code snippet. Return ONLY valid JSON. No markdown. No explanation.\n"
        "Bug types: logic, off_by_one, type, security, style, performance\n"
        "Severities: low, medium, high, critical\n"
        'Format: {"bug_type": "<type>", "severity": "<severity>", '
        '"line_number": <int>, "explanation": "<string>"}'
    ),
    "code_fix": (
        "You are an expert Python code reviewer and debugger. Analyze the code carefully.\n"
        "Find and fix the bug in the code snippet. Return ONLY valid JSON. No markdown. No explanation.\n"
        'Format: {"fixed_code": "<corrected python code as single string>", '
        '"explanation": "<what was wrong and what you changed>"}'
    ),
}

def extract_json(raw_text: str) -> dict:
    """Attempt to extract and parse JSON from the model's output text."""
    raw_text = raw_text.strip()
    
    if "```" in raw_text:
        parts = raw_text.split("```")
        for part in parts:
            if part.startswith("json\n"):
                raw_text = part[5:].strip()
                break
            elif part.startswith("json"):
                raw_text = part[4:].strip()
                break
            elif part.strip().startswith("{"):
                raw_text = part.strip()
                break
        else:
            if len(parts) > 1:
                raw_text = parts[1].strip()

    try:
        start = raw_text.find('{')
        end = raw_text.rfind('}')
        if start != -1 and end != -1:
            raw_text = raw_text[start:end+1]
        
        return json.loads(raw_text)
    except json.JSONDecodeError as e:
        print(f"  [!] JSON parse error: {e}")
        return {}


def run_agent_on_task(model, tokenizer, device, task_id: str, n_snippets: int, seed: int = 42) -> dict:
    """Run the agent on a single task and return results."""
    env = CodeReviewEnv(task_id=task_id, seed=seed)
    system_prompt = TASK_SYSTEM_PROMPTS[task_id]

    results = []
    total_score = 0.0

    for i, snippet in enumerate(BUGGY_SNIPPETS[:n_snippets]):
        obs = env.reset()
        env._current_snippet = snippet

        obs = env._make_observation()
        user_message = (
            f"Task: {obs.task_description}\n\n"
            f"Code snippet:\n```python\n{obs.code_snippet}\n```"
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        
        text_prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        model_inputs = tokenizer([text_prompt], return_tensors="pt").to(device)

        try:
            with torch.no_grad():
                generated_ids = model.generate(
                    **model_inputs,
                    max_new_tokens=256,
                    do_sample=False, 
                    pad_token_id=tokenizer.eos_token_id
                )
            
            generated_ids = [
                output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
            ]
            
            raw_text = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
            agent_response = extract_json(raw_text)
            
            # Debug: Log raw output if JSON parsing failed
            if not agent_response:
                print(f"  [!] Raw model output: {raw_text[:200]}")
                
                # Fallback handler logic
                if task_id == "bug_detection":
                    agent_response = {"has_bug": True, "line_number": 1}
                elif task_id == "bug_classification":
                    agent_response = {"bug_type": "logic", "severity": "medium", "line_number": 1, "explanation": "fallback logic"}
                elif task_id == "code_fix":
                    agent_response = {"fixed_code": obs.code_snippet, "explanation": "fallback output"}
            
        except Exception as e:
            print(f"  [!] Inference error on snippet {snippet['id']}: {e}")
            agent_response = {}

        action = Action(response=agent_response)
        obs, reward, done, info = env.step(action)

        score = info["score"]
        total_score += score
        results.append({
            "snippet_id": snippet["id"],
            "score": score,
            "reward": reward,
            "agent_response": agent_response,
        })

        print(f"  Snippet {snippet['id']:20s} | score={score:.2f} | reward={reward:.4f}")

    avg_score = total_score / len(results) if results else 0.0
    return {
        "task_id": task_id,
        "n_snippets": len(results),
        "average_score": round(avg_score, 4),
        "results": results,
    }


def main():
    parser = argparse.ArgumentParser(description="CodeReviewEnv HF Baseline")
    parser.add_argument("--model", default="Qwen/Qwen2.5-Coder-1.5B-Instruct", help="Hugging Face model ID")
    parser.add_argument("--snippets", type=int, default=5, help="Number of snippets per task")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output", default="hf_baseline_results.json", help="Output file path")
    args = parser.parse_args()

    if torch.backends.mps.is_available():
        device = torch.device("mps")
        print("\n[INFO] Detected M1/Apple Silicon. Using 'mps' backend for acceleration.\n")
    elif torch.cuda.is_available():
        device = torch.device("cuda")
        print("\n[INFO] Detected CUDA GPU. Using 'cuda' backend.\n")
    else:
        device = torch.device("cpu")
        print("\n[INFO] Using standard CPU. Generation may be slow.\n")

    print(f"{'='*60}")
    print(f"  CodeReviewEnv HF Baseline (8GB RAM Optimized)")
    print(f"  Model: {args.model} | Snippets per task: {args.snippets}")
    print(f"{'='*60}\n")
    
    print("Loading model and tokenizer... (might take a minute to download on first run)")
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        torch_dtype=torch.float16, 
        low_cpu_mem_usage=True,
    ).to(device)

    all_results = {}
    task_ids = ["bug_detection", "bug_classification", "code_fix"]

    for task_id in task_ids:
        print(f"\n[Task] {task_id}")
        print("-" * 40)
        task_results = run_agent_on_task(
            model=model,
            tokenizer=tokenizer,
            device=device,
            task_id=task_id,
            n_snippets=args.snippets,
            seed=args.seed,
        )
        all_results[task_id] = task_results
        print(f"  => Average Score: {task_results['average_score']:.4f}")

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

    with open(args.output, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"Results saved to {args.output}")


if __name__ == "__main__":
    main()
