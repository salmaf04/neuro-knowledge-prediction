from functools import lru_cache
from pydantic_settings import BaseSettings
from pypdf import PdfReader
from typing import Any

class Settings(BaseSettings):
    pdf_reader: Any  = PdfReader
    pdf_folder: Any = "./corpus" 
    txts_folder: Any = "./txts" 
    class Config:
        env_file = ".env"
        
        
@lru_cache
def get_settings():
    return Settings()