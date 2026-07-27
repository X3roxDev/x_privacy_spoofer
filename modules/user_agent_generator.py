"""Browser User-Agent generation."""

from __future__ import annotations

import secrets


class UserAgentGenerator:
    """Generate realistic Windows browser User-Agent strings."""

    @staticmethod
    def generate(browser: str | None = None, windows_version: str | None = None) -> str:
        """Generate a browser User-Agent for Windows 10 or 11 on 64-bit systems."""
        browser_name = browser or secrets.choice(["chrome", "edge", "firefox"])
        os_token = UserAgentGenerator._windows_token(windows_version)

        if browser_name.lower() in {"chrome", "google chrome"}:
            major = secrets.randbelow(18) + 122
            build = secrets.randbelow(4000) + 5900
            patch = secrets.randbelow(180) + 40
            return (
                f"Mozilla/5.0 ({os_token}; Win64; x64) AppleWebKit/537.36 "
                f"(KHTML, like Gecko) Chrome/{major}.0.{build}.{patch} Safari/537.36"
            )

        if browser_name.lower() in {"edge", "microsoft edge"}:
            major = secrets.randbelow(18) + 122
            build = secrets.randbelow(4000) + 5900
            patch = secrets.randbelow(180) + 40
            return (
                f"Mozilla/5.0 ({os_token}; Win64; x64) AppleWebKit/537.36 "
                f"(KHTML, like Gecko) Chrome/{major}.0.{build}.{patch} Safari/537.36 "
                f"Edg/{major}.0.{build}.{patch}"
            )

        major = secrets.randbelow(18) + 122
        return f"Mozilla/5.0 ({os_token}; Win64; x64; rv:{major}.0) Gecko/20100101 Firefox/{major}.0"

    @staticmethod
    def generate_all() -> dict[str, str]:
        """Generate one User-Agent per supported browser family."""
        return {
            "Google Chrome": UserAgentGenerator.generate("chrome"),
            "Microsoft Edge": UserAgentGenerator.generate("edge"),
            "Mozilla Firefox": UserAgentGenerator.generate("firefox"),
        }

    @staticmethod
    def _windows_token(windows_version: str | None = None) -> str:
        selected = windows_version or secrets.choice(["Windows NT 10.0", "Windows NT 10.0"])
        return "Windows NT 10.0" if "10" in selected or "11" in selected else "Windows NT 10.0"
