"""Dataset diagnostics with optional high-performance backends for large data."""

from __future__ import annotations

import importlib
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

try:
    pl = importlib.import_module("polars")
except Exception:  # pragma: no cover
    pl = None

try:
    duckdb = importlib.import_module("duckdb")
except Exception:  # pragma: no cover
    duckdb = None

TARGET_CANDIDATE_NAMES = {"target", "label", "class", "y", "outcome"}


def _safe_float(value: Any) -> float:
    try:
        if value is None or pd.isna(value):
            return 0.0
        return float(value)
    except Exception:
        return 0.0


def is_large_dataset(df: pd.DataFrame) -> bool:
    rows, cols = df.shape
    return rows >= 100_000 or (rows * max(cols, 1)) >= 2_000_000


def _detect_target_column(df: pd.DataFrame) -> str | None:
    lower_map = {c.lower(): c for c in df.columns}
    for name in TARGET_CANDIDATE_NAMES:
        if name in lower_map:
            return lower_map[name]

    for col in reversed(df.columns.tolist()):
        nunique = df[col].nunique(dropna=True)
        if 2 <= nunique <= 20:
            dtype = str(df[col].dtype).lower()
            if "object" in dtype or "category" in dtype or "bool" in dtype:
                return col
    return None


def _detect_type_inconsistencies(df: pd.DataFrame) -> List[str]:
    inconsistent = []
    for col in df.select_dtypes(include=["object", "string"]).columns:
        non_null = df[col].dropna().astype(str)
        if non_null.empty:
            continue
        parsed = pd.to_numeric(non_null, errors="coerce")
        if parsed.notna().mean() >= 0.85:
            inconsistent.append(col)
    return inconsistent


def _detect_correlated_features(df: pd.DataFrame, threshold: float = 0.9) -> List[List[str]]:
    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.shape[1] < 2:
        return []

    corr = numeric_df.corr().abs()
    cols = corr.columns.tolist()
    pairs: List[List[str]] = []
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            if _safe_float(corr.iloc[i, j]) >= threshold:
                pairs.append([cols[i], cols[j]])
    return pairs


def _detect_skewed_features(df: pd.DataFrame, skew_threshold: float = 1.0) -> List[str]:
    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.empty:
        return []
    skewness = numeric_df.skew(numeric_only=True)
    return [col for col, value in skewness.items() if abs(_safe_float(value)) >= skew_threshold]


def _detect_outliers_iqr(df: pd.DataFrame, factor: float = 1.5) -> Tuple[bool, Dict[str, int], int]:
    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.empty:
        return False, {}, 0

    counts: Dict[str, int] = {}
    row_flags = np.zeros(len(df), dtype=bool)

    for col in numeric_df.columns:
        series = numeric_df[col].dropna()
        if series.empty:
            counts[col] = 0
            continue

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            counts[col] = 0
            continue

        lower = q1 - factor * iqr
        upper = q3 + factor * iqr
        mask = (numeric_df[col] < lower) | (numeric_df[col] > upper)
        counts[col] = int(mask.sum())
        row_flags = row_flags | mask.fillna(False).to_numpy()

    rows = int(row_flags.sum())
    return rows > 0, counts, rows


def _class_imbalance(df: pd.DataFrame) -> Dict[str, Any]:
    label_col = _detect_target_column(df)
    if not label_col:
        return {"detected": False}

    value_counts = df[label_col].value_counts(dropna=False)
    if value_counts.empty or len(value_counts) <= 1:
        return {"detected": False, "label_column": label_col}

    max_count = int(value_counts.max())
    min_count = int(value_counts.min())
    ratio = float(max_count / max(min_count, 1))

    return {
        "detected": True,
        "label_column": label_col,
        "distribution": {str(k): int(v) for k, v in value_counts.to_dict().items()},
        "imbalance_ratio": round(ratio, 3),
        "is_imbalanced": ratio >= 3.0,
    }


