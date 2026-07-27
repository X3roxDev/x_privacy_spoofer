"""Windows privilege, platform, and clipboard utilities."""

from __future__ import annotations

import ctypes
import os
import platform
import subprocess
from dataclasses import dataclass


@dataclass(slots=True)
class OperationResult:
    """A structured result for supported system operations."""

    success: bool
    message: str
    details: str = ""


class AdminUtils:
    """Utility methods for safe Windows operations."""

    @staticmethod
    def is_windows() -> bool:
        """Return True when running on Windows."""
        return platform.system().lower() == "windows"

    @staticmethod
    def is_admin() -> bool:
        """Return True when the current process has administrator rights."""
        if not AdminUtils.is_windows():
            return False
        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except (AttributeError, OSError):
            return False

    @staticmethod
    def username() -> str:
        """Return the current local username."""
        return os.environ.get("USERNAME") or os.environ.get("USER") or "UnknownUser"

    @staticmethod
    def copy_to_clipboard(text: str) -> OperationResult:
        """Copy text to the Windows clipboard using clip.exe."""
        if not AdminUtils.is_windows():
            return OperationResult(False, "Clipboard copy is available on Windows only.")

        try:
            subprocess.run(
                ["clip.exe"],
                input=text,
                text=True,
                check=True,
                capture_output=True,
                timeout=10,
            )
        except (subprocess.SubprocessError, OSError) as exc:
            return OperationResult(False, "Could not copy text to clipboard.", str(exc))

        return OperationResult(True, "Copied to clipboard.")
