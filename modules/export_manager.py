"""Export generated profiles as JSON, TXT, or CSV."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from config import EXPORT_DIR, ensure_directories


class ExportManager:
    """Handle generated profile exports."""

    def __init__(self, export_dir: Path = EXPORT_DIR) -> None:
        ensure_directories()
        self.export_dir = export_dir

    def export(self, profile: dict[str, Any], export_format: str) -> Path:
        """Export a profile in json, txt, or csv format."""
        fmt = export_format.strip().lower()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if fmt not in {"json", "txt", "csv"}:
            raise ValueError("Export format must be json, txt, or csv.")

        path = self.export_dir / f"x_profile_{timestamp}.{fmt}"
        if fmt == "json":
            path.write_text(json.dumps(profile, indent=2), encoding="utf-8")
        elif fmt == "txt":
            lines = [f"{key}: {value}" for key, value in profile.items()]
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        else:
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(["field", "value"])
                for key, value in profile.items():
                    writer.writerow([key, value])
        return path
