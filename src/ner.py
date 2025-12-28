from config import get_settings
from transformers import pipeline
from unidecode import unidecode
import string
import hashlib

class EntityRecognizer:
    def __init__(self):
        self.stopwords = get_settings().stop_words
        self.blacklist = get_settings().blacklist
        self.ner_pipeline = pipeline(
            "ner", model=get_settings().model, aggregation_strategy="simple"
        )
        
    def trigger_pipeline(self, sentence):
        return self.ner_pipeline(sentence)
    
    def process_lema(self, ent):
        raw_word = ent["word"].strip()
        # 3. Normalización para el grafo (Clave para evitar duplicados)
        # Quita acentos y pasa a minúsculas: "Cáncer" -> "cancer"
        lemma = unidecode(raw_word.lower()) 
        
        # Limpiar signos de puntuación pegados
        lemma = lemma.strip(string.punctuation + "0123456789")
        
        return lemma, raw_word
        
    def validate_lema(self, lemma):
        if len(lemma) < 4 or lemma in self.stopwords or lemma in self.blacklist:
            return True
        
        return False
        
    def get_entities(self, sentences):
        entity_list = []

        for s in sentences:
            if len(s) < 20: 
                continue 
            
            results = self.trigger_pipeline(s)
            denotations = []
            
            for ent in results:
                # 1. Filtro de confianza
                if ent["score"] < 0.70: # Sé exigente con el score
                    continue
                lemma, raw_word = self.process_lema(ent)
                
                if not self.validate_lema(lemma):
                    continue
                    
                # Etiqueta de la entidad (ENFERMEDAD, QUIMICO, etc.)
                label = ent["entity_group"]
                
                denotations.append({
                    "obj": label,
                    "span": {"begin": ent["start"], "end": ent["end"]},
                    "lemma": lemma,  # Usamos el lema normalizado como ID del nodo
                    "original": raw_word
                })

            if len(denotations) > 0:
                entity_list.append({"text": s, "denotations": denotations})
                
        return entity_list
    
    def parse_entities(self, entity_list):
        parsed_entities = []
        for entities in entity_list:
            e = []
            # If there are not entities in the text
            if not entities.get("denotations"):
                parsed_entities.append(
                    {
                        "text": entities["text"],
                        "text_sha256": hashlib.sha256(
                            entities["text"].encode("utf-8")
                        ).hexdigest(),
                    }
                )
                continue
            for entity in entities["denotations"]:
                other_ids = [id for id in entity["id"] if not id.startswith("BERN")]
                entity_type = entity["obj"]
                # 1. Obtener lema si existe, sino el texto original
                raw_text = entities["text"][entity["span"]["begin"] : entity["span"]["end"]]
                lemma = raw_text

                # 2. Limpieza: minúsculas y quitar puntuación externa (ej: "wound to" -> "wound")
                clean_name = lemma.lower().strip(string.punctuation + " ")

                # 3. Filtrado: Ignorar si es stopword, muy corto o un número
                if clean_name in self.stopwords or len(clean_name) < 3 or len(clean_name) > 60 or clean_name.isdigit():
                    continue

                entity_name = clean_name

                try:
                    entity_id = [id for id in entity["id"] if id.startswith("BERN")][0]
                except IndexError:
                    entity_id = entity_name

                e.append(
                    {
                        "entity_id": entity_id,
                        "other_ids": other_ids,
                        "entity_type": entity_type,
                        "entity": entity_name,
                    }
                )

            parsed_entities.append(
                {
                    "entities": e,
                    "text": entities["text"],
                    "text_sha256": hashlib.sha256(entities["text"].encode("utf-8")).hexdigest(),
                }
            )
            
        return parsed_entities
    
    def run(self, sentences):
        entities = self.get_entities(sentences)
        return self.parse_entities(entities)
        
        
