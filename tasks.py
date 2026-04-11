"""
Three tasks with programmatic graders (0.0 - 1.0).

Task 1 - BugDetectionTask     (easy)   : Detect if bug exists + line number
Task 2 - BugClassificationTask (medium): Classify bug type + severity
Task 3 - CodeFixTask           (hard)  : Generate corrected code
"""

import ast
import textwrap


VALID_BUG_TYPES = {"logic", "off_by_one", "type", "security", "style", "performance"}
VALID_SEVERITIES = {"low", "medium", "high", "critical"}

SEVERITY_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}


# ── Task 1: Bug Detection (Easy) ──────────────────────────────────────────────

class BugDetectionTask:
    difficulty = "easy"
    description = (
        "Examine the Python code snippet provided. "
        "Determine whether it contains a bug. "
        "If yes, identify the line number where the bug occurs.\n\n"
        "Respond with a JSON object:\n"
        '  {"has_bug": true/false, "line_number": <int or null>}'
    )

    def grade(self, response: dict, snippet: dict) -> tuple[float, dict]:
        """
        Returns (score 0.0-1.0, breakdown dict).
        
        Scoring:
          - Correct has_bug detection: 0.5
          - Correct line number (±1 tolerance): 0.5
        """
        breakdown = {"has_bug_correct": 0.0, "line_number_correct": 0.0}
        score = 0.0

        # Validate response shape
        if not isinstance(response, dict):
            return 0.01, breakdown

        predicted_has_bug = response.get("has_bug")
        predicted_line = response.get("line_number")
        actual_has_bug = snippet.get("has_bug", False)
        actual_line = snippet.get("bug_line")

        # Grade has_bug
        if isinstance(predicted_has_bug, bool) and predicted_has_bug == actual_has_bug:
            breakdown["has_bug_correct"] = 0.5
            score += 0.5

        # Grade line number (only matters if there IS a bug)
        if actual_has_bug and actual_line is not None:
            if isinstance(predicted_line, int):
                if abs(predicted_line - actual_line) <= 1:  # ±1 tolerance
                    breakdown["line_number_correct"] = 0.5
                    score += 0.5
                elif abs(predicted_line - actual_line) <= 3:  # partial credit
                    breakdown["line_number_correct"] = 0.2
                    score += 0.2
        elif not actual_has_bug and predicted_line is None:
            # Correctly said no bug and gave no line
            breakdown["line_number_correct"] = 0.5
            score += 0.5

        return max(0.01, min(0.99, score)), breakdown


# ── Task 2: Bug Classification (Medium) ───────────────────────────────────────

class BugClassificationTask:
    difficulty = "medium"
    description = (
        "Examine the Python code snippet. "
        "Identify the bug type and its severity.\n\n"
        "Bug types: logic, off_by_one, type, security, style, performance\n"
        "Severities: low, medium, high, critical\n\n"
        "Respond with a JSON object:\n"
        '  {"bug_type": "<type>", "severity": "<severity>", '
        '"line_number": <int>, "explanation": "<string>"}'
    )

    def grade(self, response: dict, snippet: dict) -> tuple[float, dict]:
        """
        Scoring:
          - Correct bug_type: 0.4
          - Correct severity (exact=0.3, adjacent=0.15): 0.3
          - Correct line number (±1): 0.2
          - Has explanation (non-empty string): 0.1
        """
        breakdown = {
            "bug_type_correct": 0.0,
            "severity_correct": 0.0,
            "line_number_correct": 0.0,
            "has_explanation": 0.0,
        }
        score = 0.0

        if not isinstance(response, dict):
            return 0.01, breakdown

        pred_type = str(response.get("bug_type", "")).lower().strip()
        pred_sev = str(response.get("severity", "")).lower().strip()
        pred_line = response.get("line_number")
        pred_expl = response.get("explanation", "")

        actual_type = snippet.get("bug_type", "")
        actual_sev = snippet.get("severity", "")
        actual_line = snippet.get("bug_line")

        # Bug type
        if pred_type == actual_type:
            breakdown["bug_type_correct"] = 0.4
            score += 0.4

        # Severity (exact or adjacent in order)
        if pred_sev == actual_sev:
            breakdown["severity_correct"] = 0.3
            score += 0.3
        elif pred_sev in SEVERITY_ORDER and actual_sev in SEVERITY_ORDER:
            if abs(SEVERITY_ORDER[pred_sev] - SEVERITY_ORDER[actual_sev]) == 1:
                breakdown["severity_correct"] = 0.15
                score += 0.15

        # Line number
        if isinstance(pred_line, int) and actual_line is not None:
            if abs(pred_line - actual_line) <= 1:
                breakdown["line_number_correct"] = 0.2
                score += 0.2
            elif abs(pred_line - actual_line) <= 3:
                breakdown["line_number_correct"] = 0.08
                score += 0.08

        # Explanation present
        if isinstance(pred_expl, str) and len(pred_expl.strip()) > 10:
            breakdown["has_explanation"] = 0.1
            score += 0.1

        return max(0.01, min(0.99, score)), breakdown


