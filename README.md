# Credit Risk Early Warning & Risk-Based Pricing Platform

## Overview

This project simulates an end-to-end credit risk analytics workflow used by lending institutions to assess borrower risk, estimate portfolio losses, support underwriting decisions, and recommend risk-adjusted loan pricing.

Using over 1.3 million LendingClub loan applications, the platform predicts Probability of Default (PD), calibrates risk estimates, segments borrowers into actionable risk tiers, quantifies Expected Loss (EL), performs economic stress testing, and provides an interactive Streamlit-based decision platform for risk assessment and portfolio analytics.

The objective is not simply to predict defaults, but to demonstrate how predictive models can be translated into practical lending decisions through calibration, segmentation, pricing, and portfolio risk management.

---

## Key Business Outcomes

* Built a credit risk decision platform using 1.3M+ LendingClub loans
* Developed a calibrated Probability of Default (PD) model using CatBoost
* Improved probability quality through isotonic calibration, reducing Brier Score from 0.213 to 0.160 (~25% improvement)
* Segmented borrowers into four risk bands to support underwriting actions
* Quantified portfolio Expected Loss using a PD × LGD × EAD framework
* Identified that High + Critical Risk borrowers represented 55% of portfolio volume but contributed 82% of total Expected Loss
* Designed a risk-based pricing engine to recommend borrower-specific APRs
* Performed recession stress testing to estimate portfolio loss under adverse economic scenarios
* Built an interactive Streamlit application for borrower scoring, portfolio monitoring, and explainability

---

## Problem Statement

Traditional lending decisions require balancing growth and risk.

Approving too many borrowers increases default losses, while rejecting too many reduces revenue opportunities.

This project addresses five key business questions:

1. Which borrowers are most likely to default?
2. How reliable are the predicted default probabilities?
3. How should borrowers be segmented for underwriting decisions?
4. What is the expected financial loss associated with each borrower?
5. How should interest rates be adjusted based on risk?

---

## Dataset

### Source

LendingClub Accepted and Rejected Loan Data

### Development Dataset

* Accepted Loans: 2007–2018
* Rejected Loans: 2007–2018

### Repository Dataset

The original LendingClub datasets are not included due to their size.

Representative samples are available in:

```text
sample_data/
├── accepted_sample.csv
├── rejected_sample.csv
```

The deployed application operates using pre-trained models and pre-computed analytical outputs and therefore does not require the full raw datasets.

---

## Project Architecture

```text
Raw Lending Data
        │
        ▼
Data Cleaning & Preprocessing
        │
        ▼
Feature Engineering
        │
        ▼
Credit Risk Modeling
(Logistic Regression + CatBoost)
        │
        ▼
Probability Calibration
        │
        ▼
Risk Segmentation
        │
        ▼
Expected Loss Estimation
        │
        ▼
Risk-Based Pricing
        │
        ▼
Portfolio Stress Testing
        │
        ▼
Interactive Decision Platform
```

---

## Methodology

### 1. Data Preparation

* Target definition using resolved loan outcomes
* Leakage removal
* Missing value treatment
* Ordinal encoding of LendingClub grades
* Time-aware data preparation

### 2. Feature Engineering

Domain-inspired features were created to capture borrower affordability and financial stress.

Examples include:

* Monthly Payment Burden
* Income-to-Loan Ratio
* Credit Stress Score
* Delinquency Indicators
* Loan Term Risk Indicators

---

### 3. Exploratory Risk Analysis

EDA focused on identifying risk drivers rather than generic descriptive statistics.

Key questions explored:

* Does LendingClub's internal grading system predict default?
* How do debt burden and utilization affect risk?
* Which borrower characteristics are associated with higher default rates?
* Do engineered features improve risk separation?

---

### 4. Credit Risk Modeling

Two models were developed:

#### Baseline

Logistic Regression

Purpose:

* Transparent benchmark
* Interpretable coefficients
* Regulatory-style baseline

#### Champion Model

CatBoost

Purpose:

* Capture non-linear relationships
* Handle categorical variables effectively
* Improve borrower ranking performance

---

### 5. Time-Based Validation

Random train-test splits were intentionally avoided.

The model was evaluated using a chronological split:

| Split      | Years     |
| ---------- | --------- |
| Train      | 2007–2015 |
| Validation | 2016      |
| Test       | 2017–2018 |

This approach better reflects real-world deployment conditions.

---

### 6. Probability Calibration

