"""Visualization-ready payload generators for frontend quality and pipeline views."""

from __future__ import annotations

from typing import Any, Dict, List


def build_pipeline_visualization(pipeline: Dict[str, Any]) -> Dict[str, Any]:
    steps = pipeline.get("steps", [])

    nodes: List[Dict[str, Any]] = [{"id": "start", "label": "Start", "type": "start"}]
    edges: List[Dict[str, Any]] = []

    prev = "start"
    for idx, step in enumerate(steps, start=1):
        node_id = f"step_{idx}"
        nodes.append(
            {
                "id": node_id,
                "label": step.get("step", f"step_{idx}"),
                "reason": step.get("reason", ""),
                "type": "process",
            }
        )
        edges.append({"from": prev, "to": node_id})
        prev = node_id

    nodes.append({"id": "end", "label": "Ready", "type": "end"})
    edges.append({"from": prev, "to": "end"})

    return {
        "confidence": pipeline.get("confidence", 0.0),
        "nodes": nodes,
        "edges": edges,
    }


def build_quality_snapshot(report: Dict[str, Any], score: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "score": score.get("score", 0),
        "issues_count": len(report.get("issues_detected", [])),
        "duplicates": report.get("duplicates", 0),
        "missing_total": int(sum(report.get("missing_values", {}).values())),
        "outlier_rows": report.get("outlier_rows", 0),
        "engine": report.get("processing_engine", "pandas"),
    }
