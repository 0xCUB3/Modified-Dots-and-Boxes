from typing import Tuple, List, Dict, Set
import argparse

class Vertex:
    def __init__(self, raw_id: int, neighbors: List[int]) -> None:
        self.raw_id = raw_id
        self.neighbors = neighbors
        self.num_neighbors = len(neighbors)
        self.canonical_id: int = -1
        self.category_key: List[int] = None
        self.category: int = -1

    def add_neighbor(self, neighbor: int) -> None:
        self.neighbors.append(neighbor)
        self.num_neighbors += 1

class CanonicalEdges:
    def __init__(self, edges: List[Tuple[int, int]]) -> None:
        self.edges = edges
        self._init_vertices()
    
    def _init_vertices(self) -> None:
        self.vertices: Dict[int, Vertex] = {}
        for edge in self.edges:
            if edge[0] not in self.vertices:
                self.vertices[edge[0]] = Vertex(edge[0], [edge[1]])
            else:
                self.vertices[edge[0]].add_neighbor(edge[1])
            if edge[1] not in self.vertices:
                self.vertices[edge[1]] = Vertex(edge[1], [edge[0]])
            else:
                self.vertices[edge[1]].add_neighbor(edge[0])

    def calc(self) -> List[Tuple[int, int]]:
        self._categorize_vertices_by_connections()
        self._break_ties_to_finalize_canonical_ids()

    def _categorize_vertices_by_connections(self) -> None:
        self._init_category_keys()
        self._num_categories = len(self._category_keys)
        self._num_vertices = len(self.vertices)
        self._iterations = 0
        while not self._iteration_is_done():
            self._iterations += 1

    def _init_category_keys(self) -> None:
        self._category_keys = list(
            set([[v.num_neighbors] for v in self.vertices.values()])
        )
    
    def _iteration_is_done(self) -> bool:
        return (
            (self._num_categories == 1)
            or (self._num_categories == self._num_vertices)
            or (self._iterations >= self._num_vertices)
        )
    def _break_ties_to_finalize_canonical_ids(self) -> None:
        pass

