"""
Dataset of Python code snippets with intentional bugs.
Each snippet includes metadata for grading agent responses.
"""

BUGGY_SNIPPETS = [
    # ── LOGIC BUGS ────────────────────────────────────────────────────────────
    {
        "id": "logic_001",
        "code": (
            "def calculate_average(numbers):\n"
            "    total = 0\n"
            "    for n in numbers:\n"
            "        total += n\n"
            "    return total / len(numbers)\n"
            "\n"
            "result = calculate_average([])\n"
            "print(result)\n"
        ),
        "has_bug": True,
        "bug_line": 7,
        "bug_type": "logic",
        "severity": "high",
        "description": "Division by zero when input list is empty.",
        "fixed_code": (
            "def calculate_average(numbers):\n"
            "    if not numbers:\n"
            "        return 0\n"
            "    total = 0\n"
            "    for n in numbers:\n"
            "        total += n\n"
            "    return total / len(numbers)\n"
            "\n"
            "result = calculate_average([])\n"
            "print(result)\n"
        ),
        "test_input": [],
        "test_expected": 0,
        "language": "python",
    },
    {
        "id": "logic_002",
        "code": (
            "def is_palindrome(s):\n"
            "    return s == s[::-1]\n"
            "\n"
            "def count_palindromes(words):\n"
            "    count = 0\n"
            "    for word in words:\n"
            "        if is_palindrome(word):\n"
            "            count =+ 1\n"
            "    return count\n"
        ),
        "has_bug": True,
        "bug_line": 8,
        "bug_type": "logic",
        "severity": "medium",
        "description": "=+ should be += (assignment with positive, not increment).",
        "fixed_code": (
            "def is_palindrome(s):\n"
            "    return s == s[::-1]\n"
            "\n"
            "def count_palindromes(words):\n"
            "    count = 0\n"
            "    for word in words:\n"
            "        if is_palindrome(word):\n"
            "            count += 1\n"
            "    return count\n"
        ),
        "test_input": ["racecar", "hello", "level"],
        "test_expected": 2,
        "language": "python",
    },
    {
        "id": "logic_003",
        "code": (
            "def find_max(lst):\n"
            "    max_val = lst[0]\n"
            "    for i in range(len(lst)):\n"
            "        if lst[i] > max_val:\n"
            "            max_val = lst[i]\n"
            "    return max_val\n"
            "\n"
            "print(find_max([]))\n"
        ),
        "has_bug": True,
        "bug_line": 8,
        "bug_type": "logic",
        "severity": "high",
        "description": "IndexError when list is empty — no guard for empty input.",
        "fixed_code": (
            "def find_max(lst):\n"
            "    if not lst:\n"
            "        return None\n"
            "    max_val = lst[0]\n"
            "    for i in range(len(lst)):\n"
            "        if lst[i] > max_val:\n"
            "            max_val = lst[i]\n"
            "    return max_val\n"
            "\n"
            "print(find_max([]))\n"
        ),
        "test_input": [],
        "test_expected": None,
        "language": "python",
    },

    # ── OFF-BY-ONE BUGS ───────────────────────────────────────────────────────
    {
        "id": "offbyone_001",
        "code": (
            "def get_last_n(lst, n):\n"
            "    return lst[len(lst) - n + 1:]\n"
        ),
        "has_bug": True,
        "bug_line": 2,
        "bug_type": "off_by_one",
        "severity": "medium",
        "description": "Off-by-one: should be len(lst) - n, not len(lst) - n + 1.",
        "fixed_code": (
            "def get_last_n(lst, n):\n"
            "    return lst[len(lst) - n:]\n"
        ),
        "test_input": ([1, 2, 3, 4, 5], 3),
        "test_expected": [3, 4, 5],
        "language": "python",
    },
    {
        "id": "offbyone_002",
        "code": (
            "def binary_search(arr, target):\n"
            "    low, high = 0, len(arr)\n"
            "    while low <= high:\n"
            "        mid = (low + high) // 2\n"
            "        if arr[mid] == target:\n"
            "            return mid\n"
            "        elif arr[mid] < target:\n"
            "            low = mid + 1\n"
            "        else:\n"
            "            high = mid - 1\n"
            "    return -1\n"
        ),
        "has_bug": True,
        "bug_line": 2,
        "bug_type": "off_by_one",
        "severity": "high",
        "description": "high should be len(arr) - 1 to avoid index out of range.",
        "fixed_code": (
            "def binary_search(arr, target):\n"
            "    low, high = 0, len(arr) - 1\n"
            "    while low <= high:\n"
            "        mid = (low + high) // 2\n"
            "        if arr[mid] == target:\n"
            "            return mid\n"
            "        elif arr[mid] < target:\n"
            "            low = mid + 1\n"
            "        else:\n"
            "            high = mid - 1\n"
            "    return -1\n"
        ),
        "test_input": ([1, 3, 5, 7, 9], 7),
        "test_expected": 3,
        "language": "python",
    },

    # ── TYPE BUGS ─────────────────────────────────────────────────────────────
    {
        "id": "type_001",
        "code": (
            "def add_numbers(a, b):\n"
            "    return a + b\n"
            "\n"
            "x = input('Enter a number: ')\n"
            "y = input('Enter another: ')\n"
            "print(add_numbers(x, y))\n"
        ),
        "has_bug": True,
        "bug_line": 6,
        "bug_type": "type",
        "severity": "medium",
        "description": "input() returns strings; need int() conversion before addition.",
        "fixed_code": (
            "def add_numbers(a, b):\n"
            "    return a + b\n"
            "\n"
            "x = int(input('Enter a number: '))\n"
            "y = int(input('Enter another: '))\n"
            "print(add_numbers(x, y))\n"
        ),
        "test_input": ("3", "5"),
        "test_expected": 8,
        "language": "python",
    },

    # ── INFINITE LOOP / PERFORMANCE BUGS ──────────────────────────────────────
    {
        "id": "perf_001",
        "code": (
            "def remove_duplicates(lst):\n"
            "    result = []\n"
            "    i = 0\n"
            "    while i < len(lst):\n"
            "        if lst[i] not in result:\n"
            "            result.append(lst[i])\n"
            "    return result\n"
        ),
        "has_bug": True,
        "bug_line": 7,
        "bug_type": "logic",
        "severity": "critical",
        "description": "Infinite loop — i is never incremented inside while loop.",
        "fixed_code": (
            "def remove_duplicates(lst):\n"
            "    result = []\n"
            "    i = 0\n"
            "    while i < len(lst):\n"
            "        if lst[i] not in result:\n"
            "            result.append(lst[i])\n"
            "        i += 1\n"
            "    return result\n"
        ),
        "test_input": [1, 2, 2, 3, 3, 4],
        "test_expected": [1, 2, 3, 4],
        "language": "python",
    },

    # ── SECURITY BUGS ─────────────────────────────────────────────────────────
    {
        "id": "security_001",
        "code": (
            "import subprocess\n"
            "\n"
            "def run_command(user_input):\n"
            "    result = subprocess.run(\n"
            "        f'echo {user_input}',\n"
            "        shell=True,\n"
            "        capture_output=True,\n"
            "        text=True\n"
            "    )\n"
            "    return result.stdout\n"
        ),
        "has_bug": True,
        "bug_line": 4,
        "bug_type": "security",
        "severity": "critical",
        "description": "Shell injection vulnerability — user input passed directly to shell.",
        "fixed_code": (
            "import subprocess\n"
            "\n"
            "def run_command(user_input):\n"
            "    result = subprocess.run(\n"
            "        ['echo', user_input],\n"
            "        shell=False,\n"
            "        capture_output=True,\n"
            "        text=True\n"
            "    )\n"
            "    return result.stdout\n"
        ),
        "test_input": "hello",
        "test_expected": "hello\n",
        "language": "python",
    },

    # ── SCOPE / REFERENCE BUGS ────────────────────────────────────────────────
    {
        "id": "scope_001",
        "code": (
            "def make_multipliers():\n"
            "    return [lambda x: x * i for i in range(5)]\n"
            "\n"
            "multipliers = make_multipliers()\n"
            "print(multipliers[0](10))\n"
        ),
        "has_bug": True,
        "bug_line": 2,
        "bug_type": "logic",
        "severity": "medium",
        "description": "Late binding closure — all lambdas capture same i=4 at call time.",
        "fixed_code": (
            "def make_multipliers():\n"
            "    return [lambda x, i=i: x * i for i in range(5)]\n"
            "\n"
            "multipliers = make_multipliers()\n"
            "print(multipliers[0](10))\n"
        ),
        "test_input": 10,
        "test_expected": 0,
        "language": "python",
    },

    # ── MUTATION BUG ─────────────────────────────────────────────────────────
    {
        "id": "mutation_001",
        "code": (
            "def append_to(element, to=[]):\n"
            "    to.append(element)\n"
            "    return to\n"
            "\n"
            "print(append_to(1))\n"
            "print(append_to(2))\n"
        ),
        "has_bug": True,
        "bug_line": 1,
        "bug_type": "logic",
        "severity": "medium",
        "description": "Mutable default argument — list persists across calls.",
        "fixed_code": (
            "def append_to(element, to=None):\n"
            "    if to is None:\n"
            "        to = []\n"
            "    to.append(element)\n"
            "    return to\n"
            "\n"
            "print(append_to(1))\n"
            "print(append_to(2))\n"
        ),
        "test_input": None,
        "test_expected": [1],
        "language": "python",
    },

    # ── RECURSION BUG ─────────────────────────────────────────────────────────
    {
        "id": "recursion_001",
        "code": (
            "def factorial(n):\n"
            "    if n == 0:\n"
            "        return 1\n"
            "    return n * factorial(n)\n"
        ),
        "has_bug": True,
        "bug_line": 4,
        "bug_type": "logic",
        "severity": "critical",
        "description": "Infinite recursion — should call factorial(n-1) not factorial(n).",
        "fixed_code": (
            "def factorial(n):\n"
            "    if n == 0:\n"
            "        return 1\n"
            "    return n * factorial(n - 1)\n"
        ),
        "test_input": 5,
        "test_expected": 120,
        "language": "python",
    },

    # ── COMPARISON BUG ────────────────────────────────────────────────────────
    {
        "id": "compare_001",
        "code": (
            "def check_none(value):\n"
            "    if value == None:\n"
            "        return 'is none'\n"
            "    return 'not none'\n"
        ),
        "has_bug": True,
        "bug_line": 2,
        "bug_type": "style",
        "severity": "low",
        "description": "Should use 'is None' instead of '== None' (PEP8 E711).",
        "fixed_code": (
            "def check_none(value):\n"
            "    if value is None:\n"
            "        return 'is none'\n"
            "    return 'not none'\n"
        ),
        "test_input": None,
        "test_expected": "is none",
        "language": "python",
    },
]
