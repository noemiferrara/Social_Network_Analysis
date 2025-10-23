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

# Carica dati GTFS
stops = pd.read_csv('dataset/gtfs/stops.txt')
trips = pd.read_csv('dataset/gtfs/trips.txt')
stop_times = pd.read_csv('dataset/gtfs/stop_times.txt')

# Carica CSV per controllare zona delle fermate
info = pd.read_csv('dataset/lineefermate.csv', sep=';')

stops['stop_id'] = stops['stop_id'].astype(str)
info['codice_fermata'] = info['codice_fermata'].astype(str)
stop_times['stop_id'] = stop_times['stop_id'].astype(str)

# Filtra solo fermate con codice_zona 500
fermate_bologna_ids = set(info[info['codice_zona'] == 500]['codice_fermata'])

# Filtra il GTFS solo per queste fermate
stops_bologna = stops[stops['stop_id'].isin(fermate_bologna_ids)]

# Controllo corrispondenza fermate 
id_gtfs = set(stops['stop_id'])
id_match = set(stops_bologna['stop_id'])
missing_ids = fermate_bologna_ids - id_match

print(f"Fermate zona 500 definite nel CSV: {len(fermate_bologna_ids)}")
print(f"Fermate trovate anche nel GTFS: {len(id_match)}")
print(f"Fermate zona 500 nel CSV ma ASSENTI nel GTFS: {len(missing_ids)}") 

# Associa a ciascun trip_id (cioè una corsa specifica) il corrispondente route_id (la linea a cui appartiene)
trip2route = dict(zip(trips['trip_id'].astype(str), trips['route_id'].astype(str)))

# Calcolo arco per ogni (nodo1, nodo2, route), pesato con tempo medio
arco_tempi = {}

#Scorri tutti i gruppi di righe in stop_times, raggruppati per trip_id
for trip_id, group in stop_times.groupby('trip_id'):
    stops_ordered = group.sort_values('stop_sequence') #Ordina le fermate secondo la sequenza di fermata (stop_sequence)
    stops_list = stops_ordered['stop_id'].astype(str).tolist()
    arr_times = stops_ordered['arrival_time'].tolist() #Estrae la lista delle fermate e gli orari di arrivo corrispondenti
    route_id = trip2route.get(str(trip_id), None) #Recupera la linea (route_id) associata a questo trip_id
    #Per ogni coppia consecutiva di fermate (n1, n2) nella corsa
    for i in range(len(stops_list) - 1):
        n1, n2 = stops_list[i], stops_list[i+1]
        #Controlla che entrambe le fermate siano nella zona urbana
        if n1 in fermate_bologna_ids and n2 in fermate_bologna_ids and route_id:
            t1 = arr_times[i]
            t2 = arr_times[i+1]
            tempo_min = time_diff_minutes(t1, t2) #calcola il tempo di percorrenza tra le due fermate come differenza tra gli orari di arrivo
            key = (n1, n2, route_id) #Usa la tripla (n1, n2, route_id) come chiave unica per rappresentare un arco diretto su quella linea.
            if key not in arco_tempi:
                arco_tempi[key] = []
            arco_tempi[key].append(tempo_min)

#Calcola la media dei tempi raccolti per ogni arco (fermata-fermata-linea)
arco_medi = {k: sum(v)/len(v) for k, v in arco_tempi.items() if len(v) > 0}

"""
CREAZIONE DEL GRAFO
- I nodi corrispondono alle fermate
- Gli archi indicano il collegamento tra due fermate che viene fatto da una linea 

Gli archi sono PESATI sulla base del tempo di percorrenza tra due fermate consecutive.
Ciascun arco memorizza anche la linea che lo "percorre"

Il grafo è orientato: A→B e B→A sono archi distinti, ognuno con il suo tempo medio.
"""
G = nx.DiGraph()

# Nodi: fermate di Bologna
for _, row in stops_bologna.iterrows():
    G.add_node(row['stop_id'], nome=row['stop_name'], latitudine=row['stop_lat'], longitudine=row['stop_lon'])

# Archi: collegamento tra ciascuna fermata, pesati sulla base del tempo medio necessario per arrivare da una fermata all'altra (consecutive)
for (n1, n2, route_id), tempo_medio in arco_medi.items():
    G.add_edge(n1, n2, linea=route_id, peso=tempo_medio)

print(f"Grafo trasporti autobus Bologna: nodi = {G.number_of_nodes()} , archi = {G.number_of_edges()}")
print("Esempio arco:", list(G.edges(data=True))[:5])

#Salvataggio grafo
nx.write_gexf(G, "network_bologna.gexf")
print("File GEXF salvato come 'network_bologna.gexf'")


with open("network_bologna.gpickle", "wb") as f:
    pickle.dump(G, f)
print("Grafo salvato correttamente in 'network_bologna.gpickle'")
