import os
import json
import urllib.request
from openai import OpenAI

# Required environment variables
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN = os.getenv("HF_TOKEN")

if HF_TOKEN is None:
    raise ValueError("HF_TOKEN environment variable is required")

# Initialize OpenAI client through their proxy
client = OpenAI(
    base_url=API_BASE_URL,
    api_key=HF_TOKEN
)

ENV_URL = "https://Farhan487-code-review-env.hf.space"

def post_env(url, data=None):
    body = json.dumps(data or {}).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {}

def get_action(task_id, code_snippet):
    if task_id == "bug_detection":
        prompt = (
            f"Analyze this Python code and detect if it has a bug. "
            f"Return ONLY valid JSON with no markdown: "
            f'{{\"has_bug\": true, \"line_number\": 1}}\n\nCode:\n{code_snippet}'
        )
    elif task_id == "bug_classification":
        prompt = (
            f"Classify the bug in this Python code. "
            f"Return ONLY valid JSON with no markdown: "
            f'{{\"bug_type\": \"logic\", \"severity\": \"high\", '
            f'\"line_number\": 1, \"explanation\": \"bug found\"}}\n\nCode:\n{code_snippet}'
        )
    else:
        prompt = (
            f"Fix the bug in this Python code. "
            f"Return ONLY valid JSON with no markdown: "
            f'{{\"fixed_code\": \"<fixed>\", \"explanation\": \"fixed\"}}'
            f'\n\nCode:\n{code_snippet}'
        )

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are an expert Python code reviewer. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=512,
            temperature=0.0,
        )
        text = completion.choices[0].message.content.strip()
        if "```" in text:
            parts = text.split("```")
            for part in parts:
                if part.startswith("json"):
                    text = part[4:].strip()
                    break
                elif part.strip().startswith("{"):
                    text = part.strip()
                    break
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            text = text[start:end+1]
        return json.loads(text)
    except Exception:
        if task_id == "bug_detection":
            return {"has_bug": True, "line_number": 1}
        elif task_id == "bug_classification":
            return {"bug_type": "logic", "severity": "high",
                   "line_number": 1, "explanation": "bug found"}
        else:
            return {"fixed_code": code_snippet, "explanation": "fixed"}

def run():
    tasks = ["bug_detection", "bug_classification", "code_fix"]

    for task_id in tasks:
        rewards = []
        steps_taken = 0
        success = False

        print(f"[START] task={task_id} env=codereview-env model={MODEL_NAME}", flush=True)

        try:
            obs_data = post_env(f"{ENV_URL}/reset", {
                "task_id": task_id,
                "seed": 42
            })

            obs = obs_data.get("observation", {}) if obs_data else {}
            code_snippet = obs.get("code_snippet", "")
            done = False

            for step in range(1, 6):
                if done:
                    break
                try:
                    response = get_action(task_id, code_snippet)
                    result = post_env(f"{ENV_URL}/step", {"response": response})

                    reward = result.get("reward", 0.0) if result else 0.0
                    done = result.get("done", False) if result else False
                    score = result.get("info", {}).get("score", 0.0) if result else 0.0

                    rewards.append(reward)
                    steps_taken = step

                    action_str = json.dumps(response).replace(" ", "")
                    print(f"[STEP] step={step} action={action_str} reward={reward:.2f} done={str(done).lower()} error=null", flush=True)

                    if done or score >= 1.0:
                        success = True
                        break

                except Exception as e:
                    rewards.append(0.0)
                    steps_taken = step
                    print(f"[STEP] step={step} action=null reward=0.00 done=false error={str(e)}", flush=True)

        except Exception as e:
            rewards.append(0.0)
            steps_taken = 1
            print(f"[STEP] step=1 action=null reward=0.00 done=false error={str(e)}", flush=True)

        finally:
            rewards_str = ",".join(f"{r:.2f}" for r in rewards) if rewards else "0.00"
            print(f"[END] success={str(success).lower()} steps={steps_taken} rewards={rewards_str}", flush=True)

if __name__ == "__main__":
    run()
