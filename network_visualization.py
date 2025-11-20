import folium
import pickle

# Load the graph from the saved file
with open("network_bologna.gpickle", "rb") as f:
    G = pickle.load(f)
print("Graph loaded successfully.")

"""
The graph is displayed using Folium over the map of Bologna below. 
Hovering over an edge reveals the Route and Average time (weight), 
while clicking on a node displays the stop id and name.
"""

lat_centro, lon_centro = 44.4949, 11.3426

map = folium.Map(location=[lat_centro, lon_centro], zoom_start=13, tiles=None)

folium.TileLayer(
    tiles='OpenStreetMap',
    name='OSM con opacità',
    opacity=0.7 
).add_to(map)


for u, v, data in G.edges(data=True):
    lat1, lon1 = G.nodes[u]['latitudine'], G.nodes[u]['longitudine']
    lat2, lon2 = G.nodes[v]['latitudine'], G.nodes[v]['longitudine']

    folium.PolyLine(
        locations=[[lat1, lon1], [lat2, lon2]],
        color='blue',
        weight=1.5,
        tooltip=f"Route: {data['linea']}, Average time: {data['peso']:.1f} min"
    ).add_to(map)

for nodo, data in G.nodes(data=True):
    nome = str(data.get('nome', 'N/A'))
    codice = str(nodo)
    popup_text = f"ID: {codice}<br>Name: {nome}"
    
    folium.CircleMarker(
        location=[data['latitudine'], data['longitudine']],
        radius=1,
        color='red',
        fill=True,
        fill_opacity=0.7,
        popup=folium.Popup(popup_text, max_width=300)
    ).add_to(map)


map.save('network_bus_bologna.html')
print("Network visualization saved as network_bus_bologna.html.")

