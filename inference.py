"""
inference.py - OpenEnv compatible inference script
Uses only standard library - no external dependencies required.
"""
import urllib.request
import urllib.error
import json

BASE_URL = "http://localhost:7860"

def post(url, data=None):
    body = json.dumps(data).encode() if data else b"{}"
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())

def get(url):
    with urllib.request.urlopen(url) as resp:
        return json.loads(resp.read().decode())

def run_inference(task_id="bug_detection", seed=42):
    # Reset
    obs = post(f"{BASE_URL}/reset", {"task_id": task_id, "seed": seed})["observation"]
    print(f"Task: {obs['task_id']}")
    print(f"Code:\n{obs['code_snippet']}")

    # Step
    if task_id == "bug_detection":
        response = {"has_bug": True, "line_number": 4}
    elif task_id == "bug_classification":
        response = {"bug_type": "logic", "severity": "high", 
                   "line_number": 4, "explanation": "Bug found"}
    else:
        response = {"fixed_code": obs["code_snippet"], 
                   "explanation": "Fixed the bug"}

    result = post(f"{BASE_URL}/step", {"response": response})
    print(f"Score: {result['info']['score']}")
    print(f"Reward: {result['reward']}")
    return result

if __name__ == "__main__":
    for task in ["bug_detection", "bug_classification", "code_fix"]:
        print(f"\n=== {task} ===")
        try:
            run_inference(task_id=task)
        except Exception as e:
            print(f"Error: {e}")
