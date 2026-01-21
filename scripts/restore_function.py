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

def restore_function():
    path = "src/time_travel_experiment.ipynb"
    if not os.path.exists(path):
        print(f"Skipping {path} (not found)")
        return

    nb = load_notebook(path)
    cells = nb['cells']
    
    # Search for the "ROBUST STATISTICAL ANALYSIS" cell
    target_index = -1
    for i, cell in enumerate(cells):
        source = "".join(cell.get('source', []))
        if "ROBUST STATISTICAL ANALYSIS" in source:
            target_index = i
            break
            
    if target_index == -1:
        print("Could not find the 'ROBUST STATISTICAL ANALYSIS' cell.")
        return

    print(f"Found target cell at index {target_index}. Prepending train_and_predict...")

    # The missing function code
    train_func_code = [
        "# ==========================================",
        "# 4. TRAIN & PREDICT HELPER (Restored)",
        "# ==========================================",
        "",
        "def train_and_predict(G_train, top_k=50):",
        "    data, node_to_idx, idx_to_node = prepare_gcn_data(G_train)",
        "    if data is None: return []",
        "    ",
        "    # Safety check for very small graphs",
        "    if data.num_nodes < 5 or data.edge_index.size(1) < 5:",
        "        return []",
        "    ",
        "    try:",
        "        transform = RandomLinkSplit(num_val=0.1, num_test=0.1, is_undirected=True, add_negative_train_samples=False)",
        "        train_data, val_data, test_data = transform(data)",
        "    except Exception as e:",
        "        return []",
        "    ",
        "    model = GCNLinkPredictor(128, 256, 128)",
        "    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)",
        "    criterion = FocalLoss(alpha=1, gamma=2)",
        "    ",
        "    # Training loop",
        "    for epoch in range(100):",
        "        model.train()",
        "        optimizer.zero_grad()",
        "        z = model.encode(train_data.x, train_data.edge_index)",
        "        ",
        "        neg_edge_index = torch.randint(0, data.num_nodes, (2, train_data.edge_label_index.size(1)))",
        "        edge_label_index = torch.cat([train_data.edge_label_index, neg_edge_index], dim=1)",
        "        edge_label = torch.cat([train_data.edge_label, torch.zeros(neg_edge_index.size(1))], dim=0)",
        "        ",
        "        out = model.decode(z, edge_label_index)",
        "        loss = criterion(out, edge_label)",
        "        loss.backward()",
        "        optimizer.step()",
        "        ",
        "    model.eval()",
        "    with torch.no_grad():",
        "        z = model.encode(data.x, data.edge_index)",
        "        predictions = []",
        "        ",
        "        nodes = list(G_train.nodes())",
        "        # Predict for top degree nodes to speed up demonstration",
        "        top_nodes = sorted(nodes, key=lambda n: G_train.degree(n), reverse=True)[:200]",
        "        ",
        "        for i, u in enumerate(top_nodes):",
        "             for v in top_nodes[i+1:]:",
        "                if not G_train.has_edge(u, v):",
        "                    idx_u, idx_v = node_to_idx[u], node_to_idx[v]",
        "                    score = (z[idx_u] * z[idx_v]).sum().item()",
        "                    predictions.append((u, v, score))",
        "    ",
        "    predictions.sort(key=lambda x: x[2], reverse=True)",
        "    return predictions[:top_k]"
    ]

    # Insert a new cell before the robust analysis cell
    new_cell = create_code_cell(train_func_code)
    cells.insert(target_index, new_cell)
    
    # Save
    nb['cells'] = cells
    save_notebook(path, nb)
    print(f"Successfully restored functions in {path}")

if __name__ == "__main__":
    restore_function()
