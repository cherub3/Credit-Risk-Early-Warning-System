"""
Page 5 -- Model Explainability

SHAP-based global feature importance, business interpretations,
calibration curve, model comparison, and two live worked examples
(a Low-Risk and a Critical-Risk borrower) with SHAP waterfall plots.
"""

import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import shap
import streamlit as st

from utils.data_loader import (
    load_shap_summary,
    load_shap_executive_summary,
    load_calibration_curve,
    load_calibration_metrics,
    load_model_comparison,
)
from utils.risk_engine import assign_segment, build_feature_row
from utils.shap_utils import explain_single_borrower
from utils.styling import inject_global_css, render_sidebar_branding

st.set_page_config(page_title="Model Explainability", page_icon="\U0001F9E0", layout="wide")
inject_global_css()
render_sidebar_branding()

st.title("Model Explainability")
st.caption("SHAP-based interpretation of the calibrated CatBoost credit risk model")

shap_summary = load_shap_summary()
shap_exec = load_shap_executive_summary()
calib_curve = load_calibration_curve()
calib_metrics = load_calibration_metrics()
model_comparison = load_model_comparison()

# ---------------------------------------------------------------------------
# SHAP Bar Plot (global feature importance)
# ---------------------------------------------------------------------------
st.header("Global Feature Importance (SHAP)")

if not shap_summary.empty:
    shap_sorted = shap_summary.sort_values("mean_abs_shap", ascending=True)

    direction_map = {}
    if not shap_exec.empty:
        direction_map = dict(zip(shap_exec["Feature"], shap_exec["Direction"]))

    shap_sorted["Direction"] = shap_sorted["feature"].map(direction_map).fillna("Unknown")
    color_map = {"Increases Risk": "#c0392b", "Decreases Risk": "#2980b9", "Unknown": "#7f8c8d"}

    fig = px.bar(
        shap_sorted, x="mean_abs_shap", y="feature", color="Direction",
        orientation="h", color_discrete_map=color_map,
        title="Mean |SHAP value| by Feature (Global Importance)",
        labels={"mean_abs_shap": "Mean |SHAP value|", "feature": "Feature"},
        height=600,
    )
    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("`outputs/shap_summary.csv` not found.")

st.divider()

# ---------------------------------------------------------------------------
# SHAP Executive Summary Table
# ---------------------------------------------------------------------------
st.header("SHAP Executive Summary")

if not shap_exec.empty:
    display_exec = shap_exec.copy()
    display_exec["Average Impact"] = display_exec["Average Impact"].map("{:.4f}".format)
    st.dataframe(display_exec, use_container_width=True, hide_index=True)

    st.markdown(
        """
        **Top drivers:** `sub_grade` and `loan_term_flag` are by a wide margin the two most
        influential features, together exceeding the combined impact of the next four features.
        The top six drivers (`sub_grade`, `loan_term_flag`, `fico_score`, `dti`, `int_rate`,
        `home_ownership`) all align with standard underwriting logic.
        """
    )
else:
    st.warning("`outputs/shap_executive_summary.csv` not found.")

st.divider()

# ---------------------------------------------------------------------------
# Dependence Plots (descriptive — full plots available in notebook)
# ---------------------------------------------------------------------------
st.header("Key Feature Relationships")
st.markdown(
    "The four most business-relevant SHAP dependence relationships, as derived in "
    "`notebooks/04_risk_segmentation_pricing.ipynb`:"
)

dependence_features = ["fico_score", "dti", "monthly_payment_burden", "loan_term_flag"]
if not shap_exec.empty:
    dep_cols = st.columns(2)
    for i, feat in enumerate(dependence_features):
        row = shap_exec[shap_exec["Feature"] == feat]
        with dep_cols[i % 2]:
            if not row.empty:
                r = row.iloc[0]
                st.markdown(f"**`{feat}`** -- {r['Direction']} (mean |SHAP| = {r['Average Impact']:.4f})")
                st.caption(r["Business Interpretation"])
            else:
                st.markdown(f"**`{feat}`** -- not found in SHAP executive summary.")

st.divider()

