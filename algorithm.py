import argparse
import sys
import time
import igraph as ig
import matplotlib.pyplot as plt
from typing import Tuple, List, Dict

_progress = {'top_level': 1000, 'count': 0, 'start_time': None}

class Vertex:
    def __init__(self, raw_id: int, graph: ig.Graph) -> None:
        self.raw_id = raw_id
        self.neighbors = graph.neighbors(raw_id)
        self.num_neighbors = len(self.neighbors)
        self.num_loops = sum(1 for n in self.neighbors if n == raw_id)
        self.canonical_id: int = -1
        self.category_key: List[int] = None
        self.category: int = -1
        self.prior_category: int = -1

class CanonicalEdges:
    def __init__(self, graph: ig.Graph) -> None:
        self.graph = graph
        self._init_vertices()

    def _init_vertices(self) -> None:
        self.vertices: Dict[int, Vertex] = {node.index: Vertex(node.index, self.graph) for node in self.graph.vs}
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

def run(graph: ig.Graph) -> None:
    global _progress
    memo = {}
    draw_and_save_graph(graph)
    _progress['start_time'] = time.perf_counter()
    
    # Using the CanonicalEdges directly with the graph object now.
    canonical_edge_list = CanonicalEdges(graph).calc()
    net_score = _net_score(graph=graph, depth=0, memo=memo)
    # Calculate each player's score based on the net score
    first_player_score = (graph.vcount() + net_score) // 2
    second_player_score = (graph.vcount() - net_score) // 2
    print_scores(first_player_score, second_player_score)

def print_scores(first_player_score: int, second_player_score: int) -> None:
    if first_player_score > second_player_score:
        print(f'First player wins by {first_player_score - second_player_score} point(s). Score: ({first_player_score} - {second_player_score})')
    elif second_player_score > first_player_score:
        print(f'Second player wins by {second_player_score - first_player_score} point(s). Score: ({first_player_score} - {second_player_score})')
    else:
        print('Tie game!')

def _net_score(graph: ig.Graph, depth: int, memo: dict) -> int:
    # Conversion to canonical edges for memoization
    canonical_edge_list = CanonicalEdges(graph).calc()
    graph_key = str(canonical_edge_list)

    if graph_key in memo:
        return memo[graph_key]

    if graph.is_tree():
        memo[graph_key] = graph.vcount()
        return graph.vcount()

    best_outcome = -1 * graph.vcount()
    tried_edges = []
    for edge in graph.es:
        if edge in tried_edges:
            continue
        tried_edges.append(edge)
        test_graph = graph.copy()
        vertices_to_delete = []

        degrees = test_graph.degree()  # Get degrees of all vertices

        if edge.source != edge.target:  # Non-loop edge
            if degrees[edge.source] == 1 and degrees[edge.target] == 1:
                points = 2
                vertices_to_delete.extend([edge.source, edge.target])
            elif degrees[edge.source] == 1:
                points = 1
                vertices_to_delete.append(edge.source)
            elif degrees[edge.target] == 1:
                points = 1
                vertices_to_delete.append(edge.target)
            else:
                points = 0
        else:  # Loop edge
            if degrees[edge.source] == 2:
                points = 1
                vertices_to_delete.append(edge.source)
            else:
                points = 0

        test_graph.delete_edges(edge)
        if vertices_to_delete:
            test_graph.delete_vertices(vertices_to_delete)

        mult = 1 if points > 0 else -1
        if test_graph.vcount() > 0:
            outcome = points + mult * _net_score(test_graph, depth + 1, memo)
        else:
            outcome = points

        if outcome > best_outcome:
            best_outcome = outcome
            if outcome == graph.vcount():
                break

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

def draw_and_save_graph(graph: ig.Graph) -> None:
    plt.figure(figsize=(10, 8))  # Set the figure size (width, height) in inches.
    ig.plot(graph, target="graph.png", vertex_label=graph.vs.indices, vertex_size=20, vertex_color="skyblue")
    plt.savefig('graph.png')
    plt.close()  # Close the figure to prevent it from being displayed in a window.

def create_friendship_graph(n: int, loop_size: int) -> ig.Graph:
    G = ig.Graph()
    central_vertex = 0
    G.add_vertex(central_vertex)
    
    for loop_index in range(1, n + 1):
        previous_vertex = None
        for vertex_offset in range(loop_size - 1):
            current_vertex = (loop_index - 1) * (loop_size - 1) + vertex_offset + 1
            G.add_vertex(current_vertex)
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

