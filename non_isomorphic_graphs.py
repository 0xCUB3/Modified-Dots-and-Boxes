import networkx as nx
from itertools import combinations
from concurrent.futures import ProcessPoolExecutor, as_completed

def generate_subgraph(graph, edges_to_remove):
    """
    Generate a subgraph by removing `edges_to_remove` edges from the original graph.
    """
    subgraph = graph.copy()
    subgraph.remove_edges_from(edges_to_remove)
    return subgraph, edges_to_remove

def generate_subgraphs(graph, num_edges_to_remove):
    """
    Generate all possible subgraphs by removing `num_edges_to_remove` edges from the original graph.
    """
    edges = list(graph.edges())
    edges_combinations = list(combinations(edges, num_edges_to_remove))
    
    subgraphs = []
    with ProcessPoolExecutor() as executor:
        futures = {executor.submit(generate_subgraph, graph, comb): comb for comb in edges_combinations}
        for future in as_completed(futures):
            subgraphs.append(future.result())
    
    return subgraphs

def is_isomorphic_to_any(subgraph, graph_list):
    """
    Check if `subgraph` is isomorphic to any graph in `graph_list`.
    """
    for unique_graph in graph_list:
        if nx.is_isomorphic(subgraph, unique_graph):
            return True
    return False

def count_non_isomorphic_graphs(subgraphs):
    """
    Count the number of non-isomorphic graphs in the list of subgraphs.
    """
    non_isomorphic_graphs = []
    unique_sequences = []
    
    for subgraph, edges_to_remove in subgraphs:
        if not is_isomorphic_to_any(subgraph, [g for g, _ in non_isomorphic_graphs]):
            non_isomorphic_graphs.append((subgraph, edges_to_remove))
            unique_sequences.append(edges_to_remove)
    
    return len(non_isomorphic_graphs), unique_sequences

def main():
    # Example graph: complete graph with 4 nodes
    original_graph = nx.complete_graph(11)
    original_graph.remove_edge(0,1)
    original_graph.remove_edge(2,3)
    original_graph.remove_edge(4,5)
    original_graph.remove_edge(3,4)
    original_graph.remove_edge(5,6)
    
    # Number of edges to remove
    num_edges_to_remove = 2
    
    # Generate all possible subgraphs by removing num_edges_to_remove edges
    subgraphs = generate_subgraphs(original_graph, num_edges_to_remove)
    
    # Count the number of non-isomorphic subgraphs and get the unique sequences
    num_non_isomorphic_graphs, unique_sequences = count_non_isomorphic_graphs(subgraphs)
    
    print(f"Number of non-isomorphic graphs after removing {num_edges_to_remove} edges: {num_non_isomorphic_graphs}")
    print("Unique edge removal sequences resulting in non-isomorphic graphs:")
    for sequence in unique_sequences:
        print(sequence)

if __name__ == "__main__":
    main()