# Phase D Results Summary — Credit Risk Model Development

**Source:** `notebooks/03_modeling.ipynb` | **Models:** Logistic Regression (baseline) + CatBoost (champion, raw and calibrated)
**Validation methodology:** strict time-based split on `issue_year` (LendingClub accepted loans, 2007–2018)

---

## 1. Train / Validation / Test Split

| Split | Years | Loans | Default Rate |
|---|---|---|---|
| **Train** | 2007–2015 | 826,604 | 18.43% |
| **Validation** | 2016 | 293,095 | 23.28% |
| **Test** | 2017–2018 | 225,611 | 21.28% |

Chronological ordering is strictly enforced — no Validation/Test loan was issued before any Train loan. The rise in default rate from Train (18.4%) to Validation (23.3%) reflects real portfolio seasoning/vintage effects (2016 loans had more time to mature to a resolved outcome within the dataset window).

---

## 2. Logistic Regression — Baseline (Validation, threshold = 0.5)

| Metric | Value |
|---|---|
| ROC-AUC | 0.7050 |
| PR-AUC | 0.4106 |
| Precision | 0.3741 |
| Recall | 0.5874 |
| F1 | 0.4571 |
| Brier Score | 0.2113 |
| Recall@Top5% | 0.1187 |
| Recall@Top10% | 0.2148 |
| Recall@Top15% | 0.2988 |

`class_weight='balanced'` used to address the ~20% default rate. Coefficients align with underwriting intuition (e.g., `dti`, `credit_stress_score`, `loan_term_flag` push PD up; `fico_score`, `income_to_loan_ratio` push PD down).

---

## 3. Raw CatBoost (Validation, threshold = 0.5)

| Metric | Value |
|---|---|
| ROC-AUC | 0.7116 |
| PR-AUC | 0.4194 |
| Precision | 0.3644 |
| Recall | 0.6478 |
| F1 | 0.4664 |
| Brier Score | 0.2127 |
| Recall@Top5% | 0.1208 |
| Recall@Top10% | 0.2174 |
| Recall@Top15% | 0.3023 |

CatBoost improves ranking metrics (ROC-AUC, PR-AUC, Recall) over Logistic Regression but its raw Brier Score is *slightly worse* — i.e., it ranks borrowers better but its raw probabilities are less trustworthy in absolute terms.

---

## 4. Calibrated CatBoost (Validation, threshold = 0.5)

| Metric | Raw CatBoost | Calibrated CatBoost |
|---|---|---|
| ROC-AUC | 0.7116 | 0.7119 |
| PR-AUC | 0.4194 | 0.4161 |
| Brier Score | **0.2127** | **0.1603** |

Isotonic calibration (via `CalibratedClassifierCV` + `FrozenEstimator`, fit on the validation set) **cuts Brier Score by ~25%** while leaving ranking ability (ROC-AUC) essentially unchanged. This is the headline calibration result: the model becomes usable for Expected Loss / pricing arithmetic without sacrificing its ability to rank borrowers.

*(Note: at the default 0.5 threshold, calibrated probabilities are generally lower/better-spread, so Precision/Recall/F1 at 0.5 shift — Precision rises to 0.5675 / Recall falls to 0.1144 on validation. This is expected: calibration changes what "0.5" means in absolute terms. Risk-based decisions in this project use rank-based thresholds (Top 5/10/15%, Sections 7–8), not the 0.5 cutoff.)*

---

## 5. Top 10 CatBoost Feature Importances

| Rank | Feature | Importance |
|---|---|---|
| 1 | `sub_grade` | 26.90 |
| 2 | `loan_term_flag` | 13.72 |
| 3 | `int_rate` | 10.07 |
| 4 | `fico_score` | 8.00 |
| 5 | `dti` | 6.84 |
| 6 | `annual_inc` | 5.60 |
| 7 | `home_ownership` | 4.83 |
| 8 | `credit_history_years` | 3.99 |
| 9 | `monthly_payment_burden` | 3.49 |
| 10 | `emp_length` | 2.88 |

The top features (`sub_grade`, `int_rate`, `fico_score`, `dti`) directly mirror the Phase C feature governance review's "strong signal" tier — confirming the feature selection process correctly identified the dominant risk drivers ahead of modeling.

---

## 6. Top-Risk Decile Analysis (Validation, Calibrated CatBoost)

| Segment | Loans | Default Rate in Segment | Defaults Captured | Recall (% of all defaults) | Portfolio Coverage (% of volume) |
|---|---|---|---|---|---|
| Top 5% | 14,655 | 56.42% | 8,269 | 12.12% | 6.83% |
| Top 10% | 29,310 | 50.71% | 14,862 | 21.78% | 13.40% |
| Top 15% | 43,965 | 47.00% | 20,663 | 30.28% | 19.54% |

