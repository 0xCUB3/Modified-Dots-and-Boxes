# Wheel Graph Dots and Boxes Game

A strategic turn-based game for two players, implemented with Pygame. Players take turns selecting an edge on a wheel graph. Once all edges around a vertex are selected, it becomes isolated and is owned by the player. The player with the most vertices when all edges are selected wins the game.

## Features

- Dynamic generation of the wheel graph based on the number of spokes.
- Colorful interactive GUI with undo and redo functionalities.
- Simple and intuitive gameplay ideal for quick sessions and strategy enthusiasts.

## Getting Started

### Prerequisites

Before running the game, make sure you have Python and Pygame installed on your system. You can install Pygame using pip:
```
pip install pygame
```

### Installation

Clone the repository to your local machine using the command:
```
git clone https://github.com/your-github-username/wheel-graph-dot-boxes.git
```
Navigate to the cloned directory:
```
cd wheel-graph-dot-boxes
```
Run the game with Python:
```
python dots_and_boxes.py
```
or
```
python3 dots_and_boxes.py
```

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

Distributed under the MIT License. See `LICENSE` for more information.
