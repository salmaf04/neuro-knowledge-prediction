import streamlit as st
import pandas as pd
import networkx as nx
import pickle
import json
from pathlib import Path
from pyvis.network import Network
import streamlit.components.v1 as components

# Page Config
st.set_page_config(page_title="Time-Travel Graph Explorer", layout="wide")

# Paths
# Resolve paths relative to THIS script file
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent
CACHE_DIR = PROJECT_ROOT / "cache"

PREDS_PATH = CACHE_DIR / "predictions_history.csv"
YEAR_MAP_PATH = CACHE_DIR / "year_map.json"
GRAPH_DIR = CACHE_DIR / "graphs"

@st.cache_data
def load_metadata():
    if not PREDS_PATH.exists() or not YEAR_MAP_PATH.exists():
        return None, None
    
    df = pd.read_csv(PREDS_PATH)
    with open(YEAR_MAP_PATH, "r") as f:
        year_map = json.load(f)
    return df, year_map

@st.cache_resource
def load_graph(year, year_map):
    if str(year) not in year_map:
        return None
    
    graph_hash = year_map[str(year)]
    graph_path = GRAPH_DIR / f"graph_{graph_hash}.pkl"
    
    if graph_path.exists():
        with open(graph_path, "rb") as f:
            return pickle.load(f)
    return None

def build_pyvis_network(G, predictions_df, current_year, search_term=""):
    net = Network(height="600px", width="100%", bgcolor="#222222", font_color="white")
    
    # OPTIMIZATION: Smart Subgraphing
    # If no search term, ONLY show the top 100 "Hub" nodes (most connected) to avoid lagging the browser
    if not search_term:
        # Sort nodes by degree
        top_nodes = sorted(G.degree, key=lambda x: x[1], reverse=True)[:50]
        nodes_to_keep = {n for n, d in top_nodes}
        
        # Also include nodes involved in Top 10 Predictions (so they don't disappear)
        current_preds = predictions_df[predictions_df['Training_Year'] == current_year]
        top_preds = current_preds.sort_values(by="Score", ascending=False).head(10)
        for _, row in top_preds.iterrows():
            nodes_to_keep.add(row['Source'])
            nodes_to_keep.add(row['Target'])
            
        G = G.subgraph(list(nodes_to_keep))
        st.info(f"Showing 'Hub View' (Top {len(G.nodes())} nodes). Search for specific terms to see more details.")

    # Filter subgraph if search term exists
    else:
        search_term = search_term.lower()
        nodes_to_keep = {n for n in G.nodes() if search_term in n.lower()}
        
        # Add neighbors of matches to provide context
        neighbors = set()
        for n in nodes_to_keep:
            neighbors.update(G.neighbors(n))
        nodes_to_keep.update(neighbors)
        
        if not nodes_to_keep:
            return None
        
        G = G.subgraph(list(nodes_to_keep))

    # Add nodes
    # OPTIMIZATION: Scale node size by degree
    degrees = dict(G.degree())
    for node in G.nodes():
        size = 10 + (degrees.get(node, 1) * 2) # Dynamic size
        net.add_node(node, label=node, title=f"{node} (Degree: {degrees.get(node, 0)})", color="#97C2FC", size=size)

    # Add existing edges (Blue)
    for u, v in G.edges():
        net.add_edge(u, v, color="#2B7CE9", width=1)
    
    # Add PREDICTED edges for this year (Red Dashed)
    current_preds = predictions_df[predictions_df['Training_Year'] == current_year]
    top_preds = current_preds.sort_values(by="Score", ascending=False).head(50) # Show top 50 predictions
    
    for _, row in top_preds.iterrows():
        u, v = row['Source'], row['Target']
        # Only add if nodes exist in current subgraph view
        if u in G.nodes() and v in G.nodes():
             net.add_edge(u, v, color="#FF0000", width=3, title=f"Prediction Score: {row['Score']:.2f}", dashes=True)

    # Add VALIDATED edges (Green)
    past_preds = predictions_df[(predictions_df['Training_Year'] < current_year) & (predictions_df['Verified_Later'] == True)]
    verified_pairs = set()
    for _, row in past_preds.iterrows():
        pair = tuple(sorted([row['Source'], row['Target']]))
        verified_pairs.add(pair)
        
    for edge in net.edges:
        u, v = edge['from'], edge['to']
        pair = tuple(sorted([u, v]))
        if pair in verified_pairs and edge.get('color') != "#FF0000": 
            edge['color'] = "#00FF00" # Green for verified
            edge['width'] = 4
            edge['title'] = "Verified Prediction!"

    # OPTIMIZATION: Physics vs BarnsHut
    net.barnes_hut(gravity=-8000, central_gravity=0.3, spring_length=250, spring_strength=0.001, damping=0.09, overlap=0)
    return net

# ==========================================
# MAIN APP UI
# ==========================================

st.title("🕰️ Time-Travel Knowledge Graph Explorer")

df, year_map = load_metadata()

if df is None:
    st.error("❌ Data not found. Please run the notebook 'time_travel_experiment.ipynb' first to generate predictions and graphs.")
    st.stop()

# Sidebar Controls
st.sidebar.header("Controls")
available_years = sorted([int(y) for y in year_map.keys()])
selected_year = st.sidebar.select_slider("Select Year", options=available_years, value=available_years[0])

search_term = st.sidebar.text_input("Search Node (e.g., 'prolactina')", "")

# Main Content
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader(f"Graph State: {selected_year}")
    
    G = load_graph(selected_year, year_map)
    if G:
        net = build_pyvis_network(G, df, selected_year, search_term)
        if net:
            path = "graph.html"
            net.save_graph(path)
            with open(path, 'r', encoding='utf-8') as f:
                html_string = f.read()
            components.html(html_string, height=600, scrolling=True)
        else:
            st.warning(f"No nodes found matching '{search_term}' in {selected_year}.")
    else:
        st.error(f"Graph for {selected_year} not found in cache.")

with col2:
    st.subheader(f"Top Predictions ({selected_year})")
    current_preds = df[df['Training_Year'] == selected_year].sort_values(by="Score", ascending=False).head(20)
    
    for _, row in current_preds.iterrows():
        verified_icon = "✅" if row['Verified_Later'] else "⏳"
        st.markdown(f"**{row['Source']} -- {row['Target']}**")
        st.caption(f"Score: {row['Score']:.1f} | {verified_icon}")
        st.divider()

st.markdown("---")
st.markdown("**Legend**: 🔵 Existing Link | 🔴 Predicted Link (Model Guess) | 🟢 Validated Link (Past Prediction confirmed)")
