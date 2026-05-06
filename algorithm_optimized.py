from __future__ import annotations

import argparse
import time
from functools import lru_cache
from typing import Dict, Hashable, Iterable, List, Set, Tuple

from algorithm_MD import (
    CanonicalEdges,
    edges_for_complete_graph,
    edges_for_wheel,
    edges_for_m_by_n_grid,
    edges_from_input_file,
)

Edge = Tuple[int, int]
State = Tuple[Edge, ...]


def normalize_edges(edges: Iterable[Edge]) -> State:
    """Return a stable immutable edge multiset representation."""
    return tuple(sorted((a, b) if a <= b else (b, a) for a, b in edges))


class FastGameRunner:
    """
    Faster solver for the Modified Dots and Boxes impartial game.

    Optimizations over algorithm_MD.py:
    - no GameGraph object allocation per child
    - immutable tuple states
    - cached canonical keys
    - cached tree checks
    - cached degree/vertex calculations
    - duplicate move skipping via set instead of list
    """

    def __init__(self, edges: List[Edge], canonical: bool = True, progress: bool = False):
        self.initial_state: State = normalize_edges(edges)
        self.use_canonical = canonical
        self.progress = progress
        self.start_time = time.perf_counter()
        self.top_level = len(self.initial_state)
        self.count = 0
        self._memo: Dict[Hashable, int] = {}
        self._pynauty = None
        if canonical:
            try:
                import pynauty  # type: ignore
                self._pynauty = pynauty
            except Exception:
                self._pynauty = None

    def run(self) -> int:
        score = self._net_score(self.initial_state)
        if score == 0:
            print("Tie game.")
        else:
            print(f"{'P1' if score > 0 else 'P2'} wins with a net score of {score} (P1-P2).")
        print(f"states: {len(self._memo)}")
        return score

    @lru_cache(maxsize=None)
    def _state_key(self, state: State) -> Hashable:
        if not self.use_canonical:
            return state
        if self._pynauty is not None:
            return self._pynauty_certificate(state)
        return tuple(CanonicalEdges(list(state)).calc())

    def _pynauty_certificate(self, state: State) -> bytes:
        # Encode the loop/multigraph as a colored simple incidence graph:
        # original vertices color 0; ordinary edge-nodes color 1; loop edge-nodes color 2.
        vertices = sorted(self._vertices(state))
        original_id = {v: i for i, v in enumerate(vertices)}
        next_id = len(vertices)
        adjacency: Dict[int, List[int]] = {i: [] for i in range(len(vertices))}
        edge_nodes: Set[int] = set()
        loop_nodes: Set[int] = set()
        for a, b in state:
            eid = next_id
            next_id += 1
            adjacency[eid] = []
            if a == b:
                u = original_id[a]
                adjacency[eid].append(u)
                adjacency[u].append(eid)
                loop_nodes.add(eid)
            else:
                u, v = original_id[a], original_id[b]
                adjacency[eid].extend([u, v])
                adjacency[u].append(eid)
                adjacency[v].append(eid)
                edge_nodes.add(eid)
        graph = self._pynauty.Graph(
            number_of_vertices=next_id,
            directed=False,
            adjacency_dict=adjacency,
            vertex_coloring=[set(range(len(vertices))), edge_nodes, loop_nodes],
        )
        return self._pynauty.certificate(graph)

    @lru_cache(maxsize=None)
    def _vertices(self, state: State) -> frozenset[int]:
        vertices: Set[int] = set()
        for a, b in state:
            vertices.add(a)
            vertices.add(b)
        return frozenset(vertices)

    @lru_cache(maxsize=None)
    def _degrees(self, state: State) -> Dict[int, int]:
        deg: Dict[int, int] = {}
        for a, b in state:
            if a == b:
                deg[a] = deg.get(a, 0) + 1
            else:
                deg[a] = deg.get(a, 0) + 1
                deg[b] = deg.get(b, 0) + 1
        return deg

    @lru_cache(maxsize=None)
    def _is_tree(self, state: State) -> bool:
        # Forest test for an undirected multigraph. Self-loops and parallel edges are cycles.
        if not state:
            return False
        parent = {v: v for v in self._vertices(state)}

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        for a, b in state:
            if a == b:
                return False
            ra, rb = find(a), find(b)
            if ra == rb:
                return False
            parent[ra] = rb
        return True

    def _net_score(self, state: State) -> int:
        key = self._state_key(state)
        if key in self._memo:
            return self._memo[key]

        num_vertices = len(self._vertices(state))
        if num_vertices == 0:
            self._memo[key] = 0
            return 0
        if self._is_tree(state):
            self._memo[key] = num_vertices
            return num_vertices

        best = -num_vertices
        tried: Set[Edge] = set()
        for edge in state:
            if edge in tried:
                continue
            tried.add(edge)
            child, points = self._cut_edge(state, edge)
            mult = 1 if points > 0 else -1
            outcome = points + mult * self._net_score(child)
            if outcome > best:
                best = outcome
                if best == num_vertices:
                    break

        if self.progress:
            self._track_progress(len(self.initial_state) - len(state))
        self._memo[key] = best
        return best

    def _cut_edge(self, state: State, edge: Edge) -> Tuple[State, int]:
        edges = list(state)
        edges.remove(edge)
        child = tuple(edges)  # already sorted after removing one item
        old_vertices = self._vertices(state)
        new_vertices = self._vertices(child)
        points = int(edge[0] in old_vertices and edge[0] not in new_vertices)
        if edge[1] != edge[0]:
            points += int(edge[1] in old_vertices and edge[1] not in new_vertices)
        return child, points

    def _track_progress(self, depth: int) -> None:
        if depth <= self.top_level:
            if depth == self.top_level:
                self.count += 1
            else:
                self.top_level = depth
                self.count = 1
            print(f"top solved depth:{depth} count:{self.count} seconds:{time.perf_counter() - self.start_time:.2f}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Optimized Modified Dots and Boxes solver.")
    parser.add_argument("--type", default="file")
    parser.add_argument("--params", default=[], type=int, nargs="+")
    parser.add_argument("--no-canonical", action="store_true")
    parser.add_argument("--progress", action="store_true")
    args = parser.parse_args()

    if args.type == "file":
        edges = edges_from_input_file()
    elif args.type == "m_by_n":
        edges = edges_for_m_by_n_grid(args.params[0], args.params[1])
    elif args.type == "complete":
        edges = edges_for_complete_graph(args.params[0])
    elif args.type == "wheel":
        edges = edges_for_wheel(args.params[0])
    else:
        raise ValueError(f"Unrecognized edge source type: {args.type}")

    FastGameRunner(edges, canonical=not args.no_canonical, progress=args.progress).run()


if __name__ == "__main__":
    main()
