from pathlib import Path
from config import get_settings
import re


class CorpusReader:
    def __init__(self):
        self.pdf_folder = Path(get_settings().pdf_folder)
        self.txts_folder = Path(get_settings().txts_folder)
        self.pdf_proccesor = get_settings().pdf_reader

    def to_text(self, pdf_file):
        doc = self.pdf_proccesor.open(pdf_file)

        full_text_pages = []

        for page in doc:
            blocks = page.get_text("blocks")
            page_text_parts = []

            for block in blocks:
                if txt := self.process_block(block):
                    page_text_parts.append(txt)

            if page_text_parts:
                full_text_pages.append(" ".join(page_text_parts))

        doc.close()

        article_txt = " ".join(full_text_pages)
        article_txt = re.sub(r"\s+", " ", article_txt).strip()

        return article_txt

    def process_block(self, block):
        txt = block[4]
        txt = txt.replace("-\n", "")
        txt = txt.replace("\n", " ")
        txt = re.sub(r"([a-záéíóúñ])([A-ZÁÉÍÓÚÑ])", r"\1 \2", txt)
        txt = txt.strip()

        return txt

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
            self.to_txt(text, pdf_name)

    def run(self):
        self.proccess_pdf()
