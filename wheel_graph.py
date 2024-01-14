import math

# Constants
PLAYER_COUNT = 2

# Function to create a wheel graph: a center vertex connected to all outer vertices forming a cycle
def create_wheel_graph_edges_and_vertices(n_spokes):
    edges = {}
    vertices = {0: False}  # Center vertex

    # Create outer vertices connected to the center (vertex 0)
    for vertex in range(1, n_spokes + 1):
        vertices[vertex] = False
        edges[(0, vertex)] = True  # Edge from center to outer vertex

    # Connect outer vertices to form a cycle
    for vertex in range(1, n_spokes):
        edges[(vertex, vertex + 1)] = True
    edges[(n_spokes, 1)] = True  # Closing the cycle

    return edges, vertices

# Function to simulate the game recursively
def simulate_game(edges, vertices, player_scores, current_player):
    if not any(edges.values()):
        # No moves left, game over
        return current_player if player_scores[current_player] > player_scores[1 - current_player] else 1 - current_player

    best_score = float('-inf') if current_player == 0 else float('inf')
    best_move = None
    next_player = 1 - current_player

    for edge, active in edges.items():
        if active:
            new_edges = edges.copy()
            new_vertices = vertices.copy()
            new_player_scores = player_scores.copy()
            new_edges[edge] = False

            # Check for isolated vertices (those with no active edges)
            isolated = True
            for check_edge, active in new_edges.items():
                if edge[1] in check_edge and active:
                    isolated = False
                    break
            
            if isolated:
                new_vertices[edge[1]] = True
                new_player_scores[current_player] += 1

            # If no isolated vertex is created, it's the other player's turn
            if not isolated:
                winner = simulate_game(new_edges, new_vertices, new_player_scores, next_player)
            else:
                # The current player made a move that created an isolated vertex, hence they play again
                winner = simulate_game(new_edges, new_vertices, new_player_scores, current_player)

            current_score_diff = new_player_scores[current_player] - new_player_scores[next_player]
            
            # Choose the better score for the current player
            if current_player == 0:
                if current_score_diff > best_score:
                    best_score = current_score_diff
                    best_move = edge
            else:
                if current_score_diff < best_score:
                    best_score = current_score_diff
                    best_move = edge

    if best_move is None:
        # No moves improved the situation, so return the winner based on the current score
        return current_player if player_scores[current_player] > player_scores[1 - current_player] else 1 - current_player

    return winner

# Main function
def main():
    # Ask for the number of spokes (must be greater than 2)
    while True:
        n_spokes = int(input("Enter the number of spokes (3 or more): "))
        if n_spokes >= 3:
            break
    
    edges, vertices = create_wheel_graph_edges_and_vertices(n_spokes)
    initial_player_scores = [0, 0]

    winner = simulate_game(edges, vertices, initial_player_scores, 0)
    print(f"Player {winner + 1} wins with perfect play.")

if __name__ == "__main__":
    main()