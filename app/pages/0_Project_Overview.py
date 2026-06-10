"""
Page 0 -- Project Overview

Gives a recruiter a complete understanding of the project in under 60 seconds:
business problem, dataset, modeling pipeline, risk segmentation framework,
and headline results.
"""

import streamlit as st

from utils.styling import inject_global_css, render_sidebar_branding, kpi_card_row, flatten_html

st.set_page_config(page_title="Project Overview", page_icon="\U0001F4CB", layout="wide")
inject_global_css()
render_sidebar_branding()

st.title("Project Overview")
st.caption("Credit Risk Early Warning & Risk-Based Loan Pricing Engine")

# ---------------------------------------------------------------------------
# Business Problem
# ---------------------------------------------------------------------------
st.header("Business Problem")
st.markdown(
    """
    Consumer lenders price and approve loans largely on rule-based credit grades.
    This project builds a **calibrated, explainable Probability-of-Default (PD) model**
    on the LendingClub accepted-loans dataset (2007-2018) and turns it into a full
    **risk-based decisioning workflow**: risk segmentation, expected loss estimation,
    risk-based pricing, and macroeconomic stress testing -- the same building blocks
    used in a bank's credit risk and pricing functions.
    """
)

# ---------------------------------------------------------------------------
# Dataset Overview
# ---------------------------------------------------------------------------
st.header("Dataset Overview")
col1, col2 = st.columns(2)
with col1:
    st.markdown(
        """
        - **Source:** LendingClub accepted loans, 2007-2018
        - **Target:** `loan_status` -- Fully Paid (0) vs Charged Off (1)
        - **Split methodology:** strict time-based (out-of-time) split
        """
    )
with col2:
    st.markdown(
        """
        | Split | Years | Loans | Default Rate |
        |---|---|---|---|
        | Train | 2007-2015 | 826,604 | 18.43% |
        | Validation | 2016 | 293,095 | 23.28% |
        | Test | 2017-2018 | 225,611 | 21.28% |
        """
    )

# ---------------------------------------------------------------------------
# Modeling Pipeline / Workflow Diagram
# ---------------------------------------------------------------------------
st.header("Modeling Pipeline")

st.markdown(
    flatten_html("""
    <div style="display:flex; flex-direction:column; align-items:center; gap:4px; padding:10px 0;">
        <div class="flow-box">Raw Data (LendingClub 2007-2018)</div>
        <div class="flow-arrow">&#8595;</div>
        <div class="flow-box">Preprocessing (cleaning, encoding, time-based split)</div>
        <div class="flow-arrow">&#8595;</div>
        <div class="flow-box">Feature Engineering (19 governed features)</div>
        <div class="flow-arrow">&#8595;</div>
        <div class="flow-box">Credit Risk Model (Logistic Regression + CatBoost)</div>
        <div class="flow-arrow">&#8595;</div>
        <div class="flow-box">Calibration (Isotonic, CalibratedClassifierCV)</div>
        <div class="flow-arrow">&#8595;</div>
        <div class="flow-box">Risk Segmentation (Low / Medium / High / Critical)</div>
        <div class="flow-arrow">&#8595;</div>
        <div class="flow-box">Expected Loss (PD x LGD x EAD)</div>
        <div class="flow-arrow">&#8595;</div>
        <div class="flow-box">Risk-Based Pricing Engine</div>
        <div class="flow-arrow">&#8595;</div>
        <div class="flow-box">Stress Testing (Mild / Severe Recession)</div>
    </div>
    <style>
    .flow-box {
        background-color: #ffffff;
        border: 2px solid #0f3057;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: 600;
        color: #0f3057;
        text-align: center;
        min-width: 360px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    .flow-arrow {
        font-size: 1.4em;
        color: #00b4d8;
        font-weight: 700;
    }
    </style>
    """),
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Risk Segmentation Framework
# ---------------------------------------------------------------------------
st.header("Risk Segmentation Framework")
st.markdown(
    """
    | Segment | PD Range | Recommended Action |
    |---|---|---|
    | **Low Risk** | PD < 10% | Auto Approve |
    | **Medium Risk** | 10% &le; PD < 20% | Standard Approval |
    | **High Risk** | 20% &le; PD < 35% | Manual Review |
    | **Critical Risk** | PD &ge; 35% | Decline / Reprice |
    """
)

# ---------------------------------------------------------------------------
# Key Results (KPI cards)
# ---------------------------------------------------------------------------
st.header("Key Results")

kpi_card_row([
    ("Loans Analysed", "1.3M+", None),
    ("ROC-AUC (Validation)", "0.712", None),
    ("Calibrated Brier Score", "0.160", "-25% vs raw"),
])

kpi_card_row([
    ("Portfolio Expected Loss", "$634.9M", None),
    ("High + Critical Risk Share of EL", "82%", None),
    ("Top 10% Risk Borrowers", "21.8% of defaults captured", None),
])

st.markdown(
    """
    ---
    **Read more:**
    - [`outputs/phase_d_results_summary.md`](../outputs/phase_d_results_summary.md) -- full modeling results
    - [`outputs/phase_e_executive_summary.md`](../outputs/phase_e_executive_summary.md) -- full risk/pricing results
    """
)
