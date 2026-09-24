import re
from difflib import get_close_matches

AGG_KEYWORDS = {
    "sum": ["total", "sum", "how much", "revenue", "overall", "gross", "cumulative", "combined"],
    "mean": ["average", "avg", "mean", "typical", "norm"],
    "count": ["how many", "count", "number of", "volume", "frequency"],
    "max": ["highest", "max", "maximum", "most", "peak", "greatest", "best", "largest"],
    "min": ["lowest", "min", "minimum", "least", "smallest", "bottom", "worst", "cheapest"],
}

TREND_KEYWORDS = [
    "trend", "over time", "monthly", "by month", "by year", "yearly",
    "growth", "over the", "timeline", "daily", "by date", "quarterly", "historical"
]

SYNONYMS = {
    "revenue": ["sales", "income", "amount", "total_amount", "mrr", "arr", "billing", "spend"],
    "sales": ["revenue", "amount", "sales_amount", "total"],
    "profit": ["income", "earnings", "net_margin", "gain"],
    "cost": ["expense", "treatment_cost", "spend", "price"],
    "orders": ["order", "transactions", "sales", "records"],
    "customers": ["customer", "clients", "accounts", "users"],
    "products": ["product", "items", "sku"],
}

def _normalize(text: str) -> str:
    return re.sub(r"[^\w\s]", " ", text.lower())

def _find_best_column(text: str, candidates: list):
    if not candidates:
        return None
    text_norm = _normalize(text)
    tokens = set(text_norm.split())

    # 1. Exact match on full column name
    for col in candidates:
        c_norm = _normalize(col)
        if c_norm in text_norm:
            return col

    # 2. Match on individual words of candidate
    for col in candidates:
        c_tokens = set(_normalize(col).split())
        if c_tokens and c_tokens.issubset(tokens):
            return col

    # 3. Check partial token overlap or synonym match
    for col in candidates:
        c_norm = _normalize(col)
        for token in tokens:
            if token in c_norm or c_norm in token:
                return col
            # Synonyms check
            for syn_key, syn_list in SYNONYMS.items():
                if token == syn_key or token in syn_list:
                    if any(s in c_norm for s in [syn_key] + syn_list):
                        return col

    # 4. Fuzzy match
    candidate_map = {_normalize(c): c for c in candidates}
    for w in tokens:
        matches = get_close_matches(w, list(candidate_map.keys()), n=1, cutoff=0.75)
        if matches:
            return candidate_map[matches[0]]

    return None

def _detect_agg(question: str, default: str = "sum") -> str:
    q = question.lower()
    for agg, keywords in AGG_KEYWORDS.items():
        if any(re.search(rf"\b{re.escape(k)}\b", q) for k in keywords):
            return agg
    return default

def _detect_top_n(question: str):
    q = question.lower()
    # Check bottom / lowest ranking
    m_bot = re.search(r"\b(?:bottom|lowest|least|worst)\s+(\d+)\b", q)
    if m_bot:
        return int(m_bot.group(1)), True
    if any(k in q for k in ["bottom", "lowest 5", "least"]):
        return 5, True

    # Check top / highest ranking
    m_top = re.search(r"\b(?:top|highest|best|most|first)\s+(\d+)\b", q)
    if m_top:
        return int(m_top.group(1)), False
    if "top" in q or "highest" in q or "most" in q:
        return 5, False

    return None, False

def _detect_groupby(question: str, dimension_cols: list):
    q = question.lower()
    patterns = [
        r"(?:grouped by|breakdown by|broken down by|by|per|across|for each|each|in terms of)\s+([a-zA-Z0-9_ ]+)",
    ]
    for pattern in patterns:
        m = re.search(pattern, q)
        if m:
            phrase = m.group(1).strip()
            # Clean trailing words like 'sorted', 'top', etc.
            phrase = re.sub(r"\b(sorted|top|highest|descending|ascending)\b.*", "", phrase).strip()
            col = _find_best_column(phrase, dimension_cols)
            if col:
                return col

    return _find_best_column(q, dimension_cols)

def _detect_filter(question: str, dimension_cols: list, df):
    q = " " + question.lower() + " "
    for col in dimension_cols:
        values = df[col].dropna().astype(str).unique().tolist()
        for val in values:
            val_str = str(val).strip()
            if len(val_str) < 2 or val_str.lower() in ["the", "and", "for", "with"]:
                continue
            # Match with word boundaries
            pattern = rf"(?:\b|\s){re.escape(val_str.lower())}(?:\b|\s)"
            if re.search(pattern, q):
                return (col, val_str)
    return None

def parse_question(question: str, schema: dict, df, last_plan: dict = None) -> dict:
    """
    Parses natural language question into a structured execution plan.
    Supports conversational memory (follow-up questions) when last_plan is provided.
    """
    measure_cols = [c for c, m in schema.items() if m["role"] == "measure"]
    dimension_cols = [c for c, m in schema.items() if m["role"] == "dimension"]
    date_cols = [c for c, m in schema.items() if m["role"] == "date"]

    q_lower = question.lower().strip()
    is_follow_up = False

    # Check for follow-up phrasing like "what about...", "how about...", "now show...", "filter by..."
    if last_plan and any(q_lower.startswith(p) for p in ["what about", "how about", "now for", "and for", "now show", "instead", "only"]):
        is_follow_up = True

    # Detect Aggregation
    agg_explicit = any(any(re.search(rf"\b{re.escape(k)}\b", q_lower) for k in kw_list) for kw_list in AGG_KEYWORDS.values())
    if agg_explicit:
        agg = _detect_agg(question)
    elif is_follow_up and last_plan:
        agg = last_plan.get("agg", "sum")
    else:
        agg = _detect_agg(question, default="sum")

    # Detect Top-N / Sorting
    top_n, sort_ascending = _detect_top_n(question)
    if top_n is None and is_follow_up and last_plan:
        top_n = last_plan.get("top_n")
        sort_ascending = last_plan.get("sort_ascending", False)

    # Detect Trend
    is_trend = any(k in q_lower for k in TREND_KEYWORDS) and bool(date_cols)
    if not is_trend and is_follow_up and last_plan:
        if any(k in q_lower for k in ["trend", "over time", "monthly"]):
            is_trend = True and bool(date_cols)

    # Detect Metric Column
    metric_col = _find_best_column(question, measure_cols)
    if not metric_col and last_plan:
        metric_col = last_plan.get("metric_col")
    if not metric_col and measure_cols:
        metric_col = measure_cols[0]

    # Detect Group By
    groupby_col = _detect_groupby(question, dimension_cols)
    if not groupby_col and is_follow_up and last_plan:
        groupby_col = last_plan.get("groupby_col")

    # Detect Filter
    filter_tuple = _detect_filter(question, dimension_cols, df)
    if not filter_tuple and is_follow_up and last_plan:
        # Check if previous filter should be retained or replaced
        filter_tuple = last_plan.get("filter")

    date_col = date_cols[0] if date_cols else None

    # If asking for count of records, metric_col is not strictly required
    if agg == "count" and not metric_col and measure_cols:
        metric_col = measure_cols[0]

    plan = {
        "question": question,
        "agg": agg,
        "metric_col": metric_col,
        "groupby_col": groupby_col if not is_trend else None,
        "filter": filter_tuple,
        "top_n": top_n,
        "sort_ascending": sort_ascending,
        "is_trend": is_trend,
        "date_col": date_col,
        "is_follow_up": is_follow_up,
    }
    return plan
