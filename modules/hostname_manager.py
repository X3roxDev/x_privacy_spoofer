"""Hostname generation and supported Windows hostname changes."""

from __future__ import annotations

import platform
import re
import secrets
import socket
import string
import subprocess

from modules.admin_utils import AdminUtils, OperationResult
from modules.backup_manager import BackupManager


class HostnameManager:
    """Manage fictional hostname generation and supported rename operations."""

    HOSTNAME_PATTERN = re.compile(r"^[A-Z0-9](?:[A-Z0-9-]{0,13}[A-Z0-9])?$")

    @staticmethod
    def current_hostname() -> str:
        """Return the current computer hostname."""
        return socket.gethostname()

    @staticmethod
    def generate() -> str:
        """Generate a realistic Windows hostname."""
        templates = [
            "DESKTOP-{suffix}",
            "WORKSTATION-{short}",
            "DEV-PC-{digits}",
            "WINLAB-{short}",
            "QA-PC-{digits}",
            "X-LAB-{short}",
        ]
        template = secrets.choice(templates)
        suffix = "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        short = "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4))
        digits = "".join(secrets.choice(string.digits) for _ in range(4))
        return template.format(suffix=suffix, short=short, digits=digits)

    @classmethod
    def validate(cls, hostname: str) -> bool:
        """Validate a Windows-compatible computer name."""
        return bool(cls.HOSTNAME_PATTERN.fullmatch(hostname.strip().upper()))

    @classmethod
    def apply_hostname(cls, new_hostname: str, backup_manager: BackupManager) -> OperationResult:
        """Apply a hostname using Rename-Computer after validation and backup."""
        normalized = new_hostname.strip().upper()
        if not AdminUtils.is_windows():
            return OperationResult(False, "Hostname changes are supported only on Windows.")
        if not cls.validate(normalized):
            return OperationResult(False, "Invalid hostname. Use 1-15 letters, numbers, or hyphens.")
        if not AdminUtils.is_admin():
            return OperationResult(False, "Administrator privileges are required to rename this computer.")

        current = cls.current_hostname()
        if current.upper() == normalized:
            return OperationResult(False, "The requested hostname is already active.")

        backup_manager.create_backup(
            change_type="hostname",
            original_hostname=current,
            selected_network_adapter=None,
            previous_mac_config=None,
            notes=f"Preparing to rename host from {current} to {normalized}.",
        )

        command = [
            "powershell.exe",
            "-NoProfile",
            "-Command",
            "& { param($NewName) Rename-Computer -NewName $NewName -Force }",
            normalized,
        ]

        try:
            completed = subprocess.run(command, capture_output=True, text=True, timeout=90, check=False)
        except (subprocess.SubprocessError, OSError) as exc:
            return OperationResult(False, "Could not run Rename-Computer.", str(exc))

        if completed.returncode != 0:
            return OperationResult(False, "Hostname change failed.", completed.stderr.strip())

        return OperationResult(
            True,
            "Hostname change requested successfully. Restart Windows for the change to fully apply.",
        )

    @classmethod
    def restore_from_backup(cls, backup: dict[str, object], backup_manager: BackupManager) -> OperationResult:
        """Restore a hostname from a validated backup record."""
        original = str(backup.get("original_hostname") or "").strip()
        if not original:
            return OperationResult(False, "This backup does not contain an original hostname.")
        return cls.apply_hostname(original, backup_manager)

    @staticmethod
    def platform_name() -> str:
        """Return a display-friendly platform name."""
        return platform.platform()