def _fast_missing_values(df: pd.DataFrame) -> Dict[str, int]:
    if is_large_dataset(df) and pl is not None:
        pldf = pl.from_pandas(df)
        row = pldf.null_count().to_dicts()[0]
        return {k: int(v) for k, v in row.items()}
    return {k: int(v) for k, v in df.isnull().sum().to_dict().items()}


def _fast_duplicates_count(df: pd.DataFrame) -> int:
    if is_large_dataset(df) and duckdb is not None:
        rel = duckdb.from_df(df)
        total = rel.count("*").fetchone()[0]
        distinct = rel.distinct().count("*").fetchone()[0]
        return int(total - distinct)
    return int(df.duplicated().sum())


def analyze_dataset(df: pd.DataFrame) -> Dict[str, Any]:
    missing_values = _fast_missing_values(df)
    duplicates = _fast_duplicates_count(df)
    rows = max(int(df.shape[0]), 1)

    categorical_columns = [
        c for c in df.columns if str(df[c].dtype).lower() in {"object", "category", "bool"}
    ]
    numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cardinality = {
        col: int(df[col].nunique(dropna=True)) for col in categorical_columns
    }

    correlated_features = _detect_correlated_features(df)
    skewed_features = _detect_skewed_features(df)
    outliers_detected, outliers_per_column, outlier_rows = _detect_outliers_iqr(df)
    class_imbalance = _class_imbalance(df)
    type_inconsistencies = _detect_type_inconsistencies(df)

    issues_detected: List[str] = []
    suggested_fix_details: List[Dict[str, Any]] = []

    if duplicates > 0:
        issues_detected.append(f"Duplicate rows found: {duplicates}")
        duplicate_ratio = duplicates / rows
        suggested_fix_details.append(
            {
                "fix": "remove_duplicates",
                "reason": f"{duplicates} duplicate rows detected",
                "confidence": "high" if duplicate_ratio >= 0.01 else "medium",
            }
        )
    if sum(missing_values.values()) > 0:
        issues_detected.append("Missing values detected")
        numeric_missing = int(df.select_dtypes(include=[np.number]).isnull().sum().sum())
        categorical_missing = int(
            df.select_dtypes(include=["object", "category", "bool"]).isnull().sum().sum()
        )
        if numeric_missing > 0:
            strategy = "knn_imputation" if len(numeric_columns) >= 2 and rows >= 30 else "simple_numeric_imputation"
            suggested_fix_details.append(
                {
                    "fix": strategy,
                    "reason": f"{numeric_missing} missing numeric values detected",
                    "confidence": "high" if strategy == "knn_imputation" else "medium",
                }
            )
        if categorical_missing > 0:
            suggested_fix_details.append(
                {
                    "fix": "categorical_mode_imputation",
                    "reason": f"{categorical_missing} missing categorical values detected",
                    "confidence": "high",
                }
            )
    if outliers_detected:
        issues_detected.append("Potential outliers detected")
        outlier_ratio = outlier_rows / max(rows, 1)
        if len(numeric_columns) >= 3 and rows >= 100 and outlier_ratio >= 0.02:
            suggested_fix_details.append(
                {
                    "fix": "isolation_forest_outlier_removal",
                    "reason": f"{outlier_rows} outlier rows ({outlier_ratio:.1%}) detected in numeric features",
                    "confidence": "medium",
                }
            )
        else:
            suggested_fix_details.append(
                {
                    "fix": "iqr_outlier_treatment",
                    "reason": f"{outlier_rows} potential outlier rows detected; conservative capping is safer",
                    "confidence": "medium",
                }
            )
    if skewed_features:
        issues_detected.append(f"Skewed numeric features detected: {len(skewed_features)}")
        positive_skewable = 0
        for col in skewed_features:
            try:
                if _safe_float(df[col].dropna().min()) > 0:
                    positive_skewable += 1
            except Exception:
                continue
        if positive_skewable > 0:
            suggested_fix_details.append(
                {
                    "fix": "log_transform",
                    "reason": f"{positive_skewable} skewed positive numeric columns found",
                    "confidence": "medium",
                }
            )
        else:
            suggested_fix_details.append(
                {
                    "fix": "power_transform",
                    "reason": "Skewed numeric columns include non-positive values",
                    "confidence": "low",
                }
            )
    if categorical_columns:
        issues_detected.append(f"Categorical columns detected: {len(categorical_columns)}")
        low_card_cols = [c for c, n in categorical_cardinality.items() if n <= 20]
        high_card_cols = [c for c, n in categorical_cardinality.items() if n > 20]
        if low_card_cols:
            suggested_fix_details.append(
                {
                    "fix": "one_hot_encoding",
                    "reason": f"{len(low_card_cols)} low-cardinality categorical columns",
                    "confidence": "high",
                }
            )
        if high_card_cols:
            suggested_fix_details.append(
                {
                    "fix": "frequency_encoding",
                    "reason": f"{len(high_card_cols)} high-cardinality categorical columns",
                    "confidence": "high",
                }
            )
    if type_inconsistencies:
        issues_detected.append(f"Possible type inconsistencies: {len(type_inconsistencies)}")
        suggested_fix_details.append(
            {
                "fix": "fix_column_types",
                "reason": f"{len(type_inconsistencies)} columns look numeric/datetime but are stored as text",
                "confidence": "medium",
            }
        )
    if class_imbalance.get("is_imbalanced"):
        issues_detected.append("Class imbalance detected")
        suggested_fix_details.append(
            {
                "fix": "class_weight_or_resampling",
                "reason": f"Imbalance ratio is {class_imbalance.get('imbalance_ratio')}",
                "confidence": "medium",
            }
        )
    if numeric_columns:
        stds = df[numeric_columns].std(numeric_only=True).replace(0, np.nan).dropna()
        if not stds.empty:
            spread_ratio = float(stds.max() / max(float(stds.min()), 1e-12))
            if spread_ratio >= 10.0:
                suggested_fix_details.append(
                    {
                        "fix": "normalize_numeric_features",
                        "reason": f"Numeric feature scale spread ratio is {spread_ratio:.2f}",
                        "confidence": "medium",
                    }
                )

    suggested_fixes = list(dict.fromkeys([item["fix"] for item in suggested_fix_details]))

    engine = "pandas"
    if is_large_dataset(df):
        if pl is not None:
            engine = "polars+pandas"
        elif duckdb is not None:
            engine = "duckdb+pandas"

    rows = int(df.shape[0])
    columns = int(df.shape[1])
    total_missing = int(sum(missing_values.values()))

    return {
        "rows": rows,
        "columns": columns,
        "data_types": {k: str(v) for k, v in df.dtypes.astype(str).to_dict().items()},
        "missing_values": missing_values,
        "duplicates": duplicates,
        "categorical_columns": categorical_columns,
        "categorical_cardinality": categorical_cardinality,
        "numeric_columns": numeric_columns,
        "correlated_features": correlated_features,
        "skewed_features": skewed_features,
        "outliers_detected": outliers_detected,
        "outlier_rows": outlier_rows,
        "outliers_per_column": outliers_per_column,
        "class_imbalance": class_imbalance,
        "type_inconsistencies": type_inconsistencies,
        "issues_detected": issues_detected,
        "suggested_fixes": suggested_fixes,
        "suggested_fix_details": suggested_fix_details,
        "processing_engine": engine,
        "dataset_summary": {
            "rows": rows,
            "columns": columns,
            "numeric_columns_count": len(numeric_columns),
            "categorical_columns_count": len(categorical_columns),
            "missing_values_total": total_missing,
            "duplicates": duplicates,
            "outliers_detected": outliers_detected,
            "outlier_rows": outlier_rows,
        },
    }
