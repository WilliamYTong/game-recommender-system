import networkx as nx
import matplotlib.pyplot as plt
from GameRecommendationAlgorithm_Prep import buildFullTopkGraph, users, user_lookup, condenseGraph, getSCCs

#I get help from AI for the graphic drawing
def draw_graph(graph, user_lookup):
    G = nx.DiGraph()
    for user_id in graph:
        G.add_node(user_lookup[user_id].name)
    for user_id, neighbors in graph.items():
        for neighbor_id, sim in neighbors.items():
            G.add_edge(
                user_lookup[user_id].name,
                user_lookup[neighbor_id].name,
                weight=round(sim, 2)
            )
    pos = nx.spring_layout(G,scale = 2)
    edge_labels = nx.get_edge_attributes(G, "weight")
    plt.figure(figsize=(7, 5))
    nx.draw(G, pos,
            with_labels   = True,
            node_color    = "skyblue",
            node_size     = 600,
            font_size     = 9,
            arrows        = True,
            edge_color    = "gray")
    plt.title("User Similarity Graph")
    plt.show()

def draw_scc_graph(graph):
    G = nx.DiGraph()
    for node in graph:
        G.add_node(f"SCC {node}")
    for u, neighbors in graph.items():
        for v in neighbors:
            G.add_edge(f"SCC {u}", f"SCC {v}")
    pos = nx.spring_layout(G, seed=1)
    plt.figure(figsize=(7,5))
    nx.draw(G, pos,
            with_labels=True,
            node_color="skyblue",
            node_size=800,
            arrows=True)
    plt.title("Condensed SCC Graph")
    plt.show()

result_graph = buildFullTopkGraph(users, 3)
sccs = getSCCs(result_graph)
scc_graph,scc_map = condenseGraph(result_graph,sccs)
draw_graph(result_graph,user_lookup)
draw_scc_graph(scc_graph)