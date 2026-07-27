"""Application configuration for X Privacy Spoofer."""

from __future__ import annotations

from pathlib import Path


APP_NAME = "X Privacy Spoofer"
APP_VERSION = "1.0.0"
APP_PURPOSE = "privacy and software testing"
APP_REPOSITORY = "https://github.com/X3roxDev"
APP_BANNER = r"""
▒██   ██▒     ██████  ██▓███   ▒█████   ▒█████    █████▒▓█████  ██▀███
▒▒ █ █ ▒░   ▒██    ▒ ▓██░  ██▒▒██▒  ██▒▒██▒  ██▒▓██   ▒ ▓█   ▀ ▓██ ▒ ██▒
░░  █   ░   ░ ▓██▄   ▓██░ ██▓▒▒██░  ██▒▒██░  ██▒▒████ ░ ▒███   ▓██ ░▄█ ▒
 ░ █ █ ▒      ▒   ██▒▒██▄█▓▒ ▒▒██   ██░▒██   ██░░▓█▒  ░ ▒▓█  ▄ ▒██▀▀█▄
▒██▒ ▒██▒   ▒██████▒▒▒██▒ ░  ░░ ████▓▒░░ ████▓▒░░▒█░    ░▒████▒░██▓ ▒██▒
▒▒ ░ ░▓ ░   ▒ ▒▓▒ ▒ ░▒▓▒░ ░  ░░ ▒░▒░▒░ ░ ▒░▒░▒░  ▒ ░    ░░ ▒░ ░░ ▒▓ ░▒▓░
░░   ░▒ ░   ░ ░▒  ░ ░░▒ ░       ░ ▒ ▒░   ░ ▒ ▒░  ░       ░ ░  ░  ░▒ ░ ▒░
 ░    ░     ░  ░  ░  ░░       ░ ░ ░ ▒  ░ ░ ░ ▒   ░ ░       ░     ░░   ░
 ░    ░           ░               ░ ░      ░ ░             ░  ░   ░
""".strip("\n")

BASE_DIR = Path(__file__).resolve().parent
BACKUP_DIR = BASE_DIR / "backups"
EXPORT_DIR = BASE_DIR / "exports"
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "x_privacy_spoofer.log"

SUPPORTED_WINDOWS = ("Windows 10", "Windows 11")

RESTRICTED_FEATURE_MESSAGE = (
    "This feature is not available because the application is designed only "
    "for legitimate privacy protection and testing."
)

RESTRICTED_KEYWORDS = (
    "hwid",
    "hardware ban",
    "anti-cheat",
    "anticheat",
    "game ban",
    "bios",
    "motherboard",
    "disk serial",
    "volume serial",
    "tpm",
    "machineguid",
    "product id",
    "activation",
    "kernel",
    "driver",
    "defender bypass",
    "secure boot",
    "license bypass",
)


def ensure_directories() -> None:
    """Create runtime directories if they are missing."""
    for directory in (BACKUP_DIR, EXPORT_DIR, LOG_DIR):
        directory.mkdir(parents=True, exist_ok=True)
