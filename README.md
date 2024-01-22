# Modified Dots and Boxes

A strategic turn-based game for two players, implemented with Pygame. Players take turns selecting an edge on a wheel graph. Once all edges around a vertex are selected, it becomes isolated and is owned by the player. The player with the most vertices when all edges are selected wins the game.

In the algorithm file, a recursive method is used to determine outcomes for various classes of graphs. A summary of these findings can be found below. 

## Features

- Dynamic generation of the wheel graph based on the number of spokes.
- Colorful interactive GUI with undo and redo functionalities.
- Simple and intuitive gameplay ideal for quick sessions and strategy enthusiasts.

## Discoveries
In a **complete graph**, player 2 wins for odd K_n and player 1 wins for even K_n, where K_n is a complete graph with n vertices. (Proof TBD)
![K_5](https://github.com/0xCUB3/Modified-Dots-and-Boxes/assets/94565160/1ca0ca1a-dd1f-422a-952c-fe80c3a93f6d)
*Example of the complete graph K_5*

In a **wheel graph**, the same pattern is true. (Proof TBD) A wheel graph is one where there is a center vertex connected to n outer vertices which are all connected via a cycle, analogous to spokes in a wheel. In this graph family, player 2 wins with an even number of spokes and player 1 wins with an odd number of spokes. 
![Wheel graph with 5 spokes](https://github.com/0xCUB3/Modified-Dots-and-Boxes/assets/94565160/b6b48644-02fe-4326-9087-8766c6fa4d91)
*Example of the wheel graph with 5 spokes*

The next discovery came in a graph family that we defined as **hanging trees**. These graphs are similar to star graphs, but each outer vertex has an extra edge connecting to itself. In this graph family, player 1 wins for odd spokes and player 2 wins for even spokes. (Proof TBD)
![Hanging Tree with 5 spokes](https://github.com/0xCUB3/Modified-Dots-and-Boxes/assets/94565160/aae1f137-863f-4e77-9c0a-378dfa7ccae6)
*Example of a hanging tree with 5 spokes*

Afterward, we were interested if the same pattern continued when extra vertices were added to certain "spokes" of hanging trees. We found this to be the case. (Proof TBD)
![Extended Hanging Tree](https://github.com/0xCUB3/Modified-Dots-and-Boxes/assets/94565160/3362730d-989c-4b0a-8548-0d196ab976a1)
*Example of a hanging tree with 5 spokes and 2 extra vertices on one of the spokes*

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
