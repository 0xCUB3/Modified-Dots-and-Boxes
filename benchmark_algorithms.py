import contextlib
import io
import time
from typing import Callable, List, Tuple

from algorithm_MD import GameRunner, edges_for_complete_graph, edges_for_wheel, edges_for_m_by_n_grid
from algorithm_optimized import FastGameRunner

Edge = Tuple[int, int]


def time_call(fn: Callable[[], int]) -> Tuple[int, float]:
    start = time.perf_counter()
    with contextlib.redirect_stdout(io.StringIO()):
        result = fn()
    return result, time.perf_counter() - start


def baseline(edges: List[Edge]) -> int:
    runner = GameRunner(edges)
    runner._memo = {}
    return runner._net_score(runner._initial_graph, 0)


def optimized_runner(edges: List[Edge]) -> int:
    runner = FastGameRunner(edges, canonical=True, progress=False)
    return runner._net_score(runner.initial_state)


def bench_case(name: str, edges: List[Edge]) -> None:
    base_result, base_time = time_call(lambda: baseline(edges))
    opt_result, opt_time = time_call(lambda: optimized_runner(edges))
    status = "OK" if base_result == opt_result else f"MISMATCH {base_result}!={opt_result}"
    speedup = base_time / opt_time if opt_time else float("inf")
    print(f"{name:16} edges={len(edges):3} result={opt_result:3} {status:16} baseline={base_time:8.4f}s optimized={opt_time:8.4f}s speedup={speedup:6.2f}x")


def main() -> None:
    cases = []
    for n in range(3, 8):
        cases.append((f"complete K{n}", edges_for_complete_graph(n)))
    for n in range(3, 10):
        cases.append((f"wheel W{n}", edges_for_wheel(n)))
    for m, n in [(2, 2), (2, 3), (3, 3), (2, 4)]:
        cases.append((f"grid {m}x{n}", edges_for_m_by_n_grid(m, n)))

    print("Benchmarking algorithm_MD.py vs algorithm_optimized.py")
    for name, edges in cases:
        bench_case(name, edges)


if __name__ == "__main__":
    main()
