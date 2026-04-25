import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="Healthcare Financial Risk Dashboard", layout="wide")

BASE_DIR = Path(__file__).resolve().parent
REPO_DIR = BASE_DIR.parent

@st.cache_data
def load_data():
    DATA_PATH_1 = BASE_DIR / "final_dashboard_data_agg.parquet"
    DATA_PATH_2 = REPO_DIR / "final_dashboard_data_agg.parquet"
    if DATA_PATH_1.exists():
        return pd.read_parquet(DATA_PATH_1)
    elif DATA_PATH_2.exists():
        return pd.read_parquet(DATA_PATH_2)
    return None

df = load_data()

if df is None:
    st.error("Parquet file not found.")
    st.stop()

st.sidebar.header("Filters")

selected_drg = st.sidebar.selectbox(
    "Procedure",
    sorted(df["drg_definition"].dropna().unique())
)

# All rows for this procedure
drg_df = df[df["drg_definition"] == selected_drg]

state_options = sorted(drg_df["provider_state"].dropna().unique())
selected_state = st.sidebar.selectbox("State", state_options)

# All rows for this procedure + state (used for peer avg, chart, table)
state_df = drg_df[drg_df["provider_state"] == selected_state]

provider_options = sorted(state_df["provider_name"].dropna().unique())
selected_provider = st.sidebar.selectbox("Provider", provider_options)

# Only selected provider (used for risk score and provider charge)
provider_data = state_df[state_df["provider_name"] == selected_provider].iloc[0]

# Peer avg = all OTHER providers in same state+procedure
peer_avg = state_df[state_df["provider_name"] != selected_provider]["average_covered_charges"].mean()

# -----------------------
# Risk color
# -----------------------
def get_color(label):
    return {
        "Low": "#2e7d32",
        "Guarded": "#f9a825",
        "Elevated": "#ef6c00",
        "High": "#c62828"
    }.get(label, "black")

color = get_color(provider_data["risk_label"])

# -----------------------
# Layout
# -----------------------
st.title("Healthcare Financial Risk Dashboard")

col1, col2 = st.columns(2)

with col1:
    st.subheader(provider_data["provider_name"])
    st.write(f"Procedure: {selected_drg}")
    st.markdown(
        f"<h1 style='color:{color};'>Risk Score: {provider_data['risk_score']:.1f} ({provider_data['risk_label']})</h1>",
        unsafe_allow_html=True
    )

with col2:
    st.metric("Provider Charge", f"${provider_data['average_covered_charges']:,.0f}")
    st.metric("Peer Average", f"${peer_avg:,.0f}")

# -----------------------
# Cost chart — shows ALL providers in state, highlights selected
# -----------------------
st.subheader("Cost Comparison")

chart_df = state_df[["provider_name", "average_covered_charges"]].copy()
chart_df = chart_df.sort_values("average_covered_charges")
chart_df = chart_df.set_index("provider_name")
st.bar_chart(chart_df)

# -----------------------
# Explanation
# -----------------------
st.subheader("Explanation")
reasons = []
if provider_data["provider_risk_index"] > 0.7:
    reasons.append("Provider shows high historical billing risk")
if provider_data["state_risk_index"] > 0.7:
    reasons.append("Region has higher-than-average cost patterns")
if provider_data["average_covered_charges"] > peer_avg:
    reasons.append("Charges are above peer average")
if not reasons:
    reasons.append("Costs are within expected range")
for r in reasons:
    st.write(f"- {r}")

# -----------------------
# Alternatives — ALL providers in state sorted by risk
# -----------------------
st.subheader("Lower Risk Alternatives")
alt_df = (
    state_df
    .sort_values(["risk_score", "average_covered_charges"])
    .drop_duplicates(subset="provider_name")
    .head(5)
)[["provider_name", "risk_score", "average_covered_charges"]].reset_index(drop=True)

st.dataframe(alt_df)

st.markdown("---")
st.write("This tool estimates financial risk using provider billing patterns and regional comparisons based on Medicare data.")
