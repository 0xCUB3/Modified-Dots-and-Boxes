"""Small verifier for the Strings-and-Coins/Dots-and-Boxes graph game.

An edge is an object connecting one or two vertices. A loop is incident to its
single vertex once for purposes of deciding whether a coin/vertex is captured.
After removing an edge, any vertices with no remaining incident edges are scored
by the mover and removed. If at least one vertex is scored, the mover moves
again; otherwise the turn passes.
"""
from __future__ import annotations
from functools import lru_cache
from itertools import combinations
from typing import Iterable, Tuple

Vertex = str
Edge = Tuple[Vertex, Vertex]


def normalize_edge(e: Edge) -> Edge:
    a, b = e
    return (a, b) if a <= b else (b, a)


def normalize_edges(edges: Iterable[Edge]) -> Tuple[Edge, ...]:
    return tuple(sorted(normalize_edge(e) for e in edges))


def pinwheel(n: int) -> Tuple[Edge, ...]:
    """n copies of C4 sharing the vertex c.

    Square i has vertices c, a_i, b_i, d_i and edges
    c-a_i-a_i-b_i-b_i-d_i-d_i-c.
    """
    edges = []
    for i in range(n):
        a, b, d = f"a{i}", f"b{i}", f"d{i}"
        edges += [("c", a), (a, b), (b, d), ("c", d)]
    return normalize_edges(edges)


def friendship(n: int) -> Tuple[Edge, ...]:
    """n copies of K3 sharing the vertex c."""
    edges = []
    for i in range(n):
        a, b = f"a{i}", f"b{i}"
        edges += [("c", a), (a, b), ("c", b)]
    return normalize_edges(edges)


def complete_bipartite(a: int, b: int) -> Tuple[Edge, ...]:
    """The complete bipartite graph K(a,b)."""
    return normalize_edges((f"A{i}", f"B{j}") for i in range(a) for j in range(b))


def complete_graph(n: int) -> Tuple[Edge, ...]:
    """The complete graph K_n."""
    return normalize_edges((f"v{i}", f"v{j}") for i, j in combinations(range(n), 2))


def hypercube(dim: int) -> Tuple[Edge, ...]:
    """The dim-dimensional hypercube Q_dim."""
    edges = []
    for v in range(1 << dim):
        for bit in range(dim):
            w = v ^ (1 << bit)
            if v < w:
                edges.append((f"v{v}", f"v{w}"))
    return normalize_edges(edges)


def prism(n: int) -> Tuple[Edge, ...]:
    """Prism graph PG_n = C_n square P_2."""
    edges = []
    for i in range(n):
        edges.append((f"a{i}", f"a{(i + 1) % n}"))
        edges.append((f"b{i}", f"b{(i + 1) % n}"))
        edges.append((f"a{i}", f"b{i}"))
    return normalize_edges(edges)


def wheel(n: int) -> Tuple[Edge, ...]:
    """Wheel graph W_n: n cycle vertices plus center c."""
    edges = []
    for i in range(n):
        edges.append((f"v{i}", f"v{(i+1)%n}"))
        edges.append(("c", f"v{i}"))
    return normalize_edges(edges)


def loopy_cycle(n: int, k: int) -> Tuple[Edge, ...]:
    """Cycle C_n with loops on k consecutive vertices."""
    edges = [(f"v{i}", f"v{(i + 1) % n}") for i in range(n)]
    edges += [(f"v{i}", f"v{i}") for i in range(k)]
    return normalize_edges(edges)


def ferris_wheel(n: int) -> Tuple[Edge, ...]:
    """Loopy cycle C(n,n): n-cycle with one loop at every vertex."""
    return loopy_cycle(n, n)


def balloon_path(n: int) -> Tuple[Edge, ...]:
    """Balloon path BP_n: a path of length n with one loop at every vertex."""
    edges = [(f"v{i}", f"v{i}") for i in range(n + 1)]
    edges += [(f"v{i}", f"v{i + 1}") for i in range(n)]
    return normalize_edges(edges)


def two_balloon_paths(n: int) -> Tuple[Edge, ...]:
    """Two disjoint reflected copies of BP_n, used after splitting BP_{2n+1}."""
    edges = []
    for prefix in ["L", "R"]:
        for a, b in balloon_path(n):
            edges.append((prefix + a, prefix + b))
    return normalize_edges(edges)


def loopy_starlike(n: int, k: int, length: int) -> Tuple[Edge, ...]:

    """Loopy starlike tree L(n,k,length)."""
    edges = []
    for i in range(n):
        prev = "c"
        for j in range(1, length + 1):
            v = f"b{i}_{j}"
            edges.append((prev, v))
            prev = v
        for _ in range(k):
            edges.append((prev, prev))
    return normalize_edges(edges)


def petersen() -> Tuple[Edge, ...]:
    """The Petersen graph."""
    edges = []
    edges += [(f"v{i}", f"v{(i + 1) % 5}") for i in range(5)]
    edges += [("v5", "v7"), ("v7", "v9"), ("v9", "v6"), ("v6", "v8"), ("v8", "v5")]
    edges += [(f"v{i}", f"v{i + 5}") for i in range(5)]
    return normalize_edges(edges)


