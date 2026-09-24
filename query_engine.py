import pandas as pd
import numpy as np

AGG_FUNCS = {
    "sum": "sum",
    "mean": "mean",
    "count": "count",
    "max": "max",
    "min": "min",
}

def execute_query(df: pd.DataFrame, plan: dict):
    """
    Executes a structured query plan on the dataframe using deterministic pandas operations.
    Returns:
        (result_df: pd.DataFrame | None, steps: list[str], error: str | None)
    """
    steps = []
    working_df = df.copy()

    # Step 1: Filter
    if plan.get("filter"):
        col, val = plan["filter"]
        if col in working_df.columns:
            mask = working_df[col].astype(str).str.strip().str.lower() == str(val).strip().lower()
            working_df = working_df[mask]
            steps.append(f"Filtered records where **'{col}'** equals **'{val}'** ({len(working_df)} matching rows)")
            if working_df.empty:
                return None, steps, f"No matching records found where '{col}' is '{val}'."
        else:
            steps.append(f"Filter column '{col}' was not found in dataset; skipped filter.")

    metric_col = plan.get("metric_col")
    agg = plan.get("agg", "sum")

    # If count is requested and no metric specified, count rows directly
    if agg == "count" and (metric_col is None or metric_col not in working_df.columns):
        count_val = len(working_df)
        steps.append(f"Counted total rows in dataset: {count_val:,}")
        return pd.DataFrame({"Total Count": [count_val]}), steps, None

    if metric_col is None or metric_col not in working_df.columns:
        return None, steps, "Could not identify a numeric measure column to perform this calculation. Please specify a metric like sales, revenue, or profit."

    # Ensure numeric
    if not pd.api.types.is_numeric_dtype(working_df[metric_col]):
        working_df[metric_col] = pd.to_numeric(working_df[metric_col].astype(str).str.replace(r"[^\d\.-]", "", regex=True), errors="coerce")

    # Step 2: Trend Query (Time series)
    if plan.get("is_trend") and plan.get("date_col") and plan["date_col"] in working_df.columns:
        date_col = plan["date_col"]
        working_df[date_col] = pd.to_datetime(working_df[date_col], errors="coerce", format="mixed")
        valid_dates = working_df.dropna(subset=[date_col, metric_col])
        if valid_dates.empty:
            return None, steps, f"No valid date records found in column '{date_col}'."
        
        valid_dates["_period"] = valid_dates[date_col].dt.to_period("M").astype(str)
        result = valid_dates.groupby("_period", as_index=False)[metric_col].agg(AGG_FUNCS[agg])
        result = result.sort_values("_period").reset_index(drop=True)
        result.columns = [date_col, metric_col]
        steps.append(f"Parsed dates in **'{date_col}'** and aggregated by calendar month")
        steps.append(f"Computed **{agg}** of **'{metric_col}'** across each monthly period ({len(result)} periods)")
        return result, steps, None

    # Step 3: Grouped Aggregation
    if plan.get("groupby_col") and plan["groupby_col"] in working_df.columns:
        group_col = plan["groupby_col"]
        ascending = plan.get("sort_ascending", False) or (agg == "min")
        
        result = working_df.groupby(group_col, as_index=False)[metric_col].agg(AGG_FUNCS[agg])
        result = result.sort_values(metric_col, ascending=ascending).reset_index(drop=True)
        steps.append(f"Grouped dataset by dimension **'{group_col}'** ({len(result)} distinct groups)")
        steps.append(f"Computed **{agg}** of metric **'{metric_col}'** for each group")

        top_n = plan.get("top_n")
        if top_n and top_n > 0:
            result = result.head(top_n)
            rank_label = "lowest" if ascending else "top"
            steps.append(f"Selected the **{rank_label} {top_n}** groups by **'{metric_col}'**")

        return result, steps, None

    # Step 4: Overall Scalar Aggregation
    clean_series = working_df[metric_col].dropna()
    if clean_series.empty:
        return None, steps, f"No non-null numeric values found in column '{metric_col}'."

    val = clean_series.agg(AGG_FUNCS[agg])
    # Format column name nicely
    agg_title = {"sum": "Total", "mean": "Average", "count": "Count", "max": "Maximum", "min": "Minimum"}.get(agg, agg.capitalize())
    result = pd.DataFrame({f"{agg_title} {metric_col}": [val]})
    steps.append(f"Computed **{agg}** of **'{metric_col}'** across all {len(clean_series):,} non-null rows")
    return result, steps, None
