"""
features.py

Creates domain-driven features grounded in credit risk underwriting logic.
All features are derived from information available at loan origination only.

Design philosophy:
    Every feature here must answer a question a credit analyst would actually
    ask. No feature is created because it "might help the model" — each one
    has a clear business rationale that can be defended in an interview.

Threshold note:
    Binary flag thresholds (utilization, employment length) are defined as
    constants at the top of this file. They are intentionally NOT hardcoded
    inside functions — EDA in 01_eda.ipynb will validate these values and
    they can be adjusted here based on what the data shows.
"""

import pandas as pd
import numpy as np
import os


# ---------------------------------------------------------------------------
# Threshold Constants
# These are set as defaults based on industry norms, but should be reviewed
# against the actual default-rate analysis in 01_eda.ipynb before modeling.
# ---------------------------------------------------------------------------

# revol_util above this level is flagged as high credit stress.
# Industry norm: 75%. EDA will confirm whether 50% or 90% better
# separates defaulters in this specific dataset.
HIGH_UTILIZATION_THRESHOLD = 75.0

# emp_length at or above this value is considered employment-stable.
# 5 years is a standard underwriting benchmark. EDA may suggest 3 or 7
# based on the default rate curve across employment lengths.
EMPLOYMENT_STABILITY_THRESHOLD = 5


# ---------------------------------------------------------------------------
# Core Engineered Features
# ---------------------------------------------------------------------------

def add_fico_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    fico_score = (fico_range_low + fico_range_high) / 2

    LendingClub reports a FICO band rather than a point score. The midpoint
    is used as a representative value — this is standard practice in credit
    analytics because underwriting decisions are typically benchmarked against
    a representative score within the reported band, not the extremes.
    """
    if "fico_range_low" in df.columns and "fico_range_high" in df.columns:
        df["fico_score"] = (df["fico_range_low"] + df["fico_range_high"]) / 2
        df.drop(columns=["fico_range_low", "fico_range_high"], inplace=True)
    return df


def add_income_to_loan_ratio(df: pd.DataFrame) -> pd.DataFrame:
    """
    income_to_loan_ratio = annual_inc / loan_amnt

    Measures how large the loan is relative to the borrower's annual income.
    A borrower earning $50K taking a $40K loan faces a very different
    repayment burden than one earning $200K for the same loan amount.
    Higher ratio = smaller relative exposure = lower credit risk.

    Capped at the 99th percentile to prevent extreme high-income outliers
    from distorting the distribution.
    """
    df["income_to_loan_ratio"] = df["annual_inc"] / df["loan_amnt"].replace(0, np.nan)
    cap = df["income_to_loan_ratio"].quantile(0.99)
    df["income_to_loan_ratio"] = df["income_to_loan_ratio"].clip(upper=cap)
    return df


def add_monthly_payment_burden(df: pd.DataFrame) -> pd.DataFrame:
    """
    monthly_payment_burden = installment / (annual_inc / 12)

    The share of monthly gross income consumed by this single loan payment.
    This is one of the most intuitive default risk signals in the dataset.

    A borrower paying 40% of monthly income toward one loan has very little
    financial buffer for unexpected expenses — a classic default precursor.
    In practice, underwriters often flag anything above 20-25% as elevated.

    Capped at 1.0: a burden exceeding 100% of monthly income almost certainly
    reflects a data quality issue rather than a real borrower situation.
    """
    monthly_income = df["annual_inc"] / 12
    df["monthly_payment_burden"] = df["installment"] / monthly_income.replace(0, np.nan)
    df["monthly_payment_burden"] = df["monthly_payment_burden"].clip(upper=1.0)
    return df


def add_credit_stress_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    credit_stress_score = dti * (revol_util / 100)

    Combines two independent pressure indicators into a single stress signal:
        DTI (debt-to-income): how much of income is already committed to debt
        revol_util: how close the borrower is to maxing their credit lines

    Neither indicator alone tells the full story. A borrower with high DTI
    but low utilization may have manageable installment debt. A borrower
    with low DTI but maxed credit cards is also stressed. The product
    captures borrowers who are under pressure on both dimensions simultaneously.

    This feature will be validated in EDA — if it doesn't separate defaulters
    from non-defaulters better than its components alone, it will be dropped.
    """
    revol_util_norm = df["revol_util"] / 100
    df["credit_stress_score"] = df["dti"] * revol_util_norm
    return df


def add_delinquency_flag(df: pd.DataFrame) -> pd.DataFrame:
    """
    delinquency_flag = 1 if delinq_2yrs > 0 else 0

    Whether the borrower missed any payments in the past 2 years.
    Historical payment behavior is one of the strongest predictors of
    future default — a borrower who has been delinquent recently is
    statistically far more likely to default again.
    This converts the raw count to a cleaner binary signal.
    """
    df["delinquency_flag"] = (df["delinq_2yrs"] > 0).astype(int)
    return df


