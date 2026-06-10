"""
Page 4 -- Stress Testing

Shows the pre-computed Phase E stress scenarios (Base, Mild Recession,
Severe Recession) and allows the user to apply a custom PD multiplier,
recomputed live from segment-level PD/EAD using the same
EL = PD x multiplier x LGD x EAD formula.
"""

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.data_loader import load_risk_segments, load_stress_test_results
from utils.risk_engine import stress_test_segment_el
from utils.styling import inject_global_css, render_sidebar_branding, kpi_card_row, SEGMENT_COLORS

st.set_page_config(page_title="Stress Testing", page_icon="\U0001F30A", layout="wide")
inject_global_css()
render_sidebar_branding()

st.title("Stress Testing")
st.caption("Portfolio Expected Loss under macroeconomic stress scenarios")

risk_segments = load_risk_segments()
stress_results = load_stress_test_results()

if risk_segments.empty or stress_results.empty:
    st.stop()

base_el = float(stress_results.loc[stress_results["Scenario"] == "Base Case", "Portfolio Expected Loss"].iloc[0])

# ---------------------------------------------------------------------------
# Pre-computed Scenarios
# ---------------------------------------------------------------------------
st.header("Pre-Computed Scenarios")

display_stress = stress_results.copy()
display_stress["Portfolio Expected Loss"] = display_stress["Portfolio Expected Loss"].map(lambda x: f"${x / 1e6:,.1f}M")
display_stress["Change vs Base (%)"] = display_stress["Change vs Base (%)"].map("{:+.1f}%".format)
st.dataframe(display_stress, use_container_width=True, hide_index=True)

kpi_card_row([
    (row["Scenario"], f"${row['Portfolio Expected Loss'] / 1e6:,.1f}M",
     None if row["Scenario"] == "Base Case" else f"{row['Change vs Base (%)']:+.1f}%")
    for _, row in stress_results.iterrows()
])

col1, col2 = st.columns(2)

with col1:
    fig = px.bar(
        stress_results, x="Scenario", y="Portfolio Expected Loss",
        title="Portfolio Expected Loss by Scenario",
        labels={"Portfolio Expected Loss": "Portfolio Expected Loss ($)"},
        color="Scenario",
        color_discrete_sequence=["#2980b9", "#f39c12", "#c0392b"],
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # EL increase waterfall: Base -> Mild -> Severe
    fig = go.Figure(go.Waterfall(
        orientation="v",
        measure=["absolute", "relative", "relative"],
        x=["Base Case", "Mild Recession (+30%)", "Severe Recession (+70%)"],
        y=[
            stress_results.loc[stress_results["Scenario"] == "Base Case", "Portfolio Expected Loss"].iloc[0],
            stress_results.loc[stress_results["Scenario"] == "Mild Recession", "Portfolio Expected Loss"].iloc[0]
            - stress_results.loc[stress_results["Scenario"] == "Base Case", "Portfolio Expected Loss"].iloc[0],
            stress_results.loc[stress_results["Scenario"] == "Severe Recession", "Portfolio Expected Loss"].iloc[0]
            - stress_results.loc[stress_results["Scenario"] == "Mild Recession", "Portfolio Expected Loss"].iloc[0],
        ],
        connector={"line": {"color": "#7f8c8d"}},
        increasing={"marker": {"color": "#c0392b"}},
        totals={"marker": {"color": "#2980b9"}},
    ))
    fig.update_layout(title="Expected Loss Increase: Base -> Mild -> Severe")
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# Custom PD Multiplier
# ---------------------------------------------------------------------------
st.header("Custom Stress Scenario")
st.markdown(
    "Apply a custom PD multiplier to every risk segment and recompute Expected Loss "
    "using `EL = PD x multiplier x LGD (60%) x EAD`, capped at PD = 100%."
)

multiplier = st.slider("Custom PD Multiplier", min_value=1.0, max_value=2.5, value=1.0, step=0.05)

stressed = stress_test_segment_el(risk_segments, multiplier)
custom_total_el = stressed["stressed_el"].sum()
change_vs_base = (custom_total_el - base_el) / base_el * 100

kpi_card_row([
    ("Custom Scenario Portfolio EL", f"${custom_total_el / 1e6:,.1f}M", None),
    ("Change vs Base Case", f"{change_vs_base:+.1f}%", None),
    ("PD Multiplier Applied", f"{multiplier:.2f}x", None),
])

# Segment Contribution under custom scenario
display_stressed = stressed[["risk_segment", "borrower_count", "stressed_pd", "stressed_el"]].copy()
display_stressed["stressed_pd"] = display_stressed["stressed_pd"].map("{:.2%}".format)
display_stressed["stressed_el"] = display_stressed["stressed_el"].map(lambda x: f"${x / 1e6:,.1f}M")
display_stressed.columns = ["Risk Segment", "Borrowers", "Stressed PD", "Stressed Expected Loss"]
st.dataframe(display_stressed, use_container_width=True, hide_index=True)

fig = px.bar(
    stressed, x="risk_segment", y="stressed_el",
    color="risk_segment", color_discrete_map=SEGMENT_COLORS,
    title=f"Segment Contribution to Expected Loss at {multiplier:.2f}x PD Multiplier",
    labels={"stressed_el": "Stressed Expected Loss ($)", "risk_segment": "Risk Segment"},
)
fig.update_layout(showlegend=False)
st.plotly_chart(fig, use_container_width=True)

st.caption(
    "Note: the custom scenario is computed from segment-level average PD and average loan amount, "
    "and will closely approximate -- but not exactly reproduce -- the per-loan figures in the "
    "pre-computed Base Case ($634.9M) due to aggregation."
)
