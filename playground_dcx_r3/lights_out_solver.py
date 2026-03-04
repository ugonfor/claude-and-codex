"""1D Lights Out solver — verifying Codex-Worker's puzzle (by Claude-Worker)"""

from itertools import combinations


def toggle(state: list[int], i: int, n: int) -> list[int]:
    """Toggle switch i and its neighbors."""
    s = state[:]
    for j in (i - 1, i, i + 1):
        if 0 <= j < n:
            s[j] ^= 1
    return s


def apply_moves(n: int, moves: list[int]) -> list[int]:
    """Apply a sequence of moves (0-indexed) to an all-OFF board."""
    state = [0] * n
    for m in moves:
        state = toggle(state, m, n)
    return state


def brute_force_minimal(n: int) -> list[int] | None:
    """Find minimal solution by brute force (order doesn't matter in Lights Out)."""
    target = [1] * n
    # In Lights Out, each switch is either pressed or not (order irrelevant)
    for k in range(n + 1):
        for combo in combinations(range(n), k):
            if apply_moves(n, list(combo)) == target:
                return [i + 1 for i in combo]  # 1-indexed
    return None


if __name__ == "__main__":
    n = 9
    print(f"Solving 1D Lights Out for n={n}...")

    # Find minimal solution
    solution = brute_force_minimal(n)
    if solution:
        print(f"Minimal solution (length {len(solution)}): {solution}")
    else:
        print("No solution exists!")

    # Verify Codex's proposed solution: [2,4,5,7,9]
    codex_proposal = [2, 4, 5, 7, 9]
    result = apply_moves(n, [i - 1 for i in codex_proposal])
    all_on = all(x == 1 for x in result)
    print(f"\nCodex's proposal {codex_proposal}: {'CORRECT' if all_on else 'INCORRECT'}")
    if not all_on:
        print(f"  Result: {result}")

    # Also verify our brute-force solution
    if solution:
        result2 = apply_moves(n, [i - 1 for i in solution])
        print(f"Brute-force solution {solution}: {'CORRECT' if all(x == 1 for x in result2) else 'INCORRECT'}")
