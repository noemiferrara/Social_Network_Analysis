import pandas as pd
import networkx as nx
import pickle

"""
Funzione per calcolare tempi di percorrenza tra due fermate consecutive.
stop_times.txt -> contiene per ogni corsa (trip_id) l'orario di arrivo e partenza a ciascuna fermata. 
Calcoliamo il tempo di percorrenza tra due fermate consecutive come differenza tra i rispettivi orari di arrivo.
"""
def time_diff_minutes(t1, t2):
    def to_minutes(t):
        h, m, s = [int(x) for x in t.split(':')]
        return h * 60 + m + s / 60
    min1 = to_minutes(t1)
    min2 = to_minutes(t2)
    delta = min2 - min1
    # Se delta negativo (ad esempio per passaggio giorno), somma 24h
    if delta < 0:
        delta += 24 * 60
    return delta


# ==========================
# 1. CARICAMENTO DEI DATI
# ==========================

stops = pd.read_csv('dataset/gtfs/stops.txt')
trips = pd.read_csv('dataset/gtfs/trips.txt')
stop_times = pd.read_csv('dataset/gtfs/stop_times.txt')
info = pd.read_csv('dataset/lineefermate.csv', sep=';')

stops['stop_id'] = stops['stop_id'].astype(str)
info['codice_fermata'] = info['codice_fermata'].astype(str)
stop_times['stop_id'] = stop_times['stop_id'].astype(str)

# Filtra solo fermate con codice_zona 500 (area urbana Bologna)
fermate_bologna_ids = set(info[info['codice_zona'] == 500]['codice_fermata'])

# Filtra il GTFS solo per queste fermate
stops_bologna = stops[stops['stop_id'].isin(fermate_bologna_ids)]

# Controlla corrispondenze
id_gtfs = set(stops['stop_id'])
id_match = set(stops_bologna['stop_id'])
missing_ids = fermate_bologna_ids - id_match

print(f"Fermate zona 500 definite nel CSV: {len(fermate_bologna_ids)}")
print(f"Fermate trovate anche nel GTFS: {len(id_match)}")
print(f"Fermate zona 500 nel CSV ma ASSENTI nel GTFS: {len(missing_ids)}")


# ==========================
# 2. COSTRUZIONE ARCHI CON TEMPI MEDI
# ==========================

# Associa ogni trip_id alla route_id (linea)
trip2route = dict(zip(trips['trip_id'].astype(str), trips['route_id'].astype(str)))

arco_tempi = {}

# Calcolo tempi medi tra fermate consecutive per ogni corsa
for trip_id, group in stop_times.groupby('trip_id'):
    stops_ordered = group.sort_values('stop_sequence')
    stops_list = stops_ordered['stop_id'].astype(str).tolist()
    arr_times = stops_ordered['arrival_time'].tolist()
    route_id = trip2route.get(str(trip_id), None)

    for i in range(len(stops_list) - 1):
        n1, n2 = stops_list[i], stops_list[i+1]
        if n1 in fermate_bologna_ids and n2 in fermate_bologna_ids and route_id:
            t1 = arr_times[i]
            t2 = arr_times[i+1]
            tempo_min = time_diff_minutes(t1, t2)
            key = (n1, n2, route_id)
            if key not in arco_tempi:
                arco_tempi[key] = []
            arco_tempi[key].append(tempo_min)

# Calcola tempo medio per ciascun arco
arco_medi = {k: sum(v)/len(v) for k, v in arco_tempi.items() if len(v) > 0}


# ==========================
# 3. CREAZIONE DEL GRAFO
# ==========================

G = nx.DiGraph()

# Nodi = fermate
for _, row in stops_bologna.iterrows():
    G.add_node(
        row['stop_id'],
        nome=row['stop_name'],
        latitudine=row['stop_lat'],
        longitudine=row['stop_lon']
    )

# Archi = collegamenti tra fermate consecutive
for (n1, n2, route_id), tempo_medio in arco_medi.items():
    G.add_edge(n1, n2, linea=route_id, peso=tempo_medio)

