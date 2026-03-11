"""In-memory pipeline history and export tracking."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List


@dataclass
class PipelineHistoryManager:
    records: List[Dict[str, Any]] = field(default_factory=list)

    def add_generated(self, pipeline: Dict[str, Any], source: str = "auto") -> None:
        self.records.append(
            {
                "timestamp": datetime.now().isoformat(),
                "event": "pipeline_generated",
                "source": source,
                "confidence": pipeline.get("confidence", 0.0),
                "steps": pipeline.get("steps", []),
            }
        )

    def add_export(self, export_format: str, pipeline: Dict[str, Any]) -> None:
        self.records.append(
            {
                "timestamp": datetime.now().isoformat(),
                "event": "pipeline_exported",
                "format": export_format,
                "confidence": pipeline.get("confidence", 0.0),
                "steps": pipeline.get("steps", []),
            }
        )

    def list_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self.records[-limit:]
