"""Intelligent data profiling, scoring, auto-cleaning, and pipeline generation."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
from sklearn.impute import KNNImputer
from sklearn.preprocessing import StandardScaler


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

    if df.empty:
        return None

    for col in reversed(df.columns.tolist()):
        nunique = df[col].nunique(dropna=True)
        if nunique <= 20 and nunique >= 2:
            dtype = str(df[col].dtype).lower()
            if "object" in dtype or "category" in dtype or "bool" in dtype:
                return col
    return None


def _detect_type_inconsistencies(df: pd.DataFrame) -> List[str]:
    inconsistent = []
    for col in df.select_dtypes(include=["object", "string"]).columns:
        series = df[col].dropna().astype(str)
        if series.empty:
            continue
        numeric_parsed = pd.to_numeric(series, errors="coerce")
        ratio = numeric_parsed.notna().mean()
        if ratio >= 0.85:
            inconsistent.append(col)
    return inconsistent


def _detect_correlated_features(df: pd.DataFrame, threshold: float = 0.9) -> List[List[str]]:
    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.shape[1] < 2:
        return []

    corr = numeric_df.corr().abs()
    pairs: List[List[str]] = []
    cols = corr.columns.tolist()
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
    return [col for col, val in skewness.items() if abs(_safe_float(val)) >= skew_threshold]


def _detect_outliers(df: pd.DataFrame, factor: float = 1.5) -> Tuple[bool, Dict[str, int], int]:
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

    total_rows = int(row_flags.sum())
    return total_rows > 0, counts, total_rows


def _class_imbalance(df: pd.DataFrame) -> Dict[str, Any]:
    label_col = _detect_target_column(df)
    if not label_col:
        return {"detected": False}

    value_counts = df[label_col].value_counts(dropna=False)
    if value_counts.empty or len(value_counts) <= 1:
        return {"detected": False, "label_column": label_col}

    max_count = int(value_counts.max())
    min_count = int(value_counts.min())
    imbalance_ratio = float(max_count / max(min_count, 1))

    return {
        "detected": True,
        "label_column": label_col,
        "distribution": {str(k): int(v) for k, v in value_counts.to_dict().items()},
        "imbalance_ratio": round(imbalance_ratio, 3),
        "is_imbalanced": imbalance_ratio >= 3.0,
    }


def generate_dataset_health_report(df: pd.DataFrame) -> Dict[str, Any]:
    missing_values = {k: int(v) for k, v in df.isnull().sum().to_dict().items()}
    duplicates = int(df.duplicated().sum())

    categorical_columns = [
        c for c in df.columns if str(df[c].dtype).lower() in {"object", "category", "bool"}
    ]
    numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()

    correlated_features = _detect_correlated_features(df)
    skewed_features = _detect_skewed_features(df)
    outliers_detected, outlier_counts, outlier_rows = _detect_outliers(df)
    class_imbalance = _class_imbalance(df)
    type_inconsistencies = _detect_type_inconsistencies(df)

    issues: List[str] = []
    suggested_fixes: List[str] = []

    if duplicates > 0:
        issues.append(f"Duplicate rows found: {duplicates}")
        suggested_fixes.append("remove_duplicates")

    if sum(missing_values.values()) > 0:
        issues.append("Missing values detected")
        suggested_fixes.append("knn_imputation")

    if outliers_detected:
        issues.append("Potential outliers detected")
        suggested_fixes.append("isolation_forest_outlier_removal")

    if skewed_features:
        issues.append(f"Skewed numeric features detected: {len(skewed_features)}")
        suggested_fixes.append("log_transform")

    if categorical_columns:
        issues.append(f"Categorical columns detected: {len(categorical_columns)}")
        suggested_fixes.append("one_hot_encoding")

    if type_inconsistencies:
        issues.append(f"Possible type inconsistencies: {len(type_inconsistencies)}")
        suggested_fixes.append("fix_column_types")

    if class_imbalance.get("is_imbalanced"):
        issues.append("Class imbalance detected")
        suggested_fixes.append("class_weight_or_resampling")

    if numeric_columns:
        suggested_fixes.append("normalize_numeric_features")

    # Keep order but remove duplicates
    suggested_fixes = list(dict.fromkeys(suggested_fixes))

    return {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "data_types": {k: str(v) for k, v in df.dtypes.astype(str).to_dict().items()},
        "missing_values": missing_values,
        "duplicates": duplicates,
        "categorical_columns": categorical_columns,
        "numeric_columns": numeric_columns,
        "correlated_features": correlated_features,
        "skewed_features": skewed_features,
        "outliers_detected": outliers_detected,
        "outlier_rows": outlier_rows,
        "outliers_per_column": outlier_counts,
        "class_imbalance": class_imbalance,
        "type_inconsistencies": type_inconsistencies,
        "issues_detected": issues,
        "suggested_fixes": suggested_fixes,
    }


def calculate_data_quality_score(df: pd.DataFrame, report: Dict[str, Any] | None = None) -> Dict[str, Any]:
    report = report or generate_dataset_health_report(df)

    rows = max(int(df.shape[0]), 1)
    cols = max(int(df.shape[1]), 1)

    missing_count = int(sum(report.get("missing_values", {}).values()))
    duplicate_count = int(report.get("duplicates", 0))
    outlier_rows = int(report.get("outlier_rows", 0))
    skewed_count = len(report.get("skewed_features", []))
    inconsistent_count = len(report.get("type_inconsistencies", []))

    missing_pct = missing_count / max(rows * cols, 1)
    duplicate_pct = duplicate_count / rows
    outlier_pct = outlier_rows / rows
    skewed_pct = skewed_count / cols
    inconsistent_pct = inconsistent_count / cols

    imbalance_penalty = 0.0
    imbalance = report.get("class_imbalance", {})
    if imbalance.get("is_imbalanced"):
        ratio = float(imbalance.get("imbalance_ratio", 1.0))
        imbalance_penalty = min(15.0, (ratio - 1.0) * 3.0)

    score = 100.0
    score -= min(25.0, missing_pct * 100.0)
    score -= min(15.0, duplicate_pct * 100.0)
    score -= min(20.0, outlier_pct * 100.0)
    score -= min(10.0, skewed_pct * 100.0)
    score -= min(15.0, inconsistent_pct * 100.0)
    score -= imbalance_penalty
    score = max(0.0, min(100.0, score))

    return {
        "score": round(score, 2),
        "breakdown": {
            "missing_values_penalty": round(min(25.0, missing_pct * 100.0), 2),
            "duplicate_rows_penalty": round(min(15.0, duplicate_pct * 100.0), 2),
            "outliers_penalty": round(min(20.0, outlier_pct * 100.0), 2),
            "skewness_penalty": round(min(10.0, skewed_pct * 100.0), 2),
            "type_inconsistency_penalty": round(min(15.0, inconsistent_pct * 100.0), 2),
            "imbalance_penalty": round(imbalance_penalty, 2),
        },
    }


def generate_auto_pipeline(df: pd.DataFrame, report: Dict[str, Any] | None = None) -> Dict[str, Any]:
    report = report or generate_dataset_health_report(df)

    steps: List[Dict[str, str]] = []

    if int(report.get("duplicates", 0)) > 0:
        steps.append({"step": "remove_duplicates", "reason": "duplicate rows detected"})

    if sum(report.get("missing_values", {}).values()) > 0:
        numeric_count = len(report.get("numeric_columns", []))
        if numeric_count >= 2:
            steps.append({"step": "knn_imputation", "reason": "missing values present in multi-feature data"})
        else:
            steps.append({"step": "simple_imputation", "reason": "missing values present"})

    if report.get("type_inconsistencies"):
        steps.append({"step": "fix_column_types", "reason": "type inconsistencies found"})

    if report.get("categorical_columns"):
        steps.append({"step": "one_hot_encoding", "reason": "categorical variables found"})

    if report.get("skewed_features"):
        steps.append({"step": "log_transform", "reason": "skewed numeric distributions detected"})

    if report.get("outliers_detected"):
        steps.append({"step": "isolation_forest_outlier_removal", "reason": "potential outliers detected"})

    if report.get("numeric_columns"):
        steps.append({"step": "standardization", "reason": "numeric features benefit from scaling"})

    if int(df.shape[1]) >= 50 or len(report.get("numeric_columns", [])) >= 20:
        steps.append({"step": "pca", "reason": "high-dimensional feature space detected"})

    confidence = min(0.98, 0.60 + len(steps) * 0.05 + (0.05 if df.shape[0] > 1000 else 0.0))

    return {
        "confidence": round(confidence, 2),
        "steps": steps,
    }


def _fix_column_types(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    fixed_columns: List[str] = []
    result = df.copy()

    for col in result.select_dtypes(include=["object", "string"]).columns:
        series = result[col]
        non_null = series.dropna().astype(str)
        if non_null.empty:
            continue

        parsed_num = pd.to_numeric(non_null, errors="coerce")
        num_ratio = parsed_num.notna().mean()
        if num_ratio >= 0.9:
            result[col] = pd.to_numeric(result[col], errors="coerce")
            fixed_columns.append(col)
            continue

        parsed_date = pd.to_datetime(non_null, errors="coerce")
        date_ratio = parsed_date.notna().mean()
        if date_ratio >= 0.9:
            result[col] = pd.to_datetime(result[col], errors="coerce")
            fixed_columns.append(col)

    return result, fixed_columns


def auto_clean_dataset(df: pd.DataFrame) -> Dict[str, Any]:
    before_report = generate_dataset_health_report(df)
    before_score = calculate_data_quality_score(df, before_report)

    cleaned = df.copy()
    steps_applied: List[str] = []

    # 1) Remove duplicates
    before_rows = len(cleaned)
    cleaned = cleaned.drop_duplicates().reset_index(drop=True)
    if len(cleaned) < before_rows:
        steps_applied.append("remove_duplicates")

    # 2) Fix column types
    cleaned, fixed_cols = _fix_column_types(cleaned)
    if fixed_cols:
        steps_applied.append("fix_column_types")

    # 3) Handle missing values (KNN for numeric + mode fallback)
    numeric_cols = cleaned.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = [c for c in cleaned.columns if c not in numeric_cols]

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

    # 4) Outlier removal with IsolationForest
    numeric_cols = cleaned.select_dtypes(include=[np.number]).columns.tolist()
    if len(numeric_cols) >= 2 and len(cleaned) >= 20:
        iso = IsolationForest(contamination=0.05, random_state=42)
        outlier_flags = iso.fit_predict(cleaned[numeric_cols])
        keep_mask = outlier_flags == 1
        removed = int((~keep_mask).sum())
        if removed > 0:
            cleaned = cleaned.loc[keep_mask].reset_index(drop=True)
            steps_applied.append("isolation_forest_outlier_removal")

    # 5) Log transform skewed numeric features
    numeric_cols = cleaned.select_dtypes(include=[np.number]).columns.tolist()
    if numeric_cols:
        skewed_features = [
            col for col, val in cleaned[numeric_cols].skew(numeric_only=True).items() if abs(_safe_float(val)) >= 1.0
        ]
        transformed = 0
        for col in skewed_features:
            min_val = cleaned[col].min()
            shifted = cleaned[col] - min_val + 1 if _safe_float(min_val) <= 0 else cleaned[col]
            cleaned[col] = np.log1p(shifted)
            transformed += 1
        if transformed > 0:
            steps_applied.append("log_transform")

    # 6) One-hot encode categorical features
    cat_cols = cleaned.select_dtypes(include=["object", "category", "bool"]).columns.tolist()
    if cat_cols:
        cleaned = pd.get_dummies(cleaned, columns=cat_cols, drop_first=False)
        steps_applied.append("one_hot_encoding")

    # 7) Standardize numeric columns
    numeric_cols = cleaned.select_dtypes(include=[np.number]).columns.tolist()
    if numeric_cols:
        scaler = StandardScaler()
        cleaned[numeric_cols] = scaler.fit_transform(cleaned[numeric_cols])
        steps_applied.append("standardization")

    # 8) PCA for high-dimensional datasets
    numeric_cols = cleaned.select_dtypes(include=[np.number]).columns.tolist()
    if len(numeric_cols) >= 25:
        n_components = min(15, max(2, int(np.sqrt(len(numeric_cols)))))
        pca = PCA(n_components=n_components, random_state=42)
        matrix = pca.fit_transform(cleaned[numeric_cols])
        pca_cols = [f"pca_{i + 1}" for i in range(n_components)]
        cleaned = pd.DataFrame(matrix, columns=pca_cols)
        steps_applied.append("pca")

    after_report = generate_dataset_health_report(cleaned)
    after_score = calculate_data_quality_score(cleaned, after_report)

    pipeline = generate_auto_pipeline(df, before_report)

    return {
        "cleaned_df": cleaned,
        "before_score": before_score,
        "after_score": after_score,
        "before_report": before_report,
        "after_report": after_report,
        "pipeline": pipeline,
        "steps_applied": list(dict.fromkeys(steps_applied)),
    }
