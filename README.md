# Modified Dots and Boxes

A strategic turn-based game for two players, implemented with Pygame. Players take turns selecting an edge on a wheel graph. Once all edges around a vertex are selected, it becomes isolated and is owned by the player. The player with the most vertices when all edges are selected wins the game.

In the algorithm file, a recursive method is used to determine outcomes for various classes of graphs. A summary of these findings can be found below. 

## Features

- Dynamic generation of the wheel graph based on the number of spokes.
- Colorful interactive GUI with undo and redo functionalities.
- Simple and intuitive gameplay ideal for quick sessions and strategy enthusiasts.

## Discoveries

### Complete Graphs
In a **complete graph**, player 1 wins for 1 & 2 (mod 4) and player 2 wins for 3 & 4 (mod 4) vertices. (Proof TBD)
![K_5](https://github.com/0xCUB3/Modified-Dots-and-Boxes/assets/94565160/1ca0ca1a-dd1f-422a-952c-fe80c3a93f6d)
*Example of the complete graph K_5*

| Number of Vertices | Winner | Score |
| -------- | ------- | ------- |
| 1 | N/A | N/A |
| 2 | P1 | (2 - 0) |
| 3 | P2 | (0 - 3) |
| 4 | P2 | (0 - 4) |
| 5 | P1 | (4 - 1) |
| 6 | P1 | (5 - 1) |
| 7 | P2 | (2 - 5) |
| 8 | P2 | (2 - 6) |
| 9 | P1 | (7 - 2) |
| 10 | P1 | (7 - 3)? |
| 11 | NF | NF |
| 12 | NF | NF |

### Wheel Graphs
A wheel graph is one where there is a center vertex connected to n outer vertices which are all connected via a cycle, analogous to spokes in a wheel. In this graph family, player 2 wins with an even number of spokes and player 1 wins with an odd number of spokes. (Proof TBD)
![Wheel graph with 5 spokes](https://github.com/0xCUB3/Modified-Dots-and-Boxes/assets/94565160/b6b48644-02fe-4326-9087-8766c6fa4d91)
*Example of the wheel graph with 5 spokes*

| Number of Spokes | Winner | Score |
| -------- | ------- | ------- |
| 1 | N/A | N/A |
| 2 | N/A | N/A |
| 3 | P2 | (0 - 4) |
| 4 | P1 | (4 - 1) |
| 5 | P2 | (2 - 4) |
| 6 | P1 | (5 - 2) |
| 7 | P2 | (2 - 6) |
| 8 | P1 | (5 - 4) |
| 9 | P2 | (4 - 6) |
| 10 | P1 | (6 - 5) |
| 11 | P2 | (5 - 7) |
| 12 | P1 | (7 - 6) |
* Observation: A pattern seems to appear at 8 spokes...

### Hanging Trees
The next discovery came in a graph family that we defined as **hanging trees**. These graphs are similar to star graphs, but each outer vertex has an extra edge connecting to itself. In this graph family, player 1 wins for odd spokes and player 2 wins for even spokes. (Proven)
![Hanging Tree with 5 spokes](https://github.com/0xCUB3/Modified-Dots-and-Boxes/assets/94565160/aae1f137-863f-4e77-9c0a-378dfa7ccae6)
*Example of a hanging tree with 5 spokes*

| Number of Spokes | Winner | Score |
| -------- | ------- | ------- |
| 1 | P1 | (2 - 0) |
| 2 | P2 | (0 - 3) |
| 3 | P1 | (3 - 1) |
| 4 | P2 | (1 - 4) |
| 5 | P1 | (4 - 2) |
| 6 | P2 | (2 - 5) |
| 7 | P1 | (5 - 3) |
| 8 | P2 | (3 - 6) |
| 9 | P1 | (6 - 4) |
| 10 | P2 | (4 - 7) |
| 11 | P1 | (7 - 5) |
| 12 | P2 | (5 - 8) |

Afterward, we were interested if the same pattern continued when extra vertices were added to certain "spokes" of hanging trees. We found this to be the case. (Proven)
![Extended Hanging Tree](https://github.com/0xCUB3/Modified-Dots-and-Boxes/assets/94565160/3362730d-989c-4b0a-8548-0d196ab976a1)
*Example of a hanging tree with 5 spokes and 2 extra vertices on one of the spokes*

In a "normal" hanging tree with 2 outer loops, player 2 always wins, but they win by 2 for odd spokes and they win by 3 for even spokes. (Proven)

| Number of Spokes | Winner | Score |
| -------- | ------- | ------- |
| 1 | Tie | (1 - 1) |
| 2 | P2 | (1 - 2) |
| 3 | P2 | (1 - 3) |
| 4 | P2 | (1 - 4) |
| 5 | P2 | (2 - 4) |
| 6 | P2 | (2 - 5) |
| 7 | P2 | (3 - 5) |
| 8 | P2 | (3 - 6) |
| 9 | P2 | (4 - 6) |
| 10 | P2 | (4 - 7) |
| 11 | P2 | (5 - 7) |
| 12 | P2 | (5 - 8) |

In a hanging tree with 1 spokes and n outer loops, player 1 wins for odd loops, and it is a tie for even loops. (Proven)
| Number of Loops | Winner | Score |
| -------- | ------- | ------- |
| 1 | P1 | (2 - 0) |
| 2 | Tie | (1 - 1) |
| 3 | P1 | (2 - 0) |
| 4 | Tie | (1 - 1) |
| 5 | P1 | (2 - 0) |
...and so on

In a hanging tree with 2 spokes and n outer loops, player 2 always wins. (Proven)
| Number of Loops | Winner | Score |
| -------- | ------- | ------- |
| 1 | P2 | (0 - 3) |
| 2 | P2 | (1 - 2) |
| 3 | P2 | (1 - 2) |
| 4 | P2 | (1 - 2) |
| 5 | P2 | (1 - 2) |
...and so on

For more complicated hanging tree revelations, please see [hanging_trees.md](https://github.com/0xCUB3/Modified-Dots-and-Boxes/blob/main/hanging_trees.md)

### Petersen graph
The Petersen graph is a common graph used to prove or disprove a lot of graph theory-related theorems. Player 1 wins on Petersen with a score of (9 - 1) (Proof TBD). 

### Friendship graphs
A friendship graph is one with a center vertex and n triangles around it. Player 1 wins by 1 for odd n and player 2 wins by 3 for even n (Proof TBD). 
![F_3](https://github.com/0xCUB3/Modified-Dots-and-Boxes/assets/94565160/1c819731-543b-43d8-9465-1753d562dd45)


| Number of Triangles | Winner | Score |
| -------- | ------- | ------- |
| 1 | P2 | (0 - 3) |
| 2 | P1 | (3 - 2) |
| 3 | P2 | (2 - 5) |
| 4 | P1 | (5 - 4) |
| 5 | P2 | (4 - 7) |
| 6 | P1 | (7 - 6) |
| 7 | P2 | (6 - 9) |
| 8 | P1 | (9 - 8) |

But now I hear you ask, what about friendship graphs with squares instead of triangles? You asked that, right? RIGHT?????

| Number of Squares | Winner | Score |
| -------- | ------- | ------- |
| 1 | P2 | (0 - 4) |
| 2 | P2 | (2 - 5) |
| 3 | P2 | (4 - 6) |
| 4 | P2 | (6 - 7) |
| 5 | P2 | (7 - 9) |
| 6 | P2 | (9 - 10) |
| 7 | P2 | (10 - 12) |
| 8 | P2 | (12 - 13) |

## How to Play

1. Enter the desired number of spokes at the start screen.
2. Players take turns to click on the active (brighter color) edges of the graph to select them.
3. Try to isolate vertices by selecting all edges around them. They will change color to indicate your ownership.
4. If you isolate a vertex, you get another turn.
5. Use the 'Undo' and 'Redo' buttons as necessary.
6. The game ends when all edges are selected, and the player with the most vertices wins.

## Gameplay Example

https://github.com/0xCUB3/Modified-Dots-and-Boxes/assets/94565160/88254238-7efe-472b-b3e0-9427711ec044

## License

Distributed under the MIT License. See [LICENSE](https://github.com/0xCUB3/Modified-Dots-and-Boxes?tab=MIT-1-ov-file#) for more information.
