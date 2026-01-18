import pandas as pd
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from owlready2 import get_ontology
from config import get_settings

class SemanticAligner:
    def __init__(self, model_name=None, threshold=None):
        settings = get_settings()
        self.model_name = model_name or getattr(settings, "embedding_model", "cambridgeltl/SapBERT-from-PubMedBERT-fulltext")
        self.threshold = threshold or getattr(settings, "alignment_threshold", 0.82)
        
        self.model = SentenceTransformer(self.model_name)
        self.ontology_embeddings = None
        self.ontology_data = None 

    def load_ontology(self, path):
        """
        Detecta el tipo de archivo y carga la ontología.
        """
        suffix = Path(path).suffix.lower()
        
        if suffix == '.csv':
            df = pd.read_csv(path).fillna("")
        elif suffix in ['.owl', '.rdf', '.xml']:
            df = self._extract_from_owl(path)
        else:
            raise ValueError(f"Formato de archivo {suffix} no soportado.")

        # Generar string enriquecido
        enriched_strings = df.apply(
            lambda x: f"{x['label']} [SEP] {x['synonyms']} [SEP] {x['description']}", 
            axis=1
        ).tolist()
        
        print(f"Generando embeddings para {len(enriched_strings)} conceptos...")
        self.ontology_embeddings = self.model.encode(
            enriched_strings, 
            show_progress_bar=True,
            normalize_embeddings=True
        )
        self.ontology_data = df
        return self.ontology_embeddings



    def calculate_rdo(self, doc_id, parsed_entities):
        """
        Calcula el Document-in-Ontology Recall (Rdo).
        Recibe la salida de ner.py (parsed_entities).
        """
        # 1. Extraer términos únicos del documento (ya filtrados por NER)
        # Usamos el campo 'entity' que ya viene normalizado de ner.py
        doc_terms = []
        for item in parsed_entities:
            if "entities" in item:
                for ent in item["entities"]:
                    doc_terms.append(ent["entity"])
        
        unique_terms = list(set(doc_terms))
        
        if not unique_terms:
            return {"doc_id": doc_id, "Rdo": 0.0, "mapped": [], "residuals": []}

        # 2. Generar embeddings de las entidades del documento
        doc_embeddings = self.model.encode(
            unique_terms, 
            normalize_embeddings=True
        )

        # 3. Similitud de Coseno
        # Matriz: (Num Entidades Doc) x (Num Conceptos Ontología)
        sim_matrix = cosine_similarity(doc_embeddings, self.ontology_embeddings)
        
        # 4. Evaluación de Máximo Alineamiento
        max_sims = np.max(sim_matrix, axis=1)
        mapped_mask = max_sims >= self.threshold
        
        mapped_terms = [unique_terms[i] for i in range(len(unique_terms)) if mapped_mask[i]]
        residual_terms = [unique_terms[i] for i in range(len(unique_terms)) if not mapped_mask[i]]
        
        rdo = len(mapped_terms) / len(unique_terms)

        return {
            "doc_id": doc_id,
            "Rdo": round(rdo, 4),
            "total_count": len(unique_terms),
            "mapped_count": len(mapped_terms),
            "mapped_terms": mapped_terms,
            "residuals": residual_terms
        }