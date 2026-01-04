import os
from owlready2 import get_ontology, World, onto_path
import requests
import rdflib
from collections import defaultdict

class OntologyLoader:
    def __init__(self, cache_dir="./cache_ontologies"):
        self.cache_dir = cache_dir
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        
        # Add cache dir to search path for imports
        if self.cache_dir not in onto_path:
            onto_path.append(self.cache_dir)
            
        self.world = World()
        # Mapping from normalized label -> list of owlready2 Class objects
        self.label_to_class = defaultdict(list)

    def load_from_url(self, url, filename=None):
        """
        Loads an ontology from a URL. Caches it locally.
        Converts Turtle (.ttl) to RDF/XML if needed for owlready2.
        """
        if not filename:
            filename = url.split('/')[-1]
            if not filename.endswith('.owl') and not filename.endswith('.ttl'):
                if 'ttl' in url or 'turtle' in url:
                    filename += '.ttl'
                else:
                    filename += '.owl'
        
        local_path = os.path.join(self.cache_dir, filename)

        # Download if missing
        if not os.path.exists(local_path):
            print(f"Downloading ontology from {url}...")
            try:
                # Add User-Agent to avoid 403 Forbidden/Timeouts
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
                response = requests.get(url, headers=headers, timeout=60) 
                response.raise_for_status()
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                print(f"Saved to {local_path}")
            except Exception as e:
                print(f"Failed to download ontology: {e}")
                return None
        else:
            print(f"Loading cached ontology from {local_path}")

        # Conversion for Turtle files (owlready2 doesn't like them natively sometimes)
        if local_path.endswith('.ttl') or local_path.endswith('.nt'):
            xml_path = local_path + ".xml"
            if not os.path.exists(xml_path):
                print(f"Converting {local_path} to RDF/XML for owlready2...")
                try:
                    g = rdflib.Graph()
                    g.parse(local_path, format="turtle" if local_path.endswith('.ttl') else "nt")
                    g.serialize(destination=xml_path, format="xml")
                    local_path = xml_path # Switch to loading the XML version
                except Exception as e:
                    print(f"Error converting Turtle to XML: {e}")
                    # Try loading original anyway just in case
            else:
                local_path = xml_path

        try:
            onto = self.world.get_ontology(local_path).load()
            # Populate fast label->class mapping for quick lookups
            self._add_labels_from_ontology(onto)
            return onto
        except Exception as e:
            print(f"Error loading ontology with owlready2: {e}")
            return None

    def _add_labels_from_ontology(self, ontology):
        """
        Populate/extend self.label_to_class with labels from the given ontology.
        Each label maps to a list of Class objects (multiple classes may share a label across ontologies).
        """
        if not ontology:
            return
        for c in ontology.classes():
            # collect candidate labels (primary name + rdfs:label annotations)
            lbls = {str(c.name).lower()}
            if hasattr(c, 'label'):
                for l in c.label:
                    lbls.add(str(l).lower())
            for l in lbls:
                self.label_to_class[l].append(c)

    def get_classes_by_label(self, label):
        """
        Return a shallow copy of the list of classes for a normalized label.
        """
        if label is None:
            return []
        return list(self.label_to_class.get(label.lower(), []))

    def get_term_labels(self, ontology=None):
        """
        Extracts all labels from the ontology for fuzzy matching.
        Returns a set of normalized labels. If ontology is None, returns all labels
        available in the internal mapping.
        """
        labels = set()
        if ontology:
            for c in ontology.classes():
                # Add class name
                labels.add(c.name.lower())
                # Add label annotations if available
                if hasattr(c, 'label'):
                    for l in c.label:
                        labels.add(str(l).lower())
            return labels
        # If no ontology provided, return labels from the fast mapping
        return set(self.label_to_class.keys())
