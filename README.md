# 📊 HTH-GA-09: Schema-Agnostic Natural Language Data Analyst

> **Automated, transparent spreadsheet analytics for business teams — without hardcoded column schemas or hallucinated numbers.**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32%2B-FF4B4B.svg)](https://streamlit.io/)
[![Pandas](https://img.shields.io/badge/Pandas-2.0%2B-150458.svg)](https://pandas.pydata.org/)
[![Status](https://img.shields.io/badge/Status-Hackathon--Ready-success.svg)]()

---

## 1. Problem & Innovation

Business teams frequently wait days for data analysts to answer routine questions about spreadsheets and CSVs because business users cannot write SQL or Pandas queries. While LLMs can generate text, relying on an LLM to guess calculations leads to hallucinations, silent errors, and lack of verifiability.

**Our Solution:**
1. **Schema-Agnostic Inference Engine:** Automatically infers column roles (`date`, `measure`, `dimension`, `id`) using heuristics on data types, cardinalities, and statistical properties. Zero hardcoded column names.
2. **Deterministic Query Engine:** Translates natural language into verified, executable Pandas operations (`groupby`, `agg`, `filter`, `nlargest`). No hallucinated numbers.
3. **Transparent Reasoning Steps:** Explains exactly how the calculation was performed step-by-step, along with the underlying Pandas code.
4. **Interactive Auto-Selected Visualizations:** Dynamically picks between bar charts for categorical comparisons and line charts for time-series trends.
5. **Bonus Features:**
   - **Conversational Follow-Up Memory:** Seamlessly answers follow-ups like *"What about West?"* or *"Show average instead"* by preserving query context.
   - **Automatic Anomaly Detection:** Identifies statistical outliers ($Z > 3\sigma$) on numeric columns upon file upload.

---

## 2. Architecture & File Structure

```
schema-agnostic/
├── app.py                 # Streamlit UI with quick presets, charts & explanation
├── schema_inference.py    # Infers column roles (date, measure, dimension, id)
├── nlp_query.py           # Parses NL query into structured query plan with memory
├── query_engine.py        # Deterministic pandas query execution + step logging
├── explain.py             # Plain-language explanation + anomaly detection
├── requirements.txt       # Dependencies
├── test_engine.py         # Automated verification suite across all 3 datasets
└── sample_data/           # 3 distinct domain datasets for instant demo
    ├── ecommerce_orders.csv
    ├── saas_subscriptions.csv
    └── hospital_admissions.csv
```

### Data Flow Pipeline
```
[User CSV/Excel Upload]
        │
        ▼
[schema_inference.py] ───► Detects Roles (Date, Measure, Dimension, ID)
        │
        ▼
[User Question] ───► [nlp_query.py] ───► Structured Plan (Agg, Metric, GroupBy, Filter, Trend)
                                               │
                                               ▼
[query_engine.py] ◄── Executes Pandas Plan & Logs Sequential Steps
        │
        ▼
[explain.py] ───► Formats Reasoning + Code Equivalent + Outlier Detection
        │
        ▼
[app.py] ───► Renders KPI Card / Chart (Bar or Line) + Data Table + Reasoning
```

---

## 3. Quickstart & Local Setup

### Prerequisites
Python 3.10 or higher.

### Installation
```bash
# Clone the repository
git clone https://github.com/your-username/schema-agnostic-analyst.git
cd schema-agnostic-analyst

# Install dependencies
pip install -r requirements.txt
```

### Run Automated Test Suite
```bash
python test_engine.py
```

### Launch Streamlit Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 4. Demo Walkthrough: 3 Unseen Datasets & 5+ Question Types

The app includes 3 preloaded datasets from distinct domains:

### Dataset 1: 🛒 E-Commerce Retail (`ecommerce_orders.csv`)
Columns: `order_id`, `order_date`, `customer_segment`, `region`, `category`, `sub_category`, `sales_amount`, `profit`, `quantity`, `discount`
- **Q1 (Scalar Aggregation):** *"What is the total sales amount?"*
- **Q2 (Categorical Breakdown):** *"Total sales amount by region"*
- **Q3 (Top-N Ranking):** *"Top 3 categories by sales amount"*
- **Q4 (Time-Series Trend):** *"Monthly sales amount trend"*
- **Q5 (Filtered Query):** *"Average sales amount in West"*
- **Q6 (Follow-Up):** *"Show average instead"*

### Dataset 2: 💻 SaaS Subscriptions (`saas_subscriptions.csv`)
Columns: `subscription_id`, `signup_date`, `plan_tier`, `billing_cycle`, `country`, `mrr_usd`, `active_seats`, `support_tickets_raised`, `churn_risk_score`
- **Q1 (Categorical Breakdown):** *"Average mrr by plan tier"*
- **Q2 (Top-N Ranking):** *"Top 3 countries by mrr"*
- **Q3 (Time-Series Trend):** *"MRR trend over time"*
- **Q4 (Filtered Query):** *"Total mrr for Enterprise"*

### Dataset 3: 🏥 Hospital Admissions (`hospital_admissions.csv`)
Columns: `admission_code`, `admit_date`, `department`, `insurance_type`, `patient_age`, `length_of_stay_days`, `total_treatment_cost`, `satisfaction_rating`
- **Q1 (Categorical Breakdown):** *"Average treatment cost by department"*
- **Q2 (Top-N Ranking):** *"Top 4 departments by treatment cost"*
- **Q3 (Time-Series Trend):** *"Treatment cost trend over time"*
- **Q4 (Filtered Query):** *"Average treatment cost in Cardiology"*

---

## 5. 60–90 Second Pitch Script

> *"Business teams often cannot answer simple questions about their own spreadsheets without waiting days on a data analyst. We built the **Schema-Agnostic Natural Language Data Analyst**.*
>
> *Upload any CSV or Excel file, ask questions in plain English, and get an answer, an interactive chart, and a step-by-step plain-language explanation of exactly how it was calculated.*
>
> *Unlike conventional tools that are secretly hardcoded to one specific column structure, our engine automatically infers what each column represents — date, measure, category, or ID — entirely from data properties. It works on spreadsheets it has never seen before.*
>
> *We prove this live across three distinct datasets: retail e-commerce, B2B SaaS, and hospital healthcare operations. Every calculation is 100% deterministic and verified via Pandas — not an LLM hallucinating numbers.*
>
> *With built-in conversational follow-up memory and automatic anomaly detection, it functions not like a rigid query interface, but like a real, transparent data analyst."*

---

## 6. Judge Q&A Cheat Sheet

- **Q: Why does schema-agnostic capability matter?**  
  *A:* Real-world business spreadsheets differ wildly in column headers and structure. Hardcoding breaks on any new file. We infer semantic roles dynamically based on data types, cardinalities, and statistical heuristics.
- **Q: Why deterministic Pandas rather than an LLM directly giving numbers?**  
  *A:* LLMs are notorious for mathematical hallucination when processing tabular data. By translating natural language into verified Pandas operations, every calculation is 100% accurate, repeatable, and transparent.
- **Q: How are ambiguous or unanswerable questions handled?**  
  *A:* If the parser cannot identify a relevant measure or dimension column, it gracefully returns a clear, actionable message rather than guessing.
- **Q: What is the biggest technical challenge solved?**  
  *A:* Reliably mapping informal, varied phrasing to structured query plans across unseen schemas without depending on heavy cloud models or brittle hardcoded regexes.

---

## 7. Deployment Instructions (Streamlit Community Cloud)

1. Push this repository to GitHub.
2. Visit [share.streamlit.io](https://share.streamlit.io) and log in with your GitHub account.
3. Click **"New app"**, select your repository, branch, and specify `app.py` as the main file path.
4. Click **"Deploy"**. The app will be live with a public URL in 2 minutes.