def add_high_utilization_flag(
    df: pd.DataFrame,
    threshold: float = HIGH_UTILIZATION_THRESHOLD,
) -> pd.DataFrame:
    """
    high_utilization_flag = 1 if revol_util > threshold else 0

    A binary signal that the borrower is using a high fraction of available
    revolving credit. FICO scoring models penalize utilization heavily above
    certain thresholds because it signals financial strain and reduces the
    borrower's ability to absorb unexpected expenses.

    Default threshold: HIGH_UTILIZATION_THRESHOLD (see top of file).
    This should be confirmed against the EDA default-rate curve before
    being used in the final model.
    """
    df["high_utilization_flag"] = (df["revol_util"] > threshold).astype(int)
    return df


def add_employment_stability_flag(
    df: pd.DataFrame,
    threshold: int = EMPLOYMENT_STABILITY_THRESHOLD,
) -> pd.DataFrame:
    """
    employment_stability_flag = 1 if emp_length >= threshold else 0

    Proxy for income stability. Borrowers with long employment tenure are
    less likely to face sudden income disruption — a key driver of default.
    emp_length was converted to numeric (0–10) in preprocessing.

    Default threshold: EMPLOYMENT_STABILITY_THRESHOLD (see top of file).
    EDA will show the default rate curve across employment lengths to
    confirm whether 3, 5, or 7 years is the right cutoff.
    """
    df["employment_stability_flag"] = (df["emp_length"] >= threshold).astype(int)
    return df


def add_loan_term_flag(df: pd.DataFrame) -> pd.DataFrame:
    """
    loan_term_flag = 1 if term == 60 (months) else 0

    60-month loans default at a materially higher rate than 36-month loans —
    longer-term borrowers tend to be less creditworthy (smaller installments
    spread over more time) and carry more exposure windows for financial
    disruption. Since term only takes two values, this binary flag is a
    1:1 recoding that replaces raw 'term' in the model feature list.
    """
    df["loan_term_flag"] = (df["term"] == 60).astype(int)
    return df


def add_pub_rec_flag(df: pd.DataFrame) -> pd.DataFrame:
    """
    pub_rec_flag = 1 if pub_rec > 0 else 0

    Whether the borrower has any public derogatory records (bankruptcies,
    civil judgments, tax liens). Even a single public record signals a
    history of financial failure severe enough to appear in court records —
    a strong indicator of elevated default risk.
    """
    df["pub_rec_flag"] = (df["pub_rec"] > 0).astype(int)
    return df


# ---------------------------------------------------------------------------
# Bucketed Features — for EDA and Dashboard display only
# These are NOT fed into the model. Continuous versions are used instead.
# ---------------------------------------------------------------------------

def add_utilization_bucket(df: pd.DataFrame) -> pd.DataFrame:
    """
    Discretize revol_util for human-readable EDA charts and dashboard.
    The model uses the continuous revol_util — buckets are for people.
    """
    bins = [-1, 30, 75, 101]
    labels = ["Low (<30%)", "Medium (30-75%)", "High (>75%)"]
    df["utilization_bucket"] = pd.cut(
        df["revol_util"], bins=bins, labels=labels
    )
    return df


def add_loan_to_income_bucket(df: pd.DataFrame) -> pd.DataFrame:
    """
    Categorize income_to_loan_ratio into risk tiers for display.
    Ratio below 1 means loan exceeds annual income — very high relative exposure.
    """
    conditions = [
        df["income_to_loan_ratio"] < 1,
        (df["income_to_loan_ratio"] >= 1) & (df["income_to_loan_ratio"] < 3),
        df["income_to_loan_ratio"] >= 3,
    ]
    choices = ["High Exposure (< 1x)", "Moderate Exposure (1-3x)", "Low Exposure (> 3x)"]
    df["loan_to_income_bucket"] = np.select(conditions, choices, default="Unknown")
    return df


# ---------------------------------------------------------------------------
# Feature Summary Report
# ---------------------------------------------------------------------------

