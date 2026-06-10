"""
risk_engine.py

Business logic shared across the Credit Risk Decision Platform:
    - converts raw borrower inputs into the 19 FINAL_MODEL_FEATURES
      using the exact same formulas as src/features.py
    - maps a PD to a risk segment and recommended action
      (locked thresholds from Phase E)
    - computes Expected Loss and Risk-Based Pricing for a single loan

This module intentionally mirrors src/features.py and the Phase E
notebook so the live app produces numbers consistent with the
pre-computed Phase D/E artifacts.
"""

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Locked constants (from Phase E)
# ---------------------------------------------------------------------------
LGD = 0.60                  # Loss Given Default (fixed)
FUNDING_COST = 0.04         # Annual funding cost
TARGET_MARGIN = 0.03        # Target margin

# Risk segmentation bands (locked, Phase E)
PD_BAND_LOW = 0.10
PD_BAND_MEDIUM = 0.20
PD_BAND_HIGH = 0.35

SEGMENT_ACTIONS = {
    "Low Risk": "Auto Approve",
    "Medium Risk": "Standard Approval",
    "High Risk": "Manual Review",
    "Critical Risk": "Decline / Reprice",
}

# Feature engineering thresholds (must match src/features.py)
HIGH_UTILIZATION_THRESHOLD = 75.0

# Ordinal sub_grade encoding (A1=1 ... G5=35), matches src/preprocessing.py
_GRADES = ["A", "B", "C", "D", "E", "F", "G"]
SUBGRADE_MAP = {}
_rank = 1
for _g in _GRADES:
    for _n in range(1, 6):
        SUBGRADE_MAP[f"{_g}{_n}"] = _rank
        _rank += 1

# Final feature order required by the trained CatBoost model
FINAL_MODEL_FEATURES = [
    "loan_amnt",
    "int_rate",
    "sub_grade",
    "fico_score",
    "annual_inc",
    "dti",
    "revol_util",
    "emp_length",
    "credit_history_years",
    "home_ownership",
    "purpose",
    "verification_status",
    "monthly_payment_burden",
    "income_to_loan_ratio",
    "credit_stress_score",
    "delinquency_flag",
    "pub_rec_flag",
    "loan_term_flag",
    "high_utilization_flag",
]

CAT_FEATURE_NAMES = ["home_ownership", "purpose", "verification_status"]

HOME_OWNERSHIP_OPTIONS = ["RENT", "OWN", "MORTGAGE", "OTHER"]

PURPOSE_OPTIONS = [
    "DEBT_CONSOLIDATION", "CREDIT_CARD", "HOME_IMPROVEMENT", "OTHER",
    "MAJOR_PURCHASE", "SMALL_BUSINESS", "CAR", "MEDICAL", "MOVING",
    "VACATION", "HOUSE", "WEDDING", "RENEWABLE_ENERGY", "EDUCATIONAL",
]

VERIFICATION_OPTIONS = ["VERIFIED", "SOURCE VERIFIED", "NOT VERIFIED"]

SUBGRADE_OPTIONS = list(SUBGRADE_MAP.keys())


def _calculate_installment(loan_amnt: float, int_rate: float, term_months: int) -> float:
    """
    Standard amortizing-loan monthly payment formula.

    installment = P * r * (1+r)^n / ((1+r)^n - 1)

    Used to derive monthly_payment_burden, since the user supplies
    loan_amnt/term/int_rate rather than a pre-computed installment.
    """
    monthly_rate = (int_rate / 100) / 12
    n = term_months
    if monthly_rate == 0:
        return loan_amnt / n
    factor = (1 + monthly_rate) ** n
    return loan_amnt * monthly_rate * factor / (factor - 1)


