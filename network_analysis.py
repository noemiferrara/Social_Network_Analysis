import networkx as nx
import pickle
import pandas as pd
import matplotlib.pyplot as plt

# Load the graph
with open("network_bologna.gpickle", "rb") as f:
    G = pickle.load(f)

print("Graph loaded successfully.")
print(f"Nodes: {len(G.nodes())}, Edges: {len(G.edges())}")

# =========================
# BETWEENNESS CENTRALITY 
# which calculates shortest paths based on the weight of the edges
# =========================
# Extracting the largest strongly connected component 
largest_scc = max(nx.strongly_connected_components(G), key=len)
G_scc = G.subgraph(largest_scc).copy()
print(f"Largest strongly connected component: {len(G_scc.nodes())} nodes.")

# Calculating betweenness on the SCC
bc_scc_non_norm = nx.betweenness_centrality(G_scc, k=None, normalized=False, weight='peso')
bc_scc_norm = nx.betweenness_centrality(G_scc, k=None, normalized=True, weight='peso')

df_bc = pd.DataFrame({
    "node": list(G.nodes()),
    "betweenness_scc_non_normalized": [bc_scc_non_norm.get(n, 0) for n in G.nodes()],
    "betweenness_scc_normalized": [bc_scc_norm.get(n, 0) for n in G.nodes()]
})

for col in df_bc.columns[1:]:
    df_bc[col] = df_bc[col].apply(lambda x: int(x) if float(x).is_integer() else x)

df_bc.to_csv("betweenness_centrality_bologna.csv", sep=';', index=False, encoding='utf-8')

print("File saved as 'betweenness_centrality_bologna.csv'")

# =========================
# LOCAL CLUSTERING COEFFICIENT AND REDUNDANCY
# =========================

G_und = G.to_undirected()

# Degree (number of unique neighbors) for each node
degree_dict = dict(G_und.degree())  # d_i

# Local clustering coefficient (NetworkX)
clustering_dict = nx.clustering(G_und)  # C_i

# Redundancy 
results = []
for node, di in degree_dict.items():
    Ci = clustering_dict.get(node, 0.0)
    Ri = Ci * (di - 1) if di > 0 else 0.0
    results.append((node, di, Ci, Ri))

df_results = pd.DataFrame(results, columns=["Node", "Degree", "C_i", "R_i"])

df_results["C_i"] = df_results["C_i"].astype(float).round(6)
df_results["R_i"] = df_results["R_i"].astype(float).round(6)


df_results.to_csv("clustering_redundancy_bologna.csv", sep=';', index=False, encoding='utf-8')
print("File saved as 'clustering_redundancy_bologna.csv'")

avg_clustering = df_results["C_i"].mean()
print(f"\nAverage clustering coefficient: {avg_clustering:.6f}")
avg_redundancy = df_results["R_i"].mean()
print(f"\nAverage redundancy: {avg_redundancy:.6f}")