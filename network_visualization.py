import networkx as nx
import folium
import matplotlib.pyplot as plt
import pickle

# Carica il grafo dal file salvato
with open("network_bologna.gpickle", "rb") as f:
    G = pickle.load(f)
print("Grafo caricato correttamente.")

"""
Visualizzazione con Folium del grafo con sotto la mappa di Bologna
"""
lat_centro, lon_centro = 44.4949, 11.3426
mappa = folium.Map(location=[lat_centro, lon_centro], zoom_start=13)
for nodo, data in G.nodes(data=True):
    folium.CircleMarker(
        location=[data['latitudine'], data['longitudine']],
        radius=3,
        color='blue',
        fill=True,
        fill_opacity=0.7
    ).add_to(mappa)

for u, v, data in G.edges(data=True):
    lat1, lon1 = G.nodes[u]['latitudine'], G.nodes[u]['longitudine']
    lat2, lon2 = G.nodes[v]['latitudine'], G.nodes[v]['longitudine']
    folium.PolyLine(
        locations=[[lat1, lon1], [lat2, lon2]],
        color='gray',
        weight=1,
        opacity=0.4,
        tooltip=f"Linea: {data['linea']}, Tempo medio: {data['peso']:.1f} min"
    ).add_to(mappa)

mappa.save('network_bus_bologna.html')
print("Visualizzazione network con mappa salvata in network_bus_bologna.html")

# Ricava posizione nodi da lat/lon (x=longitudine, y=latitudine)
pos = {n: (data['longitudine'], data['latitudine']) for n, data in G.nodes(data=True)}

plt.figure(figsize=(13, 13))

# Disegna nodi come punti blu
nx.draw_networkx_nodes(G, pos, node_size=10, node_color='blue', alpha=0.7)

# Disegna gli archi 
nx.draw_networkx_edges(G, pos, edge_color='gray', alpha=0.4, width=1)

plt.title('Network degli Autobus di Bologna')
plt.axis('off')

# Salva l'immagine direttamente su file
plt.savefig('network_bus_bologna.png', dpi=300, bbox_inches='tight')
plt.close()
