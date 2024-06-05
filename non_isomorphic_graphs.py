import networkx as nx
from networkx.algorithms import weisfeiler_lehman_graph_hash
from itertools import combinations

def generate_subgraphs_optimized(n, k):
    if k == 0:
        return [nx.complete_graph(n)]
    if k >= n * (n - 1) // 2:
        return [nx.Graph()]

    G = nx.complete_graph(n)
    initial_edges_removed = [(0, 1)]  # Store initially removed edge

    unique_subgraphs = []

    if k > 0:
        # Case 1: Second edge adjacent to the first
        G1 = G.copy()
        G1.remove_edge(1, 2)
        unique_subgraphs.extend(generate_subgraphs_recursive(G1, k - 1, initial_edges_removed + [(1, 2)]))

        # Case 2: Second edge not adjacent to the first
        G2 = G.copy()
        G2.remove_edge(2, 3) 
        unique_subgraphs.extend(generate_subgraphs_recursive(G2, k - 1, initial_edges_removed + [(2, 3)]))
    else:
        unique_subgraphs.append((G, initial_edges_removed)) # Return graph and removed edges

    return get_non_isomorphic_graphs(unique_subgraphs)

def generate_subgraphs_recursive(G, k, removed_edges):
    unique_subgraphs = {}
    edges_to_remove = list(combinations(G.edges(), k))

    for edges in edges_to_remove:
        subgraph = G.copy()
        subgraph.remove_edges_from(edges)
        wl_hash = weisfeiler_lehman_graph_hash(subgraph)

        if wl_hash not in unique_subgraphs:
            unique_subgraphs[wl_hash] = (subgraph, removed_edges + list(edges)) 

    return list(unique_subgraphs.values())

def get_non_isomorphic_graphs(graphs):
    non_isomorphic = []
    hashes = set()
    for graph, removed_edges in graphs:
        h = weisfeiler_lehman_graph_hash(graph)
        if h not in hashes:
            non_isomorphic.append((graph, removed_edges))
            hashes.add(h)
    return non_isomorphic

# Test the program
n = 11  
k = 6

unique_subgraphs = generate_subgraphs_optimized(n, k)

print(f"Unique non-isomorphic subgraphs of K_{n} with {k} edges removed:\n")
for i, (subgraph, removed_edges) in enumerate(unique_subgraphs):
    print(f"Subgraph {i + 1}:")
    print("   Removed Edges:", removed_edges)
    print("   Edge List:", subgraph.edges())
    print("-" * 20)