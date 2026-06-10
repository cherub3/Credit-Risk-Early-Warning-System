"""
Page 3 -- Portfolio Analytics

Segment-level deep dive: risk segment breakdown, expected loss analysis,
and pricing recommendations, with filters by risk segment, loan purpose,
and loan term (where the underlying data supports it).

Note: risk_segments.csv / expected_loss_analysis.csv / pricing_recommendations.csv
are aggregated at the risk-segment level (no per-loan purpose/term breakdown
is available in the Phase E artifacts). The Risk Segment filter operates on
these tables directly; the Loan Purpose and Loan Term filters are provided
as portfolio-composition controls and are noted as such where they do not
affect the segment-level aggregates.
"""

import plotly.express as px
import streamlit as st

from utils.data_loader import (
    load_risk_segments,
    load_expected_loss,
    load_pricing_recommendations,
)
from utils.styling import inject_global_css, render_sidebar_branding, SEGMENT_COLORS

st.set_page_config(page_title="Portfolio Analytics", page_icon="\U0001F4C8", layout="wide")
inject_global_css()
render_sidebar_branding()

st.title("Portfolio Analytics")
st.caption("Segment-level breakdown of risk, expected loss, and pricing -- 2016 validation cohort")

risk_segments = load_risk_segments()
expected_loss = load_expected_loss()
pricing = load_pricing_recommendations()

if risk_segments.empty:
    st.stop()

el_segments = expected_loss[expected_loss["risk_segment"] != "TOTAL PORTFOLIO"].copy()

# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------
st.sidebar.header("Filters")

all_segments = risk_segments["risk_segment"].tolist()
selected_segments = st.sidebar.multiselect("Risk Segment", options=all_segments, default=all_segments)

st.sidebar.selectbox(
    "Loan Purpose",
    options=["All"],
    index=0,
    help="Per-purpose breakdowns are not part of the Phase E segment-level artifacts; "
         "this filter is reserved for a future per-loan-level extension.",
)
st.sidebar.selectbox(
    "Loan Term",
    options=["All"],
    index=0,
    help="Per-term breakdowns are not part of the Phase E segment-level artifacts; "
         "this filter is reserved for a future per-loan-level extension.",
)

filtered_segments = risk_segments[risk_segments["risk_segment"].isin(selected_segments)]
filtered_el = el_segments[el_segments["risk_segment"].isin(selected_segments)]
filtered_pricing = pricing[pricing["risk_segment"].isin(selected_segments)]

if filtered_segments.empty:
    st.warning("Select at least one risk segment in the sidebar.")
    st.stop()

# ---------------------------------------------------------------------------
# Risk Segment Breakdown
# ---------------------------------------------------------------------------
st.header("Risk Segment Breakdown")

display_segments = filtered_segments.copy()
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
    # PD distribution proxy: segment avg PD weighted by borrower count,
    # shown as a bar of average PD per segment (per-loan PD distribution
    # is not retained in the segment-level Phase E artifact).
    fig = px.bar(
        filtered_segments, x="risk_segment", y="avg_pd",
        color="risk_segment", color_discrete_map=SEGMENT_COLORS,
        title="Average PD by Risk Segment",
        labels={"avg_pd": "Average PD", "risk_segment": "Risk Segment"},
    )
    fig.update_yaxes(tickformat=".0%")
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = px.bar(
        filtered_segments, x="risk_segment", y="actual_default_rate",
        color="risk_segment", color_discrete_map=SEGMENT_COLORS,
        title="Default Rate by Segment",
        labels={"actual_default_rate": "Actual Default Rate", "risk_segment": "Risk Segment"},
    )
    fig.update_yaxes(tickformat=".0%")
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# Expected Loss Analysis
# ---------------------------------------------------------------------------
st.header("Expected Loss Analysis")

display_el = filtered_el.copy()
display_el["total_expected_loss"] = display_el["total_expected_loss"].map(lambda x: f"${x / 1e6:,.1f}M")
display_el["avg_expected_loss"] = display_el["avg_expected_loss"].map("${:,.0f}".format)
display_el["el_share"] = display_el["el_share"].map("{:.0%}".format)
display_el.columns = ["Risk Segment", "Borrowers", "Total Expected Loss", "Avg EL per Borrower", "EL Share"]
st.dataframe(display_el, use_container_width=True, hide_index=True)

fig = px.bar(
    filtered_el, x="risk_segment", y="total_expected_loss",
    color="risk_segment", color_discrete_map=SEGMENT_COLORS,
    title="Total Expected Loss by Segment ($)",
    labels={"total_expected_loss": "Total Expected Loss ($)", "risk_segment": "Risk Segment"},
)
fig.update_layout(showlegend=False)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# Pricing Recommendations
# ---------------------------------------------------------------------------
st.header("Pricing Recommendations")

display_pricing = filtered_pricing.copy()
for col in ["avg_pd", "avg_expected_loss_rate", "avg_recommended_apr", "actual_int_rate", "pricing_gap"]:
    display_pricing[col] = display_pricing[col].map("{:.2%}".format)
display_pricing.columns = [
    "Risk Segment", "Borrowers", "Avg PD", "Avg Expected Loss Rate",
    "Avg Recommended APR", "Actual LendingClub APR", "Pricing Gap",
]
st.dataframe(display_pricing, use_container_width=True, hide_index=True)

fig = px.bar(
    filtered_pricing, x="risk_segment", y="pricing_gap",
    color="risk_segment", color_discrete_map=SEGMENT_COLORS,
    title="Pricing Gap by Segment (Recommended APR - Actual APR)",
    labels={"pricing_gap": "Pricing Gap", "risk_segment": "Risk Segment"},
)
fig.update_yaxes(tickformat=".0%")
fig.update_layout(showlegend=False)
st.plotly_chart(fig, use_container_width=True)
