from functools import lru_cache
from pydantic_settings import BaseSettings
import fitz
from typing import Any

STOPWORDS = set(
    [
        "introducción",
        "método",
        "métodos",
        "resultado",
        "resultados",
        "discusión",
        "conclusión",
        "figura",
        "tabla",
        "referencia",
        "estudio",
        "análisis",
        "datos",
        "artículo",
        "sección",
        "mostrado",
        "usando",
        "usado",
        "basado",
        "encontrado",
        "también",
        "sin embargo",
        "aunque",
        "año",
        "años",
        "tiempo",
        "alto",
        "bajo",
        "valor",
        "caso",
        "grupo",
        "et",
        "al",
        "probabilidad",
        "momento",
        "situaciones",
        "descubrir",
        "mantiene",
        "significaba",
        "quizás",
        "debido",
        "uso",
        "hacer",
        "obtener",
        "puede",
        "podría",
        "listado",
        "conferencias",
        "antecedentes",
        "significancia",
        "derechos de autor",
        "autor",
        "fig",
        "ec",
        "vol",
    ]
)

BLACKLIST = {
    "fig", "figura", "figure", "tabla", "table", "cuadro", "doi", "issn", 
    "url", "http", "www", "et", "al", "vol", "no", "pág", "pag", "ed",
    "estudio", "análisis", "datos", "método", "resultado", "conclusión" # Palabras genéricas
}

class Settings(BaseSettings):
    pdf_reader: Any  = fitz
    pdf_folder: Any = "./corpus" 
    txts_folder: Any = "./txts" 
    model: Any = "HUMADEX/spanish_medical_ner"
    stop_words: Any = STOPWORDS
    blacklist: Any = BLACKLIST
    class Config:
        env_file = ".env"
        
        
@lru_cache
def get_settings():
    return Settings()