"""Safe fictional identifier generation for development and QA."""

from __future__ import annotations

import secrets
import uuid


class IdentifierGenerator:
    """Generate fictional identifiers that are not Windows system identifiers."""

    @staticmethod
    def generate() -> dict[str, str]:
        """Return a bundle of safe test identifiers."""
        return {
            "uuid_v4": str(uuid.uuid4()),
            "session_id": f"sess_{secrets.token_urlsafe(24)}",
            "client_id": f"client_{secrets.token_hex(12)}",
            "installation_token": f"install_test_{secrets.token_urlsafe(28)}",
            "device_token": f"device_test_{secrets.token_hex(18)}",
            "api_test_key": f"x_test_{secrets.token_urlsafe(32)}",
            "sid_like_fictional_identifier": IdentifierGenerator._fictional_sid(),
            "license_test_identifier": f"LIC-TEST-{secrets.token_hex(4).upper()}-{secrets.token_hex(4).upper()}",
            "notice": "All values are fictional test identifiers and are not real Windows system identifiers.",
        }

    @staticmethod
    def _fictional_sid() -> str:
        parts = [str(secrets.randbelow(900000000) + 100000000) for _ in range(4)]
        return "S-1-99-" + "-".join(parts)