def vertices_of(edges: Iterable[Edge]) -> frozenset[Vertex]:
    vs = set()
    for a, b in edges:
        vs.add(a); vs.add(b)
    return frozenset(vs)


def incident_count(edges: Iterable[Edge], vertices: Iterable[Vertex]) -> dict[Vertex, int]:
    counts = {v: 0 for v in vertices}
    for a, b in edges:
        if a == b:
            counts[a] += 1
        else:
            counts[a] += 1
            counts[b] += 1
    return counts


def remove_edge(edges: Tuple[Edge, ...], alive: frozenset[Vertex], move: Edge):
    edge_list = list(edges)
    edge_list.remove(move)
    new_edges = tuple(edge_list)
    counts = incident_count(new_edges, alive)
    captured = frozenset(v for v in alive if counts[v] == 0)
    if captured:
        alive2 = alive - captured
        # Drop any remaining loops/edges incident to captured vertices. In a valid
        # position there should be none, since captured vertices have count zero.
        new_edges = tuple(e for e in new_edges if e[0] in alive2 and e[1] in alive2)
    else:
        alive2 = alive
    return normalize_edges(new_edges), alive2, len(captured), captured


@lru_cache(maxsize=None)
def solve(edges: Tuple[Edge, ...], alive: frozenset[Vertex], player: int = 0) -> Tuple[int, int]:
    """Optimal remaining score from this state, in absolute P0/P1 coordinates."""
    if not edges:
        return (0, 0)
    best = None
    for move in edges:
        e2, a2, gained, _ = remove_edge(edges, alive, move)
        next_player = player if gained else 1 - player
        s0, s1 = solve(e2, a2, next_player)
        if player == 0:
            s0 += gained
            key = s0 - s1
            best_key = None if best is None else best[0] - best[1]
            if best is None or key > best_key:
                best = (s0, s1)
        else:
            s1 += gained
            key = s1 - s0
            best_key = None if best is None else best[1] - best[0]
            if best is None or key > best_key:
                best = (s0, s1)
    assert best is not None
    return best


def legal_outcomes(edges, alive, player=0):
    out = []
    for move in edges:
        e2, a2, gained, captured = remove_edge(edges, alive, move)
        next_player = player if gained else 1-player
        s0, s1 = solve(e2, a2, next_player)
        if player == 0: s0 += gained
        else: s1 += gained
        out.append((move, gained, tuple(sorted(captured)), (s0, s1)))
    return out


@lru_cache(maxsize=None)
def double_loopy_star_margin(a: int, b: int, c: int, d: int, e: int) -> int:
    """Current-player margin for the reduced L(n,2) branch-count recurrence.

    Branch types are A=SLL, B=SL, C=S, D=LL, E=L, where S is the spoke to
    the center and L is a loop. This recurrence is used in the paper's proof
    of the double loopy star formula.
    """
    if a + b + c + d + e == 0:
        return 0

    spokes = a + b + c
    best = -10**9

    def consider(na: int, nb: int, nc: int, nd: int, ne: int, gained: int) -> None:
        nonlocal best
        rest = double_loopy_star_margin(na, nb, nc, nd, ne)
        value = gained + rest if gained else -rest
        best = max(best, value)

    if a:
        consider(a - 1, b + 1, c, d, e, 0)                         # remove a loop from A
        consider(a - 1, b, c, d + 1, e, 1 if spokes == 1 else 0)   # remove the spoke from A
    if b:
        consider(a, b - 1, c + 1, d, e, 0)                         # remove a loop from B
        consider(a, b - 1, c, d, e + 1, 1 if spokes == 1 else 0)   # remove the spoke from B
    if c:
        consider(a, b, c - 1, d, e, 1 + (1 if spokes == 1 else 0)) # score leaf, maybe center
    if d:
        consider(a, b, c, d - 1, e + 1, 0)                         # remove a loop from D
    if e:
        consider(a, b, c, d, e - 1, 1)                             # score E leaf

    return best


def double_loopy_star_formula_score(n: int) -> Tuple[int, int]:
    """Closed-form score for L(n,2) from the paper."""
    if n == 1:
        return (1, 1)
    if n == 2:
        return (1, 2)
    if n % 2:
        k = (n - 1) // 2
        return (k, k + 2)
    k = n // 2
    return (k - 1, k + 2)


def describe_pinwheel_edge(e: Edge) -> str:
    a, b = e
    if a == 'c' or b == 'c':
        x = b if a == 'c' else a
        return f"spoke {e}"
    return f"outer {e}"


