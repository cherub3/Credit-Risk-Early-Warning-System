"""
app.py

Entry point for the Credit Risk Early Warning & Risk-Based Loan Pricing
Engine -- a premium, dark-theme "Credit Risk Decision Platform" built on
top of the Phase D (Modeling) and Phase E (Risk Segmentation, Expected
Loss, Pricing, Stress Testing) artifacts.

Run with:
    streamlit run app/app.py
"""

import streamlit as st

from utils.styling import (
    inject_global_css,
    render_sidebar_branding,
    render_sidebar_footer,
    render_hero,
    render_flow_panel,
    kpi_card_row,
    section_header,
)

st.set_page_config(
    page_title="Credit Risk Decision Platform",
    page_icon="\U0001F3E6",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_global_css()
render_sidebar_branding()

# ---------------------------------------------------------------------------
# Hero Section
# ---------------------------------------------------------------------------
render_hero(
    title_lines=["Credit Risk Early Warning &", "Risk-Based Pricing Platform"],
    subtitle="Machine Learning Powered Credit Risk Decision System &mdash; "
             "PD Estimation, Risk Segmentation, Expected Loss & Pricing, and Stress Testing "
             "on the LendingClub (2007&ndash;2018) loan portfolio.",
)

# ---------------------------------------------------------------------------
# Headline KPI Cards
# ---------------------------------------------------------------------------
section_header("Platform at a Glance")

kpi_card_row([
    ("Loans Analysed", "1.3M+", "LendingClub 2007-2018"),
    ("ROC-AUC (Validation)", "0.712", "Calibrated CatBoost"),
    ("Calibrated Brier Score", "0.160", "-25% vs raw model"),
])

kpi_card_row([
    ("Portfolio Expected Loss", "$634.9M", "2016 validation cohort"),
    ("EL Concentration", "82%", "in High + Critical Risk segments"),
    ("Top 10% Risk Captures", "21.8% of Defaults", "from 13.4% of volume"),
])

# ---------------------------------------------------------------------------
# Executive Workflow Panel
# ---------------------------------------------------------------------------
section_header("Executive Workflow")

render_flow_panel([
    ("Problem", "Predict Default Risk"),
    ("Model", "Calibrated CatBoost"),
    ("Business Layer", "Expected Loss & Pricing"),
    ("Output", "Risk-Based Decisions"),
])

# ---------------------------------------------------------------------------
# Navigation Guide
# ---------------------------------------------------------------------------
section_header("Explore the Platform")

st.markdown(
    """
    Use the navigation menu in the sidebar to explore each module:

    - **0 &middot; Project Overview** &mdash; business problem, dataset, pipeline, and headline results
    - **1 &middot; Executive Dashboard** &mdash; portfolio-level risk, expected loss, and pricing summary
    - **2 &middot; Borrower Risk Assessment** &mdash; score a single borrower in real time (PD, segment, EL, pricing, SHAP)
    - **3 &middot; Portfolio Analytics** &mdash; segment-level deep dive with filters
    - **4 &middot; Stress Testing** &mdash; recession scenario analysis on portfolio Expected Loss
    - **5 &middot; Model Explainability** &mdash; SHAP insights and model calibration

    ---

    **Methodology at a glance:** a calibrated CatBoost model estimates each borrower's
    Probability of Default (PD). Borrowers are segmented into Low / Medium / High / Critical
    risk tiers, Expected Loss is computed as `PD x LGD x EAD`, and a risk-based recommended
    APR is derived as `Funding Cost + Expected Loss Rate + Margin`. All figures shown in this
    app are pre-computed from the 2016 validation portfolio (293,095 loans) unless otherwise noted.
    """
)

st.info("Start with **0 - Project Overview** in the sidebar for a full walkthrough of the project.")

render_sidebar_footer()
