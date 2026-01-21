import networkx as nx
import sys
import os
import unittest
import numpy as np
from unittest.mock import MagicMock, patch

# Add src and root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, '..', 'src')
root_path = os.path.join(current_dir, '..')
sys.path.insert(0, src_path)
sys.path.insert(0, root_path)

from statistics import calculate_p_value
from automl import GraphAutoML
from extended_graph import ExtendedGraph

class TestFeatures(unittest.TestCase):
    
    def test_p_value(self):
        print("\nTesting P-value calculation...")
        model_score = 0.9
        # Need at least 19 samples to get p <= 0.05
        baseline_scores = [0.1] * 20 
        p = calculate_p_value(model_score, baseline_scores)
        self.assertLessEqual(p, 0.05)
        
        model_score_bad = 0.05
        baseline_scores_better = [0.9] * 20
        p_bad = calculate_p_value(model_score_bad, baseline_scores_better)
        self.assertGreater(p_bad, 0.05)
        print("✅ P-value test passed")

    @patch('automl.hpo_pipeline')
    def test_automl_mock(self, mock_hpo):
        print("\nTesting AutoML wrapper (Mock)...")
        mock_result = MagicMock()
        mock_result.study.best_params = {'model': 'TransE', 'embedding_dim': 50}
        mock_hpo.return_value = mock_result
        
        # Helper to create a dummy triples factory
        from pykeen.triples import TriplesFactory
        import numpy as np
        # Need enough triples for 80/20 split simulation (though we mock split)
        triples = np.array([
            ['a', 'r', 'b'], ['b', 'r', 'c'], ['c', 'r', 'd'], ['d', 'r', 'e'],
            ['e', 'r', 'f'], ['f', 'r', 'g']
        ])
        tf = TriplesFactory.from_labeled_triples(triples)
        # Mock split to avoid PyKEEN strict coverage checks
        tf.split = MagicMock(return_value=(MagicMock(), MagicMock()))
        
        automl = GraphAutoML(tf)
        result = automl.run_optimization(n_trials=1)
        
        self.assertEqual(result.study.best_params['model'], 'TransE')
        print("✅ AutoML mock test passed")

    def test_extended_graph_integration_mock(self):
        print("\nTesting ExtendedGraph integration (Mock)...")
        # Create a small graph
        g = nx.Graph()
        for i in range(10):
            g.add_edge(f"N{i}", f"N{i+1}", relation="rel")
        
        class MockGraphWrapper:
            def __init__(self, nx_graph):
                self.graph = nx_graph
                
        base_graph_wrapper = MockGraphWrapper(g)
        ext_graph = ExtendedGraph(base_graph_wrapper)
        
        # Mock pipeline to avoid actual training
        with patch('extended_graph.pipeline') as mock_pipeline:
            # Setup mock pipeline return
            mock_pipeline.return_value.metric_results.to_flat_dict.return_value = {'hits@10': 0.5}
            mock_pipeline.return_value.model = MagicMock()
            
            # Mock TriplesFactory in extended_graph to avoid split error
            with patch('extended_graph.TriplesFactory') as mock_tf_class:
                 mock_tf_instance = mock_tf_class.from_labeled_triples.return_value
                 # Mock split return values
                 mock_tf_instance.split.return_value = (MagicMock(), MagicMock())
            
                 # Mock GraphAutoML inside extended_graph
                 with patch('extended_graph.GraphAutoML') as mock_automl_class:
                      mock_automl_instance = mock_automl_class.return_value
                      # Set the return of run_optimization
                      mock_automl_instance.run_optimization.return_value.study.best_params = {'model': 'RotatE'}
                      
                      # Run with optimization
                      ext_graph.predict_edges(optimize=True, epochs=1)
                      
                      # Check if AutoML was instanced and called
                      mock_automl_class.assert_called()
                      mock_automl_instance.run_optimization.assert_called()
                      print("✅ ExtendedGraph optimization call verified")

if __name__ == '__main__':
    unittest.main()
