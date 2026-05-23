# Paper verification

This directory contains a small, self-contained verifier for the graph version of Dots and Boxes used in the paper.

The verifier is intentionally separate from the older GUI and benchmark code in the repository. It uses the paper's edge-object convention:

- each ordinary edge is one removable object;
- each loop is one removable object;
- a loop counts once as incident to its vertex for scoring;
- after a move, every vertex with no remaining incident edge-object is scored by the mover;
- a scoring move gives the same player another move.

Run it from the repository root with:

```bash
python3 verification/solve_graph_game.py
```

The script performs exhaustive memoized minimax checks for representative finite cases from the paper, including:

- pinwheel graphs;
- friendship graphs;
- complete bipartite graphs `K(2,b)`;
- loopy cycles near the Ferris Wheel cases;
- wheel and Ferris Wheel graphs;
- balloon paths and two-copy balloon-path split positions;
- complete graphs through `K_6`;
- hypercubes through `Q_3`;
- prism graphs through `PG_5`;
- loopy stars and double loopy stars;
- selected loopy starlike trees;
- the Petersen graph.

It also checks the finite-state recurrence used in the double-loopy-star proof through `n=20`.

This verifier is meant to support the manuscript's finite tables and small cases. General statements in the paper should still be read from the proofs in the manuscript, not from computation alone.
