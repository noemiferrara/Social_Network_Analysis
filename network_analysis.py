import networkx as nx
import pickle

# Carica il grafo dal file salvato
with open("network_bologna.gpickle", "rb") as f:
    G = pickle.load(f)
print("Grafo caricato correttamente.")