# app.py
import streamlit as st
import pandas as pd
import networkx as nx
from pyvis.network import Network
import tempfile
import streamlit.components.v1 as components

st.set_page_config(page_title="mini drug-graph", layout="wide")
st.markdown(
    """
    <style>
    .big-title {
        font-size: 36px;
        font-weight: 700;
        margin-bottom: 0.2em;
    }
    .subtitle {
        font-size: 16px;
        color: #6b7280;
        margin-bottom: 1.5em;
    }
    .card {
        background-color: #f9fafb;
        padding: 1.2em;
        border-radius: 12px;
        margin-bottom: 1em;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="big-title">drug–drug interaction explorer</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">a simple knowledge graph to visualize known drug interactions (replicate)</div>',
    unsafe_allow_html=True
)

st.title("mini knowledge graph")

@st.cache_data
def load_data(drugs_path="drugs.csv", interactions_path="interactions.csv"):
    drugs = pd.read_csv(drugs_path, dtype=str).fillna("")
    interactions = pd.read_csv(interactions_path, dtype=str).fillna("")
    return drugs, interactions

drugs, interactions = load_data()

# helper lookups
drug_by_id = {r["id"]: r for _, r in drugs.iterrows()}
id_by_name = {r["name"].lower(): r["id"] for _, r in drugs.iterrows()}

# sidebar: search/select
st.sidebar.markdown("## 🔍 find a drug")
st.sidebar.markdown(
    """
    ---
    **how to use**
    - search or select a drug  
    - click nodes to explore  
    - view interactions below  

    *educational prototype*
    """
)

query = st.sidebar.text_input("search by name", "")
if query:
    # fuzzy-ish simple filter
    matches = [r["name"] for _, r in drugs.iterrows() if query.lower() in r["name"].lower()]
else:
    matches = list(drugs["name"].tolist())

selected_name = st.sidebar.selectbox("select a drug", ["-- none --"] + matches)
st.sidebar.markdown("---")
st.sidebar.write("data source: local CSVs")

# build graph (networkx -> pyvis)
G = nx.Graph()
for _, r in drugs.iterrows():
    G.add_node(r["id"], label=r["name"], title=f"{r['name']}<br/>{r['drug_class']}")

for _, e in interactions.iterrows():
    s = e["source"]; t = e["target"]
    if s not in drug_by_id or t not in drug_by_id:
        continue
    # weight or color by severity if you want
    G.add_edge(s, t, title=f"{e.get('type','')} ({e.get('severity','')})<br/>{e.get('notes','')}")

# generate pyvis network
nt = Network(height="650px", width="100%", notebook=False)
nt.from_nx(G)
nt.toggle_physics(True)
# nodes: show label and tooltip
for node in nt.nodes:
    did = node["id"]
    row = drug_by_id.get(did, {})
    tooltip = f"<b>{row.get('name','')}</b><br/>{row.get('drug_class','')}<br/>targets: {row.get('targets','')}"
    node["title"] = tooltip
    node["label"] = row.get("name","")

# export to temp html and embed
tmpfile = tempfile.NamedTemporaryFile(suffix=".html", delete=False)
nt.save_graph(tmpfile.name)
st.markdown("## interaction graph")
st.markdown(
    '<div class="subtitle">nodes represent drugs • edges represent known interactions</div>',
    unsafe_allow_html=True
)

components.html(
    open(tmpfile.name, "r", encoding="utf-8").read(),
    height=700
)
components.html(open(tmpfile.name, "r", encoding="utf-8").read(), height=700)

# details panel (below or right)
st.markdown("---")
st.markdown("## drug details")
st.markdown('<div class="card">', unsafe_allow_html=True)

def show_details_by_id(did):
    st.markdown('</div>', unsafe_allow_html=True)

    r = drug_by_id.get(did)
    if not r:
        st.info("pick a drug from the search box or click a node (use the dropdown for now).")
        return
        st.subheader(r["name"])

    st.markdown(f"**drug class:** {r.get('drug_class','')}")
    st.markdown(f"**primary use:** {r.get('primary_use','')}")
    st.markdown(f"**common side effects:** {r.get('common_side_effects','')}")

    # interacting partners
    related = interactions[
        (interactions["source"] == did) | (interactions["target"] == did)
    ]

    if related.empty:
        st.write("no recorded interactions in this dataset.")
    else:
        st.write("known interactions:")
        for _, row in related.iterrows():
            other = row["target"] if row["source"] == did else row["source"]
            o_name = drug_by_id.get(other, {}).get("name", other)

            st.markdown(
                f"- **{o_name}** — severity: {row.get('severity','')} — {row.get('notes','')}"
            )
