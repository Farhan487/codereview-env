"""
inference.py - OpenEnv compatible inference script
"""
import requests
import json

BASE_URL = "http://localhost:7860"

def run_inference(task_id="bug_detection", seed=42):
    # Reset
    reset_resp = requests.post(f"{BASE_URL}/reset", json={
        "task_id": task_id,
        "seed": seed
    })
    obs = reset_resp.json()["observation"]
    print(f"Task: {obs['task_id']}")
    print(f"Code:\n{obs['code_snippet']}")

    # Step
    if task_id == "bug_detection":
        response = {"has_bug": True, "line_number": 4}
    elif task_id == "bug_classification":
        response = {"bug_type": "logic", "severity": "high", "line_number": 4, "explanation": "Bug found"}
    else:
        response = {"fixed_code": obs["code_snippet"], "explanation": "Fixed"}

    step_resp = requests.post(f"{BASE_URL}/step", json={"response": response})
    result = step_resp.json()
    print(f"Score: {result['info']['score']}")
    print(f"Reward: {result['reward']}")
    return result

if __name__ == "__main__":
    for task in ["bug_detection", "bug_classification", "code_fix"]:
        print(f"\n=== {task} ===")
        run_inference(task_id=task)
