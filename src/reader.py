from pathlib import Path
from config import get_settings

class CorpusReader:
    def __init__(self):
        self.pdf_folder = Path(get_settings().pdf_folder)
        self.txts_folder = Path(get_settings().txts_folder)
        self.pdf_proccesor = get_settings().pdf_reader
           
    def to_text(self, pdf_file):
        doc = self.pdf_proccesor.open(pdf_file)
        article = []
        for page in doc:
            txt = page.get_text("text")
            if txt:
                txt = txt.replace("-\n", "")
                txt = txt.replace("\n", " ")
                article.append(txt)
        article_txt = " ".join(article)
        return article_txt
    
    def to_txt(self, article_text, pdf_name):
        output_file = pdf_name.with_suffix(".txt")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(article_text)
            
    def get_filename(self, pdf_file):
        pdf_file_name = pdf_file.with_suffix(".txt").as_posix()
        pdf_file_name = pdf_file_name.split("/")[-1]
        file_name = Path(f"./txts/{pdf_file_name}")
        return file_name
            
    def proccess_pdf(self):
        for pdf_file in self.pdf_folder.glob("*.pdf"):
            pdf_name = self.get_filename(pdf_file)
            
            if pdf_name.exists():
                print(f"The file {pdf_name.name} already exists. Skipping...")
                continue
            
            text = self.to_text(pdf_file)
            self.to_txt(text,pdf_name)
            
    def run(self):
        self.proccess_pdf()
    