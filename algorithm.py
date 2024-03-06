import argparse
import sys
import time
import networkx as nx
import matplotlib.pyplot as plt

_progress = {'top_level': 1000, 'count': 0, 'start_time': None}

def run(graph: nx.Graph) -> None:
    global _progress  # Declare that we'll use the global version
    memo = {}
    draw_and_save_graph(graph)
    _progress['start_time'] = time.perf_counter()
    net_score = _net_score(graph=graph, depth=0, memo=memo)
    # Calculate each player's score based on the net score
    first_player_score = (graph.number_of_nodes() + net_score) // 2
    second_player_score = (graph.number_of_nodes() - net_score) // 2
    print_scores(first_player_score, second_player_score)

def print_scores(first_player_score: int, second_player_score: int) -> None:
    if first_player_score > second_player_score:
        print(f'First player wins by {first_player_score - second_player_score} point(s). Score: ({first_player_score} - {second_player_score})')
    elif second_player_score > first_player_score:
        print(f'Second player wins by {second_player_score - first_player_score} point(s). Score: ({first_player_score} - {second_player_score})')
    else:
        print('Tie game!')

def _net_score(graph: nx.Graph, depth: int, memo: dict) -> int:
    # graph_key = nx.weisfeiler_lehman_graph_hash(graph)
    graph_key = build_graph_key(graph)
    if graph_key in memo:
        return memo[graph_key]
    
    if nx.is_forest(graph):
        # Edge case for trees where the sequence of moves leading to realizing it's a tree is relevant.
        memo[graph_key] = graph.number_of_nodes()
        return graph.number_of_nodes()

    best_outcome = -1 * graph.number_of_nodes()  # Initialize with the worst possible score
    
    tried_edges = []
    for e in graph.edges:
        if e in tried_edges:
            continue
        tried_edges.append(e)
        # Each edge considered for cutting creates a new branch of exploration with its own sequence.
        test_graph = graph.copy()
        if e[0] != e[1]:
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
        else:
            if test_graph.degree(e[0]) == 2:
                points = 1
                test_graph.remove_edge(*e)
                test_graph.remove_node(e[0])
            else:
                points = 0
                test_graph.remove_edge(*e)

        mult = 1 if points > 0 else -1
        if test_graph.number_of_nodes() > 0:
            outcome = points + mult * _net_score(test_graph, depth + 1, memo)
        else:
            outcome = points

        if (outcome > best_outcome):
            best_outcome = outcome
            if outcome == graph.number_of_nodes():
                break
    
    # Before returning, ensure this best outcome and its sequence is memoized to avoid re-computation.
    _track_progress(depth)
    memo[graph_key] = best_outcome
    return best_outcome

def _track_progress(depth: int) -> None:
    global _progress
    if depth <= _progress['top_level']:
        if depth == _progress['top_level']:
            _progress['count'] += 1
        else:
            _progress['top_level'] = depth
            _progress['count'] = 1
        elapsed_secs = time.perf_counter() - _progress["start_time"]
        print(
            f'top solved depth:{depth} ' +
            f'count:{_progress["count"]} '+
            f'seconds:{elapsed_secs:.2f}'
        )

def build_graph_key(graph: nx.Graph) -> str:
    key = []
    for e in graph.edges:
        key.append(f'{e[0]}-{e[1]}')
    return '|'.join(key)

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

def create_balloon_path_graph(n: int) -> nx.Graph:
    G = nx.Graph()
    for i in range(n - 1):
        G.add_node(i)
        G.add_node(i + 1)
        G.add_edge(i, i + 1)
    for vertex in G.nodes:
        G.add_edge(vertex, vertex)
    return G

def create_balloon_cycle_graph(n: int) -> nx.Graph:
    G = create_balloon_path_graph(n)
    G.add_edge(n - 1, 0)
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
    elif src_type == 'balloon_path':
        if args.nodes is None:
            raise ValueError('Nodes parameter must be provided for "balloon_path" type.')
        _ = run(create_balloon_path_graph(args.nodes))
    elif src_type == 'balloon_cycle':
        if args.nodes is None:
            raise ValueError('Nodes parameter must be provided for "balloon_cycle" type.')
        _ = run(create_balloon_cycle_graph(args.nodes))
    elif src_type == 'other':
        G = nx.Graph()
        G.add_nodes_from([1, 2, 3, 4])
        G.add_edges_from([(1,2), (2,3)])
        _ = run(G)

if __name__ == '__main__':
    main()