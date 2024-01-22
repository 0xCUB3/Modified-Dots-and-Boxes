import time
from visualize_graph import visualize_graph

# Create a Hanging Tree Graph
def create_hanging_tree_edges_and_vertices(n_leaves):
    edges = {(0, vertex): True for vertex in range(1, n_leaves + 1)}
    edges.update({(vertex, vertex): True for vertex in range(1, n_leaves + 1)})  # Adding loops
    vertices = {vertex for vertex in range(0, n_leaves + 1)}
    return edges, vertices

# Create a Hanging Tree Graph with Extra Vertices
def create_extended_hanging_tree_edges_and_vertices(n_leaves, extra_spokes=0, extra_vertices=0):
    edges = {}
    vertices = {0}  # Central vertex (root)

    current_id = n_leaves + 1

    for spoke in range(1, n_leaves + 1):
        vertices.add(spoke)
        
        # Determine whether to add extra vertices to the current spoke
        if extra_spokes > 0:
            extra_spokes -= 1
            last_id = 0  # Start from the root
            for _ in range(extra_vertices):
                vertices.add(current_id)
                edges[(last_id, current_id)] = True  # Connect the last vertex in the path to the current one
                last_id = current_id
                current_id += 1
            edges[(last_id, spoke)] = True
        else:
            edges[(0, spoke)] = True  # Directly connect the root to the spoke

        # Add a loop at each outer vertex
        edges[(spoke, spoke)] = True

    return edges, vertices

# Create a Wheel Graph
def create_wheel_graph_edges_and_vertices(n_spokes):
    edges = {(0, vertex): True for vertex in range(1, n_spokes + 1)}
    edges.update({(vertex, vertex + 1): True for vertex in range(1, n_spokes)})
    edges[(n_spokes, 1)] = True
    vertices = {0, *range(1, n_spokes + 1)}
    return edges, vertices

def simulate_game(edges, vertices, player_scores, current_player, memo):
    # Convert the current game state to a hashable key for memoization
    game_state_key = (frozenset(edges), frozenset(vertices), tuple(player_scores), current_player)

    # If the result for this game state is already memoized, return it
    if game_state_key in memo:
        return memo[game_state_key]

    # Base case: If there are no remaining edges, the game is over
    if not any(edges.values()):
        # Determine the winner based on the player with the higher score
        winner = 1 - current_player
        memo[game_state_key] = winner
        return winner

    # Determine the next player's turn
    next_player = 1 - current_player

    # Initialize variables to keep track of the best move and score
    best_score = float('-inf') if current_player == 0 else float('inf')
    best_move = None

    # Iterate through each edge in the current game state
    for edge, active in edges.items():
        if active:
            # Create copies of the game state to simulate the effect of the move
            new_edges = dict(edges)
            new_vertices = set(vertices)
            new_player_scores = player_scores.copy()
            new_edges[edge] = False

            # Check if the move creates an isolated vertex
            isolated = all(edge[1] not in check_edge or not active for check_edge, active in new_edges.items())

            # If an isolated vertex is created, update game state and scores
            if isolated:
                new_vertices.add(edge[1])
                new_player_scores[current_player] += 1

            # Determine the winner based on the simulated move
            if not isolated:
                winner = simulate_game(new_edges, new_vertices, new_player_scores, next_player, memo)
            else:
                winner = simulate_game(new_edges, new_vertices, new_player_scores, current_player, memo)

            # Calculate the score difference for the current player
            current_score_diff = new_player_scores[0] - new_player_scores[1]

            # Update the best move and score for the current player
            if current_player == 0:
                if current_score_diff > best_score:
                    best_score = current_score_diff
                    best_move = edge
            else:
                if current_score_diff < best_score:
                    best_score = current_score_diff
                    best_move = edge

    # If no moves improved the situation, determine the winner based on the current score
    if best_move is None:
        winner = 1 - current_player
    else:
        winner = winner

    # Memoize the result before returning it
    memo[game_state_key] = winner
    return winner


def main():
    graph_type = input("Enter 'wheel' for a Wheel Graph, 'hanging' for a Hanging Tree, or 'extended' for an Extended Hanging Tree with extra vertices: ").lower()
    mode = input("Enter 'specific' for a specific number or 'range' for a range: ").lower()

    if graph_type == 'wheel':
        create_graph = create_wheel_graph_edges_and_vertices
    elif graph_type == 'hanging':
        create_graph = create_hanging_tree_edges_and_vertices
    elif graph_type == 'extended':
        extra_vertices = int(input("Enter the number of extra vertices to add: "))
        extra_spokes = int(input("Enter the number of spokes to extend with extra vertices: "))
        def create_graph(n_leaves):
            return create_extended_hanging_tree_edges_and_vertices(n_leaves, extra_spokes, extra_vertices)
    else:
        print("Invalid graph type selected.")
        return

    # Find the value for 1 size
    if mode == 'specific':
        n_elements = int(input("Enter the number of elements (3 or more): "))
        while n_elements < 3:
            n_elements = int(input("Please enter a valid number (3 or more): "))
        edges, vertices = create_graph(n_elements)
        initial_player_scores = [0, 0]
        memo = {}

        start_time = time.time()
        winner = simulate_game(edges, vertices, initial_player_scores, 0, memo)
        elapsed_time = time.time() - start_time

        print(f"For {n_elements} elements: Player {winner + 1} wins with perfect play. Time taken: {elapsed_time:.4f} seconds.")

        # Call to visualize the graph here
        visualize_graph(edges, vertices)
    # Find the value for a range of sizes (3 to X)
    elif mode == 'range':
        x_value = int(input("Enter the maximum number (X) for the range (3 to X): "))
        while x_value < 3:
            x_value = int(input("Please enter a valid number (3 or more): "))
        memo = {}

        for n_elements in range(3, x_value + 1):
            edges, vertices = create_graph(n_elements)
            initial_player_scores = [0, 0]

            start_time = time.time()
            winner = simulate_game(edges, vertices, initial_player_scores, 0, memo)
            elapsed_time = time.time() - start_time

            print(f"{n_elements} elements - Player {winner + 1} wins with perfect play. Time taken: {elapsed_time:.4f} seconds.")
    else:
        print("Invalid mode selected. Please enter 'specific' or 'range'.")

if __name__ == "__main__":
    main()