def build_feature_row(raw: dict) -> pd.DataFrame:
    """
    Convert a dict of RAW borrower inputs into a single-row DataFrame
    with the 19 FINAL_MODEL_FEATURES, in the exact order/dtypes the
    CatBoost model expects.

    Expected keys in `raw`:
        loan_amnt, term (36 or 60), sub_grade (e.g. 'B3'), fico_score,
        annual_inc, dti, revol_util, emp_length (0-10),
        credit_history_years, home_ownership, purpose,
        verification_status, int_rate, delinq_2yrs (>=0),
        pub_rec (>=0)
    """
    loan_amnt = float(raw["loan_amnt"])
    term = int(raw["term"])
    int_rate = float(raw["int_rate"])
    annual_inc = float(raw["annual_inc"])

    installment = _calculate_installment(loan_amnt, int_rate, term)

    # --- engineered features (mirrors src/features.py) -------------------
    income_to_loan_ratio = annual_inc / loan_amnt if loan_amnt else np.nan

    monthly_income = annual_inc / 12
    monthly_payment_burden = installment / monthly_income if monthly_income else np.nan
    monthly_payment_burden = min(monthly_payment_burden, 1.0)

    revol_util = float(raw["revol_util"])
    dti = float(raw["dti"])
    credit_stress_score = dti * (revol_util / 100)

    delinquency_flag = int(raw.get("delinq_2yrs", 0) > 0)
    pub_rec_flag = int(raw.get("pub_rec", 0) > 0)
    loan_term_flag = int(term == 60)
    high_utilization_flag = int(revol_util > HIGH_UTILIZATION_THRESHOLD)

    sub_grade_encoded = SUBGRADE_MAP[raw["sub_grade"]]

    row = {
        "loan_amnt": loan_amnt,
        "int_rate": int_rate,
        "sub_grade": sub_grade_encoded,
        "fico_score": float(raw["fico_score"]),
        "annual_inc": annual_inc,
        "dti": dti,
        "revol_util": revol_util,
        "emp_length": int(raw["emp_length"]),
        "credit_history_years": float(raw["credit_history_years"]),
        "home_ownership": str(raw["home_ownership"]).upper(),
        "purpose": str(raw["purpose"]).upper(),
        "verification_status": str(raw["verification_status"]).upper(),
        "monthly_payment_burden": monthly_payment_burden,
        "income_to_loan_ratio": income_to_loan_ratio,
        "credit_stress_score": credit_stress_score,
        "delinquency_flag": delinquency_flag,
        "pub_rec_flag": pub_rec_flag,
        "loan_term_flag": loan_term_flag,
        "high_utilization_flag": high_utilization_flag,
    }

    df = pd.DataFrame([row])[FINAL_MODEL_FEATURES]

    # CatBoost categorical columns must be strings
    for col in CAT_FEATURE_NAMES:
        df[col] = df[col].astype(str)

    return df


def assign_segment(pd_value: float) -> str:
    """Map a PD to a risk segment using the Phase E locked bands."""
    if pd_value < PD_BAND_LOW:
        return "Low Risk"
    if pd_value < PD_BAND_MEDIUM:
        return "Medium Risk"
    if pd_value < PD_BAND_HIGH:
        return "High Risk"
    return "Critical Risk"


def recommended_action(segment: str) -> str:
    return SEGMENT_ACTIONS.get(segment, "Manual Review")


def expected_loss(pd_value: float, loan_amnt: float, lgd: float = LGD) -> float:
    """Expected Loss = PD * LGD * EAD."""
    return pd_value * lgd * loan_amnt


def recommended_apr(pd_value: float, lgd: float = LGD,
                     funding_cost: float = FUNDING_COST,
                     margin: float = TARGET_MARGIN) -> float:
    """Recommended APR = Funding Cost + Expected Loss Rate (PD x LGD) + Margin."""
    return funding_cost + (pd_value * lgd) + margin


def pricing_gap(recommended: float, actual: float) -> float:
    return recommended - actual


def stress_test_segment_el(risk_segments: pd.DataFrame, multiplier: float) -> pd.DataFrame:
    """
    Recompute segment-level Expected Loss under a custom PD multiplier,
    using the same formula as the Phase E stress test
    (EL = PD * multiplier * LGD * loan_amnt, capped at PD=1.0).

    Requires risk_segments with columns:
        risk_segment, borrower_count, avg_pd, avg_loan_amnt
    """
    df = risk_segments.copy()
    stressed_pd = (df["avg_pd"] * multiplier).clip(upper=1.0)
    df["stressed_pd"] = stressed_pd
    df["stressed_el"] = stressed_pd * LGD * df["avg_loan_amnt"] * df["borrower_count"]
    return df
