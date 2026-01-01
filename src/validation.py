import networkx as nx
import sys
import os

# Add project root to path if running as script
current_dir = os.path.dirname(os.path.abspath(__file__)) # src
project_root = os.path.dirname(current_dir) # root
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from src.utils.ontology_loader import OntologyLoader
except ImportError:
    # Fallback if somehow src path logic fails
    try:
        from utils.ontology_loader import OntologyLoader
    except ImportError:
        # Emergency fallback
        sys.path.append(os.path.join(current_dir, "utils"))
        from ontology_loader import OntologyLoader
from difflib import get_close_matches

class GraphValidator:
    def __init__(self, ontology_urls=None):
        self.loader = OntologyLoader()
        self.known_terms = set()
        self.ontologies = []
        
        if ontology_urls:
            for url in ontology_urls:
                onto = self.loader.load_from_url(url)
                if onto:
                    self.ontologies.append(onto)
                    self.known_terms.update(self.loader.get_term_labels(onto))
    
    def validate_term(self, term):
        """
        Checks if a term exists in the loaded ontologies.
        Returns exact match, or close match, or None.
        """
        term_lower = term.lower()
        if term_lower in self.known_terms:
            return {"status": "valid", "match": term_lower, "type": "exact"}
        
        # Fuzzy match
        matches = get_close_matches(term_lower, self.known_terms, n=1, cutoff=0.85)
        if matches:
            return {"status": "valid", "match": matches[0], "type": "fuzzy"}
            
        return {"status": "invalid", "match": None, "type": "none"}

    def validate_graph(self, graph):
        """
        Validates the nodes and edges of a NetworkX graph.
        """
        report = {
            "total_nodes": graph.number_of_nodes(),
            "valid_nodes": 0,
            "invalid_nodes": 0,
            "node_details": {},
            "total_edges": graph.number_of_edges(),
            # Edge validation would require more complex reasoning (checking paths in ontology)
        }

        print("Validating nodes...")
        for node in graph.nodes():
            result = self.validate_term(str(node))
            report["node_details"][node] = result
            if result["status"] == "valid":
                report["valid_nodes"] += 1
            else:
                report["invalid_nodes"] += 1
        
        if report["total_nodes"] > 0:
            report["precision"] = report["valid_nodes"] / report["total_nodes"]
        else:
            report["precision"] = 0.0
            
        return report

if __name__ == "__main__":
    # Example usage / Test
    # Using a small subset or a public URL for testing. 
    # NIFSTD is large, so for this example/placeholder we might might want to mock or use a small file.
    # For now, let's try to load a very small simple ontology or just instantiate the class.
    
    validator = GraphValidator() 
    # In a real run, we would pass: 
    # ontology_urls=["http://ontology.neuinfo.org/NIF/NIF-Structural-Anatomy.owl"]
    
    # Create a dummy graph
    G = nx.Graph()
    G.add_node("Neuron")
    G.add_node("Cortex")
    G.add_node("Asdflkjsd") # Invalid
    
    # Mocking known terms for the test since we didn't load a real massive ontology in this quick test
    validator.known_terms = {"neuron", "cortex", "brain", "synapse"}
    
    report = validator.validate_graph(G)
    print("Validation Report:", report)