def create_balloon_path_graph(n: int) -> ig.Graph:
    G = ig.Graph()
    for i in range(n - 1):
        G.add_vertex(i)
        G.add_vertex(i + 1)
        G.add_edge(i, i + 1)
    for vertex in G.vs:
        G.add_edge(vertex, vertex)
    return G

def create_balloon_cycle_graph(n: int) -> ig.Graph:
    G = create_balloon_path_graph(n)
    G.add_edge(n - 1, 0)
    return G

def create_balloon_family(a: int, b: int, c: int) -> ig.Graph:
    """
    Create a graph consisting of several "balloon" type connected components.

    Args:
    - a: Number of connected components with 2 vertices connected by an edge, both having self-loops.
    - b: Number of connected components with 3 vertices, connected in a path, each having self-loops.
    - c: Number of connected components with 3 vertices, connected in a path, vertices at the ends having self-loops.
    Returns:
    - G: A NetworkX graph containing the balloon family.
    """
    G = ig.Graph()
    current_node = 0

    # Create components with 2 vertices each having a loop
    for _ in range(a):
        G.add_edge(current_node, current_node + 1)
        G.add_edge(current_node, current_node)  # Self-loop on first vertex
        G.add_edge(current_node + 1, current_node + 1)  # Self-loop on second vertex
        current_node += 2  # Move to the next set of nodes

    # Create components with 3 vertices each having loops
    for _ in range(b):
        G.add_edge(current_node, current_node + 1)
        G.add_edge(current_node + 1, current_node + 2)
        G.add_edge(current_node, current_node)  # Self-loop on first vertex
        G.add_edge(current_node + 1, current_node + 1)  # Self-loop on second vertex
        G.add_edge(current_node + 2, current_node + 2)  # Self-loop on third vertex
        current_node += 3

    # Create components with 3 vertices, only vertices at the ends have loops
    for _ in range(c):
        G.add_edge(current_node, current_node + 1)
        G.add_edge(current_node + 1, current_node + 2)
        G.add_edge(current_node, current_node)  # Self-loop on first vertex
        G.add_edge(current_node + 2, current_node + 2)  # Self-loop on third vertex
        current_node += 3

    return G

def create_double_ngon_graph(n):
    """
    Creates a graph consisting of two n-gons with corresponding vertices connected.
    
    Args:
    - n (int): The number of vertices in each n-gon.
    
    Returns:
    - G (nx.Graph): A NetworkX graph representing the double n-gon structure.
    """
    G = ig.Graph()

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
    parser.add_argument(
        '--balloon_config',
        type=str,
        help='Configuration for balloon families in format "a,b,c" where "a" is number of components with 2 vertices and loops, "b" is with 3 vertices all with loops, "c" is with 3 vertices ends with loops.'
    )
    args = parser.parse_args()
    src_type: str = args.type
    if src_type == 'complete':
        if args.nodes is None:
            raise ValueError('Nodes parameter must be provided for "complete" type.')
        G = ig.Graph.Full(n=args.nodes)
        _ = run(G)
    elif src_type == 'wheel':
        if args.nodes is None:
            raise ValueError('Nodes parameter must be provided for "wheel" type.')
        _ = run(ig.Graph.Wheel(n=args.nodes + 1))
    elif src_type == 'petersen':
        _ = run(ig.Graph.Petersen())
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
    elif args.type == 'balloon_family':
        if args.balloon_config is None:
            raise ValueError('Balloon configuration must be provided for "balloon_family" type.')
        balloon_a, balloon_b, balloon_c = map(int, args.balloon_config.split(','))
        run(create_balloon_family(balloon_a, balloon_b, balloon_c))
    elif args.type == 'hypercube':
        if args.nodes is None:
            raise ValueError('Nodes (dimensions) parameter must be provided for "hypercube" type.')
        graph = ig.Graph.Hypercube(args.nodes)
        run(graph)
    elif args.type == 'double_ngon':
        if args.nodes is None or args.nodes < 3:
            raise ValueError('A valid number of vertices (at least 3) must be provided for "double_ngon" type.')
        graph = create_double_ngon_graph(args.nodes)
        run(graph)
    elif src_type == 'other':
        G = ig.Graph()
        G.add_vertices(9)
        G.add_edges([(1, 4), (1, 5), (1, 8), (2, 4), (2, 5), (3, 5), (3, 6), (4, 6), (4, 7), (5, 8), (6, 7), (7, 0), (8, 0)])
        _ = run(G)


if __name__ == '__main__':
    main()