**Key insight:** the top 10% riskiest borrowers (by predicted PD) have a default rate of ~51% — roughly **2.2x the portfolio-wide default rate (23.3%)** — and capture ~22% of all eventual defaults while representing only ~13% of loan volume. A manual review or repricing focused on this decile would target a heavily concentrated pocket of risk.

---

## 7. Business Impact Analysis (Validation, Calibrated CatBoost)

**Assumptions:** LGD = 60% of `loan_amnt`; EAD = `loan_amnt`; Revenue proxy = `loan_amnt` × `int_rate` (one year of interest) for rejected non-defaulting borrowers.

| Strategy | Loans Approved | Loans Rejected | Defaults Avoided | Est. Loss Reduction | Revenue Foregone | Net Impact | Remaining Loss vs Baseline | Recall |
|---|---|---|---|---|---|---|---|---|
| A: Approve Everyone | 293,095 | 0 | 0 | $0 | $0 | $0 | 100.0% | 0.0% |
| B: Reject Top 5% | 278,440 | 14,655 | 8,269 | $97.9M | $30.1M | **+$67.8M** | 84.5% | 12.1% |
| C: Reject Top 10% | 263,785 | 29,310 | 14,862 | $172.9M | $60.2M | **+$112.7M** | 72.6% | 21.8% |
| D: Reject Top 15% | 249,130 | 43,965 | 20,663 | $233.5M | $88.8M | **+$144.8M** | 63.0% | 30.3% |

Every rejection strategy produces a **positive net impact** (loss reduction exceeds revenue foregone) on this portfolio, and the marginal benefit diminishes as the rejection threshold widens (each additional 5% of rejections avoids progressively less loss per dollar of revenue given up). All figures use transparent, simplified assumptions (flat 60% LGD) for methodology demonstration, not as a calibrated economic forecast.

---

## 8. Validation vs Test (Out-of-Time, 2017–2018)

| Metric | LR (Val) | LR (Test) | CatBoost (Val) | CatBoost (Test) | Calib. CatBoost (Val) | Calib. CatBoost (Test) |
|---|---|---|---|---|---|---|
| ROC-AUC | 0.7050 | 0.6955 | 0.7116 | 0.7027 | 0.7119 | 0.7026 |
| PR-AUC | 0.4106 | 0.3576 | 0.4194 | 0.3705 | 0.4161 | 0.3670 |
| Brier Score | 0.2113 | 0.2124 | 0.2127 | 0.2168 | 0.1603 | **0.1541** |
| Recall@Top10% | 0.2148 | 0.2021 | 0.2174 | 0.2055 | 0.2178 | 0.2042 |

All models show a **modest, expected decline** (~0.01 ROC-AUC, ~0.05 PR-AUC) moving from Validation (2016) to Test (2017–2018) — consistent with normal economic drift across vintages, not a breakdown. Notably, the **calibrated CatBoost's Brier Score actually improves slightly on Test (0.1541 vs 0.1603)**, and `Recall@Top10%` holds up well (20.4% vs 21.8%), indicating the ranking and calibration both generalize reasonably to genuinely unseen, more recent borrowers.

---

## 9. Key Modeling Conclusions

1. **CatBoost outperforms Logistic Regression on every ranking metric** (ROC-AUC, PR-AUC, Recall, Recall@TopK%), driven by `sub_grade`, `loan_term_flag`, `int_rate`, and `fico_score` — but the gap is modest (~0.006–0.01 ROC-AUC), and Logistic Regression remains a fully transparent, regulator-auditable benchmark.
2. **Calibration is the single highest-value modeling step performed**: a ~25% Brier Score reduction (0.213 → 0.160) at essentially zero cost to ranking ability — directly enabling the probabilities to be used for Expected Loss and pricing.
3. **Risk is highly concentrated**: the riskiest 10% of borrowers default at >2x the portfolio rate and account for ~22% of all defaults from ~13% of volume — a clear, actionable segmentation for underwriting review or risk-based pricing.
4. **Business impact is positive and quantifiable** under transparent assumptions — every tested rejection strategy reduces estimated portfolio losses by more than the interest revenue it forgoes.
5. **The model generalizes out-of-time**: performance on 2017–2018 (entirely unseen during training, validation, calibration, and threshold selection) declines only marginally from 2016, and calibration quality is preserved — supporting deployment with a standard monitoring/recalibration cadence rather than indicating the model is unreliable on future borrowers.
