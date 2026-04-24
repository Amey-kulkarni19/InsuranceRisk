import streamlit as st
import pandas as pd
from pathlib import path

st.set_page_config(page_title="Healthcare Financial Risk Dashboard", layout="wide")

# -----------------------
# Load Data
# -----------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "final_dashboard_data.parquet"

@st.cache_data
def load_data():
    return pd.read_parquet(DATA_PATH)

df = load_data()

# -----------------------
# Sidebar filters
# -----------------------
st.sidebar.header("Filters")

selected_drg = st.sidebar.selectbox(
    "Procedure",
    sorted(df["drg_definition"].dropna().unique())
)

filtered_df = df[df["drg_definition"] == selected_drg]

selected_state = st.sidebar.selectbox(
    "State",
    sorted(filtered_df["provider_state"].dropna().unique())
)

filtered_df = filtered_df[filtered_df["provider_state"] == selected_state]

selected_provider = st.sidebar.selectbox(
    "Provider",
    sorted(filtered_df["provider_name"].dropna().unique())
)

provider_data = filtered_df[
    filtered_df["provider_name"] == selected_provider
].iloc[0]

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

# -----------------------
# Risk score display
# -----------------------
with col1:
    st.subheader(provider_data["provider_name"])
    st.write(f"Procedure: {selected_drg}")

    st.markdown(
        f"""
        <h1 style='color:{color};'>
        Risk Score: {provider_data['risk_score']:.1f} ({provider_data['risk_label']})
        </h1>
        """,
        unsafe_allow_html=True
    )

# -----------------------
# Cost comparison
# -----------------------
with col2:
    peer_avg = filtered_df["average_covered_charges"].mean()

    st.metric(
        "Provider Charge",
        f"${provider_data['average_covered_charges']:,.0f}"
    )

    st.metric(
        "Peer Average",
        f"${peer_avg:,.0f}"
    )

# -----------------------
# Cost chart
# -----------------------
st.subheader("Cost Comparison")

chart_df = pd.DataFrame({
    "Category": ["Provider", "Peer Average"],
    "Cost": [
        provider_data["average_covered_charges"],
        peer_avg
    ]
})

st.bar_chart(chart_df.set_index("Category"))

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
# Alternatives
# -----------------------
st.subheader("Lower Risk Alternatives")

# alt_df = filtered_df.sort_values("risk_score").head(5)
alt_df = (
    filtered_df
    .sort_values(["risk_score", "average_covered_charges"])
    .drop_duplicates(subset="provider_name")
    .head(5)
)

alt_df_display = alt_df.reset_index(drop=True)

st.dataframe(alt_df_display[[
    "provider_name",
    "risk_score",
    "average_covered_charges"
]])

# -----------------------
# Footer
# -----------------------
st.markdown("---")
st.write(
    "This tool estimates financial risk using provider billing patterns and regional comparisons based on Medicare data."
)
