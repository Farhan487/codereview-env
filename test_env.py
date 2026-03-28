from env import CodeReviewEnv, Action

env = CodeReviewEnv(task_id= "bug_detection", seed=42)
obs = env.reset()

print("=== CODE SNIPPET (with line numbers) ===")
for i, line in enumerate(obs.code_snippet.splitlines(), 1):
    print(f" {i}: {line}")



# print(obs.code_snippet)
# print("\n=== TASK ===")
# print(obs.task_description)

action = Action(response={"has_bug": True, "line number": 7})
obs, reward, done, info = env.step(action)


print("\n=== RESULT ===")
print(f"Score:  {info['score']}")
print(f"Reward: {reward}")
print(f"Details: {info['breakdown']}")
print("\n --- Testing all 3 tasks----")


tasks = {
    "bug_detection":     {"has_bug": True, "line_number": 4},
    "bug_classification":{"bug_type": "logic", "severity": "critical", "line_number": 4, "explanation": "Infinite recursion, should be factorial(n-1)"},
    "code_fix":          {"fixed_code": "def factorial(n):\n    if n == 0:\n        return 1\n    return n * factorial(n - 1)\n", "explanation": "Changed factorial(n) to factorial(n-1) to avoid infinite recursion"},
}

for task_id, response in tasks.items():
    env2 = CodeReviewEnv(task_id=task_id, seed=42)
    env2.reset()
    _, reward, _, info = env2.step(Action(response=response))
    print(f"  {task_id:30s} | score={info['score']:.2f} | reward={reward:.4f}")

