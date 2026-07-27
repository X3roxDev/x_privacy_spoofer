"""Fictional Windows test profile generation."""

from __future__ import annotations

import locale
import platform
import secrets
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

from config import APP_PURPOSE
from modules.hostname_manager import HostnameManager
from modules.identifier_generator import IdentifierGenerator
from modules.mac_manager import MacManager
from modules.user_agent_generator import UserAgentGenerator


class ProfileGenerator:
    """Create realistic fictional Windows test device profiles."""

    MANUFACTURERS = ("Dell Inc.", "HP", "Lenovo", "ASUS", "Acer", "Microsoft Corporation")
    MODELS = (
        "Latitude 5440",
        "EliteBook 840 G10",
        "ThinkPad T14 Gen 4",
        "ExpertBook B5",
        "Aspire 5",
        "Surface Laptop 6",
    )
    USER_PREFIXES = ("TestUser", "LabUser", "DevUser", "QAUser", "PrivacyUser")

    @classmethod
    def generate(cls) -> dict[str, str]:
        """Generate a complete fictional profile without modifying Windows."""
        identifiers = IdentifierGenerator.generate()
        windows_version = secrets.choice(["Windows 10 Pro", "Windows 11 Pro", "Windows 11 Enterprise"])
        architecture = secrets.choice(["AMD64", "x86_64"])
        hostname = HostnameManager.generate()
        username = f"{secrets.choice(cls.USER_PREFIXES)}{secrets.randbelow(90) + 10}"
        now = datetime.now().replace(microsecond=0).isoformat()
        current_locale = locale.getlocale()[0] or "en_US"

        return {
            "profile_name": "Windows Test Profile",
            "generated_at": now,
            "hostname": hostname,
            "username": username,
            "device_uuid": str(uuid.uuid4()),
            "installation_id": f"INST-{secrets.token_hex(8).upper()}",
            "machine_style_test_identifier": f"X-MACHINE-{secrets.token_hex(10).upper()}",
            "operating_system_name": "Microsoft Windows",
            "windows_version": windows_version,
            "architecture": architecture,
            "manufacturer": secrets.choice(cls.MANUFACTURERS),
            "device_model": secrets.choice(cls.MODELS),
            "time_zone": cls._timezone_name(),
            "locale": current_locale,
            "browser_user_agent": UserAgentGenerator.generate(windows_version=windows_version),
            "local_ip_placeholder": f"192.168.{secrets.randbelow(255)}.{secrets.randbelow(254) + 1}",
            "mac_address": MacManager.generate(),
            "test_client_id": identifiers["client_id"],
            "session_id": identifiers["session_id"],
            "device_token": identifiers["device_token"],
            "purpose": APP_PURPOSE,
            "safety_notice": "Generated values are fictional and do not overwrite protected Windows identifiers.",
        }

    @staticmethod
    def _timezone_name() -> str:
        try:
            return datetime.now().astimezone().tzinfo.key  # type: ignore[attr-defined]
        except AttributeError:
            return str(datetime.now(ZoneInfo("UTC")).astimezone().tzinfo)
        except Exception:
            return "Local"
