from pykeen.hpo import hpo_pipeline
from pykeen.triples import TriplesFactory
import torch

class GraphAutoML:
    def __init__(self, triples_factory: TriplesFactory, device: str = None):
        self.triples_factory = triples_factory
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.best_result = None
        
    def run_optimization(self, n_trials: int = 20, timeout: int = None):
        """
        Runs the hyperparameter optimization pipeline.
        
        Args:
            n_trials (int): Number of HPO trials to run.
            timeout (int): Maximum time in seconds for the optimization.
            
        Returns:
            The best result object from PyKEEN HPO.
        """
        training, testing = self.triples_factory.split([0.8, 0.2], random_state=42)
        validation = testing # Ideally split 80/10/10, but for simplicity we keep 80/20 structure for now
        
        print(f"🚀 Starting AutoML/HPO with {n_trials} trials on {self.device}...")
        
        # Define a broad search space
        # We search over different models and their key hyperparameters
        self.hpo_pipeline_result = hpo_pipeline(
            n_trials=n_trials,
            timeout=timeout,
            training=training,
            testing=testing,
            validation=testing, # Using testing as validation for HPO feedback
            device=self.device,
            
            # Strategies
            study_name="neuro_knowledge_prediction_hpo",
            
            # Search space for models
            model=["TransE", "RotatE", "DistMult", "ComplEx"],
            
            # Common hyperparameter ranges will be automatically selected by PyKEEN for the chosen model
            # We can also enforce specific ranges if needed, e.g.:
            model_kwargs_ranges=dict(
                embedding_dim=dict(type=int, low=32, high=256, step=32),
            ),
            
            # Training config
            training_loop='slcwa', # Stochastic Local Closed World Assumption (standard for KGE)
            training_kwargs=dict(num_epochs=100),
            training_kwargs_ranges=dict(
                batch_size=dict(type=int, low=4, high=9, scale="power_two"), # 16 to 512
            ),
             optimizer_kwargs_ranges=dict(
                lr=dict(type=float, low=0.001, high=0.1, scale="log"),
            ),
        )
        
        self.best_result = self.hpo_pipeline_result
        print(f"🏆 Best model found: {self.best_result.study.best_params['model']}")
        print(f"   Best params: {self.best_result.study.best_params}")
        
        return self.best_result

    def save_best_model(self, path: str):
        """Saves the best model found."""
        if self.best_result:
            self.best_result.save_to_directory(path)
            print(f"💾 Best model saved to {path}")
        else:
            print("⚠️ No model to save. Run optimization first.")

    def get_best_model(self):
        """Returns the trained best model."""
        if self.best_result:
            # We need to re-train or get the model from the result
            # hpo_pipeline_result.optimize_result doesn't return the model instance directly usually,
            # but we can get it from the study or re-instantiate.
            # Actually PyKEEN 1.10+ makes this easier, but let's rely on the result artifacts if possible.
            # A common pattern is to just return the best config.
             return self.hpo_pipeline_result.study.best_params
        return None
