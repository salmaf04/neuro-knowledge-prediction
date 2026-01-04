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

# Try to use rapidfuzz for fuzzy matching; fallback to difflib if not available
try:
    from rapidfuzz import process, fuzz
    _USE_RAPIDFUZZ = True
except Exception:
    from difflib import get_close_matches
    _USE_RAPIDFUZZ = False

class GraphValidator:
    def __init__(self, ontology_urls=None):
        self.loader = OntologyLoader()
        self.known_terms = set()
        self.ontologies = []
        # Caches to avoid recomputing expensive operations
        self._dist_cache = {}        # (id_a, id_b) -> distance
        self._ancestors_cache = {}   # class_obj -> {ancestor: dist}
        
        if ontology_urls:
            for url in ontology_urls:
                onto = self.loader.load_from_url(url)
                if onto:
                    self.ontologies.append(onto)
                    self.known_terms.update(self.loader.get_term_labels(onto))
    
    def _choose_cutoff(self, term: str) -> int:
        """
        Compute a dynamic cutoff (0-100) for fuzzy matching.
        Heuristics:
        - Short terms (<=3) need stricter cutoff to avoid false positives.
        - Medium terms get a small boost.
        - Very long terms relax the cutoff a bit.
        - Larger known_terms vocab increases cutoff slightly.
        Returns an integer in [50, 98].
        """
        t = (term or "").strip().lower()
        length = len(t)
        base = 85
        if length <= 3:
            base += 10
        elif length <= 6:
            base += 5
        if length >= 20:
            base -= 10

        vocab = len(self.known_terms) if self.known_terms else 0
        if vocab > 10000:
            base += 5
        elif vocab > 1000:
            base += 2

        return max(50, min(98, int(base)))

    def validate_term(self, term):
        """
        Checks if a term exists in the loaded ontologies.
        Returns exact match, or close match, or None.
        """
        term_lower = term.lower()
        if term_lower in self.known_terms:
            return {"status": "valid", "match": term_lower, "type": "exact"}
        
        # Dynamic cutoff (0-100)
        cutoff = self._choose_cutoff(term_lower)

        # Fuzzy match using rapidfuzz when available (score 0-100)
        if _USE_RAPIDFUZZ and self.known_terms:
            match = process.extractOne(term_lower, self.known_terms, scorer=fuzz.ratio, score_cutoff=cutoff)
            if match:
                matched_label, score = match[0], match[1]
                return {"status": "valid", "match": matched_label, "type": "fuzzy", "score": score}
        else:
            # difflib expects cutoff in 0..1
            if self.known_terms:
                matches = get_close_matches(term_lower, self.known_terms, n=1, cutoff=cutoff/100.0)
                if matches:
                    return {"status": "valid", "match": matches[0], "type": "fuzzy"}

        return {"status": "invalid", "match": None, "type": "none"}

    def _get_ontology_class(self, term):
        """
        Finds the actual owlready2 Class object for a given term.
        """
        term_lower = term.lower()

        # Fast path: use loader's label->class mapping if available
        try:
            classes = self.loader.get_classes_by_label(term_lower)
            if classes:
                return classes[0]
        except Exception:
            # If loader does not provide mapping for some reason, continue to slower search
            pass

        # Slower path: iterate ontologies and search (existing behavior)
        for onto in self.ontologies:
            # Direct check if possible, mostly we rely on search or known labels
            # owlready2 search:
            try:
                res = onto.search(label = term_lower, _case_sensitive=False)
                if res: return res[0]
                res = onto.search(iri = f"*{term}", _case_sensitive=False)
                if res: return res[0]
            except Exception:
                # ignore ontology-specific search errors and continue
                continue

        # Fuzzy match fallback: try to resolve a close label to a class using the fast mapping first
        match_label = None
        cutoff = self._choose_cutoff(term_lower)
        if _USE_RAPIDFUZZ and self.known_terms:
            candidates = process.extract(term_lower, self.known_terms, scorer=fuzz.ratio, limit=2)
            if candidates:
                best_label, best_score = candidates[0][0], candidates[0][1]
                second_score = candidates[1][1] if len(candidates) > 1 else None
                # Accept if above cutoff or clear gap relative to second candidate
                if best_score >= cutoff or (second_score is not None and (best_score - second_score) >= 10 and best_score >= (cutoff - 5)):
                    match_label = best_label
                    try:
                        classes = self.loader.get_classes_by_label(match_label)
                        if classes:
                            return classes[0]
                    except Exception:
                        pass
        else:
            if self.known_terms:
                matches = get_close_matches(term_lower, self.known_terms, n=2, cutoff=cutoff/100.0)
                if matches:
                    match_label = matches[0]
                    try:
                        classes = self.loader.get_classes_by_label(match_label)
                        if classes:
                            return classes[0]
                    except Exception:
                        pass

        # Final slow fallback: try search on ontologies for the fuzzy label
        if match_label:
            for onto in self.ontologies:
                try:
                    res = onto.search(label = match_label, _case_sensitive=False)
                    if res: return res[0]
                except Exception:
                    continue

        return None

    def _calculate_semantic_distance(self, cls_a, cls_b):
        """
        Calculates distance via Lowest Common Ancestor (LCA) in is-a hierarchy.
        Returns int distance or float('inf'). Uses caching to avoid recomputation.
        """
        if cls_a == cls_b:
            return 0

        def _id_of(c):
            return getattr(c, 'iri', None) or getattr(c, 'name', None) or str(c)

        key = tuple(sorted((_id_of(cls_a), _id_of(cls_b))))
        if key in self._dist_cache:
            return self._dist_cache[key]

        # Get ancestors with distance (BFS up) with memoization per node
        def get_ancestors_dist(start_node):
            if start_node in self._ancestors_cache:
                return self._ancestors_cache[start_node]

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

            # store in cache
            self._ancestors_cache[start_node] = dists
            return dists

        dists_a = get_ancestors_dist(cls_a)
        dists_b = get_ancestors_dist(cls_b)

        # Find common ancestors
        common = set(dists_a.keys()) & set(dists_b.keys())

        if not common:
            self._dist_cache[key] = float('inf')
            return float('inf')

        # Min distance = min(dist_a + dist_b)
        min_dist = float('inf')
        for anc in common:
            d = dists_a[anc] + dists_b[anc]
            if d < min_dist:
                min_dist = d

        self._dist_cache[key] = min_dist
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
    # Batch test/demo for validate_term and fuzzy behavior
    validator = GraphValidator()

    # Provide a moderate known_terms set for testing fuzzy behavior
    validator.known_terms = {
        "neuron", "cortex", "brain", "synapse",
        "hippocampus", "hippocampal", "femur", "heart", "lung",
        "seizure", "epilepsy", "headache", "neural network", "simulation"
    }

    examples = [
        "Neuron",        # exact
        "neoron",        # small typo
        "HippoCampus",   # case + spacing
        "hippocampal",   # alternate form
        "fumur",         # typo
        "nn",            # very short ambiguous
        "NeuralNet",     # partial compound
        "Asdfhjkl",      # nonsense
        "brain",         # exact
        "head ache"      # spaced form
    ]

    print("\n=== validate_term batch demo ===")
    for q in examples:
        res = validator.validate_term(q)
        line = f"Query: '{q}' -> {res}"

        # If rapidfuzz available, show cutoff and best candidate(s)
        if _USE_RAPIDFUZZ and validator.known_terms:
            cutoff = validator._choose_cutoff(q)
            try:
                best = process.extractOne(q.lower(), validator.known_terms, scorer=fuzz.ratio)
                if best:
                    # rapidfuzz may return (label, score) or (label, score, idx)
                    if isinstance(best, (list, tuple)) and len(best) >= 2:
                        best_label, best_score = best[0], best[1]
                    else:
                        best_label, best_score = str(best), None
                    line += f"    | cutoff={cutoff} best=({best_label}, {best_score})"
            except Exception as e:
                line += f"    | rapidfuzz error: {e}"

        print(line)

    # Mock graph validation to show integration (edges + node validation)
    print("\n=== Mock graph validation ===")
    G = nx.Graph()
    G.add_nodes_from(["Neuron", "Cortex", "Asdfhjkl", "Femur"])
    G.add_edge("Neuron", "Cortex")
    G.add_edge("Neuron", "Femur")

    report = validator.validate_graph(G)
    print("Graph validation report:")
    print(report)

    print("\nDemo complete. Run this script directly to re-run the tests.")