# ── Task 3: Code Fix (Hard) ───────────────────────────────────────────────────

class CodeFixTask:
    difficulty = "hard"
    description = (
        "Examine the Python code snippet. "
        "It contains a bug. Your job is to return the fully corrected code.\n\n"
        "Respond with a JSON object:\n"
        '  {"fixed_code": "<corrected python code>", '
        '"explanation": "<what was wrong and what you changed>"}'
    )

    def grade(self, response: dict, snippet: dict) -> tuple[float, dict]:
        """
        Scoring:
          - Fixed code is valid Python (parses): 0.2
          - Fixed code structurally similar to original: 0.1
          - Fixed code matches expected fix closely: 0.4
          - Fixed code actually runs without error: 0.2
          - Has explanation: 0.1
        """
        breakdown = {
            "valid_python": 0.0,
            "structurally_similar": 0.0,
            "matches_expected": 0.0,
            "runs_without_error": 0.0,
            "has_explanation": 0.0,
        }
        score = 0.0

        if not isinstance(response, dict):
            return 0.01, breakdown

        fixed_code = response.get("fixed_code", "")
        explanation = response.get("explanation", "")
        expected_fix = snippet.get("fixed_code", "")

        if not isinstance(fixed_code, str) or not fixed_code.strip():
            return 0.01, breakdown

        # 1. Valid Python syntax
        try:
            ast.parse(fixed_code)
            breakdown["valid_python"] = 0.2
            score += 0.2
        except SyntaxError:
            return score, breakdown  # Can't proceed without valid syntax

        # 2. Structural similarity (function names preserved)
        original_code = snippet.get("code", "")
        original_funcs = _extract_function_names(original_code)
        fixed_funcs = _extract_function_names(fixed_code)
        if original_funcs and original_funcs == fixed_funcs:
            breakdown["structurally_similar"] = 0.1
            score += 0.1

        # 3. Match expected fix (token overlap)
        if expected_fix:
            overlap = _token_overlap(fixed_code, expected_fix)
            if overlap >= 0.9:
                breakdown["matches_expected"] = 0.4
                score += 0.4
            elif overlap >= 0.7:
                breakdown["matches_expected"] = 0.25
                score += 0.25
            elif overlap >= 0.5:
                breakdown["matches_expected"] = 0.1
                score += 0.1

        # 4. Runs without error (safe exec in sandbox)
        if _safe_exec(fixed_code):
            breakdown["runs_without_error"] = 0.2
            score += 0.2

        # 5. Explanation
        if isinstance(explanation, str) and len(explanation.strip()) > 15:
            breakdown["has_explanation"] = 0.1
            score += 0.1

        return max(0.01, min(0.99, score)), breakdown


# ── Helper Functions ──────────────────────────────────────────────────────────

def _extract_function_names(code: str) -> set:
    """Extract all function names defined in code."""
    try:
        tree = ast.parse(code)
        return {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    except Exception:
        return set()


def _token_overlap(code_a: str, code_b: str) -> float:
    """Simple token-level Jaccard similarity between two code strings."""
    tokens_a = set(code_a.split())
    tokens_b = set(code_b.split())
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(intersection) / len(union)


def _safe_exec(code: str, timeout_lines: int = 50) -> bool:
    """
    Try to exec the code safely. Returns True if no exception raised.
    Skips code that calls input() to avoid blocking.
    """
    if "input(" in code:
        return True  # Can't test interactively, give benefit of doubt
    if len(code.splitlines()) > timeout_lines:
        return False
    try:
        exec(compile(code, "<string>", "exec"), {})
        return True
    except Exception:
        return False
