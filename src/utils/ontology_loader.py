import os
from owlready2 import get_ontology, World
import requests

class OntologyLoader:
    def __init__(self, cache_dir="./cache_ontologies"):
        self.cache_dir = cache_dir
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        self.world = World()

    def load_from_url(self, url, filename=None):
        """
        Loads an ontology from a URL. Caches it locally.
        """
        if not filename:
            filename = url.split('/')[-1]
            if not filename.endswith('.owl'):
                filename += '.owl'
        
        local_path = os.path.join(self.cache_dir, filename)

        if not os.path.exists(local_path):
            print(f"Downloading ontology from {url}...")
            try:
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                print(f"Saved to {local_path}")
            except Exception as e:
                print(f"Failed to download ontology: {e}")
                return None
        else:
            print(f"Loading cached ontology from {local_path}")

        try:
            onto = self.world.get_ontology(local_path).load()
            return onto
        except Exception as e:
            print(f"Error loading ontology with owlready2: {e}")
            return None

    def get_term_labels(self, ontology):
        """
        Extracts all labels from the ontology for fuzzy matching.
        Returns a dictionary or set of normalized labels.
        """
        labels = set()
        if not ontology:
            return labels
            
        for c in ontology.classes():
            # Add class name
            labels.add(c.name.lower())
            # Add label annotations if available
            if hasattr(c, 'label'):
                for l in c.label:
                    labels.add(str(l).lower())
        return labels
