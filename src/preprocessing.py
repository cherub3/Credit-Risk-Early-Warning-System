"""
preprocessing.py

Handles all raw data cleaning for the LendingClub dataset.
This runs before any feature engineering or modeling.

Key responsibility: produce a clean, leak-free DataFrame with correct
target variable, usable column types, and a data quality report.

Design note on encoding:
    Grade, sub_grade, home_ownership, and purpose are intentionally kept
    as strings or lightly processed here. Model-specific encoding happens
    in the modeling notebooks:
        - CatBoost receives raw categorical strings (it handles them natively)
        - Logistic Regression receives a separately encoded version
    This prevents the preprocessing layer from imposing assumptions that
    only make sense for one model.
"""

import os
import pandas as pd
import numpy as np


# ---------------------------------------------------------------------------
# Target Variable
# ---------------------------------------------------------------------------

def create_target(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert loan_status to a binary target.

    Fully Paid  → 0 (non-default)
    Charged Off → 1 (default)

    All other statuses (Current, Late, In Grace Period, etc.) are excluded
    because their final outcome is unknown. Including ambiguous statuses
    would introduce noise into training labels.
    """
    keep_statuses = {"Fully Paid", "Charged Off"}
    df = df[df["loan_status"].isin(keep_statuses)].copy()
    df["target"] = (df["loan_status"] == "Charged Off").astype(int)
    df.drop(columns=["loan_status"], inplace=True)
    return df


# ---------------------------------------------------------------------------
# Column Selection
# ---------------------------------------------------------------------------

# These columns are unavailable at loan origination and therefore would leak
# future information into the model. They are known only after the loan
# outcome has already been determined — using them would mean the model
# is "learning from the answer" rather than making a genuine prediction.
# Examples: total payments received, recovery amounts, last payment date.
LEAKAGE_COLUMNS = [
    "total_pymnt", "total_pymnt_inv", "total_rec_prncp",
    "total_rec_int", "total_rec_late_fee", "recoveries",
    "collection_recovery_fee", "last_pymnt_d", "last_pymnt_amnt",
    "next_pymnt_d", "last_credit_pull_d", "out_prncp", "out_prncp_inv",
    "funded_amnt_inv",
]

# Identifiers, free text, near-constant columns, joint-application fields,
# and post-origination hardship/settlement data with no predictive value
# at origination time.
JUNK_COLUMNS = [
    "id", "member_id", "url", "desc", "title", "zip_code",
    "policy_code", "application_type", "acc_now_delinq",
    "chargeoff_within_12_mths", "delinq_amnt", "tax_liens",
    "hardship_flag", "hardship_type", "hardship_reason",
    "hardship_status", "hardship_amount", "hardship_start_date",
    "hardship_end_date", "payment_plan_start_date",
    "hardship_loan_status", "hardship_dpd", "hardship_payoff_balance_amount",
    "hardship_last_payment_amount", "orig_projected_additional_accrued_interest",
    "debt_settlement_flag", "debt_settlement_flag_date",
    "settlement_status", "settlement_date", "settlement_amount",
    "settlement_percentage", "settlement_term",
    "sec_app_earliest_cr_line", "sec_app_inq_last_6mths",
    "sec_app_mort_acc", "sec_app_open_acc", "sec_app_revol_util",
    "sec_app_open_act_il", "sec_app_num_rev_accts",
    "sec_app_chargeoff_within_12_mths", "sec_app_collections_12_mths_ex_med",
    "sec_app_mths_since_last_major_derog",
    "verification_status_joint", "annual_inc_joint", "dti_joint",
    "pymnt_plan",
]

# Columns retained for modeling and analysis.
# Every column here is available at loan origination time.
FEATURE_COLUMNS = [
    "loan_amnt", "funded_amnt", "term", "int_rate", "installment",
    "grade", "sub_grade", "emp_length", "home_ownership",
    "annual_inc", "verification_status", "purpose",
    "dti", "delinq_2yrs", "fico_range_low", "fico_range_high",
    "inq_last_6mths", "open_acc", "pub_rec", "revol_bal",
    "revol_util", "total_acc", "mort_acc", "pub_rec_bankruptcies",
    "issue_d",  # kept for out-of-time splitting only — dropped before modeling
    "earliest_cr_line",  # used to compute credit history length
]


def select_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Retain only the columns needed for analysis and modeling.
    Leakage columns are removed first to make that intent explicit.
    """
    df = df.drop(columns=[c for c in LEAKAGE_COLUMNS if c in df.columns])
    df = df.drop(columns=[c for c in JUNK_COLUMNS if c in df.columns])

    cols_to_keep = [c for c in FEATURE_COLUMNS if c in df.columns]
    if "target" in df.columns:
        cols_to_keep.append("target")

    return df[cols_to_keep].copy()


# ---------------------------------------------------------------------------
# String Column Cleaning
# ---------------------------------------------------------------------------

def clean_string_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fix columns stored as strings that should be numeric.
    This is a data quality issue specific to how LendingClub exports data.
    """
    # Stored as "13.56%" — strip percent symbol and convert
    if "int_rate" in df.columns:
        df["int_rate"] = (
            df["int_rate"].astype(str)
            .str.replace("%", "", regex=False).str.strip()
        )
        df["int_rate"] = pd.to_numeric(df["int_rate"], errors="coerce")

    # Same pattern as int_rate
    if "revol_util" in df.columns:
        df["revol_util"] = (
            df["revol_util"].astype(str)
            .str.replace("%", "", regex=False).str.strip()
        )
        df["revol_util"] = pd.to_numeric(df["revol_util"], errors="coerce")

    # Stored as " 36 months" or " 60 months" — extract integer
    if "term" in df.columns:
        df["term"] = df["term"].astype(str).str.extract(r"(\d+)")[0]
        df["term"] = pd.to_numeric(df["term"], errors="coerce")

    # Stored as "10+ years", "< 1 year", "n/a" — map to numeric scale
    if "emp_length" in df.columns:
        emp_map = {
            "< 1 year": 0,  "1 year": 1,  "2 years": 2,
            "3 years": 3,   "4 years": 4,  "5 years": 5,
            "6 years": 6,   "7 years": 7,  "8 years": 8,
            "9 years": 9,   "10+ years": 10,
        }
        df["emp_length"] = df["emp_length"].map(emp_map)
        # "n/a" and blanks become NaN — handled in imputation step

    return df


# ---------------------------------------------------------------------------
# Encoding Strategy
# ---------------------------------------------------------------------------

def encode_sub_grade(df: pd.DataFrame) -> pd.DataFrame:
    """
    Encode sub_grade as an ordinal integer (A1=1 through G5=35).

    sub_grade has a genuine risk ordering — A1 is the safest and G5
    is the riskiest. We preserve this ordering for both models.

    For grade: we intentionally keep it as a string (e.g. "A", "B", "C").
        - CatBoost will handle it as a native categorical.
        - Logistic Regression will encode it separately in the modeling notebook
          using one-hot or ordinal encoding as needed.
    Imposing a numeric order on grade here would distort CatBoost's handling.
    """
    if "sub_grade" in df.columns:
        grades = ["A", "B", "C", "D", "E", "F", "G"]
        subgrade_map = {}
        rank = 1
        for g in grades:
            for n in range(1, 6):
                subgrade_map[f"{g}{n}"] = rank
                rank += 1
        df["sub_grade"] = df["sub_grade"].map(subgrade_map)

    return df


def standardize_categoricals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize string categorical columns for consistency.
    We do NOT encode home_ownership, purpose, or verification_status
    into integers here because:
        - CatBoost accepts string categoricals directly
        - Label encoding (Rent=0, Own=1, Mortgage=2) creates a fake
          ordinal relationship that does not exist
        - Model-specific encoding is handled in the modeling notebooks

    We only clean up casing and strip whitespace.
    """
    string_cats = ["grade", "home_ownership", "purpose", "verification_status"]
    for col in string_cats:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper()

    return df


# ---------------------------------------------------------------------------
# Date Handling
# ---------------------------------------------------------------------------

def parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert date columns to useful numeric representations.
    issue_d  → issue_year, issue_month (for OOT splitting)
    earliest_cr_line → credit_history_years (length of credit history)
    """
    if "issue_d" in df.columns:
        df["issue_d"] = pd.to_datetime(df["issue_d"], format="%b-%Y", errors="coerce")
        df["issue_year"] = df["issue_d"].dt.year
        df["issue_month"] = df["issue_d"].dt.month
        df.drop(columns=["issue_d"], inplace=True)

    if "earliest_cr_line" in df.columns:
        earliest = pd.to_datetime(
            df["earliest_cr_line"], format="%b-%Y", errors="coerce"
        )
        # Reference point: use a fixed date so the feature is stable
        reference_date = pd.Timestamp("2016-01-01")
        df["credit_history_years"] = (
            (reference_date - earliest).dt.days / 365.25
        ).clip(lower=0)
        df.drop(columns=["earliest_cr_line"], inplace=True)

    return df


# ---------------------------------------------------------------------------
# Missing Value Handling + Data Quality Report
# ---------------------------------------------------------------------------

def generate_data_quality_report(df: pd.DataFrame, output_dir: str = "outputs") -> pd.DataFrame:
    """
    Produce a simple missing-value and data-type report.
    Saved as outputs/data_quality_report.csv.

    Useful for README, dashboard, and interview discussions about
    data quality — shows you audited the data before modeling.
    """
    report = pd.DataFrame({
        "column": df.columns,
        "dtype": df.dtypes.values,
        "missing_count": df.isnull().sum().values,
        "missing_pct": (df.isnull().mean() * 100).round(2).values,
        "unique_values": df.nunique().values,
    })
    report = report.sort_values("missing_pct", ascending=False).reset_index(drop=True)

    os.makedirs(output_dir, exist_ok=True)
    report.to_csv(os.path.join(output_dir, "data_quality_report.csv"), index=False)
    print(f"Data quality report saved to {output_dir}/data_quality_report.csv")

    # Print a quick summary to the notebook
    high_missing = report[report["missing_pct"] > 20]
    if not high_missing.empty:
        print(f"\nColumns with >20% missing values ({len(high_missing)} columns):")
        print(high_missing[["column", "missing_pct"]].to_string(index=False))

    return report


def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Impute missing values before modeling.

    Strategy:
        Numeric columns  → median imputation
            Median is more robust than mean for financial data because
            income and loan amounts have heavy right tails. A single
            high-income outlier would shift the mean substantially.

        Categorical strings → fill with "UNKNOWN"
            This is transparent. It avoids inventing a category value
            and lets the model treat missingness as its own signal.

    emp_length is already numeric after clean_string_columns() — median applies.
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if "target" in numeric_cols:
        numeric_cols.remove("target")

    imputed_cols = []
    for col in numeric_cols:
        n_missing = df[col].isnull().sum()
        if n_missing > 0:
            df[col] = df[col].fillna(df[col].median())
            imputed_cols.append(col)

    string_cols = df.select_dtypes(include=["object"]).columns.tolist()
    for col in string_cols:
        if df[col].isnull().sum() > 0:
            df[col] = df[col].fillna("UNKNOWN")

    if imputed_cols:
        print(f"Median imputation applied to: {imputed_cols}")

    return df


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------

def prepare_data(df: pd.DataFrame, output_dir: str = "outputs") -> pd.DataFrame:
    """
    Full preprocessing pipeline. Run this once on the raw LendingClub CSV.

    Steps (order matters):
    1.  Filter to final-outcome loans only, create binary target
    2.  Remove leakage columns (post-origination information)
    3.  Remove junk columns (identifiers, free text, sparse fields)
    4.  Clean string-typed numeric columns (%, text in numbers)
    5.  Encode sub_grade ordinally (genuine risk ordering)
    6.  Standardize categorical strings (no fake numeric encoding)
    7.  Parse dates → issue_year, issue_month, credit_history_years
    8.  Generate and save data quality report
    9.  Impute missing values

    Returns a clean DataFrame ready for feature engineering.
    """
    print("=" * 55)
    print("PREPROCESSING PIPELINE")
    print("=" * 55)
    print(f"Input shape: {df.shape}")

    df = create_target(df)
    print(f"\nAfter target filter (Fully Paid / Charged Off only): {df.shape}")
    print(f"Default rate: {df['target'].mean():.2%}")

    df = select_columns(df)
    print(f"\nAfter column selection: {df.shape}")

    df = clean_string_columns(df)
    df = encode_sub_grade(df)
    df = standardize_categoricals(df)
    df = parse_dates(df)

    print("\nGenerating data quality report (pre-imputation)...")
    generate_data_quality_report(df, output_dir=output_dir)

    df = handle_missing_values(df)

    print(f"\nFinal clean shape: {df.shape}")
    print(f"Missing values remaining: {df.isnull().sum().sum()}")
    print("=" * 55)

    return df
