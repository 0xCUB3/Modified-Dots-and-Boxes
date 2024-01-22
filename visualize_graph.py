# Creates a visualization of a "specific" graph
import networkx as nx
import matplotlib.pyplot as plt

def visualize_graph(edges, vertices):
    # Initialize a graph object
    G = nx.Graph()

    # Add edges to the graph
    for edge in edges:
        if edges[edge]:  # Only add the edge if it is active (based on boolean value)
            G.add_edge(*edge)

    # Draw the graph
    pos = nx.spring_layout(G)  # positions for all nodes
    nx.draw(G, pos, with_labels=True)
    plt.show()