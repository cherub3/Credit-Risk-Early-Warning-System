"""
shap_utils.py

SHAP explainability helpers for the Borrower Risk Assessment page.
Builds a TreeExplainer once (cached) on the raw CatBoost model and
computes a live SHAP explanation for a single borrower row.
"""

import shap
import streamlit as st
from catboost import Pool

from utils.data_loader import load_raw_catboost_model
from utils.risk_engine import CAT_FEATURE_NAMES, FINAL_MODEL_FEATURES


@st.cache_resource
def get_explainer():
    """Build (and cache) a SHAP TreeExplainer on the raw CatBoost model."""
    model = load_raw_catboost_model()
    if model is None:
        return None
    return shap.TreeExplainer(model)


def explain_single_borrower(feature_row):
    """
    Compute SHAP values for a single-row DataFrame of FINAL_MODEL_FEATURES.

    Returns a shap.Explanation object with `.data` and `.feature_names`
    correctly set so it can be passed directly to shap.plots.waterfall.
    """
    explainer = get_explainer()
    if explainer is None:
        return None

    cat_indices = [FINAL_MODEL_FEATURES.index(c) for c in CAT_FEATURE_NAMES]
    pool = Pool(feature_row, cat_features=cat_indices)

    shap_values = explainer(pool)

    # Pool objects are not subscriptable -- attach the raw values/feature
    # names so downstream plotting (waterfall) works correctly.
    shap_values.data = feature_row.values
    shap_values.feature_names = list(feature_row.columns)

    return shap_values
