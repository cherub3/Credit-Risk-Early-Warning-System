"""
Page 1 -- Executive Dashboard

Portfolio-level summary of risk segmentation, expected loss, and pricing,
built entirely from Phase E artifacts.
"""

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.data_loader import (
    load_risk_segments,
    load_expected_loss,
    load_pricing_recommendations,
)
from utils.styling import (
    inject_global_css,
    render_sidebar_branding,
    kpi_card_row,
    SEGMENT_COLORS,
)

st.set_page_config(page_title="Executive Dashboard", page_icon="\U0001F4CA", layout="wide")
inject_global_css()
render_sidebar_branding()

st.title("Executive Dashboard")
st.caption("Portfolio risk, expected loss, and pricing summary -- 2016 validation cohort (293,095 loans)")

risk_segments = load_risk_segments()
expected_loss = load_expected_loss()
pricing = load_pricing_recommendations()

if risk_segments.empty or expected_loss.empty or pricing.empty:
    st.stop()

total_borrowers = int(risk_segments["borrower_count"].sum())
portfolio_default_rate = (
    risk_segments["actual_default_rate"] * risk_segments["borrower_count"]
).sum() / total_borrowers

el_total_row = expected_loss[expected_loss["risk_segment"] == "TOTAL PORTFOLIO"]
total_el = float(el_total_row["total_expected_loss"].iloc[0]) if not el_total_row.empty else expected_loss["total_expected_loss"].sum()

high_critical_el_share = expected_loss.loc[
    expected_loss["risk_segment"].isin(["High Risk", "Critical Risk"]), "el_share"
].sum()

avg_pricing_gap = (pricing["pricing_gap"] * pricing["borrower_count"]).sum() / pricing["borrower_count"].sum()

# ---------------------------------------------------------------------------
# Portfolio Summary
# ---------------------------------------------------------------------------
st.header("Portfolio Summary")
kpi_card_row([
    ("Total Borrowers", f"{total_borrowers:,}", None),
    ("Portfolio Default Rate", f"{portfolio_default_rate:.2%}", None),
    ("Total Expected Loss", f"${total_el / 1e6:,.1f}M", None),
    ("Avg. Pricing Gap", f"+{avg_pricing_gap:.2%}", None),
])

st.divider()

# ---------------------------------------------------------------------------
# Risk Segment Summary
# ---------------------------------------------------------------------------
st.header("Risk Segment Summary")

display_segments = risk_segments.copy()
display_segments["portfolio_share"] = display_segments["portfolio_share"].map("{:.1%}".format)
display_segments["actual_default_rate"] = display_segments["actual_default_rate"].map("{:.2%}".format)
display_segments["avg_pd"] = display_segments["avg_pd"].map("{:.2%}".format)
display_segments["avg_loan_amnt"] = display_segments["avg_loan_amnt"].map("${:,.0f}".format)
display_segments["avg_int_rate"] = display_segments["avg_int_rate"].map("{:.2f}%".format)
display_segments.columns = [
    "Risk Segment", "Borrowers", "Portfolio Share", "Actual Default Rate",
    "Avg PD", "Avg Loan Amount", "Avg Interest Rate",
]
st.dataframe(display_segments, use_container_width=True, hide_index=True)

col1, col2 = st.columns(2)
with col1:
    fig = px.bar(
        risk_segments, x="risk_segment", y="portfolio_share",
        color="risk_segment", color_discrete_map=SEGMENT_COLORS,
        title="Portfolio Share by Risk Segment",
        labels={"portfolio_share": "Portfolio Share", "risk_segment": "Risk Segment"},
    )
    fig.update_yaxes(tickformat=".0%")
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = px.bar(
        risk_segments, x="risk_segment", y="actual_default_rate",
        color="risk_segment", color_discrete_map=SEGMENT_COLORS,
        title="Default Rate by Risk Segment",
        labels={"actual_default_rate": "Actual Default Rate", "risk_segment": "Risk Segment"},
    )
    fig.update_yaxes(tickformat=".0%")
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# Expected Loss Summary
# ---------------------------------------------------------------------------
st.header("Expected Loss Summary")

el_segments = expected_loss[expected_loss["risk_segment"] != "TOTAL PORTFOLIO"].copy()

display_el = el_segments.copy()
display_el["total_expected_loss"] = display_el["total_expected_loss"].map(lambda x: f"${x / 1e6:,.1f}M")
display_el["avg_expected_loss"] = display_el["avg_expected_loss"].map("${:,.0f}".format)
display_el["el_share"] = display_el["el_share"].map("{:.0%}".format)
display_el.columns = ["Risk Segment", "Borrowers", "Total Expected Loss", "Avg EL per Borrower", "EL Share"]
st.dataframe(display_el, use_container_width=True, hide_index=True)

col1, col2 = st.columns(2)
with col1:
    fig = px.bar(
        el_segments, x="risk_segment", y="el_share",
        color="risk_segment", color_discrete_map=SEGMENT_COLORS,
        title="Expected Loss Share by Risk Segment",
        labels={"el_share": "EL Share", "risk_segment": "Risk Segment"},
    )
    fig.update_yaxes(tickformat=".0%")
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Portfolio Share vs EL Share -- core concentration visualization
    concentration = risk_segments[["risk_segment", "portfolio_share"]].merge(
        el_segments[["risk_segment", "el_share"]], on="risk_segment"
    )
    fig = go.Figure()
    fig.add_bar(
        x=concentration["risk_segment"], y=concentration["portfolio_share"],
        name="Portfolio Share", marker_color="#2980b9",
    )
    fig.add_bar(
        x=concentration["risk_segment"], y=concentration["el_share"],
        name="Expected Loss Share", marker_color="#c0392b",
    )
    fig.update_layout(
        title="Portfolio Share vs Expected Loss Share",
        barmode="group", yaxis_tickformat=".0%",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig, use_container_width=True)

st.info(
    f"**Risk concentration:** High + Critical Risk borrowers represent "
    f"{risk_segments.loc[risk_segments['risk_segment'].isin(['High Risk', 'Critical Risk']), 'portfolio_share'].sum():.0%} "
    f"of portfolio volume but **{high_critical_el_share:.0%} of total Expected Loss**."
)

st.divider()

# ---------------------------------------------------------------------------
# Pricing Summary
# ---------------------------------------------------------------------------
st.header("Pricing Summary")

display_pricing = pricing.copy()
for col in ["avg_pd", "avg_expected_loss_rate", "avg_recommended_apr", "actual_int_rate", "pricing_gap"]:
    display_pricing[col] = display_pricing[col].map("{:.2%}".format)
display_pricing.columns = [
    "Risk Segment", "Borrowers", "Avg PD", "Avg Expected Loss Rate",
    "Avg Recommended APR", "Actual LendingClub APR", "Pricing Gap",
]
st.dataframe(display_pricing, use_container_width=True, hide_index=True)

fig = go.Figure()
fig.add_bar(x=pricing["risk_segment"], y=pricing["actual_int_rate"], name="Actual LendingClub APR", marker_color="#2980b9")
fig.add_bar(x=pricing["risk_segment"], y=pricing["avg_recommended_apr"], name="Recommended APR", marker_color="#c0392b")
fig.update_layout(
    title="Actual vs Recommended APR by Risk Segment",
    barmode="group", yaxis_tickformat=".0%",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)
st.plotly_chart(fig, use_container_width=True)
