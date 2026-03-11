"""Data quality scoring utilities (0-100)."""

from __future__ import annotations

from typing import Any, Dict, Tuple


def calculate_data_quality_score(shape: Tuple[int, int], report: Dict[str, Any]) -> Dict[str, Any]:
    rows = max(int(shape[0]), 1)
    cols = max(int(shape[1]), 1)

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