print(f"Grafo iniziale: nodi = {G.number_of_nodes()} , archi = {G.number_of_edges()}")


# ==========================
# 4. UNIONE "STAZIONE CENTRALE"
# ==========================
# ==========================
# CONTROLLO ARCHI TRA FERMATE CON LO STESSO NOME ("STAZIONE CENTRALE")
# ==========================

# Trova tutte le fermate che si chiamano "STAZIONE CENTRALE"
centrali = [n for n, d in G.nodes(data=True)
            if d.get('nome', '').strip().upper() == "STAZIONE CENTRALE"]

if len(centrali) > 1:
    archi_centrali = []
    for u, v, data in G.edges(data=True):
        if u in centrali and v in centrali and u != v:
            archi_centrali.append((u, v, data))

    if archi_centrali:
        print("\n⚠️  ATTENZIONE: trovati archi tra due fermate 'STAZIONE CENTRALE' diverse:")
        for u, v, data in archi_centrali:
            print(f" - {u} → {v} | linea {data.get('linea')} | peso {data.get('peso'):.2f} min")
    else:
        print("\n✅ Nessun arco diretto collega due fermate 'STAZIONE CENTRALE'.")
else:
    print("\nSolo una fermata 'STAZIONE CENTRALE' trovata, nessun controllo necessario.")


# Trova tutte le fermate con nome "STAZIONE CENTRALE"
stazioni_centrali = [n for n, d in G.nodes(data=True)
                     if d.get('nome', '').strip().upper() == "STAZIONE CENTRALE"]

print(f"Fermate trovate con nome 'STAZIONE CENTRALE': {stazioni_centrali}")

if len(stazioni_centrali) > 1:
    nodo_unificato = "STAZIONE_CENTRALE_AGGREGATA"

    # Crea nuovo nodo con coordinate medie
    lat_media = sum(G.nodes[n]['latitudine'] for n in stazioni_centrali) / len(stazioni_centrali)
    lon_media = sum(G.nodes[n]['longitudine'] for n in stazioni_centrali) / len(stazioni_centrali)
    G.add_node(nodo_unificato, nome="STAZIONE CENTRALE", latitudine=lat_media, longitudine=lon_media)

    # Sposta tutti gli archi entranti e uscenti
    for n in stazioni_centrali:
        # Archi uscenti
        for _, target, data in list(G.out_edges(n, data=True)):
            if target != nodo_unificato:
                G.add_edge(nodo_unificato, target, **data)
        # Archi entranti
        for source, _, data in list(G.in_edges(n, data=True)):
            if source != nodo_unificato:
                G.add_edge(source, nodo_unificato, **data)
        # Rimuove nodo originale
        G.remove_node(n)

    # Rimozione archi duplicati identici (stesso u,v,linea)
    edges_seen = set()
    edges_to_remove = []
    for u, v, data in G.edges(data=True):
        key = (u, v, data.get('linea'))
        if key in edges_seen:
            edges_to_remove.append((u, v))
        else:
            edges_seen.add(key)
    G.remove_edges_from(edges_to_remove)

    print(f"Nodi 'STAZIONE CENTRALE' uniti in '{nodo_unificato}'.")
    print(f"Rimossi {len(edges_to_remove)} archi duplicati dopo l’unione.")
else:
    print("Solo una fermata 'STAZIONE CENTRALE' trovata, nessuna unione necessaria.")


# ==========================
# 5. SALVATAGGIO GRAFO
# ==========================

print(f"Grafo finale: nodi = {G.number_of_nodes()} , archi = {G.number_of_edges()}")
print("Esempio arco:", list(G.edges(data=True))[:5])

nx.write_gexf(G, "network_stazione_uniti.gexf")
print("File GEXF salvato come 'network_stazione_uniti.gexf'")

with open("network_stazione_uniti.gpickle", "wb") as f:
    pickle.dump(G, f)
print("Grafo salvato correttamente in 'network_stazione_uniti.gpickle'")
