from src.reader import CorpusReader

if __name__ == "__main__":
    corpus = CorpusReader()
    print("Starting the reader")
    corpus.run()