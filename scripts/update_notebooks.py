import json
import os

def load_notebook(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_notebook(path, nb):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1)

def create_code_cell(source_lines):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + "\n" for line in source_lines]
    }

def create_markdown_cell(source_lines):
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in source_lines]
    }

def update_time_travel_experiment():
    path = "src/time_travel_experiment.ipynb"
    if not os.path.exists(path):
        print(f"Skipping {path} (not found)")
        return

    nb = load_notebook(path)
    
    # 1. Add Statistics Cell
    stats_header = create_markdown_cell(["# 📊 Statistical Significance Code\n", "We calculate the P-value to verify if our model is truly better than random chance."])
    
    stats_code = create_code_cell([
        "from statistics import calculate_p_value",
        "import numpy as np",
        "",
        "# Example usage after model training loop",
        "# Assuming 'auc_scores' contains the model's AUC for each year",
        "# and we simulate a baseline distribution",
        "",
        "def run_significance_test(model_score, n_permutations=100):",
        "    print(f'Testing significance for score: {model_score:.4f}...')",
        "    # In a real simplified baseline, random chance for link prediction is often low",
        "    # Here simulating a random distribution centered around 0.5 (random guess in balanced) or lower in unbalanced",
        "    baseline = np.random.normal(0.5, 0.05, n_permutations)",
        "    p_val = calculate_p_value(model_score, baseline)",
        "    print(f'  P-value: {p_val:.6f}')",
        "    return p_val",
        "",
        "# Uncomment to test:",
        "# run_significance_test(0.85)"
    ])
    
    nb['cells'].append(stats_header)
    nb['cells'].append(stats_code)
    
    save_notebook(path, nb)
    print(f"Updated {path}")

def update_project_notebook():
    path = "src/Project.ipynb"
    if not os.path.exists(path):
        print(f"Skipping {path} (not found)")
        return

    nb = load_notebook(path)
    
    # 1. Add AutoML Cell
    automl_header = create_markdown_cell(["# 🧠 AutoML & Hyperparameter Optimization\n", "Automatically find the best Knowledge Graph Embedding model."])
    
    automl_code = create_code_cell([
        "from extended_graph import ExtendedGraph",
        "from automl import GraphAutoML",
        "from pykeen.triples import TriplesFactory",
        "import pandas as pd",
        "import torch",
        "",
        "# Assuming G is your NetworkX graph from previous cells",
        "# ext_g = ExtendedGraph(G) # Wrap it",
        "",
        "def run_automl_demo(graph_nx):",
        "    print('Preparing graph for AutoML...')",
        "    triples_list = []",
        "    for u, v, data in graph_nx.edges(data=True):",
        "        rel = data.get('relation', 'related_to')",
        "        triples_list.append([str(u), str(rel), str(v)])",
        "    ",
        "    df = pd.DataFrame(triples_list, columns=['head', 'time', 'tail']) # relation col middle",
        "    tf = TriplesFactory.from_labeled_triples(df[['head', 'time', 'tail']].values)",
        "    ",
        "    automl = GraphAutoML(tf)",
        "    best_result = automl.run_optimization(n_trials=5) # Low trials for demo",
        "    return best_result",
        "",
        "# Uncomment to run:",
        "# best = run_automl_demo(G)"
    ])
    
    nb['cells'].append(automl_header)
    nb['cells'].append(automl_code)
    
    save_notebook(path, nb)
    print(f"Updated {path}")

if __name__ == "__main__":
    update_time_travel_experiment()
    update_project_notebook()
