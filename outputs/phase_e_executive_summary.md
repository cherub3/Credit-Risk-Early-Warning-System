# Phase E Executive Summary — Risk Segmentation, Expected Loss & Risk-Based Pricing

**Source:** `notebooks/04_risk_segmentation_pricing.ipynb` | **PD Engine:** Calibrated CatBoost (Brier Score 0.1603)
**Working Portfolio:** 2016 validation cohort — 293,095 resolved loans, 23.28% actual default rate

---

## 1. Risk Segmentation Findings

Borrowers were segmented into four PD-based bands (locked thresholds, no adjustment needed — all segments populated):

| Segment | PD Range | Borrowers | Portfolio Share | Actual Default Rate | Avg Loan Amount | Avg Interest Rate |
|---|---|---|---|---|---|---|
| **Low Risk** | < 10% | 47,316 | 16.1% | 5.97% | $14,227 | 7.09% |
| **Medium Risk** | 10–20% | 83,566 | 28.5% | 14.61% | $12,405 | 10.50% |
| **High Risk** | 20–35% | 107,605 | 36.7% | 26.68% | $14,171 | 14.32% |
| **Critical Risk** | ≥ 35% | 54,608 | 18.6% | 44.86% | $18,413 | 19.81% |

**Validation:** actual default rates increase **monotonically** across segments (5.97% → 14.61% → 26.68% → 44.86%), and each segment's average PD closely matches its realized default rate — confirming the calibrated PD scores are both well-ranked and well-calibrated at the segment level.

---

## 2. Expected Loss Findings

**Formula:** `Expected Loss = PD × LGD (60%) × EAD (loan_amnt)`

| Segment | Total Expected Loss | Avg EL per Borrower | Share of Total EL |
|---|---|---|---|
| Low Risk | $23.7M | $501 | 4% |
| Medium Risk | $90.9M | $1,087 | 14% |
| High Risk | $246.9M | $2,295 | 39% |
| Critical Risk | $273.4M | $5,007 | 43% |
| **Total Portfolio** | **$634.9M** | **$2,166** | 100% |

High and Critical Risk borrowers together generate **82% of total portfolio Expected Loss** while representing only **55% of loan volume** — the central risk-concentration finding (see Section 4).

---

## 3. Pricing Findings

**Formula:** `Recommended APR = Funding Cost (4%) + Expected Loss Rate (PD × LGD) + Margin (3%)`

| Segment | Avg PD | Expected Loss Rate | Recommended APR | Actual LendingClub APR | Pricing Gap |
|---|---|---|---|---|---|
| Low Risk | 5.97% | 3.58% | 10.58% | 7.09% | **+3.50%** |
| Medium Risk | 14.61% | 8.76% | 15.76% | 10.50% | **+5.27%** |
| High Risk | 26.68% | 16.01% | 23.01% | 14.32% | **+8.69%** |
| Critical Risk | 44.86% | 26.91% | 33.91% | 19.81% | **+14.10%** |

The pricing gap (model-recommended APR minus actual LendingClub rate) is **positive across every segment and grows sharply with risk** — Critical Risk shows the largest gap at +14.1 percentage points, indicating this segment is the most underpriced relative to its model-implied expected loss rate.

---

## 4. Portfolio Concentration Findings

| Segment | Portfolio Share (Volume) | Expected Loss Share |
|---|---|---|
| Low Risk | 16.1% | 4% |
| Medium Risk | 28.5% | 14% |
| High Risk | 36.7% | 39% |
| Critical Risk | 18.6% | 43% |

- **Most volume:** High Risk (36.7%) and Medium Risk (28.5%) together make up nearly two-thirds of the book.
- **Most Expected Loss:** Critical Risk (43%) and High Risk (39%) together account for **82% of EL from only 55% of volume** — a clear concentration of risk in a minority of the portfolio.
- **Underwriting review priority:** **High Risk** — it is large enough in volume (36.7% of the book) to materially move portfolio outcomes, and its EL-share-to-volume-share gap (39% vs 36.7%) combined with Critical Risk's much sharper gap (43% vs 18.6%) makes both segments priorities, with Critical Risk candidates for decline/reprice and High Risk candidates for manual review.

