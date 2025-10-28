import pandas as pd
import networkx as nx
import pickle

def time_diff_minutes(t1, t2):
    def to_minutes(t):
        h, m, s = [int(x) for x in t.split(':')]
        return h * 60 + m + s / 60
    min1 = to_minutes(t1)
    min2 = to_minutes(t2)
    delta = min2 - min1
    if delta < 0:
        delta += 24 * 60
    return delta

# Carica dati GTFS
stops = pd.read_csv('dataset/gtfs/stops.txt')
trips = pd.read_csv('dataset/gtfs/trips.txt')
stop_times = pd.read_csv('dataset/gtfs/stop_times.txt')

# Carica info su zona urbana
info = pd.read_csv('dataset/lineefermate.csv', sep=';')

# Assicurati che i tipi siano stringhe
stops['stop_id'] = stops['stop_id'].astype(str)
info['codice_fermata'] = info['codice_fermata'].astype(str)
stop_times['stop_id'] = stop_times['stop_id'].astype(str)

# Filtra solo fermate della zona urbana (es: codice_zona 500)
fermate_bologna_ids = set(info[info['codice_zona'] == 500]['codice_fermata'])
stops_bologna = stops[stops['stop_id'].isin(fermate_bologna_ids)]

# Mappa stop_id → stop_name per le fermate urbane
id2name = {row['stop_id']: row['stop_name'] for _, row in stops_bologna.iterrows()}

# Associa trip_id (corsa) a route_id (linea)
trip2route = dict(zip(trips['trip_id'].astype(str), trips['route_id'].astype(str)))

# Calcola tempi di percorrenza tra fermate consecutive (archi tra stop_id)
arco_tempi = {}
for trip_id, group in stop_times.groupby('trip_id'):
    stops_ordered = group.sort_values('stop_sequence')
    stops_list = stops_ordered['stop_id'].astype(str).tolist()
    arr_times = stops_ordered['arrival_time'].tolist()
    route_id = trip2route.get(str(trip_id), None)
    for i in range(len(stops_list) - 1):
        n1, n2 = stops_list[i], stops_list[i+1]
        if n1 in fermate_bologna_ids and n2 in fermate_bologna_ids and route_id:
            t1, t2 = arr_times[i], arr_times[i+1]
            tempo_min = time_diff_minutes(t1, t2)
            key = (n1, n2, route_id)
            if key not in arco_tempi:
                arco_tempi[key] = []
            arco_tempi[key].append(tempo_min)

# Aggrega le fermate con lo stesso nome per creare i super-nodi
arco_tempi_nomi = {}
for (n1, n2, route_id), tempi in arco_tempi.items():
    nome1 = id2name.get(n1)
    nome2 = id2name.get(n2)
    if nome1 and nome2 and route_id:
        key = (nome1, nome2, route_id)
        if key not in arco_tempi_nomi:
            arco_tempi_nomi[key] = []
        arco_tempi_nomi[key].extend(tempi)

arco_medi_nomi = {k: sum(v)/len(v) for k, v in arco_tempi_nomi.items() if len(v) > 0}

# Scegli una posizione rappresentativa per ogni nodo (primo stop_id trovato per ogni nome)
nome2latlon = {}
for nome, group in stops_bologna.groupby('stop_name'):
    row = group.iloc[0]
    nome2latlon[nome] = (row['stop_lat'], row['stop_lon'])

# Crea il nuovo grafo orientato e pesato sui super-nodi
G_nome = nx.DiGraph()

# Aggiungi nodi
for nome, (lat, lon) in nome2latlon.items():
    G_nome.add_node(nome, latitudine=lat, longitudine=lon)

# Aggiungi archi
for (nome1, nome2, route_id), tempo_medio in arco_medi_nomi.items():
    G_nome.add_edge(nome1, nome2, linea=route_id, peso=tempo_medio)

print(f"Grafo aggregato: nodi = {G_nome.number_of_nodes()} , archi = {G_nome.number_of_edges()}")
print("Esempio arco:", list(G_nome.edges(data=True))[:5])

# Salva i file
nx.write_gexf(G_nome, "network_nodi_uniti.gexf")
print("File GEXF salvato come 'network_nodi_uniti.gexf'")

with open("network_nodi_uniti.gpickle", "wb") as f:
    pickle.dump(G_nome, f)
print("Grafo aggregato salvato correttamente in 'network_nodi_uniti.gpickle'")