if __name__ == '__main__':
    # The direct solver is intentionally small rather than optimized. PW_6 and
    # above need symmetry reduction to be fast, so this smoke test checks the
    # first five pinwheels and compares them with the recurrence in the paper.
    for n in range(1, 5):
        solve.cache_clear()
        edges = pinwheel(n)
        alive = vertices_of(edges)
        print(f"PW_{n}: vertices={len(alive)} edges={len(edges)} score={solve(edges, alive, 0)}")
    print("\nPW_2 first moves:")
    edges = pinwheel(2); alive = vertices_of(edges)
    for row in legal_outcomes(edges, alive, 0):
        print(describe_pinwheel_edge(row[0]), "gain", row[1], row[2], "optimal final", row[3])

    print("\nFriendship graphs:")
    for n in range(1, 6):
        solve.cache_clear()
        edges = friendship(n)
        alive = vertices_of(edges)
        print(f"F_{n}: vertices={len(alive)} edges={len(edges)} score={solve(edges, alive, 0)}")

    print("\nComplete bipartite graphs K(2,b):")
    for b in range(1, 7):
        solve.cache_clear()
        edges = complete_bipartite(2, b)
        alive = vertices_of(edges)
        print(f"K(2,{b}): vertices={len(alive)} edges={len(edges)} score={solve(edges, alive, 0)}")

    print("\nLoopy cycles near the Ferris wheel cases:")
    # Keep this list short; the direct solver is intentionally simple.
    for n, k in [(8, 7), (8, 8), (9, 8), (9, 9)]:
        solve.cache_clear()
        edges = loopy_cycle(n, k)
        alive = vertices_of(edges)
        print(f"C({n},{k}): vertices={len(alive)} edges={len(edges)} score={solve(edges, alive, 0)}")

    print("\nWheel and Ferris wheel graphs:")
    for n in range(3, 8):
        solve.cache_clear()
        w_edges = wheel(n)
        w_alive = vertices_of(w_edges)
        w_score = solve(w_edges, w_alive, 0)
        solve.cache_clear()
        f_edges = ferris_wheel(n)
        f_alive = vertices_of(f_edges)
        f_score = solve(f_edges, f_alive, 0)
        print(f"n={n}: W_n vertices={len(w_alive)} score={w_score}; C(n,n) vertices={len(f_alive)} score={f_score}")

    print("\nBalloon paths:")
    for n in range(1, 10):
        solve.cache_clear()
        edges = balloon_path(n)
        alive = vertices_of(edges)
        print(f"BP_{n}: vertices={len(alive)} edges={len(edges)} score={solve(edges, alive, 0)}")

    print("\nTwo-copy balloon path split positions:")
    for n in range(1, 5):
        solve.cache_clear()
        edges = two_balloon_paths(n)
        alive = vertices_of(edges)
        print(f"BP_{n} + BP_{n}: vertices={len(alive)} edges={len(edges)} score={solve(edges, alive, 0)}")

    print("\nComplete graphs:")
    for n in range(1, 7):
        solve.cache_clear()
        edges = complete_graph(n)
        # For K_1, include the isolated vertex explicitly. The paper omits this
        # edgeless case because starting vertices are assumed to have nonzero degree.
        alive = frozenset(f"v{i}" for i in range(n))
        print(f"K_{n}: vertices={len(alive)} edges={len(edges)} score={solve(edges, alive, 0)}")

    print("\nHypercubes:")
    for dim in range(1, 4):
        solve.cache_clear()
        edges = hypercube(dim)
        alive = vertices_of(edges)
        print(f"Q_{dim}: vertices={len(alive)} edges={len(edges)} score={solve(edges, alive, 0)}")

    print("\nPrism graphs:")
    for n in range(3, 6):
        solve.cache_clear()
        edges = prism(n)
        alive = vertices_of(edges)
        print(f"PG_{n}: vertices={len(alive)} edges={len(edges)} score={solve(edges, alive, 0)}")

    print("\nLoopy stars and double loopy stars:")
    for k in [1, 2]:
        for n in range(1, 6):
            solve.cache_clear()
            edges = loopy_starlike(n, k, 1)
            alive = vertices_of(edges)
            print(f"L({n},{k},1): vertices={len(alive)} edges={len(edges)} score={solve(edges, alive, 0)}")

    print("\nDouble loopy star recurrence check:")
    for n in range(1, 21):
        margin = double_loopy_star_margin(n, 0, 0, 0, 0)
        score = ((n + 1 + margin) // 2, (n + 1 - margin) // 2)
        expected = double_loopy_star_formula_score(n)
        assert score == expected, (n, score, expected)
    print("L(n,2) recurrence agrees with the closed form for n=1..20")

    print("\nLoopy starlike trees with length 4:")
    for n, k in [(2, 1), (3, 1), (2, 2), (1, 3), (2, 3)]:
        solve.cache_clear()
        edges = loopy_starlike(n, k, 4)
        alive = vertices_of(edges)
        print(f"L({n},{k},4): vertices={len(alive)} edges={len(edges)} score={solve(edges, alive, 0)}")

    print("\nPetersen graph:")
    solve.cache_clear()
    edges = petersen()
    alive = vertices_of(edges)
    print(f"Petersen: vertices={len(alive)} edges={len(edges)} score={solve(edges, alive, 0)}")
