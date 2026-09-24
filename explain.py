import pandas as pd
import numpy as np

def generate_explanation(plan: dict, steps: list) -> str:
    """
    Produces a human-readable explanation of how the computation was performed,
    including step-by-step logic and the transparent underlying pandas operation.
    """
    if not steps:
        return "No computation steps were recorded."

    agg_label = {
        "sum": "Total (Sum)",
        "mean": "Average (Mean)",
        "count": "Record Count",
        "max": "Maximum",
        "min": "Minimum",
    }.get(plan.get("agg", "sum"), plan.get("agg", "sum"))

    lines = ["### 🧠 Calculation Reasoning & Steps"]
    for i, step in enumerate(steps, start=1):
        lines.append(f"{i}. {step}")

    # Generate transparent code equivalent
    code_parts = ["df"]
    if plan.get("filter"):
        col, val = plan["filter"]
        code_parts.append(f"[df['{col}'] == '{val}']")

    metric = plan.get("metric_col", "column")
    agg = plan.get("agg", "sum")

    if plan.get("is_trend") and plan.get("date_col"):
        date_col = plan["date_col"]
        code = f"{''.join(code_parts)}.groupby(pd.to_datetime(df['{date_col}']).dt.to_period('M'))['{metric}'].{agg}()"
    elif plan.get("groupby_col"):
        grp = plan["groupby_col"]
        if plan.get("top_n"):
            n = plan["top_n"]
            asc = plan.get("sort_ascending", False)
            method = "nsmallest" if asc else "nlargest"
            code = f"{''.join(code_parts)}.groupby('{grp}')['{metric}'].{agg}().{method}({n})"
        else:
            code = f"{''.join(code_parts)}.groupby('{grp}')['{metric}'].{agg}()"
    else:
        code = f"{''.join(code_parts)}['{metric}'].{agg}()"

    lines.append(f"\n**Deterministic Computation:** `{code}`")
    lines.append(f"_Aggregation applied: **{agg_label}** on column **'{metric}'**._")

    return "\n\n".join([lines[0], "\n".join(lines[1:-2]), lines[-2], lines[-1]])

def detect_anomalies(df: pd.DataFrame, schema: dict, z_threshold: float = 3.0) -> list:
    """
    Detects statistical anomalies across numeric measures using Z-scores.
    Returns plain-English descriptions of detected outliers.
    """
    flags = []
    measure_cols = [c for c, m in schema.items() if m.get("role") == "measure"]

    for col in measure_cols:
        series = pd.to_numeric(df[col], errors="coerce").dropna()
        if len(series) < 8 or series.std(ddof=0) == 0:
            continue

        mean = float(series.mean())
        std = float(series.std(ddof=0))
        z_scores = (series - mean) / std
        outliers = series[abs(z_scores) > z_threshold]

        if not outliers.empty:
            count = len(outliers)
            sample_val = round(float(outliers.iloc[0]), 2)
            lower_expected = round(mean - 2.5 * std, 2)
            upper_expected = round(mean + 2.5 * std, 2)
            flags.append({
                "column": col,
                "count": count,
                "sample_outlier": sample_val,
                "expected_min": max(0.0, lower_expected) if (series >= 0).all() else lower_expected,
                "expected_max": upper_expected,
                "message": (
                    f"**{col}**: {count} anomaly value(s) detected (e.g. **{sample_val:,.2f}**). "
                    f"Normal range: ~**{max(0.0, lower_expected) if (series >= 0).all() else lower_expected:,.2f}** "
                    f"to **{upper_expected:,.2f}**."
                )
            })

    return flags
