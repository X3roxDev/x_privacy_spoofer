"""Backup creation, validation, listing, and loading."""

from __future__ import annotations

import json
import logging
import secrets
from datetime import datetime
from pathlib import Path
from typing import Any

from config import APP_VERSION, BACKUP_DIR, ensure_directories


class BackupManager:
    """Manage timestamped backups for supported changes."""

    REQUIRED_KEYS = {"application_version", "date_time", "change_type"}

    def __init__(self, backup_dir: Path = BACKUP_DIR) -> None:
        ensure_directories()
        self.backup_dir = backup_dir

    def create_backup(
        self,
        change_type: str,
        original_hostname: str | None,
        selected_network_adapter: str | None,
        previous_mac_config: dict[str, Any] | None,
        notes: str = "",
    ) -> Path:
        """Create a timestamped JSON backup file."""
        timestamp = datetime.now().replace(microsecond=0).isoformat()
        safe_timestamp = timestamp.replace(":", "").replace("-", "")
        record: dict[str, Any] = {
            "application_version": APP_VERSION,
            "date_time": timestamp,
            "change_type": change_type,
            "original_hostname": original_hostname,
            "selected_network_adapter": selected_network_adapter,
            "previous_mac_config": previous_mac_config,
            "notes": notes,
        }
        filename = f"backup_{safe_timestamp}_{change_type}_{secrets.token_hex(3)}.json"
        path = self.backup_dir / filename
        path.write_text(json.dumps(record, indent=2), encoding="utf-8")
        logging.getLogger("x_privacy_spoofer").info("Backup created: %s (%s)", filename, change_type)
        return path

    def list_backups(self) -> list[Path]:
        """List backup files newest first."""
        return sorted(self.backup_dir.glob("backup_*.json"), key=lambda item: item.stat().st_mtime, reverse=True)

    def load_backup(self, path: Path) -> dict[str, Any]:
        """Load and validate a backup record."""
        if path.parent.resolve() != self.backup_dir.resolve():
            raise ValueError("Backup path is outside the backups directory.")
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Backup file must contain a JSON object.")
        self.validate_backup(data)
        return data

    @classmethod
    def validate_backup(cls, data: dict[str, Any]) -> None:
        """Validate backup schema and supported change type."""
        missing = cls.REQUIRED_KEYS.difference(data)
        if missing:
            raise ValueError(f"Backup is missing required fields: {', '.join(sorted(missing))}")
        if data["change_type"] not in {"manual", "hostname", "mac_address"}:
            raise ValueError("Backup change_type is not supported.")
