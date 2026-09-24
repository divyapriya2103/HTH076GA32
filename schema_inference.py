import pandas as pd
import re

DATE_HINTS = ["date", "time", "day", "month", "year", "created", "updated", "timestamp", "period", "dob"]
MEASURE_HINTS = [
    "amount", "amt", "price", "cost", "revenue", "sales", "qty",
    "quantity", "total", "value", "profit", "income", "count", "mrr",
    "arr", "fee", "score", "rate", "discount", "margin", "salary", "expense", "budget"
]
ID_HINTS = ["id", "code", "sku", "number", "no", "key", "uuid", "identifier"]

def _try_parse_date(series: pd.Series) -> bool:
    sample = series.dropna().astype(str).head(30)
    if sample.empty:
        return False
    # If all values are pure integers, only consider them dates if they are 4-digit years (1900-2100)
    if sample.str.isnumeric().all():
        if (sample.str.len() == 4).all() and (sample.astype(int) >= 1900).all() and (sample.astype(int) <= 2100).all():
            return True
        return False
    try:
        parsed = pd.to_datetime(sample, errors="coerce", format="mixed")
        return parsed.notna().mean() > 0.7
    except Exception:
        return False

def _name_hint(col_name: str, hints: list) -> bool:
    name = str(col_name).lower().replace("_", " ").replace("-", " ")
    words = set(re.findall(r"[a-z0-9]+", name))
    return any(h in words or h in name for h in hints)

def infer_schema(df: pd.DataFrame) -> dict:
    """
    Infers the analytical role of each column in an unseen dataframe:
    - 'date': Timestamp or date dimension for trend analysis
    - 'measure': Numeric quantitative metric suitable for aggregation (sum, mean, etc.)
    - 'dimension': Low-to-medium cardinality categorical column suitable for grouping / filtering
    - 'id': High-cardinality unique identifier or key
    - 'text': High-cardinality descriptive text not suited for direct grouping
    """
    schema = {}
    n_rows = len(df)
    if n_rows == 0:
        return schema

    for col in df.columns:
        series = df[col]
        nunique = series.nunique(dropna=True)
        null_count = int(series.isna().sum())
        role = "text"

        if pd.api.types.is_datetime64_any_dtype(series) or (not pd.api.types.is_numeric_dtype(series) and _try_parse_date(series)) or _name_hint(col, DATE_HINTS):
            role = "date"
        elif pd.api.types.is_numeric_dtype(series):
            if _name_hint(col, ID_HINTS) and nunique > 0.8 * n_rows:
                role = "id"
            elif _name_hint(col, MEASURE_HINTS):
                role = "measure"
            elif nunique > max(15, 0.4 * n_rows):
                # High cardinality numeric without ID hints is typically a continuous measure
                role = "measure"
            elif nunique <= 15:
                # Low cardinality numeric (e.g. status code 1/2/3, rating 1-5, discount tiers) can act as dimension
                role = "dimension"
            else:
                role = "measure"
        else:
            if _name_hint(col, ID_HINTS) and nunique > 0.8 * n_rows:
                role = "id"
            elif nunique <= max(50, 0.5 * n_rows):
                role = "dimension"
            else:
                role = "text"

        sample_vals = [str(x) for x in series.dropna().unique()[:4]]
        schema[col] = {
            "role": role,
            "dtype": str(series.dtype),
            "n_unique": int(nunique),
            "null_count": null_count,
            "sample_values": sample_vals
        }
    return schema

def get_columns_by_role(schema: dict, role: str) -> list:
    return [c for c, meta in schema.items() if meta["role"] == role]
