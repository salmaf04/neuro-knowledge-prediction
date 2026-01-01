import networkx as nx
import sys
import os

# Ensure src module is visible
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.validation import GraphValidator

def create_mock_graph():
    """
    Creates a mock graph for demonstration if the real graph isn't available yet.
    Replace this with your actual graph loading logic.
    """
    G = nx.Graph()
    # Mix of Neuro terms, General Anatomy, and Disease terms
    nodes = [
        "Neuron", "Cortex", "Brain", "Synapse", # Neuro (NIFSTD should catch these)
        "Femur", "Heart", "Lung",               # Anatomy (FMA should catch these)
        "Seizure", "Epilepsy", "Headache",      # Phenotype/Disease (HPO)
        "Neural Network", "Simulation",         # Computational (CNO)
        "UnknownTerm123", "Asdfhjkl"            # Nonsense
    ]
    G.add_nodes_from(nodes)
    return G

def run_benchmark():
    # 1. Define Ontologies
    ontologies = {
        "NIFSTD (Neuroscience)": "http://ontology.neuinfo.org/NIF/ttl/nif.ttl",
        "FMA (Anatomy)": "http://purl.obolibrary.org/obo/fma.owl", 
        "CNO (Comp. Neuro)": "http://purl.org/incf/ontology/Computational_Neurosciences/cno_alpha.owl",
        "HPO (Phenotypes)": "http://purl.obolibrary.org/obo/hp.owl"
    }

    # 2. Load Graph
    # TODO: Load your specific graph here. Using mock for now.
    graph = create_mock_graph()
    print(f"Benchmarking Graph with {graph.number_of_nodes()} nodes...\n")

    results = []

    # 3. Iterate and Validate
    print(f"{'Ontología':<25} | {'Válidos':<7} | {'Inválidos':<9} | {'Precisión':<10}")
    print("-" * 55)

    for name, url in ontologies.items():
        print(f"Cargando {name}...", end="\r")
        try:
            validator = GraphValidator(ontology_urls=[url])
            report = validator.validate_graph(graph)
            
            valid = report['valid_nodes']
            invalid = report['invalid_nodes']
            precision = report['precision']
            
            print(f"{name:<25} | {valid:<7} | {invalid:<9} | {precision:.2%}")
            
            results.append({
                "ontology": name,
                "report": report
            })
            
        except Exception as e:
            print(f"{name:<25} | ERROR: {str(e)}")

    print("-" * 55)
    print("\nBenchmark Completado.")

if __name__ == "__main__":
    run_benchmark()
