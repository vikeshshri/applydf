"""Automated dataset cleaning orchestrator."""

from __future__ import annotations

import importlib
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
from sklearn.impute import KNNImputer
from sklearn.preprocessing import StandardScaler

from data_quality_score import calculate_data_quality_score
from dataset_analyzer import analyze_dataset, is_large_dataset
from pipeline_generator import generate_auto_pipeline

try:
    pl = importlib.import_module("polars")
except Exception:  # pragma: no cover
    pl = None

TARGET_CANDIDATE_NAMES = {"target", "label", "class", "y", "outcome"}


def _safe_float(value: Any) -> float:
    try:
        if value is None or pd.isna(value):
            return 0.0
        return float(value)
    except Exception:
        return 0.0


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


def _fast_drop_duplicates(df: pd.DataFrame) -> Tuple[pd.DataFrame, str]:
    if is_large_dataset(df) and pl is not None:
        pldf = pl.from_pandas(df)
        deduped = pldf.unique(maintain_order=True).to_pandas()
        return deduped, "polars"
    return df.drop_duplicates().reset_index(drop=True), "pandas"


def _fix_column_types(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    fixed: List[str] = []
    result = df.copy()

    for col in result.select_dtypes(include=["object", "string"]).columns:
        non_null = result[col].dropna().astype(str)
        if non_null.empty:
            continue

        numeric_try = pd.to_numeric(non_null, errors="coerce")
        if numeric_try.notna().mean() >= 0.9:
            result[col] = pd.to_numeric(result[col], errors="coerce")
            fixed.append(col)
            continue

        datetime_try = pd.to_datetime(non_null, errors="coerce")
        if datetime_try.notna().mean() >= 0.9:
            result[col] = pd.to_datetime(result[col], errors="coerce")
            fixed.append(col)

    return result, fixed


def auto_clean_dataset(df: pd.DataFrame) -> Dict[str, Any]:
    before_report = analyze_dataset(df)
    before_score = calculate_data_quality_score(df.shape, before_report)

    cleaned = df.copy()
    steps_applied: List[str] = []
    target_col = _detect_target_column(cleaned)

    # 1) duplicates
    before_rows = len(cleaned)
    cleaned, dedupe_engine = _fast_drop_duplicates(cleaned)
    if len(cleaned) < before_rows:
        steps_applied.append("remove_duplicates")

    # 2) types
    cleaned, fixed_cols = _fix_column_types(cleaned)
    if fixed_cols:
        steps_applied.append("fix_column_types")

    # 3) missing values
    numeric_cols = [
        c for c in cleaned.select_dtypes(include=[np.number]).columns.tolist() if c != target_col
    ]
    categorical_cols = [c for c in cleaned.columns if c not in numeric_cols and c != target_col]

    if cleaned.isnull().sum().sum() > 0:
        if len(numeric_cols) >= 2 and len(cleaned) >= 3:
            n_neighbors = min(5, max(1, len(cleaned) - 1))
            imputer = KNNImputer(n_neighbors=n_neighbors)
            cleaned[numeric_cols] = imputer.fit_transform(cleaned[numeric_cols])
            steps_applied.append("knn_imputation")
        elif numeric_cols:
            for col in numeric_cols:
                cleaned[col] = cleaned[col].fillna(cleaned[col].median())
            steps_applied.append("simple_numeric_imputation")

        for col in categorical_cols:
            if cleaned[col].isna().any():
                mode = cleaned[col].mode(dropna=True)
                fill_value = mode.iloc[0] if not mode.empty else "unknown"
                cleaned[col] = cleaned[col].fillna(fill_value)
        if categorical_cols:
            steps_applied.append("categorical_mode_imputation")

    # 4) outliers
    numeric_cols = [
        c for c in cleaned.select_dtypes(include=[np.number]).columns.tolist() if c != target_col
    ]
    if len(numeric_cols) >= 3 and len(cleaned) >= 100:
        iso = IsolationForest(contamination=0.05, random_state=42)
        mask = iso.fit_predict(cleaned[numeric_cols]) == 1
        removed = int((~mask).sum())
        removed_ratio = removed / max(len(cleaned), 1)
        if removed > 0 and removed_ratio >= 0.02:
            cleaned = cleaned.loc[mask].reset_index(drop=True)
            steps_applied.append("isolation_forest_outlier_removal")

    # 5) skewness
    numeric_cols = [
        c for c in cleaned.select_dtypes(include=[np.number]).columns.tolist() if c != target_col
    ]
    if numeric_cols:
        skewed = [
            col
            for col, val in cleaned[numeric_cols].skew(numeric_only=True).items()
            if abs(_safe_float(val)) >= 1.0
        ]
        transformed = 0
        for col in skewed:
            min_val = cleaned[col].min()
            shifted = cleaned[col] - min_val + 1 if _safe_float(min_val) <= 0 else cleaned[col]
            cleaned[col] = np.log1p(shifted)
            transformed += 1
        if transformed:
            steps_applied.append("log_transform")

    # 6) categorical encoding with guardrails
    cat_cols = [
        c
        for c in cleaned.select_dtypes(include=["object", "category", "bool"]).columns.tolist()
        if c != target_col
    ]
    if cat_cols:
        one_hot_cols: List[str] = []
        freq_encode_cols: List[str] = []

        original_col_count = max(int(df.shape[1]), 1)
        max_allowed_cols = min(original_col_count + 200, int(original_col_count * 3.0))
        projected_cols = int(cleaned.shape[1])

        for col in cat_cols:
            unique_count = int(cleaned[col].nunique(dropna=True))
            projected_after_one_hot = projected_cols - 1 + unique_count

            # One-hot only when low cardinality and projected width remains reasonable.
            if unique_count <= 20 and projected_after_one_hot <= max_allowed_cols:
                one_hot_cols.append(col)
                projected_cols = projected_after_one_hot
            else:
                freq_encode_cols.append(col)

        if freq_encode_cols:
            for col in freq_encode_cols:
                freqs = cleaned[col].value_counts(dropna=False, normalize=True)
                cleaned[col] = cleaned[col].map(freqs).fillna(0.0).astype(float)
            steps_applied.append("frequency_encoding")

        if one_hot_cols:
            cleaned = pd.get_dummies(cleaned, columns=one_hot_cols, drop_first=False)
            steps_applied.append("one_hot_encoding")

    # 7) scaling
    numeric_cols = [
        c for c in cleaned.select_dtypes(include=[np.number]).columns.tolist() if c != target_col
    ]
    if numeric_cols:
        scaler = StandardScaler()
        cleaned[numeric_cols] = scaler.fit_transform(cleaned[numeric_cols])
        steps_applied.append("standardization")

    # 8) PCA for genuinely high-dimensional feature spaces
    numeric_cols = [
        c for c in cleaned.select_dtypes(include=[np.number]).columns.tolist() if c != target_col
    ]
    if len(numeric_cols) >= 100 or cleaned.shape[1] >= 150:
        target_series = cleaned[target_col].copy() if target_col and target_col in cleaned.columns else None
        n_components = min(30, max(2, int(np.sqrt(len(numeric_cols)))))
        pca = PCA(n_components=n_components, random_state=42)
        transformed = pca.fit_transform(cleaned[numeric_cols])
        pca_cols = [f"pca_{i + 1}" for i in range(n_components)]
        cleaned = pd.DataFrame(transformed, columns=pca_cols)
        if target_series is not None:
            cleaned[target_col] = target_series.reset_index(drop=True)
        steps_applied.append("pca")

    after_report = analyze_dataset(cleaned)
    after_score = calculate_data_quality_score(cleaned.shape, after_report)
    pipeline = generate_auto_pipeline(before_report, df.shape)

    return {
        "cleaned_df": cleaned,
        "before_report": before_report,
        "after_report": after_report,
        "before_score": before_score,
        "after_score": after_score,
        "steps_applied": list(dict.fromkeys(steps_applied)),
        "pipeline": pipeline,
        "processing_engine": dedupe_engine,
    }