def generate_feature_summary(df: pd.DataFrame, output_dir: str = "outputs") -> pd.DataFrame:
    """
    Save a quick summary of all engineered features: mean, median, std,
    and default rate correlation. Useful for README and EDA discussion.
    """
    engineered = [
        "income_to_loan_ratio", "monthly_payment_burden", "credit_stress_score",
        "delinquency_flag", "high_utilization_flag", "employment_stability_flag",
        "pub_rec_flag", "fico_score",
    ]
    cols = [c for c in engineered if c in df.columns]

    summary_rows = []
    for col in cols:
        row = {
            "feature": col,
            "mean": df[col].mean(),
            "median": df[col].median(),
            "std": df[col].std(),
            "missing_pct": df[col].isnull().mean() * 100,
        }
        if "target" in df.columns:
            # Point-biserial correlation with default flag
            row["default_correlation"] = df[col].corr(df["target"]).round(4)
        summary_rows.append(row)

    summary = pd.DataFrame(summary_rows)
    os.makedirs(output_dir, exist_ok=True)
    summary.to_csv(os.path.join(output_dir, "feature_summary.csv"), index=False)
    print(f"Feature summary saved to {output_dir}/feature_summary.csv")

    return summary


# ---------------------------------------------------------------------------
# Feature Lists
# Finalized after Phase B (EDA). RAW and ENGINEERED lists are defined now.
# FINAL_MODEL_FEATURES will be confirmed in 02_feature_engineering.ipynb
# after validating that each feature meaningfully separates defaulters.
# ---------------------------------------------------------------------------

RAW_FEATURES = [
    "loan_amnt", "funded_amnt", "term", "int_rate", "installment",
    "grade", "sub_grade", "emp_length", "home_ownership",
    "annual_inc", "verification_status", "purpose",
    "dti", "delinq_2yrs", "inq_last_6mths", "open_acc",
    "pub_rec", "revol_bal", "revol_util", "total_acc",
    "mort_acc", "pub_rec_bankruptcies", "credit_history_years",
    "fico_score",
]

ENGINEERED_FEATURES = [
    "income_to_loan_ratio",
    "monthly_payment_burden",
    "credit_stress_score",
    "delinquency_flag",
    "high_utilization_flag",
    "employment_stability_flag",
    "pub_rec_flag",
]

# ---------------------------------------------------------------------------
# FINAL_MODEL_FEATURES
#
# Locked after the feature governance review in 02_feature_engineering.ipynb.
# This is the single source of truth for modeling, calibration, and the
# Streamlit app. 19 features total.
#
# Governance notes:
#   - 'grade' dropped: redundant with 'sub_grade' (near-perfect correlation,
#     sub_grade is a strict refinement of grade)
#   - 'installment' dropped: overlaps with 'monthly_payment_burden', which
#     already captures payment affordability relative to income
#   - 'delinq_2yrs', 'pub_rec', 'pub_rec_bankruptcies', 'revol_bal' dropped:
#     redundant with their derived binary flags / revol_util
#   - 'open_acc', 'total_acc', 'mort_acc', 'inq_last_6mths' dropped: weak,
#     undefended signal not tied to any EDA finding
#   - 'employment_stability_flag' dropped: emp_length retained directly,
#     carries the same information with less duplication
#   - 'int_rate' kept: market pricing of risk, conceptually distinct from
#     fico_score (bureau view) and sub_grade (LendingClub internal view)
#   - 'loan_amnt' kept: directly interpretable exposure size, used in
#     expected-loss calculations (Phase 8)
#   - 'annual_income_log' is a Logistic-Regression-only transform of
#     annual_inc, applied in the modeling pipeline -- NOT included here
# ---------------------------------------------------------------------------
FINAL_MODEL_FEATURES = [
    # Raw features (12)
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

    # Engineered features (7)
    "monthly_payment_burden",
    "income_to_loan_ratio",
    "credit_stress_score",
    "delinquency_flag",
    "pub_rec_flag",
    "loan_term_flag",
    "high_utilization_flag",
]


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------

def create_all_features(df: pd.DataFrame, output_dir: str = "outputs") -> pd.DataFrame:
    """
    Apply all feature engineering in sequence.
    Call this after preprocessing.prepare_data().

    Bucket features (utilization_bucket, loan_to_income_bucket) are created
    for EDA and dashboard use. They are not included in FINAL_MODEL_FEATURES.
    """
    print("=" * 55)
    print("FEATURE ENGINEERING")
    print("=" * 55)
    original_cols = df.shape[1]

    df = add_fico_score(df)
    df = add_income_to_loan_ratio(df)
    df = add_monthly_payment_burden(df)
    df = add_credit_stress_score(df)
    df = add_delinquency_flag(df)
    df = add_high_utilization_flag(df)
    df = add_employment_stability_flag(df)
    df = add_loan_term_flag(df)
    df = add_pub_rec_flag(df)
    df = add_utilization_bucket(df)
    df = add_loan_to_income_bucket(df)

    new_cols = df.shape[1] - original_cols
    print(f"Added {new_cols} new columns. Final shape: {df.shape}")

    generate_feature_summary(df, output_dir=output_dir)

    print("=" * 55)
    return df
