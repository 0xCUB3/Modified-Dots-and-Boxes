import argparse
import sys
import time
import networkx as nx
import matplotlib.pyplot as plt
from typing import Tuple, List, Dict

_progress = {'top_level': 1000, 'count': 0, 'start_time': None}

class Vertex:
    def __init__(self, raw_id: int, graph: nx.Graph) -> None:
        self.raw_id = raw_id
        self.neighbors = list(graph.neighbors(raw_id))
        self.num_neighbors = len(self.neighbors)
        self.num_loops = sum(1 for n in self.neighbors if n == raw_id)
        self.canonical_id: int = -1
        self.category_key: List[int] = None
        self.category: int = -1
        self.prior_category: int = -1

class CanonicalEdges:
    def __init__(self, graph: nx.Graph) -> None:
        self.graph = graph
        self._init_vertices()

    def _init_vertices(self) -> None:
        self.vertices: Dict[int, Vertex] = {node: Vertex(node, self.graph) for node in self.graph.nodes()}
        self._num_vertices = len(self.vertices)

    def calc(self) -> List[Tuple[int, int]]:
        self._categorize_vertices_by_connections()
        self._finalize_canonical_ids()
        raw_edges = [
            (v.canonical_id, self.vertices[n].canonical_id)
            for v in self.vertices.values() for n in v.neighbors
            if v.canonical_id <= self.vertices[n].canonical_id
        ]
        return sorted(raw_edges)

    def _categorize_vertices_by_connections(self) -> None:
        self._init_category_iteration_variables()
        while not self._iteration_is_done():
            self._update_category_iteration_variables()

    def _init_category_iteration_variables(self) -> None:
        self._iterations = 0
        for v in self.vertices.values():
            v.category_key = [v.num_neighbors, -1 * v.num_loops]
        self._update_categories_based_on_category_keys()

    def _update_categories_based_on_category_keys(self) -> None:
        self._category_keys = list(set(
            [tuple(v.category_key) for v in self.vertices.values()]
        ))
        self._category_keys.sort()
        self._num_categories = len(self._category_keys)
        vertices_for_category_key: Dict[Tuple[int, ...], List[Vertex]] = {
            category_key: [] for category_key in self._category_keys
        }
        for v in self.vertices.values():
            vertices_for_category_key[tuple(v.category_key)].append(v)
        for i, category_key in enumerate(self._category_keys):
            for v in vertices_for_category_key[category_key]:
                v.category = i
        self._iterations += 1

    def _iteration_is_done(self) -> bool:
        done_for_simple_cases = (
            (self._num_categories == 1)
            or (self._num_categories == self._num_vertices)
            or (self._iterations >= self._num_vertices)
        )
        if done_for_simple_cases:
            return True
        else:
            a_category_has_changed = False
            for v in self.vertices.values():
                if v.category != v.prior_category:
                    a_category_has_changed = True
                    break
            return not a_category_has_changed

    def _update_category_iteration_variables(self) -> None:
        for v in self.vertices.values():
            v.prior_category = v.category
            v.category_key = [v.category]
            num_neighbors_for_category = [
                0 for _ in range(self._num_categories)
            ]
            for n in v.neighbors:
                num_neighbors_for_category[self.vertices[n].category] += 1
            v.category_key.extend(reversed(num_neighbors_for_category))
        self._update_categories_based_on_category_keys()

    def _finalize_canonical_ids(self) -> None:
        if self._num_categories == self._num_vertices:
            for v in self.vertices.values():
                v.canonical_id = v.category
        else:
            vertices_for_category: Dict[int, List[Vertex]] = {
                i: [] for i in range(self._num_categories)
            }
            for v in self.vertices.values():
                vertices_for_category[v.category].append(v)
            self._next_canonical_id = 0
            for i in range(self._num_categories):
                self._assign_canonical_ids_for_ties(
                    vertices_for_category[i]
                )

    def _assign_canonical_ids_for_ties(self,
        vertices: List[Vertex]
    ) -> None:
        for _ in range(len(vertices)):
            if len(vertices) == 1:
                next_vertex = vertices[0]
            else:
                connected_to_canonical_id, not_connected_to_canonical_id = \
                    self._split_by_connection_to_canonical_id(vertices)
                if connected_to_canonical_id:
                    min_canonical_id = {
                        v.raw_id: self._num_vertices
                        for v in connected_to_canonical_id
                    }
                    for v in connected_to_canonical_id:
                        for n in v.neighbors:
                            if self.vertices[n].canonical_id != -1:
                                if (
                                    self.vertices[n].canonical_id <
                                    min_canonical_id[v.raw_id]
                                ):
                                    min_canonical_id[v.raw_id] = \
                                        self.vertices[n].canonical_id
                    connected_to_canonical_id.sort(
                        key=lambda v:
                        (min_canonical_id[v.raw_id], v.raw_id)
                    )
                    next_vertex = connected_to_canonical_id[0]
                else:
                    not_connected_to_canonical_id.sort(
                        key=lambda v: v.raw_id
                    )
                    next_vertex = not_connected_to_canonical_id[0]
            next_vertex.canonical_id = self._next_canonical_id
            self._next_canonical_id += 1
            vertices.remove(next_vertex)

    def _split_by_connection_to_canonical_id(self,
        vertices: List[Vertex]
    ) -> Tuple[List[Vertex], List[Vertex]]:
        connected_to_canonical_id: List[Vertex] = []
        not_connected_to_canonical_id: List[Vertex] = []
        for v in vertices:
            connected = False
            for n in v.neighbors:
                if self.vertices[n].canonical_id != -1:
                    connected_to_canonical_id.append(v)
                    connected = True
                    break
            if not connected:
                not_connected_to_canonical_id.append(v)
        return (connected_to_canonical_id, not_connected_to_canonical_id)

