import pandas as pd
import networkx as nx
import torch
from pykeen.pipeline import pipeline
from pykeen.triples import TriplesFactory
from pykeen.predict import predict_target
from graph import Graph

class ExtendedGraph(Graph):
    def __init__(self, graph):
        super().__init__()
        self.graph = graph.graph.copy()
        self.predicted_edges = []
        self.evaluation_metrics = {}
        
    def predict_edges(self, relacion_busqueda="relacionado_con", n_predicciones=10, epochs=100):
        """
        Entrena un modelo de Knowledge Graph Embedding y añade nuevas aristas al grafo original.
        Modifica el grafo actual y almacena las aristas predichas en self.predicted_edges.
        
        Args:
            relacion_busqueda (str): Tipo de relación a predecir. Por defecto "relacionado_con".
            n_predicciones (int): Número de predicciones top a considerar por nodo. Por defecto 10.
            epochs (int): Número de épocas para entrenar el modelo. Por defecto 100.
        """
        triples_list = []
        for u, v, data in self.graph.edges(data=True):
            rel = data.get('relation', 'relacionado_con')
            triples_list.append([str(u), str(rel), str(v)])
        
        df_triples = pd.DataFrame(triples_list, columns=['head', 'relation', 'tail'])
        
        tf = TriplesFactory.from_labeled_triples(triples=df_triples.values)
        training_factory, testing_factory = tf.split([0.8, 0.2], random_state=42)
        
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"Usando dispositivo: {device}")
        print(f"Entrenando modelo para {len(self.graph.nodes)} nodos...")
        
        result = pipeline(
            training=training_factory,
            testing=testing_factory,
            model='RotatE',
            epochs=epochs,
            device=device,
            random_seed=42
        )
        
        self.evaluation_metrics = result.metric_results.to_flat_dict()
        
        print("\n" + "="*80)
        print("MÉTRICAS DE EVALUACIÓN DEL MODELO")
        print("="*80)
        for metric_name, metric_value in self.evaluation_metrics.items():
            if isinstance(metric_value, (int, float)):
                print(f"{metric_name}: {metric_value:.4f}")
            else:
                print(f"{metric_name}: {metric_value}")
        print("="*80 + "\n")
        
        for u, v in self.graph.edges():
            self.graph[u][v]['origin'] = 'real'
        
        print("Generando predicciones de nuevas conexiones...")
        
        self.predicted_edges = []
        
        for nodo in self.graph.nodes():
            try:
                predicciones = predict_target(
                    model=result.model,
                    head=str(nodo),
                    relation=relacion_busqueda,
                    triples_factory=tf
                ).df
                
                top_preds = predicciones.sort_values(by='score', ascending=False).head(n_predicciones)
                
                for _, row in top_preds.iterrows():
                    target = row['tail_label']
                    score = row['score']
                    
                    if not self.graph.has_edge(nodo, target) and nodo != target:
                        self.graph.add_edge(nodo, target, 
                                           relation=relacion_busqueda, 
                                           origin='predicha', 
                                           weight=score)
                        self.predicted_edges.append({
                            'source': nodo,
                            'target': target,
                            'relation': relacion_busqueda,
                            'score': score
                        })
            except Exception as e:
                continue
                
        print(f"¡Proceso completado! Aristas totales: {self.graph.number_of_edges()}")
        print(f"Aristas predichas añadidas: {len(self.predicted_edges)}")
    
    def print_img(self, remove_outliers=True, img_name="extended_graph.png"):
        """
        Imprime el grafo enriquecido, diferenciando entre aristas reales y predichas.
        
        Args:
            remove_outliers (bool): Si es True, elimina nodos con grado 1 para mejor visualización.
            img_name (str): Nombre del archivo de imagen donde se guardará el grafo.
        """
        import matplotlib.pyplot as plt
        
        G_viz = self.graph.copy()
        
        if remove_outliers:
            low_degree_nodes = [node for node, degree in dict(G_viz.degree()).items() if degree <= 1]
            G_viz.remove_nodes_from(low_degree_nodes)
        
        pos = nx.spring_layout(G_viz, seed=42)
        
        plt.figure(figsize=(12, 12))
        
        nx.draw_networkx_nodes(G_viz, pos, node_size=300, node_color='lightblue')
        
        real_edges = [(u, v) for u, v, d in G_viz.edges(data=True) if d.get('origin') == 'real']
        nx.draw_networkx_edges(G_viz, pos, edgelist=real_edges, edge_color='green', label='Real', width=2)
        
        predicted_edges = [(u, v) for u, v, d in G_viz.edges(data=True) if d.get('origin') == 'predicha']
        nx.draw_networkx_edges(G_viz, pos, edgelist=predicted_edges, edge_color='red', style='dashed', label='Predicha', width=2)
        
        nx.draw_networkx_labels(G_viz, pos, font_size=10)
        
        plt.title("Grafo Enriquecido con Predicciones de Conexiones", fontsize=15)
        plt.legend(scatterpoints=1)
        plt.axis('off')
        plt.savefig(img_name)
        plt.show()
        
        
    def print_predictions(self):
        """
        Imprime las aristas que fueron predichas por el modelo.
        """
        if not self.predicted_edges:
            print("No hay aristas predichas almacenadas.")
            return
            
        print(f"\nAristas Predichas ({len(self.predicted_edges)} total):")
        print("-" * 80)
        for edge in self.predicted_edges:
            print(f"{edge['source']} --({edge['relation']}, score: {edge['score']:.4f})--> {edge['target']}")
        print("-" * 80)
    
    def get_predicted_edges_dataframe(self):
        """
        Retorna un DataFrame de pandas con las aristas predichas.
        
        Returns:
            pd.DataFrame: DataFrame con columnas 'source', 'target', 'relation', 'score'
        """
        if not self.predicted_edges:
            return pd.DataFrame(columns=['source', 'target', 'relation', 'score'])
        return pd.DataFrame(self.predicted_edges)
    
    def export_predicted_edges_img(self, remove_outliers=True, img_name="predicted_edges_only.png"):
        """
        Exporta una imagen mostrando únicamente las aristas predichas por el modelo.
        
        Args:
            remove_outliers (bool): Si es True, elimina nodos con grado 1 para mejor visualización.
            img_name (str): Nombre del archivo de imagen donde se guardará el grafo.
        """
        import matplotlib.pyplot as plt
        
        G_predicted = nx.DiGraph()
        
        for u, v, data in self.graph.edges(data=True):
            if data.get('origin') == 'predicha':
                G_predicted.add_edge(u, v, **data)
        
        if G_predicted.number_of_edges() == 0:
            print("No hay aristas predichas para visualizar.")
            return
        
        if remove_outliers:
            low_degree_nodes = [node for node, degree in dict(G_predicted.degree()).items() if degree <= 1]
            G_predicted.remove_nodes_from(low_degree_nodes)
        
        if G_predicted.number_of_nodes() == 0:
            print("No hay nodos para visualizar después de remover outliers.")
            return
        
        pos = nx.spring_layout(G_predicted, seed=42, k=2, iterations=50)
        
        plt.figure(figsize=(14, 10))
        
        nx.draw_networkx_nodes(G_predicted, pos, node_size=500, node_color='lightcoral', alpha=0.9)
        
        edges = list(G_predicted.edges(data=True))
        weights = [d.get('weight', 0.5) for _, _, d in edges]
        
        nx.draw_networkx_edges(
            G_predicted, 
            pos, 
            edge_color=weights,
            edge_cmap=plt.cm.Reds,
            width=2,
            arrows=True,
            arrowsize=20,
            arrowstyle='->',
            connectionstyle='arc3,rad=0.1'
        )
        
        nx.draw_networkx_labels(G_predicted, pos, font_size=10, font_weight='bold')
        
        edge_labels = {(u, v): f"{d.get('weight', 0):.3f}" for u, v, d in G_predicted.edges(data=True)}
        nx.draw_networkx_edge_labels(G_predicted, pos, edge_labels, font_size=8)
        
        plt.title(f"Aristas Predichas por el Modelo\n({G_predicted.number_of_edges()} conexiones predichas)", 
                  fontsize=16, fontweight='bold')
        
        sm = plt.cm.ScalarMappable(cmap=plt.cm.Reds, norm=plt.Normalize(vmin=min(weights), vmax=max(weights)))
        sm.set_array([])
        plt.colorbar(sm, label='Score de Confianza', ax=plt.gca(), shrink=0.8)
        
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(img_name, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Imagen exportada exitosamente: {img_name}")
        print(f"Nodos en el grafo: {G_predicted.number_of_nodes()}")
        print(f"Aristas predichas: {G_predicted.number_of_edges()}")
    
    def export_predicted_edges_txt(self, txt_name="predicted_edges.txt", format="detailed"):
        """
        Exporta las aristas predichas a un archivo de texto.
        
        Args:
            txt_name (str): Nombre del archivo de texto donde se guardarán las aristas.
            format (str): Formato de exportación. Opciones:
                - "detailed": Formato detallado con toda la información
                - "simple": Formato simple (source -> target)
                - "csv": Formato CSV separado por comas
                - "tsv": Formato TSV separado por tabulaciones
        """
        if not self.predicted_edges:
            print("No hay aristas predichas para exportar.")
            return
        
        try:
            with open(txt_name, 'w', encoding='utf-8') as f:
                if format == "detailed":
                    f.write("=" * 80 + "\n")
                    f.write("ARISTAS PREDICHAS POR EL MODELO\n")
                    f.write("=" * 80 + "\n")
                    f.write(f"Total de aristas predichas: {len(self.predicted_edges)}\n")
                    f.write("=" * 80 + "\n\n")
                    
                    for i, edge in enumerate(self.predicted_edges, 1):
                        f.write(f"{i}. {edge['source']} --({edge['relation']}, score: {edge['score']:.4f})--> {edge['target']}\n")
                
                elif format == "simple":
                    for edge in self.predicted_edges:
                        f.write(f"{edge['source']} -> {edge['target']}\n")
                
                elif format == "csv":
                    f.write("source,target,relation,score\n")
                    for edge in self.predicted_edges:
                        f.write(f"{edge['source']},{edge['target']},{edge['relation']},{edge['score']:.4f}\n")
                
                elif format == "tsv":
                    f.write("source\ttarget\trelation\tscore\n")
                    for edge in self.predicted_edges:
                        f.write(f"{edge['source']}\t{edge['target']}\t{edge['relation']}\t{edge['score']:.4f}\n")
                
                else:
                    print(f"Formato '{format}' no reconocido. Usando formato 'detailed'.")
                    f.write("=" * 80 + "\n")
                    f.write("ARISTAS PREDICHAS POR EL MODELO\n")
                    f.write("=" * 80 + "\n")
                    f.write(f"Total de aristas predichas: {len(self.predicted_edges)}\n")
                    f.write("=" * 80 + "\n\n")
                    
                    for i, edge in enumerate(self.predicted_edges, 1):
                        f.write(f"{i}. {edge['source']} --({edge['relation']}, score: {edge['score']:.4f})--> {edge['target']}\n")
            
            print(f"Aristas predichas exportadas exitosamente a: {txt_name}")
            print(f"Formato: {format}")
            print(f"Total de aristas: {len(self.predicted_edges)}")
        
        except Exception as e:
            print(f"Error al exportar las aristas predichas: {e}")
    
    def get_extended_graph(self):
        """
        Retorna un nuevo objeto Graph que contiene el grafo extendido con todas las aristas
        (originales + predichas).
        
        Returns:
            Graph: Nuevo objeto Graph con todas las aristas incluidas.
        """
        extended_graph_obj = Graph()
        extended_graph_obj.graph = self.graph.copy()
        return extended_graph_obj
    
    def get_predicted_graph(self):
        """
        Retorna un grafo NetworkX que contiene únicamente las aristas predichas.
        Útil para validación de solo las predicciones.
        
        Returns:
            nx.DiGraph: Grafo con solo las aristas predichas.
        """
        G_predicted = nx.DiGraph()
        
        for u, v, data in self.graph.edges(data=True):
            if data.get('origin') == 'predicha':
                G_predicted.add_edge(u, v, **data)
        
        return G_predicted
    
    def get_evaluation_metrics(self):
        """
        Retorna las métricas de evaluación del modelo.
        
        Returns:
            dict: Diccionario con las métricas de evaluación (MRR, Hits@k, etc.)
        """
        return self.evaluation_metrics
    
    def print_evaluation_metrics(self):
        """
        Imprime las métricas de evaluación del modelo de forma formateada.
        """
        if not self.evaluation_metrics:
            print("No hay métricas de evaluación disponibles. Ejecuta predict_edges() primero.")
            return
        
        print("\n" + "="*80)
        print("MÉTRICAS DE EVALUACIÓN DEL MODELO")
        print("="*80)
        for metric_name, metric_value in self.evaluation_metrics.items():
            print(f"{metric_name}: {metric_value:.4f}")
        print("="*80 + "\n")
    
    def export_evaluation_metrics_txt(self, txt_name="evaluation_metrics.txt"):
        """
        Exporta las métricas de evaluación a un archivo de texto.
        
        Args:
            txt_name (str): Nombre del archivo donde se guardarán las métricas.
        """
        if not self.evaluation_metrics:
            print("No hay métricas de evaluación disponibles. Ejecuta predict_edges() primero.")
            return
        
        try:
            with open(txt_name, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("MÉTRICAS DE EVALUACIÓN DEL MODELO\n")
                f.write("=" * 80 + "\n\n")
                
                for metric_name, metric_value in self.evaluation_metrics.items():
                    f.write(f"{metric_name}: {metric_value:.4f}\n")
                
                f.write("\n" + "=" * 80 + "\n")
                f.write("DESCRIPCIÓN DE LAS MÉTRICAS\n")
                f.write("=" * 80 + "\n\n")
                f.write("MRR (Mean Reciprocal Rank): Promedio del inverso del rango de la respuesta correcta.\n")
                f.write("  - Valores más altos son mejores (rango: 0-1)\n\n")
                f.write("Hits@k: Proporción de respuestas correctas en el top-k predicciones.\n")
                f.write("  - Valores más altos son mejores (rango: 0-1)\n\n")
                
            print(f"Métricas exportadas exitosamente a: {txt_name}")
        
        except Exception as e:
            print(f"Error al exportar las métricas: {e}")
                
    