def canonical_edges(edges: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    return sorted([tuple(sorted(e)) for e in edges])

class GameGraph:
    def __init__(self, edges: List[Tuple[int, int]]):
        self.edges = edges
        self.key = self._key()
        self.vertices = self._vertices()
        self.num_edges = len(self.edges)
        self.num_vertices = len(self.vertices)
        self._have_determined_if_is_tree = False
    
    def _key(self) -> str:
        return self._key_for_edges(self.edges)

    def _key_for_edges(self, edges: List[Tuple[int, int]]) -> str:
        edge_strs = [f'{e[0]}-{e[1]}' for e in edges]
        return ','.join(edge_strs)

    def _vertices(self) -> List[int]:
        vertices: Set[int] = set()
        for edge in self.edges:
            vertices.add(edge[0])
            vertices.add(edge[1])
        return list(vertices)

    def contains_vertex(self, vertex: int) -> bool:
        return vertex in self.vertices

    @property
    def is_tree(self) -> bool:
        if not self._have_determined_if_is_tree:
            if self.num_edges > self.num_vertices:
                self._is_tree = False
            elif self.num_edges == 1:
                self._is_tree = True
            else:
                self._iteratively_pare_tree()
                self._is_tree = len(self._tree_edges) == 0
            self._have_determined_if_is_tree = True
        return self._is_tree

    def _iteratively_pare_tree(self) -> None:
        self._initialize_tree_attributes()
        while len(self._tree_ends) > 0:
            self._remove_ends_from_tree()
    
    def _initialize_tree_attributes(self) -> None:
        self._tree_edges = self.edges.copy()
        self._num_edges_for_tree_vertex = {v: 0 for v in self.vertices}
        for e in self._tree_edges:
            self._num_edges_for_tree_vertex[e[0]] += 1
            if e[1] != e[0]:
                self._num_edges_for_tree_vertex[e[1]] += 1
        self._update_tree_ends()
    
    def _update_tree_ends(self) -> None:
        self._tree_ends = [
            v for v, num in self._num_edges_for_tree_vertex.items() if num == 1
        ]

    def _remove_ends_from_tree(self) -> None:
        for e in self._tree_edges.copy():
            if (e[0] in self._tree_ends) or (e[1] in self._tree_ends):
                self._decrement_num_edges_for_tree_vertex(e[0])
                if e[1] != e[0]:
                    self._decrement_num_edges_for_tree_vertex(e[1])
                self._tree_edges.remove(e)
        self._update_tree_ends()
    
    def _decrement_num_edges_for_tree_vertex(self, vertex: int) -> None:
        self._num_edges_for_tree_vertex[vertex] -= 1
        if self._num_edges_for_tree_vertex[vertex] == 0:
            del self._num_edges_for_tree_vertex[vertex]

class GameRunner:
    def __init__(self, edges: List[Tuple[int, int]]):
        self.edges = sorted(edges)
        self._initial_graph = GameGraph(self.edges)
        self._memo: Dict[str, int] = {}

    def run(self) -> None:
        net_score, sequence = self._net_score(self._initial_graph, depth=0, moves=[])
        # Calculate each player's score based on the net score
        first_player_score = (self._initial_graph.num_vertices + net_score) // 2
        second_player_score = (self._initial_graph.num_vertices - net_score) // 2
        self.print_scores(first_player_score, second_player_score)
        print(f"Winning Moves Sequence: {sequence}")
    
    def print_scores(self, first_player_score: int, second_player_score: int) -> None:
        if first_player_score > second_player_score:
            print(f'First player wins by {first_player_score - second_player_score} point(s). Score: ({first_player_score} - {second_player_score})')
        elif second_player_score > first_player_score:
            print(f'Second player wins by {second_player_score - first_player_score} point(s). Score: ({first_player_score} - {second_player_score})')
        else:
            print('Tie game!')

    def _net_score(self, graph: GameGraph, depth: int, moves: List[Tuple[int, int]]) -> Tuple[int, List[Tuple[int, int]]]:
        if graph.key in self._memo:
            return self._memo[graph.key]
        
        if graph.is_tree:
            # Edge case for trees where the sequence of moves leading to realizing it's a tree is relevant.
            self._memo[graph.key] = (graph.num_vertices, moves)
            return graph.num_vertices, moves
        
        best_outcome = -graph.num_vertices  # Initialize with the worst possible score
        best_sequence = moves  # Start with the current sequence
        
        for e in graph.edges:
            # Each edge considered for cutting creates a new branch of exploration with its own sequence.
            new_moves = moves + [e]
            new_graph, points = self._cut_edge(graph, e)
            mult = 1 if points > 0 else -1
            outcome, sequence_for_outcome = self._net_score(new_graph, depth + 1, new_moves)
            outcome = points + mult * outcome

            if (best_sequence is moves or outcome > best_outcome):  
                # Found a new best outcome, update the best outcome and its sequence.
                best_outcome = outcome
                best_sequence = sequence_for_outcome
        
        # Before returning, ensure this best outcome and its sequence is memoized to avoid re-computation.
        self._memo[graph.key] = (best_outcome, best_sequence)
        return best_outcome, best_sequence

    def _cut_edge(self,
        graph: GameGraph, edge: Tuple[int, int]
    ) -> Tuple[GameGraph, int]:
        new_edges = graph.edges.copy()
        new_edges.remove(edge)
        new_graph = GameGraph(new_edges)
        points = 0
        if not new_graph.contains_vertex(edge[0]):
            points += 1
        if edge[1] != edge[0]:
            if not new_graph.contains_vertex(edge[1]):
                points += 1
        return (new_graph, points)

# Hanging tree with n loops and one spoke extended by m vertices
def edges_for_hanging_tree_with_loops(spokes: int, loops: int) -> List[Tuple[int, int]]:
    edges: List[Tuple[int, int]] = []
    max_vertex_id = 0
    # 0 is the root vertex
    for spoke in range(1, spokes + 1):
        # Connect each spoke to the root
        edges.append((0, spoke))
        # Determine the current max vertex id
        max_vertex_id = max(max_vertex_id, spoke)
        # Create loops at each outer vertex
        for _ in range(loops):
            edges.append((spoke, spoke))

    return canonical_edges(edges)

def edges_for_complete_graph(n: int) -> List[Tuple[int, int]]:
    edges: List[Tuple[int, int]] = []
    for i in range(n - 1):
        for j in range(i + 1, n):
            edges.append((i, j))
    return canonical_edges(edges)

def edges_for_wheel_graph(spokes: int) -> List[Tuple[int, int]]:
    if spokes < 3:
        raise ValueError('Wheel graph must have at least 3 spokes.')

    # The hub of the wheel is vertex 0, and the outer vertices are 1 through spokes.
    edges: List[Tuple[int, int]] = []
    for spoke in range(1, spokes + 1):
        # Connect the hub to each spoke.
        edges.append((0, spoke))
        # Connect each outer vertex to the next, forming a cycle.
        next_spoke = spoke + 1 if spoke < spokes else 1
        edges.append((spoke, next_spoke))

    return canonical_edges(edges)

def edges_for_cycle_graph_with_loops(n: int, loops: int) -> List[Tuple[int, int]]:
    edges: List[Tuple[int, int]] = []
    for i in range(n):
        edges.append((i, (i + 1) % n))
        for _ in range(loops):
            edges.append((i, i))
    return canonical_edges(edges)

def edges_from_input_file() -> List[Tuple[int, int]]:
    with open('game_input.txt', 'r') as file:
        lines = file.readlines()
    edges = [
        (int(line.split(',')[0]), int(line.split(',')[1])) for line in lines
    ]
    return canonical_edges(edges)

def edges_for_m_by_n_grid(m: int, n: int) -> List[Tuple[int, int]]:
    edges: List[Tuple[int, int]] = []
    for i in range(m):
        for j in range(n):
            vertex = i * n + j
            if i == 0:
                edges.append((vertex, vertex))
            if i == m - 1:
                edges.append((vertex, vertex))
            else:
                edges.append((vertex, vertex + n))
            if j == 0:
                edges.append((vertex, vertex))                    
            if j == n - 1:
                edges.append((vertex, vertex))
            else:
                edges.append((vertex, vertex + 1))
    return canonical_edges(edges)

def main():
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
        '--spokes',
        type=int,
        help='Number of spokes for a wheel graph.'
    )
    parser.add_argument(
        '--loops',
        type=int,
        help='Number of loops for a hanging tree graph.'
    )
    
    args = parser.parse_args()
    src_type: str = args.type

    if src_type == 'hanging_tree':
        if args.spokes is None or args.loops is None:
            raise ValueError('Spokes and loops parameters must be provided for "hanging_tree" type.')
        edges = edges_for_hanging_tree_with_loops(args.spokes, args.loops)
    elif src_type == 'complete':
        if args.nodes is None:
            raise ValueError('Nodes parameter must be provided for "complete" type.')
        edges = edges_for_complete_graph(args.nodes)
    elif src_type == 'wheel':
        if args.spokes is None:
            raise ValueError('Spokes parameter must be provided for "wheel" type.')
        edges = edges_for_wheel_graph(args.spokes)
    elif src_type == 'cycle_with_loops':
        if args.nodes is None or args.loops is None:
            raise ValueError('Nodes and loops parameters must be provided for "cycle_with_loops" type.')
        edges = edges_for_cycle_graph_with_loops(args.nodes, args.loops)
    
    GameRunner(edges).run()
if __name__ == '__main__':
    main()