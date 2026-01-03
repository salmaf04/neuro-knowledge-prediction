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

    def _get_ontology_class(self, term):
        """
        Finds the actual owlready2 Class object for a given term.
        """
        term_lower = term.lower()
        if term_lower in self.known_terms:
            # This is slow if known_terms is just a set of strings. 
            # We need a map from label -> class object.
            # For iteration 1 efficiency: we iterate ontologies to find match.
            for onto in self.ontologies:
                # Direct check if possible, mostly we rely on search or known labels
                # owlready2 search:
                res = onto.search(label = term_lower, _case_sensitive=False)
                if res: return res[0]
                res = onto.search(iri = f"*{term}", _case_sensitive=False)
                if res: return res[0]
        
        # Fuzzy match fallback logic implies we might accept "close" terms, 
        # but for distance calc we need a concrete class.
        # Let's try to search close matches if exact failed.
        matches = get_close_matches(term_lower, self.known_terms, n=1, cutoff=0.85)
        if matches:
            match_label = matches[0]
            for onto in self.ontologies:
                res = onto.search(label = match_label, _case_sensitive=False)
                if res: return res[0]
        
        return None

    def _calculate_semantic_distance(self, cls_a, cls_b):
        """
        Calculates distance via Lowest Common Ancestor (LCA) in is-a hierarchy.
        Returns int distance or float('inf').
        """
        if cls_a == cls_b:
            return 0
            
        # Get ancestors with distance (BFS up)
        def get_ancestors_dist(start_node):
            dists = {start_node: 0}
            queue = [start_node]
            idx = 0
            while idx < len(queue):
                curr = queue[idx]
                idx += 1
                curr_dist = dists[curr]
                
                # owlready2 is_a gives superclasses
                try:
                    parents = curr.is_a
                except AttributeError:
                    continue
                    
                for p in parents:
                    # Filter for actual entities (ignore restrictions like 'part_of some X')
                    if hasattr(p, 'name') and p not in dists:
                        dists[p] = curr_dist + 1
                        queue.append(p)
            return dists

        dists_a = get_ancestors_dist(cls_a)
        dists_b = get_ancestors_dist(cls_b)
        
        # Find common ancestors
        common = set(dists_a.keys()) & set(dists_b.keys())
        
        if not common:
            return float('inf')
            
        # Min distance = min(dist_a + dist_b)
        min_dist = float('inf')
        for anc in common:
            d = dists_a[anc] + dists_b[anc]
            if d < min_dist:
                min_dist = d
                
        return min_dist

    def validate_edges(self, graph):
        """
        Validates edges by calculating semantic distance between endpoints.
        """
        report = {
            "total_edges": graph.number_of_edges(),
            "valid_rels": 0,
            "weak_rels": 0,
            "avg_distance": 0.0,
            "details": {}
        }
        
        total_dist = 0
        count_dist = 0
        
        for u, v in graph.edges():
            cls_u = self._get_ontology_class(str(u))
            cls_v = self._get_ontology_class(str(v))
            
            status = "unknown_nodes"
            dist = None
            
            if cls_u and cls_v:
                dist = self._calculate_semantic_distance(cls_u, cls_v)
                if dist < 5: # Threshold for "Strong" relationship
                    status = "strong"
                    report["valid_rels"] += 1
                elif dist < float('inf'):
                    status = "weak"
                    report["weak_rels"] += 1
                else:
                    status = "disconnected"
                
                if dist < float('inf'):
                    total_dist += dist
                    count_dist += 1
            
            report["details"][f"{u}--{v}"] = {"status": status, "distance": dist}

        if count_dist > 0:
            report["avg_distance"] = total_dist / count_dist
            
        return report

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
            "edge_report": None,
            "precision": 0.0
        }

        # Node Validation
        for node in graph.nodes():
            result = self.validate_term(str(node))
            report["node_details"][node] = result
            if result["status"] == "valid":
                report["valid_nodes"] += 1
            else:
                report["invalid_nodes"] += 1
        
        if report["total_nodes"] > 0:
            report["precision"] = report["valid_nodes"] / report["total_nodes"]
            
        # Edge Validation (New)
        if self.ontologies:
            report["edge_report"] = self.validate_edges(graph)

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
