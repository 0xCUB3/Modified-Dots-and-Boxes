import math
import time

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

# Function to simulate the game recursively with memoization
def simulate_game(edges, vertices, player_scores, current_player, memo):
    # Convert game state to a hashable key for memoization
    game_state_key = (tuple(sorted(edges.items())), tuple(sorted(vertices.items())), tuple(player_scores), current_player)
    
    if game_state_key in memo:
        # Return the cached result
        return memo[game_state_key]

    if not any(edges.values()):
        # No moves left, game over
        winner = current_player if player_scores[current_player] > player_scores[1 - current_player] else 1 - current_player
        memo[game_state_key] = winner
        return winner

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
                winner = simulate_game(new_edges, new_vertices, new_player_scores, next_player, memo)
            else:
                # The current player made a move that created an isolated vertex, hence they play again
                winner = simulate_game(new_edges, new_vertices, new_player_scores, current_player, memo)

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
        winner = current_player if player_scores[current_player] > player_scores[1 - current_player] else 1 - current_player
    else:
        winner = winner

    # Cache the result before returning it
    memo[game_state_key] = winner
    return winner

def main():
    mode = input("Enter 'specific' for a specific number of spokes or 'range' for a range of spokes: ").lower()
    if mode == 'specific':
        n_spokes = int(input("Enter the number of spokes (3 or more): "))
        while n_spokes < 3:
            n_spokes = int(input("Please enter a valid number of spokes (3 or more): "))
        edges, vertices = create_wheel_graph_edges_and_vertices(n_spokes)
        initial_player_scores = [0, 0]
        memo = {}

        start_time = time.time()
        winner = simulate_game(edges, vertices, initial_player_scores, 0, memo)
        elapsed_time = time.time() - start_time

        print(f"For {n_spokes} spokes: Player {winner + 1} wins with perfect play. Time taken: {elapsed_time:.4f} seconds.")
    elif mode == 'range':
        x_value = int(input("Enter the maximum number of spokes (X) for range (3 to X): "))
        while x_value < 3:
            x_value = int(input("Please enter a valid maximum number of spokes (3 or more): "))
        memo = {}
        
        for n_spokes in range(3, x_value + 1):
            edges, vertices = create_wheel_graph_edges_and_vertices(n_spokes)
            initial_player_scores = [0, 0]

            start_time = time.time()
            winner = simulate_game(edges, vertices, initial_player_scores, 0, memo)
            elapsed_time = time.time() - start_time

            print(f"{n_spokes} spokes - Player {winner + 1} wins with perfect play. Time taken: {elapsed_time:.4f} seconds.")
    else:
        print("Invalid mode selected. Please enter 'specific' or 'range'.")
if __name__ == "__main__":
    main()