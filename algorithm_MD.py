from typing import Tuple, List, Dict, Set
import argparse
import time

class Vertex:
    def __init__(self, raw_id: int, neighbors: List[int]) -> None:
        self.raw_id = raw_id
        self.neighbors = neighbors
        self.num_neighbors = len(neighbors)
        self._init_num_loops()
        self.canonical_id: int = -1
        self.category_key: List[int] = None
        self.category: int = -1
        self.prior_category: int = -1

    def _init_num_loops(self) -> None:
        self.num_loops = 0
        for n in self.neighbors:
            if n == self.raw_id:
                self.num_loops += 1

    def add_neighbor(self, neighbor: int) -> None:
        self.neighbors.append(neighbor)
        self.num_neighbors += 1
        if neighbor == self.raw_id:
            self.num_loops += 1

class CanonicalEdges:
    def __init__(self, edges: List[Tuple[int, int]]) -> None:
        self.edges = edges
        self._init_vertices()

    def _init_vertices(self) -> None:
        self.vertices: Dict[int, Vertex] = {}
        for v0, v1 in self.edges:
            if v0 not in self.vertices:
                self.vertices[v0] = Vertex(v0, [v1])
            else:
                self.vertices[v0].add_neighbor(v1)
            if v1 != v0:
                if v1 not in self.vertices:
                    self.vertices[v1] = Vertex(v1, [v0])
                else:
                    self.vertices[v1].add_neighbor(v0)
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

def edges_from_input_file() -> List[Tuple[int, int]]:
    with open('game_input.txt', 'r') as file:
        lines = file.readlines()
    edges: List[Tuple[int, int]] = []
    for line in lines:
        vertices = line.split(',')
        edges.append((int(vertices[0]), int(vertices[1])))
    return edges

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
    return edges

def edges_for_complete_graph(n: int) -> List[Tuple[int, int]]:
    edges: List[Tuple[int, int]] = []
    for i in range(n - 1):
        for j in range(i + 1, n):
            edges.append((i, j))
    return edges

def edges_for_wheel(n: int) -> List[Tuple[int, int]]:
    edges: List[Tuple[int, int]] = []
    for i in range(n - 1):
        edges.append((i, i + 1))
        edges.append((i, n))
    edges.append((n - 1, 0))
    edges.append((n - 1, n))
    return edges

class GameGraph:
    def __init__(self, edges: List[Tuple[int, int]]):
        self.edges = edges
        self.vertices = self._vertices()
        self.num_edges = len(self.edges)
        self.num_vertices = len(self.vertices)
        self._have_set_key = False
        self._have_determined_if_is_tree = False

    def _vertices(self) -> List[int]:
        vertices: Set[int] = set()
        for edge in self.edges:
            vertices.add(edge[0])
            vertices.add(edge[1])
        return list(vertices)

    def contains_vertex(self, vertex: int) -> bool:
        return vertex in self.vertices

    @property
    def key(self) -> str:
        if not self._have_set_key:
            self._key = self._key_for_edges(CanonicalEdges(self.edges).calc())
            self._have_set_key = True
        return self._key

    def _key_for_edges(self, edges: List[Tuple[int, int]]) -> str:
        edge_strs = [f'{e[0]}-{e[1]}' for e in edges]
        return '|'.join(edge_strs)

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
        self._memo_file = 'net_scores.txt'
        self._progress = {
            'top_level': self._initial_graph.num_edges,
            'count': 0,
            'start_time': time.perf_counter()
        }

    def run(self, write_file: bool = False) -> int:
        self._init_memo()
        net_score = self._net_score(self._initial_graph, depth=0)
        if net_score == 0:
            print('Tie game.')
        else:
            winner = 'P1' if net_score > 0 else 'P2'
            print(f'{winner} wins with a net score of {net_score} (P1-P2).')
        if write_file:
            self._write_memo()

    def _init_memo(self) -> None:
        self._memo: Dict[str, int] = {}
        with open(self._memo_file, 'r') as file:
            lines = file.readlines()
        for line in lines:
            items = line.split(',')
            self._memo[items[0]] = int(items[1])

    def _write_memo(self) -> None:
        with open(self._memo_file, 'w') as file:
            for key, value in self._memo.items():
                file.write(f'{key},{value}\n')

    def _net_score(self, graph: GameGraph, depth: int) -> int:
        if graph.key in self._memo:
            return self._memo[graph.key]
        if graph.is_tree:
            self._memo[graph.key] = graph.num_vertices
            return graph.num_vertices
        new_depth = depth + 1
        best_outcome = -1 * graph.num_vertices
        tried_edges = []
        for e in graph.edges:
            if e in tried_edges:
                continue
            tried_edges.append(e)
            new_graph, points = self._cut_edge(graph, e)
            mult = 1 if points > 0 else -1
            outcome = points + mult * self._net_score(new_graph, new_depth)
            if outcome > best_outcome:
                best_outcome = outcome
                if outcome == graph.num_vertices:
                    break
        self._track_progress(depth)
        self._memo[graph.key] = best_outcome
        return best_outcome

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

    def _track_progress(self, depth: int) -> None:
        if depth <= self._progress['top_level']:
            if depth == self._progress['top_level']:
                self._progress['count'] += 1
            else:
                self._progress['top_level'] = depth
                self._progress['count'] = 1
            elapsed_secs = time.perf_counter() - self._progress["start_time"]
            print(
                f'top solved depth:{depth} ' +
                f'count:{self._progress["count"]} '+
                f'seconds:{elapsed_secs:.2f}'
            )

def main():
    parser = argparse.ArgumentParser(
        description='Solve a game.'
    )
    parser.add_argument(
        '--type',
        default='file',
        type=str,
        help='Edge source type name (defaults to "file").'
    )
    parser.add_argument(
        '--params',
        default=[],
        type=int,
        nargs='+',
        help='Any integer(s) needed for edge source type (e.g., m_by_n grid dimensions separated by a space).'
    )
    parser.add_argument(
        '--save_memo',
        action='store_true',
        default=False,
        help='Save the memo for future use (defaults to False).'
    )
    args = parser.parse_args()
    save_memo: bool = args.save_memo
    src_type: str = args.type
    params: List[int] = args.params

    if src_type == 'file':
        edges = edges_from_input_file()
    elif src_type == 'm_by_n':
        edges = edges_for_m_by_n_grid(params[0], params[1])
    elif src_type == 'complete':
        edges = edges_for_complete_graph(params[0])
    elif src_type == 'wheel':
        edges = edges_for_wheel(params[0])
    else:
        raise ValueError(f'Unrecognized edge source type: {src_type}')
    GameRunner(edges).run(save_memo)

if __name__ == '__main__':
    main()