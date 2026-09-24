import os
import streamlit as st
import pandas as pd
from schema_inference import infer_schema, get_columns_by_role
from nlp_query import parse_question
from query_engine import execute_query
from explain import generate_explanation, detect_anomalies

# Page Configuration
st.set_page_config(
    page_title="Schema-Agnostic NL Data Analyst",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for polished, premium visual styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-badge {
        display: inline-block;
        padding: 0.25rem 0.65rem;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        background-color: rgba(59, 130, 246, 0.15);
        color: #3b82f6;
        border: 1px solid rgba(59, 130, 246, 0.3);
        margin-bottom: 1rem;
    }
    .role-badge {
        display: inline-block;
        padding: 0.2rem 0.5rem;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 0.3rem;
    }
    .role-date { background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.3); }
    .role-measure { background: rgba(59, 130, 246, 0.15); color: #3b82f6; border: 1px solid rgba(59, 130, 246, 0.3); }
    .role-dimension { background: rgba(245, 158, 11, 0.15); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.3); }
    .role-id { background: rgba(139, 92, 246, 0.15); color: #8b5cf6; border: 1px solid rgba(139, 92, 246, 0.3); }
    .role-text { background: rgba(107, 114, 128, 0.15); color: #9ca3af; border: 1px solid rgba(107, 114, 128, 0.3); }
    .result-card {
        border-radius: 12px;
        padding: 1.25rem;
        border: 1px solid rgba(128, 128, 128, 0.2);
        margin-bottom: 1.5rem;
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 800;
        color: #3b82f6;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "history" not in st.session_state:
    st.session_state.history = []
if "df" not in st.session_state:
    st.session_state.df = None
if "schema" not in st.session_state:
    st.session_state.schema = None
if "dataset_name" not in st.session_state:
    st.session_state.dataset_name = ""
if "last_plan" not in st.session_state:
    st.session_state.last_plan = None
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

SAMPLE_DATASETS = {
    "🛒 E-Commerce Retail Orders": {
        "file": "sample_data/ecommerce_orders.csv",
        "sample_questions": [
            "Total sales amount by region",
            "Top 3 categories by sales amount",
            "Monthly sales amount trend",
            "Average profit by customer segment",
            "Total sales amount in West"
        ]
    },
    "💻 SaaS Subscriptions & Churn": {
        "file": "sample_data/saas_subscriptions.csv",
        "sample_questions": [
            "Average mrr by plan tier",
            "Top 3 countries by mrr",
            "MRR trend over time",
            "Total active seats by country",
            "Total mrr for Enterprise"
        ]
    },
    "🏥 Hospital Admissions & Cost": {
        "file": "sample_data/hospital_admissions.csv",
        "sample_questions": [
            "Average treatment cost by department",
            "Top 4 departments by treatment cost",
            "Treatment cost trend over time",
            "Average stay days by department",
            "Average treatment cost in Cardiology"
        ]
    }
}

# Sidebar: File Upload & Sample Loader
with st.sidebar:
    st.markdown("### 📁 Data Source")
    st.caption("Upload your own spreadsheet or choose a preloaded demo dataset.")

    uploaded_file = st.file_uploader(
        "Upload CSV or Excel file",
        type=["csv", "xlsx", "xls"],
        help="Upload any tabular spreadsheet. No column schema needed!"
    )

    st.markdown("---")
    st.markdown("### ⚡ Quick Demo Datasets")
    st.caption("Test instant schema generalization on 3 distinct domains:")

    selected_sample = st.selectbox(
        "Choose preloaded sample",
        options=["(Select a demo dataset)"] + list(SAMPLE_DATASETS.keys()),
        index=0
    )

    if selected_sample != "(Select a demo dataset)":
        if st.session_state.dataset_name != selected_sample:
            sample_info = SAMPLE_DATASETS[selected_sample]
            if os.path.exists(sample_info["file"]):
                df_loaded = pd.read_csv(sample_info["file"])
                st.session_state.df = df_loaded
                st.session_state.schema = infer_schema(df_loaded)
                st.session_state.dataset_name = selected_sample
                st.session_state.history = []
                st.session_state.last_plan = None
                st.session_state.pending_question = None
                st.rerun()

    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".csv"):
                df_loaded = pd.read_csv(uploaded_file)
            else:
                df_loaded = pd.read_excel(uploaded_file)
            
            if st.session_state.dataset_name != uploaded_file.name:
                st.session_state.df = df_loaded
                st.session_state.schema = infer_schema(df_loaded)
                st.session_state.dataset_name = uploaded_file.name
                st.session_state.history = []
                st.session_state.last_plan = None
                st.session_state.pending_question = None
                st.rerun()
        except Exception as e:
            st.error(f"Error loading file: {e}")

    if st.session_state.df is not None:
        st.markdown("---")
        st.markdown("### 📊 Active Dataset Stats")
        df_cur = st.session_state.df
        st.metric("Total Records", f"{len(df_cur):,}")
        st.metric("Total Columns", f"{df_cur.shape[1]}")

        if st.button("🧹 Clear Conversation", use_container_width=True):
            st.session_state.history = []
            st.session_state.last_plan = None
            st.session_state.pending_question = None
            st.rerun()

# Main Application Area
st.markdown('<div class="main-header">📊 Schema-Agnostic Natural Language Data Analyst</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-badge">HTH-GA-09 Hackathon Edition • 100% Deterministic Pandas • Anti-Hallucination</div>', unsafe_allow_html=True)
st.markdown("Upload any CSV or Excel file. Ask questions in plain English. Get direct answers, auto-selected charts, and transparent calculation steps.")

# If no dataset is loaded, show guidance banner
if st.session_state.df is None:
    st.info("👈 **To get started:** Select one of the 3 Quick Demo Datasets in the sidebar, or upload your own CSV/Excel file.")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown("#### 1. Zero Hardcoding")
        st.write("Automatically infers column roles (dates, numeric measures, categories, identifiers) regardless of column naming.")
    with col_b:
        st.markdown("#### 2. Deterministic Queries")
        st.write("Translates natural language into verified pandas operations, avoiding LLM hallucinations and calculation errors.")
    with col_c:
        st.markdown("#### 3. Full Explainability")
        st.write("Generates step-by-step reasoning, equivalent pandas code, and statistical anomaly detection flags.")
    st.stop()

df = st.session_state.df
schema = st.session_state.schema

# 1. Inferred Schema Explorer
with st.expander(f"🔍 Inferred Schema for **{st.session_state.dataset_name}** (Click to inspect column roles)", expanded=False):
    st.write("Every column was analyzed without hardcoded assumptions based on data types, cardinalities, and statistical heuristics:")
    
    schema_rows = []
    role_icon = {
        "date": "📅 Date",
        "measure": "📊 Measure (Numeric)",
        "dimension": "🏷️ Dimension (Category)",
        "id": "🔑 Identifier",
        "text": "📝 Free Text"
    }
    for col, meta in schema.items():
        schema_rows.append({
            "Column Name": col,
            "Inferred Role": role_icon.get(meta["role"], meta["role"]),
            "Data Type": meta["dtype"],
            "Unique Values": meta["n_unique"],
            "Null Count": meta["null_count"],
            "Sample Values": ", ".join(meta.get("sample_values", [])[:3])
        })
    st.dataframe(pd.DataFrame(schema_rows), use_container_width=True)

# 2. Anomaly Detection Callout
anomalies = detect_anomalies(df, schema)
if anomalies:
    with st.expander(f"⚠️ Automatic Anomaly Detection ({len(anomalies)} statistical outlier column(s) detected)", expanded=True):
        for item in anomalies:
            st.warning(item["message"])

# 3. Quick Question Suggestions (if demo dataset)
active_preset = SAMPLE_DATASETS.get(st.session_state.dataset_name)
if active_preset and active_preset.get("sample_questions"):
    st.markdown("##### 💡 Try an instant sample question:")
    q_cols = st.columns(len(active_preset["sample_questions"]))
    for idx, sample_q in enumerate(active_preset["sample_questions"]):
        if q_cols[idx].button(sample_q, key=f"quick_btn_{idx}"):
            st.session_state.pending_question = sample_q
            st.rerun()

# 4. Question Input Bar
st.markdown("### 💬 Ask a Business Question")

# Check if a pending question was triggered from quick button
default_text = ""
if st.session_state.pending_question:
    default_text = st.session_state.pending_question
    st.session_state.pending_question = None

with st.form("query_form", clear_on_submit=True):
    col_input, col_btn = st.columns([5, 1])
    with col_input:
        user_question = st.text_input(
            "Enter your question:",
            value=default_text,
            placeholder="e.g. 'Total sales by region', 'Top 5 products by revenue', 'Monthly trend of MRR', 'Average profit in West'",
            label_visibility="collapsed"
        )
    with col_btn:
        submit = st.form_submit_button("Run Query 🚀", use_container_width=True)

if (submit and user_question.strip()) or default_text:
    active_q = user_question.strip() if submit else default_text
    with st.spinner("Analyzing schema and executing query plan..."):
        plan = parse_question(active_q, schema, df, last_plan=st.session_state.last_plan)
        result_df, steps, error = execute_query(df, plan)
        
        if error:
            st.error(f"❌ {error}")
        else:
            explanation = generate_explanation(plan, steps)
            st.session_state.last_plan = plan
            st.session_state.history.append({
                "question": active_q,
                "result_df": result_df,
                "explanation": explanation,
                "plan": plan,
                "steps": steps
            })

# 5. Display Answer History (Latest First)
if st.session_state.history:
    st.markdown("---")
    st.markdown("### 📈 Analysis Results & Conversational History")

    for item_idx, item in enumerate(reversed(st.session_state.history)):
        q = item["question"]
        res_df = item["result_df"]
        expl = item["explanation"]
        plan = item["plan"]

        with st.container():
            st.markdown(f"#### ❓ {q}")
            if plan.get("is_follow_up"):
                st.caption("🔄 *Contextual follow-up question (inherited prior query filters/metrics)*")

            col_res, col_expl = st.columns([3, 2])

            with col_res:
                # Scenario A: Single scalar metric result
                if res_df is not None and len(res_df) == 1 and res_df.shape[1] == 1:
                    metric_label = res_df.columns[0]
                    raw_val = res_df.iloc[0, 0]
                    if isinstance(raw_val, (int, float)):
                        st.metric(label=metric_label, value=f"{raw_val:,.2f}")
                    else:
                        st.metric(label=metric_label, value=str(raw_val))
                    st.dataframe(res_df, use_container_width=True)

                # Scenario B: Multi-row result with 2 columns (Dimension + Metric) -> Chart + Table
                elif res_df is not None and len(res_df) > 1 and res_df.shape[1] == 2:
                    dim_col = res_df.columns[0]
                    metric_col = res_df.columns[1]
                    chart_df = res_df.set_index(dim_col)

                    tab_chart, tab_table = st.tabs(["📊 Interactive Chart", "📋 Data Table"])
                    with tab_chart:
                        if plan.get("is_trend"):
                            st.caption(f"📈 Line Chart: **{metric_col}** over **{dim_col}**")
                            st.line_chart(chart_df)
                        else:
                            st.caption(f"📊 Bar Chart: **{metric_col}** by **{dim_col}**")
                            st.bar_chart(chart_df)
                    with tab_table:
                        st.dataframe(res_df, use_container_width=True)

                # Scenario C: Generic multi-column table
                elif res_df is not None:
                    st.dataframe(res_df, use_container_width=True)

                # Export CSV button
                if res_df is not None and not res_df.empty:
                    csv_data = res_df.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="📥 Export Result CSV",
                        data=csv_data,
                        file_name=f"query_result_{len(st.session_state.history) - item_idx}.csv",
                        mime="text/csv",
                        key=f"dl_{item_idx}"
                    )

            with col_expl:
                st.markdown(expl)

            st.divider()