Because lending decisions depend on accurate probabilities rather than rankings alone, isotonic calibration was applied.

Result:

| Metric      | Raw CatBoost | Calibrated CatBoost |
| ----------- | ------------ | ------------------- |
| ROC-AUC     | 0.7116       | 0.7119              |
| Brier Score | 0.2127       | 0.1603              |

Calibration significantly improved probability quality while preserving ranking performance.

---

## Model Performance

### Validation Results

| Metric   | Logistic Regression | CatBoost |
| -------- | ------------------- | -------- |
| ROC-AUC  | 0.7050              | 0.7116   |
| PR-AUC   | 0.4106              | 0.4194   |
| Recall   | 0.5874              | 0.6478   |
| F1 Score | 0.4571              | 0.4664   |

---

## Risk Segmentation Framework

Borrowers were segmented into four risk categories using calibrated Probability of Default.

| Segment       | PD Range |
| ------------- | -------- |
| Low Risk      | <10%     |
| Medium Risk   | 10–20%   |
| High Risk     | 20–35%   |
| Critical Risk | ≥35%     |

### Underwriting Actions

| Segment       | Recommendation    |
| ------------- | ----------------- |
| Low Risk      | Auto Approve      |
| Medium Risk   | Standard Approval |
| High Risk     | Manual Review     |
| Critical Risk | Decline / Reprice |

---

## Expected Loss Framework

Expected Loss was estimated using:

Expected Loss = PD × LGD × EAD

Where:

* PD = Probability of Default
* LGD = Loss Given Default
* EAD = Exposure at Default

Portfolio Expected Loss:

**$634.9M**

---

## Portfolio Risk Findings

### Risk Concentration

| Segment Group        | Portfolio Volume | Expected Loss Share |
| -------------------- | ---------------- | ------------------- |
| High + Critical Risk | 55%              | 82%                 |

This indicates a significant concentration of portfolio risk among a minority of borrowers.

---

## Risk-Based Pricing

A pricing engine was developed to recommend risk-adjusted APRs.

Formula:

```text
Recommended APR =
Funding Cost
+ Expected Loss Rate
+ Target Margin
```

The largest pricing gap was observed among Critical Risk borrowers, suggesting they were materially underpriced relative to model-implied risk.

---

## Economic Stress Testing

Three macroeconomic scenarios were evaluated:

| Scenario         | Portfolio Expected Loss |
| ---------------- | ----------------------- |
| Base Case        | $634.9M                 |
| Mild Recession   | $825.4M                 |
| Severe Recession | $1.08B                  |

A severe recession increased portfolio Expected Loss by approximately 70%.

---

## Model Explainability

SHAP was used to explain model predictions globally and at the individual borrower level.

Most influential risk drivers:

* Sub Grade
* Loan Term
* FICO Score
* Debt-to-Income Ratio
* Interest Rate
* Home Ownership

These drivers align with standard underwriting intuition and improve model transparency.

---

## Interactive Streamlit Application

The project includes a multi-page Streamlit dashboard featuring:

### Project Overview

Business context, methodology, and model performance

### Executive Dashboard

Portfolio risk metrics and segmentation summaries

### Borrower Risk Assessment

* Probability of Default
* Risk Segment
* Expected Loss
* Recommended APR
* SHAP Explanations

### Portfolio Analytics

* Risk Distribution
* Expected Loss Analysis
* Pricing Recommendations

### Stress Testing

Scenario-based portfolio risk analysis

### Model Explainability

SHAP visualizations and model governance metrics

---

## Technology Stack

### Languages

* Python

### Data Analysis

* Pandas
* NumPy

### Visualization

* Plotly
* Matplotlib
* Seaborn

### Machine Learning

* Scikit-Learn
* CatBoost

### Explainability

* SHAP

### Deployment

* Streamlit

---

## Repository Structure

```text
credit-risk-early-warning-system/

├── app/
├── models/
├── notebooks/
├── outputs/
├── sample_data/
├── src/
├── README.md
├── requirements.txt
└── .gitignore
```

---

## Future Enhancements

* Real-time model monitoring
* Automated drift detection
* Portfolio optimization engine
* Dynamic pricing simulations
* Alternative credit scoring signals

---

## Disclaimer

This project was developed for educational and portfolio purposes using publicly available LendingClub data. The pricing, expected loss, and stress testing assumptions are simplified and are intended to demonstrate risk analytics methodologies rather than production lending policies.
