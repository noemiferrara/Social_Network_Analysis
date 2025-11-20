import pandas as pd
import networkx as nx
import pickle

"""
Function to calculate travel times between two consecutive stops.
stop_times.txt -> contains the arrival and departure times at each stop for each trip (trip_id).
We calculate the travel time between two consecutive stops as the difference between their respective arrival times.
"""
def time_diff_minutes(t1, t2):
    def to_minutes(t):
        h, m, s = [int(x) for x in t.split(':')]
        return h * 60 + m + s / 60
    min1 = to_minutes(t1)
    min2 = to_minutes(t2)
    delta = min2 - min1
    # If delta is negative (e.g. for day transition), add 24h
    if delta < 0:
        delta += 24 * 60
    return delta

# Load GTFS data
stops = pd.read_csv('dataset/gtfs/stops.txt')
trips = pd.read_csv('dataset/gtfs/trips.txt')
stop_times = pd.read_csv('dataset/gtfs/stop_times.txt')

# Load CSV to check the bus stop area
info = pd.read_csv('dataset/lineefermate.csv', sep=';')

stops['stop_id'] = stops['stop_id'].astype(str)
info['codice_fermata'] = info['codice_fermata'].astype(str)
stop_times['stop_id'] = stop_times['stop_id'].astype(str)

# # Filter only stops with codice_zona 500
fermate_bologna_ids = set(info[info['codice_zona'] == 500]['codice_fermata'])

# Filter GTFS for these stops only
stops_bologna = stops[stops['stop_id'].isin(fermate_bologna_ids)]

# Checking the correspondence between stops
id_gtfs = set(stops['stop_id'])
id_match = set(stops_bologna['stop_id'])

# Associate each trip_id (i.e. a specific trip) with the corresponding route_id (the line it belongs to)
trip2route = dict(zip(trips['trip_id'].astype(str), trips['route_id'].astype(str)))

# Edge calculation for each (node1, node2, route), weighted with average time
arco_tempi = {}

#Iterate through all row groups in stop_times, grouped by trip_id
for trip_id, group in stop_times.groupby('trip_id'):
    stops_ordered = group.sort_values('stop_sequence') #Sort stops by stop sequence (stop_sequence)
    stops_list = stops_ordered['stop_id'].astype(str).tolist()
    arr_times = stops_ordered['arrival_time'].tolist() #Extracts the list of stops and corresponding arrival times
    route_id = trip2route.get(str(trip_id), None) #Retrieves the route (route_id) associated with this trip_id
    #For each consecutive pair of stops (n1, n2) in the route
    for i in range(len(stops_list) - 1):
        n1, n2 = stops_list[i], stops_list[i+1]
        #Check that both stops are in the urban zone
        if n1 in fermate_bologna_ids and n2 in fermate_bologna_ids and route_id:
            t1 = arr_times[i]
            t2 = arr_times[i+1]
            tempo_min = time_diff_minutes(t1, t2) #calculates the travel time between the two stops as the difference between the arrival times
            key = (n1, n2, route_id) #Use the triple (n1, n2, route_id) as a unique key to represent a directed edge on that line.
            if key not in arco_tempi:
                arco_tempi[key] = []
            arco_tempi[key].append(tempo_min)

#Calculate the average of the times collected for each edge (stop-stop-route)
arco_medi = {k: sum(v)/len(v) for k, v in arco_tempi.items() if len(v) > 0}

"""
GRAPH CREATION
- Nodes correspond to stops
- Edges indicate the connection between two stops, which is made by a line.

Edges are WEIGHTED based on the travel time between two consecutive stops.
Each edge also stores the line that "travels" through it.

The graph is directed: A→B and B→A are distinct edges, each with its own average travel time.
"""
G = nx.DiGraph()

# Nodes: Bologna's stops
for _, row in stops_bologna.iterrows():
    G.add_node(row['stop_id'], nome=row['stop_name'], latitudine=row['stop_lat'], longitudine=row['stop_lon'])

# Edges: connection between each stop, weighted based on the average time needed to get from one stop to another (consecutive)
for (n1, n2, route_id), tempo_medio in arco_medi.items():
    G.add_edge(n1, n2, linea=route_id, peso=tempo_medio)

print(f"Bologna bus transport graph: nodes = {G.number_of_nodes()} , edges = {G.number_of_edges()}")
print("Example of edge:", list(G.edges(data=True))[:5])

#Salvataggio grafo
nx.write_gexf(G, "network_bologna.gexf")
print("GEXF file saved as 'network_bologna.gexf'")


with open("network_bologna.gpickle", "wb") as f:
    pickle.dump(G, f)
print("Graph successfully saved as 'network_bologna.gpickle'")
