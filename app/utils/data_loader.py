"""
data_loader.py

Centralized, cached loaders for all Phase D / Phase E artifacts.
Every page in the app must import its data through this module —
no page should read a CSV or pickle directly.

Path resolution:
    app/utils/data_loader.py
        parents[0] -> app/utils
        parents[1] -> app
        parents[2] -> project root (contains models/ and outputs/)
"""

from pathlib import Path

import joblib
import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
MODELS_DIR = PROJECT_ROOT / "models"


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------
def _read_csv(filename: str) -> pd.DataFrame:
    path = OUTPUTS_DIR / filename
    if not path.exists():
        st.error(f"Missing artifact: `{path}`. Re-run the corresponding notebook to regenerate it.")
        return pd.DataFrame()
    return pd.read_csv(path)


# ---------------------------------------------------------------------------
# Phase E artifacts (cached as data — small, static CSVs)
# ---------------------------------------------------------------------------
@st.cache_data
def load_risk_segments() -> pd.DataFrame:
    return _read_csv("risk_segments.csv")


@st.cache_data
def load_expected_loss() -> pd.DataFrame:
    return _read_csv("expected_loss_analysis.csv")


@st.cache_data
def load_pricing_recommendations() -> pd.DataFrame:
    return _read_csv("pricing_recommendations.csv")


@st.cache_data
def load_stress_test_results() -> pd.DataFrame:
    return _read_csv("stress_test_results.csv")


@st.cache_data
def load_shap_summary() -> pd.DataFrame:
    return _read_csv("shap_summary.csv")


@st.cache_data
def load_shap_executive_summary() -> pd.DataFrame:
    return _read_csv("shap_executive_summary.csv")


@st.cache_data
def load_top_risk_analysis() -> pd.DataFrame:
    return _read_csv("top_risk_analysis.csv")


# ---------------------------------------------------------------------------
# Phase D artifacts
# ---------------------------------------------------------------------------
@st.cache_data
def load_model_metrics() -> pd.DataFrame:
    return _read_csv("model_metrics.csv")


@st.cache_data
def load_model_comparison() -> pd.DataFrame:
    return _read_csv("model_comparison.csv")


@st.cache_data
def load_calibration_metrics() -> pd.DataFrame:
    return _read_csv("calibration_metrics.csv")


@st.cache_data
def load_calibration_curve() -> pd.DataFrame:
    return _read_csv("calibration_curve_data.csv")


@st.cache_data
def load_business_impact_summary() -> pd.DataFrame:
    return _read_csv("business_impact_summary.csv")


@st.cache_data
def load_feature_summary() -> pd.DataFrame:
    return _read_csv("feature_summary.csv")


# ---------------------------------------------------------------------------
# Models (cached as resources — must not be re-pickled per session)
# ---------------------------------------------------------------------------
@st.cache_resource
def load_calibrated_model():
    """Load the calibrated CatBoost model (CalibratedClassifierCV)."""
    path = MODELS_DIR / "calibrated_catboost.pkl"
    if not path.exists():
        st.error(f"Missing model artifact: `{path}`.")
        return None
    return joblib.load(path)


@st.cache_resource
def load_raw_catboost_model():
    """
    Extract the underlying raw CatBoostClassifier from inside the
    calibrated model wrapper (CalibratedClassifierCV -> FrozenEstimator
    -> CatBoostClassifier). Used for SHAP explanations.
    """
    calibrated = load_calibrated_model()
    if calibrated is None:
        return None
    frozen_estimator = calibrated.calibrated_classifiers_[0].estimator
    return frozen_estimator.estimator


# ---------------------------------------------------------------------------
# Markdown summaries (for the Project Overview / About sections)
# ---------------------------------------------------------------------------
@st.cache_data
def load_markdown(filename: str) -> str:
    path = OUTPUTS_DIR / filename
    if not path.exists():
        return f"*Missing file: {filename}*"
    return path.read_text(encoding="utf-8")