def run(graph: nx.Graph) -> None:
    global _progress
    memo = {}
    draw_and_save_graph(graph)
    _progress['start_time'] = time.perf_counter()
    
    # Using the CanonicalEdges directly with the graph object now.
    canonical_edge_list = CanonicalEdges(graph).calc()
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
    #graph_key = nx.weisfeiler_lehman_graph_hash(graph)
    #graph_key = build_graph_key(graph)
    # Conversion to canonical edges for memoization
    canonical_edge_list = CanonicalEdges(graph).calc()
    graph_key = str(canonical_edge_list)

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
    # Use a combination of graph invariants to generate a more unique key.
    # This includes degree sequences, but also other structural properties.
    degrees = tuple(sorted(dict(graph.degree()).values()))
    edges = tuple(sorted(map(sorted, graph.edges())))
    num_nodes = graph.number_of_nodes()
    # Example addition: Number of connected components could also influence outcomes.
    num_components = nx.number_connected_components(graph)
    
    # Serialize this information into a string key.
    key = f"{degrees}-{edges}-{num_nodes}-{num_components}"
    return key

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

def create_double_ngon_graph(n):
    G = nx.Graph()

    # Add vertices and edges for the first n-gon
    for i in range(n):
        G.add_edge(i, (i + 1) % n)  # Wrap around using modulo

    # Add vertices and edges for the second n-gon (offset vertices by n)
    for i in range(n, 2*n):
        G.add_edge(i, ((i + 1) % n) + n)

    # Connect corresponding vertices from the first n-gon to the second n-gon
    for i in range(n):
        G.add_edge(i, i + n)

    return G

def create_loopy_star(n: int, k: int) -> nx.MultiGraph:
    """
    Create a loopy star graph with n spokes and k outer loops.

    Args:
        n (int): Number of spokes.
        k (int): Number of outer loops on each spoke.

    Returns:
        networkx.Graph: The loopy star graph.
    """
    G = nx.MultiGraph()

    # Add the central vertex
    G.add_node(0)

    # Add the spoke vertices and connect them to the central vertex
    for i in range(1, n + 1):
        G.add_node(i)
        G.add_edge(0, i)

        # Add the outer loop vertices and connect them to the spoke vertex
        for j in range(k):
            G.add_edge(i, i)
    print(G.edges())
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
    elif src_type == 'double_ngon':
        if args.nodes is None:
            raise ValueError('Nodes parameter must be provided for "double_ngon" type.')
        _ = run(create_double_ngon_graph(args.nodes))
    elif src_type == 'hypercube':
        if args.nodes is None:
            raise ValueError('Nodes parameter must be provided for "hypercube" type.')
        _ = run(nx.hypercube_graph(args.nodes))
    elif src_type == 'loopy_star':
        if args.nodes is None or args.loops is None:
            raise ValueError('Nodes & loops parameters must be provided for "loopy_star" type.')
        _ = run(create_loopy_star(args.nodes, args.loops))
    elif src_type == 'other':
        G = nx.Graph()
        G.add_nodes_from([0, 1, 2, 3, 4, 5, 6, 7, 8])
        G.add_edges_from([(1,4), (1,5), (1,8), (2,4), (2,5), (3,5), (3,6), (4,6), (4,7), (5,8), (6,7), (7,0), (8,0)])
        _ = run(G)

if __name__ == '__main__':
    main()