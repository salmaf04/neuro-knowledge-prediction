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

def refactor_notebook():
    path = "src/time_travel_experiment.ipynb"
    if not os.path.exists(path):
        print(f"Skipping {path} (not found)")
        return

    nb = load_notebook(path)
    cells = nb['cells']
    
    # Search for the cell with "ROLLING ANALYSIS WITH CACHING" to identify the loop cell
    # It contains "if sorted_years and len(sorted_years) > 3:"
    target_index = -1
    for i, cell in enumerate(cells):
        source = "".join(cell.get('source', []))
        if "ROLLING ANALYSIS WITH CACHING" in source and "sorted_years" in source:
            target_index = i
            break
            
    if target_index == -1:
        print("Could not find the 'Routing Analysis' cell to replace.")
        return

    print(f"Found target cell at index {target_index}. Replacing with Robust Loop...")

    # New Robust Logic
    new_source_code = [
        "# ==========================================",
        "# 5. ROBUST STATISTICAL ANALYSIS (Repeated Experiments)",
        "# ==========================================",
        "",
        "import numpy as np",
        "from collections import defaultdict",
        "import pandas as pd",
        "import matplotlib.pyplot as plt",
        "",
        "def run_robust_rolling_analysis(n_iterations=10):",
        "    print(f\"\\n🔄 ROBUST ROLLING ANALYSIS (N={n_iterations} iterations per year)\")",
        "    print(\"=\"*60)",
        "    ",
        "    if not sorted_years or len(sorted_years) <= 3:",
        "        print(\"Not enough years of data.\")",
        "        return",
        "",
        "    years_to_scan = [y for y in sorted_years if y > sorted_years[2] and y < sorted_years[-1]]",
        "    cumulative_docs = []",
        "    ",
        "    # Pre-fill cumulative docs up to start year",
        "    for y in sorted_years:",
        "        if y < years_to_scan[0]: cumulative_docs.extend(docs_by_year[y])",
        "",
        "    results_by_year = defaultdict(list)",
        "    detailed_stats = []",
        "",
        "    for year in years_to_scan:",
        "        print(f\"\\n📅 Analyzing Year: {year}\")",
        "        cumulative_docs.extend(docs_by_year[year])",
        "        ",
        "        future_docs = []",
        "        for fy in sorted_years:",
        "            if fy > year: future_docs.extend(docs_by_year[fy])",
        "        if not future_docs: break",
        "        ",
        "        # Build Graph Once per Year (Deterministic part: static graph)",
        "        G_now = build_graph_from_texts(cumulative_docs, ner_pipeline, nlp)",
        "        G_future = build_graph_from_texts(future_docs, ner_pipeline, nlp)",
        "        future_edges = set([frozenset([u,v]) for u,v in G_future.edges()])",
        "        ",
        "        # Run N Iterations of Training (Stochastic part: GCN init & dropout)",
        "        year_accuracies = []",
        "        print(f\"   Running {n_iterations} experiments... \", end=\"\")",
        "        for i in range(n_iterations):",
        "            # Train model",
        "            # Note: train_and_predict re-initializes model layers each call",
        "            preds = train_and_predict(G_now, top_k=200)",
        "            ",
        "            # Evaluate",
        "            hit_count = 0",
        "            for u, v, score in preds:",
        "                if frozenset([u,v]) in future_edges: hit_count += 1",
        "            ",
        "            accuracy = hit_count / 200 if preds else 0",
        "            year_accuracies.append(accuracy)",
        "            print(\".\", end=\"\")",
        "        ",
        "        mean_acc = np.mean(year_accuracies)",
        "        std_acc = np.std(year_accuracies)",
        "        results_by_year[year] = year_accuracies",
        "        ",
        "        print(f\" DONE\")",
        "        print(f\"   ✅ Year {year} Summary: Mean Acc = {mean_acc:.2%} ± {std_acc:.2%}\")",
        "        ",
        "        detailed_stats.append({",
        "            \"Year\": year,",
        "            \"Mean_Accuracy\": mean_acc,",
        "            \"Std_Dev\": std_acc,",
        "            \"Min\": np.min(year_accuracies),",
        "            \"Max\": np.max(year_accuracies),",
        "            \"Samples\": n_iterations",
        "        })",
        "",
        "    # Statistical Report",
        "    print(\"\\n\" + \"=\"*60)",
        "    print(\"📊 STATISTICAL SUMMARY REPORT\")",
        "    print(\"=\"*60)",
        "    df_stats = pd.DataFrame(detailed_stats)",
        "    display(df_stats)",
        "    ",
        "    # Plot with Error Bars",
        "    plt.figure(figsize=(12, 6))",
        "    plt.errorbar(df_stats['Year'], df_stats['Mean_Accuracy'], yerr=df_stats['Std_Dev'], ",
        "                 fmt='-o', ecolor='red', capsize=5, label='Model Accuracy (Mean ± Std)')",
        "    plt.title(f'Temporal Prediction Accuracy (N={n_iterations} runs)')",
        "    plt.xlabel('Year')",
        "    plt.ylabel('Validation Rate (Top-200)')",
        "    plt.grid(True, alpha=0.3)",
        "    plt.legend()",
        "    plt.show()",
        "    ",
        "    return results_by_year",
        "",
        "# Run the robust analysis",
        "# You can change n_iterations to 20 or 30 for final paper results",
        "robust_results = run_robust_rolling_analysis(n_iterations=10)"
    ]

    # Replace the cell
    cells[target_index] = create_code_cell(new_source_code)
    
    # Save
    nb['cells'] = cells
    save_notebook(path, nb)
    print(f"Successfully refactored {path}")

if __name__ == "__main__":
    refactor_notebook()
