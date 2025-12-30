import re
import nltk

class TextTokenizer:
    def __init__(self):
        pass
    
    def clean_text(self, text):
        # 1. Eliminar todo lo que esté después de "Referencias" o "Bibliografía"
        text = re.split(r'\n\s*(Referencia|Bibliograf|Bibliography|References)', text, flags=re.IGNORECASE)[0]

        # 2. Eliminar patrones de encabezados/pies de página comunes (e.g., "Page 1 of 10", "Vol. 12")
        text = re.sub(r'Pág\.\s*\d+|Page\s*\d+\s*of\s*\d+|Vol\.\s*\d+', '', text, flags=re.IGNORECASE)

        # 3. Eliminar URLs y correos electrónicos
        text = re.sub(r'http\S+|www\.\S+|\S+@\S+', '', text)

        # 4. Eliminar citas bibliográficas como [1], [1, 2], etc.
        text = re.sub(r'\[\d+(?:,\s*\d+)*\]', '', text)

        # 5. Eliminar citas bibliográficas en paréntesis como (1), (1, 2), etc.
        text = re.sub(r'\(\s*\d+(?:,\s*\d+)*\s*\)', '', text)

        # 6. Eliminar símbolos aislados como | y · que son artefactos de PDF
        text = re.sub(r'\|', '', text)
        text = re.sub(r'·', '', text)

        # 7. Eliminar líneas muy cortas que suelen ser basura de formato
        clean_lines = [
            line.strip() 
            for line in text.split("\n") 
            if len(line.split()) > 3  # Si la línea tiene menos de 3 palabras, la borramos
        ]
        
        return " ".join(clean_lines)
    
    def tokenize_sentences(self, text):
        ctext = self.clean_text(text)
        sentences = nltk.tokenize.sent_tokenize(ctext, language="spanish")
        return sentences
    
    def run(self, text):
        return self.tokenize_sentences(text)
