import networkx as nx
from itertools import combinations

class Graph:
    def __init__(self):
        self.graph= nx.Graph()
        
    def add_edge(self, source, target):
        if self.graph.has_edge(source, target):
            # Si la conexión ya existe, aumentamos el "peso" (frecuencia)
            self.graph[source][target]["weight"] += 1
        else:
            # Si es nueva, creamos la arista con peso 1
            self.graph.add_edge(source, target, weight=1)
            
    def build_relations(self, entity_names):
        pairs = combinations(entity_names, 2)
        
        for source, target in pairs:
            self.add_edge(source, target)
    
    def build_graph(self, parsed_entities):
        for item in parsed_entities:
            if "entities" in item:
                entity_names = [e["entity"].lower().strip() for e in item["entities"]]
                entity_names = list(set(entity_names))

                # Si hay menos de 2 entidades, no podemos hacer una conexión
                if len(entity_names) < 2:
                    continue
                
                self.build_relations(entity_names)
                
    def run(self, parsed_entities):
        self.build_graph(parsed_entities)
            
            
    