import pdf2image
import pytesseract
from pathlib import Path
import os

class CorpusReader:
    def __init__(self, path):
        self.path = path
        
    def convert_to_image(self, pdf_file):
        return pdf2image.convert_from_path(str(pdf_file))
    
    def image_to_text(self, image):
        article = []

        for _, page_data in enumerate(image):
            txt = pytesseract.image_to_string(page_data).encode("utf-8")
            article.append(txt)

        return " ".join(article)
    
    def to_txt(self, article_text, pdf_file):
        output_file = pdf_file.with_suffix(".txt")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(article_text)
            
    def proccess_pdf(self):
        for file in os.listdir(self.path):
            if file.endswith('.pdf'):
                pdf_file = Path(os.path.join(self.path,file))
                images = self.convert_to_image(pdf_file)
                text = self.image_to_text(images)
                self.to_txt(text,pdf_file)
    