# ---------------------------------------------------------------------------
# Calibration Curve
# ---------------------------------------------------------------------------
st.header("Model Calibration")

col1, col2 = st.columns([2, 1])

with col1:
    if not calib_curve.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=calib_curve["mean_predicted_raw"], y=calib_curve["fraction_of_positives_raw"]
            if "fraction_of_positives_raw" in calib_curve.columns else calib_curve.iloc[:, 1],
            mode="lines+markers", name="Raw CatBoost", line=dict(color="#7f8c8d"),
        ))
        fig.add_trace(go.Scatter(
            x=calib_curve["mean_predicted_raw"], y=calib_curve["fraction_of_positives_calibrated"],
            mode="lines+markers", name="Calibrated CatBoost", line=dict(color="#2980b9"),
        ))
        fig.add_trace(go.Scatter(
            x=[0, 1], y=[0, 1], mode="lines", name="Perfect Calibration",
            line=dict(color="#c0392b", dash="dash"),
        ))
        fig.update_layout(
            title="Calibration Curve: Predicted vs Actual Default Rate",
            xaxis_title="Mean Predicted Probability", yaxis_title="Fraction of Positives",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("`outputs/calibration_curve_data.csv` not found.")

with col2:
    if not calib_metrics.empty:
        st.markdown("**Brier Score (lower = better)**")
        st.dataframe(calib_metrics.set_index(calib_metrics.columns[0]).loc[["Brier Score"]], use_container_width=True)
        st.success("Isotonic calibration cuts Brier Score by ~25% (0.2127 -> 0.1603) with no loss in ranking ability.")

st.divider()

# ---------------------------------------------------------------------------
# Model Comparison Table
# ---------------------------------------------------------------------------
st.header("Model Comparison")

if not model_comparison.empty:
    st.dataframe(model_comparison.set_index(model_comparison.columns[0]), use_container_width=True)
else:
    st.warning("`outputs/model_comparison.csv` not found.")

st.divider()

# ---------------------------------------------------------------------------
# Worked Examples: Low-Risk and Critical-Risk Borrowers
# ---------------------------------------------------------------------------
st.header("Worked Examples")
st.markdown("Live SHAP explanations for two representative borrower profiles.")

EXAMPLES = {
    "Low-Risk Borrower": {
        "loan_amnt": 10000, "term": 36, "int_rate": 7.0, "sub_grade": "A2",
        "fico_score": 760, "annual_inc": 95000, "dti": 8.0, "revol_util": 15.0,
        "emp_length": 10, "credit_history_years": 18.0, "home_ownership": "MORTGAGE",
        "purpose": "DEBT_CONSOLIDATION", "verification_status": "VERIFIED",
        "delinq_2yrs": 0, "pub_rec": 0,
    },
    "Critical-Risk Borrower": {
        "loan_amnt": 25000, "term": 60, "int_rate": 24.0, "sub_grade": "F2",
        "fico_score": 650, "annual_inc": 38000, "dti": 32.0, "revol_util": 95.0,
        "emp_length": 1, "credit_history_years": 4.0, "home_ownership": "RENT",
        "purpose": "SMALL_BUSINESS", "verification_status": "SOURCE VERIFIED",
        "delinq_2yrs": 1, "pub_rec": 1,
    },
}

tabs = st.tabs(list(EXAMPLES.keys()))

for tab, (label, raw) in zip(tabs, EXAMPLES.items()):
    with tab:
        from utils.data_loader import load_calibrated_model
        model = load_calibrated_model()
        if model is None:
            st.warning("Model artifact not available.")
            continue

        feature_row = build_feature_row(raw)
        pd_value = float(model.predict_proba(feature_row)[0, 1])
        segment = assign_segment(pd_value)

        st.markdown(f"**Predicted PD:** {pd_value:.2%} &nbsp;|&nbsp; **Segment:** {segment}")

        with st.spinner("Computing SHAP explanation..."):
            shap_values = explain_single_borrower(feature_row)

        if shap_values is not None:
            fig_shap, ax = plt.subplots(figsize=(9, 6))
            shap.plots.waterfall(shap_values[0], show=False)
            st.pyplot(fig_shap, use_container_width=True)
            plt.close(fig_shap)
