"""
Page 2 -- Borrower Risk Assessment (flagship page)

Lets the user enter RAW borrower information. All engineered features
(monthly_payment_burden, income_to_loan_ratio, credit_stress_score, etc.)
are derived internally via utils/risk_engine.py, which mirrors
src/features.py exactly. The calibrated CatBoost model then produces a
live PD, risk segment, recommended action, Expected Loss, recommended
APR, pricing gap, and a SHAP waterfall explanation.
"""

import matplotlib.pyplot as plt
import plotly.graph_objects as go
import shap
import streamlit as st

from utils.data_loader import load_calibrated_model, load_risk_segments
from utils.risk_engine import (
    HOME_OWNERSHIP_OPTIONS,
    PURPOSE_OPTIONS,
    SUBGRADE_OPTIONS,
    VERIFICATION_OPTIONS,
    assign_segment,
    build_feature_row,
    expected_loss,
    pricing_gap,
    recommended_apr,
    recommended_action,
)
from utils.shap_utils import explain_single_borrower
from utils.styling import (
    COLOR_DANGER,
    COLOR_SUCCESS,
    COLOR_WARNING,
    inject_global_css,
    render_sidebar_branding,
    segment_badge_html,
    SEGMENT_COLORS,
)

st.set_page_config(page_title="Borrower Risk Assessment", page_icon="\U0001F50D", layout="wide")
inject_global_css()
render_sidebar_branding()

st.title("Borrower Risk Assessment")
st.caption("Enter raw borrower information. All credit-risk features are engineered automatically.")

model = load_calibrated_model()
risk_segments = load_risk_segments()

# ---------------------------------------------------------------------------
# Input Form
# ---------------------------------------------------------------------------
st.header("Borrower Information")

with st.form("borrower_form"):
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Loan Details")
        loan_amnt = st.number_input("Loan Amount ($)", min_value=1000, max_value=40000, value=15000, step=500)
        term = st.selectbox("Term (months)", options=[36, 60], index=0)
        int_rate = st.slider("Interest Rate (%)", min_value=5.0, max_value=31.0, value=13.0, step=0.1)
        sub_grade = st.selectbox("LendingClub Sub-Grade", options=SUBGRADE_OPTIONS, index=SUBGRADE_OPTIONS.index("B3"))
        purpose = st.selectbox("Loan Purpose", options=PURPOSE_OPTIONS, index=0)

    with col2:
        st.subheader("Income & Affordability")
        annual_inc = st.number_input("Annual Income ($)", min_value=10000, max_value=500000, value=65000, step=1000)
        dti = st.slider("Debt-to-Income Ratio (DTI, %)", min_value=0.0, max_value=50.0, value=18.0, step=0.5)
        emp_length = st.slider("Employment Length (years, 10 = 10+)", min_value=0, max_value=10, value=5)
        verification_status = st.selectbox("Income Verification Status", options=VERIFICATION_OPTIONS, index=0)
        home_ownership = st.selectbox("Home Ownership", options=HOME_OWNERSHIP_OPTIONS, index=2)

    with col3:
        st.subheader("Credit Bureau Profile")
        fico_score = st.slider("FICO Score", min_value=600, max_value=850, value=690, step=1)
        revol_util = st.slider("Revolving Credit Utilization (%)", min_value=0.0, max_value=150.0, value=45.0, step=1.0)
        credit_history_years = st.slider("Credit History Length (years)", min_value=0.0, max_value=50.0, value=10.0, step=0.5)
        has_delinquency = st.checkbox("Delinquency in last 2 years?")
        has_public_record = st.checkbox("Any public derogatory record?")

    submitted = st.form_submit_button("Calculate Risk", type="primary", use_container_width=True)

# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------
if submitted:
    if model is None:
        st.error("Model artifact not available -- cannot score borrower.")
        st.stop()

    raw_input = {
        "loan_amnt": loan_amnt,
        "term": term,
        "int_rate": int_rate,
        "sub_grade": sub_grade,
        "fico_score": fico_score,
        "annual_inc": annual_inc,
        "dti": dti,
        "revol_util": revol_util,
        "emp_length": emp_length,
        "credit_history_years": credit_history_years,
        "home_ownership": home_ownership,
        "purpose": purpose,
        "verification_status": verification_status,
        "delinq_2yrs": 1 if has_delinquency else 0,
        "pub_rec": 1 if has_public_record else 0,
    }

    feature_row = build_feature_row(raw_input)

    pd_value = float(model.predict_proba(feature_row)[0, 1])
    segment = assign_segment(pd_value)
    action = recommended_action(segment)
    el_value = expected_loss(pd_value, loan_amnt)
    apr_recommended = recommended_apr(pd_value)
    actual_apr = int_rate / 100
    gap = pricing_gap(apr_recommended, actual_apr)

    st.divider()
    st.header("Risk Assessment Results")

    # --- Top row: PD gauge + segment badge -------------------------------
    col_gauge, col_badge = st.columns([2, 1])

    with col_gauge:
        gauge_color = COLOR_SUCCESS
        if segment == "Medium Risk":
            gauge_color = COLOR_WARNING
        elif segment in ("High Risk", "Critical Risk"):
            gauge_color = COLOR_DANGER

        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=pd_value * 100,
            number={"suffix": "%"},
            title={"text": "Probability of Default (PD)"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": gauge_color},
                "steps": [
                    {"range": [0, 10], "color": "#d4efdf"},
                    {"range": [10, 20], "color": "#fdebd0"},
                    {"range": [20, 35], "color": "#fad7a0"},
                    {"range": [35, 100], "color": "#f5b7b1"},
                ],
            },
        ))
        fig.update_layout(height=300, margin=dict(t=50, b=10, l=30, r=30))
        st.plotly_chart(fig, use_container_width=True)

    with col_badge:
        st.markdown("<br/>", unsafe_allow_html=True)
        st.markdown(segment_badge_html(segment), unsafe_allow_html=True)

    # --- Metric row ---------------------------------------------------------
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Probability of Default", f"{pd_value:.2%}")
    m2.metric("Expected Loss", f"${el_value:,.0f}")
    m3.metric("Recommended APR", f"{apr_recommended:.2%}")
    m4.metric("Pricing Gap vs Input Rate", f"{gap:+.2%}")

    st.markdown(f"**Recommended Action:** {action}")

    # --- Comparison vs segment averages -------------------------------------
    if not risk_segments.empty:
        seg_row = risk_segments[risk_segments["risk_segment"] == segment]
        if not seg_row.empty:
            seg_row = seg_row.iloc[0]
            st.subheader(f"This Borrower vs. {segment} Segment Average")
            comp_col1, comp_col2, comp_col3 = st.columns(3)
            comp_col1.metric("Borrower PD", f"{pd_value:.2%}", f"{(pd_value - seg_row['avg_pd']):+.2%} vs segment avg")
            comp_col2.metric("Borrower Loan Amount", f"${loan_amnt:,.0f}", f"${loan_amnt - seg_row['avg_loan_amnt']:+,.0f} vs segment avg")
            comp_col3.metric("Borrower Interest Rate", f"{int_rate:.2f}%", f"{(int_rate - seg_row['avg_int_rate']):+.2f} pp vs segment avg")

    # --- SHAP waterfall --------------------------------------------------
    st.divider()
    st.subheader("Why this prediction? (SHAP Explanation)")

    with st.spinner("Computing SHAP explanation..."):
        shap_values = explain_single_borrower(feature_row)

    if shap_values is not None:
        fig_shap, ax = plt.subplots(figsize=(9, 6))
        shap.plots.waterfall(shap_values[0], show=False)
        st.pyplot(fig_shap, use_container_width=True)
        plt.close(fig_shap)
        st.caption(
            "Positive (red) bars push the predicted PD higher; negative (blue) bars push it lower. "
            "`E[f(x)]` is the model's average prediction across the training population."
        )
    else:
        st.warning("SHAP explainer unavailable.")

else:
    st.info("Fill in the borrower information above and click **Calculate Risk** to generate an assessment.")
