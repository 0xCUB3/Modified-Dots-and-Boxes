from typing import Tuple, List
import argparse
import sys
import time
import networkx as nx
import matplotlib.pyplot as plt

def run(graph: nx.Graph) -> None:
    draw_and_save_graph(graph)
    start_time = time.time()
    memo = {}
    net_score, sequence = _net_score(graph=graph, depth=0, moves=[], memo=memo)
    print(f'Elapsed time: {time.time() - start_time:.2f} seconds')
    # Calculate each player's score based on the net score
    first_player_score = (graph.number_of_nodes() + net_score) // 2
    second_player_score = (graph.number_of_nodes() - net_score) // 2
    print_scores(first_player_score, second_player_score)
    print(f"Winning Moves Sequence: {sequence}")

def print_scores(first_player_score: int, second_player_score: int) -> None:
    if first_player_score > second_player_score:
        print(f'First player wins by {first_player_score - second_player_score} point(s). Score: ({first_player_score} - {second_player_score})')
    elif second_player_score > first_player_score:
        print(f'Second player wins by {second_player_score - first_player_score} point(s). Score: ({first_player_score} - {second_player_score})')
    else:
        print('Tie game!')

def _net_score(graph: nx.Graph, depth: int, moves: List[Tuple[int, int]], memo: dict) -> Tuple[int, List[Tuple[int, int]]]:
    graph_key = nx.weisfeiler_lehman_graph_hash(graph)
    if graph_key in memo:
        return memo[graph_key]
    
    if nx.is_forest(graph):
        # Edge case for trees where the sequence of moves leading to realizing it's a tree is relevant.
        memo[graph_key] = (graph.number_of_nodes(), moves)
        return graph.number_of_nodes(), moves

    best_outcome = -graph.number_of_nodes()  # Initialize with the worst possible score
    best_sequence = moves  # Start with the current sequence
    
    for e in graph.edges:
        # Each edge considered for cutting creates a new branch of exploration with its own sequence.
        new_moves = moves + [e]
        test_graph = graph.copy()
        if test_graph.degree(e[0]) == 1 and test_graph.degree(e[1]) == 1:
            points = 2
            test_graph.remove_edge(*e)
            test_graph.remove_node(e[0])
            test_graph.remove_node(e[1])
        elif test_graph.degree(e[0]) == 1:
            points = 1
            test_graph.remove_edge(*e)
            test_graph.remove_node(e[0])
        elif graph.degree(e[1]) == 1:
            points = 1
            test_graph.remove_edge(*e)
            test_graph.remove_node(e[1])
        else:
            points = 0
            test_graph.remove_edge(*e)

        mult = 1 if points > 0 else -1
        outcome, sequence_for_outcome = _net_score(test_graph, depth + 1, new_moves, memo)
        outcome = points + mult * outcome

        if (best_sequence is moves or outcome > best_outcome):  
            # Found a new best outcome, update the best outcome and its sequence.
            best_outcome = outcome
            best_sequence = sequence_for_outcome
    
    # Before returning, ensure this best outcome and its sequence is memoized to avoid re-computation.
    memo[graph_key] = (best_outcome, best_sequence)
    return best_outcome, best_sequence

def draw_and_save_graph(graph: nx.Graph) -> None:
    plt.figure(figsize=(10, 8))  # Set the figure size (width, height) in inches.
    nx.draw(graph, with_labels=True, node_size=500, node_color='skyblue', font_size=10, font_weight='bold')
    plt.savefig('graph.png')
    plt.close()  # Close the figure to prevent it from being displayed in a window.

def create_friendship_graph(n: int, loop_size: int) -> nx.Graph:
    G = nx.Graph()
    central_vertex = 0
    G.add_node(central_vertex)
    
    for loop_index in range(1, n + 1):
        previous_vertex = None
        for vertex_offset in range(loop_size - 1):
            current_vertex = (loop_index - 1) * (loop_size - 1) + vertex_offset + 1
            G.add_node(current_vertex)
            if previous_vertex is not None:
                G.add_edge(previous_vertex, current_vertex)
            else:
                G.add_edge(central_vertex, current_vertex)
            previous_vertex = current_vertex
        
        # Connecting the last vertex of the loop back to the central vertex
        # and the first vertex of the loop to complete the loop
        if loop_size > 2:
            G.add_edge(previous_vertex, central_vertex)

    return G

def main():
    sys.setrecursionlimit(10000)
    parser = argparse.ArgumentParser(description='Solve a game.')
    parser.add_argument(
        '--type',
        default='file',
        type=str,
        help='Edge source type name (defaults to "file").'
    )
    parser.add_argument(
        '--nodes',
        type=int,
        help='Number of nodes for a complete graph.'
    )
    parser.add_argument(
        '--loops',
        type=int,
        help='Number of loops for a friendship graph.'
    )

    args = parser.parse_args()
    src_type: str = args.type

    if src_type == 'complete':
        if args.nodes is None:
            raise ValueError('Nodes parameter must be provided for "complete" type.')
        G = nx.complete_graph(args.nodes)
        _ = run(G)
    elif src_type == 'wheel':
        if args.nodes is None:
            raise ValueError('Nodes parameter must be provided for "wheel" type.')
        _ = run(nx.wheel_graph(args.nodes+1))
    elif src_type == 'petersen':
        _ = run(nx.petersen_graph())
    elif src_type == 'friendship':
        if args.nodes is None or args.loops is None:
            raise ValueError('Nodes & loops parameters must be provided for "friendship" type.')
        _ = run(create_friendship_graph(args.nodes, args.loops))
    elif src_type == 'other':
        G = nx.Graph()
        G.add_nodes_from([1, 2, 3, 4])
        G.add_edges_from([(1,2), (2,3)])
        _ = run(G)

if __name__ == '__main__':
    main()