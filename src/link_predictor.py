from config import get_settings
from networkx.algorithms import link_prediction

class LinkPredictor:
    def __init__(self):
        self.predictive_method = f"link_prediction.{get_settings().prediction_method}"

    def predict(self, graph, top_k):

        nx_graph = graph.graph
        preds = list(eval(self.predictive_method)(nx_graph))
        preds.sort(key=lambda x: x[2], reverse=True)
        return preds[:top_k]

    def run(self, graph, top_k):
        return self.predict(graph, top_k)