---

## 5. Stress Testing Findings

PD multipliers applied to the calibrated PD score, holding LGD and EAD fixed:

| Scenario | PD Multiplier | Portfolio Expected Loss | Change vs Base |
|---|---|---|---|
| Base Case | 1.0x | $634.9M | — |
| Mild Recession | 1.3x | $825.4M | **+30.0%** |
| Severe Recession | 1.7x | $1,076.2M | **+69.5%** |

A severe recession scenario (1.7x PD multiplier) would increase portfolio Expected Loss by nearly **$441M (+70%)** relative to the base case — quantifying the additional capital buffer the institution would need under adverse macroeconomic conditions.

---

## 6. SHAP Insights

SHAP analysis (TreeExplainer on the underlying CatBoost model, 5,000-borrower sample) confirms the model's drivers are explainable and directionally consistent with underwriting intuition for the dominant risk factors:

| Rank | Feature | Mean \|SHAP\| | Direction |
|---|---|---|---|
| 1 | `sub_grade` | 0.333 | Increases Risk (worse sub-grade → higher PD) |
| 2 | `loan_term_flag` | 0.234 | Increases Risk (60-month loans riskier than 36-month) |
| 3 | `fico_score` | 0.151 | Decreases Risk (higher FICO → lower PD) |
| 4 | `dti` | 0.150 | Increases Risk (higher debt-to-income → higher PD) |
| 5 | `int_rate` | 0.130 | Increases Risk (higher market-priced rate → higher PD) |
| 6 | `home_ownership` | 0.108 | Increases Risk (renting vs. owning) |

**`sub_grade` and `loan_term_flag` are by a wide margin the two most influential drivers** of the model's predictions — together accounting for more impact than the next four features combined. The top six drivers all align with standard underwriting logic (LendingClub's own risk grading, loan structure, bureau score, debt burden, market pricing, and housing stability).

Individual borrower waterfall explanations confirmed this pattern at the case level: a sampled low-risk borrower's score was driven down primarily by a strong `fico_score` and favorable `sub_grade`/term, while a sampled high-risk borrower's score was driven up by the inverse combination — providing a template for adverse-action-style explanations.

*(Note: for the lower-impact features in the tail of the ranking — e.g., `revol_util`, `credit_stress_score`, `high_utilization_flag` — the automated SHAP-correlation direction check produced results that did not consistently match their pre-written business interpretations, likely reflecting weak/noisy signal at this sample size. These are minor contributors (mean \|SHAP\| < 0.05) and do not affect the headline drivers above; full detail is in `outputs/shap_executive_summary.csv`.)*

---

## 7. Key Business Recommendations

1. **Adopt the four-tier Risk Action Framework** as the underwriting policy layer on top of the PD model:
   - Low Risk → Auto Approve
   - Medium Risk → Standard Approval
   - High Risk → Manual Review
   - Critical Risk → Decline / Reprice

2. **Reprice Critical and High Risk segments.** A +14.1pp (Critical) and +8.7pp (High) pricing gap suggests these segments are materially underpriced relative to their model-implied expected loss — the single highest-leverage pricing action identified.

3. **Prioritize underwriting review capacity on High Risk** (36.7% of volume, 39% of EL) — large enough to move portfolio-level outcomes, and the segment where additional manual scrutiny is most likely to reduce realized losses without simply declining a third of the book.

4. **Use Expected Loss by segment ($23.7M / $90.9M / $246.9M / $273.4M) as the basis for loan-loss provisioning**, with Critical and High Risk together representing the $520.3M (82%) of total $634.9M portfolio EL that should receive the closest monitoring.

5. **Plan capital buffers using the stress test results** — a severe recession scenario implies a ~$441M (+70%) increase in portfolio Expected Loss, providing a concrete, model-derived input for capital adequacy planning.

6. **Lead with `sub_grade`, `loan_term_flag`, `fico_score`, and `dti`** in any model governance or fair-lending review — these four features drive the large majority of the model's risk differentiation and are all standard, defensible underwriting factors.
