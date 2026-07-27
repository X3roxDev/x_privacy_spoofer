"""Read-only current system identity collection."""

from __future__ import annotations

import getpass
import platform
import socket
import time
from datetime import datetime

import psutil

from modules.admin_utils import AdminUtils


class SystemInfo:
    """Collect and mask local system identity information."""

    @staticmethod
    def collect(mask_sensitive: bool = True) -> dict[str, object]:
        """Collect read-only system information."""
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        info: dict[str, object] = {
            "hostname": socket.gethostname(),
            "current_username": getpass.getuser(),
            "windows_edition": platform.platform(),
            "windows_version": platform.version(),
            "build_number": platform.win32_ver()[1] if AdminUtils.is_windows() else platform.release(),
            "cpu_architecture": platform.machine(),
            "local_ip_address": SystemInfo.local_ip(),
            "network_adapters": SystemInfo.network_adapters(mask_sensitive=mask_sensitive),
            "system_uptime": SystemInfo.format_uptime(time.time() - psutil.boot_time()),
            "time_zone": datetime.now().astimezone().tzname() or "Unknown",
            "administrator_status": "Administrator" if AdminUtils.is_admin() else "Standard user",
        }
        if mask_sensitive:
            info["hostname"] = SystemInfo.mask_text(str(info["hostname"]))
            info["current_username"] = SystemInfo.mask_text(str(info["current_username"]))
            info["local_ip_address"] = SystemInfo.mask_ip(str(info["local_ip_address"]))
        return info

    @staticmethod
    def local_ip() -> str:
        """Return a likely local IPv4 address without querying a public IP service."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.connect(("8.8.8.8", 80))
                return str(sock.getsockname()[0])
        except OSError:
            try:
                return socket.gethostbyname(socket.gethostname())
            except OSError:
                return "Unavailable"

    @staticmethod
    def network_adapters(mask_sensitive: bool = True) -> list[dict[str, str]]:
        """Return adapter names, MAC addresses, and state."""
        stats = psutil.net_if_stats()
        rows: list[dict[str, str]] = []
        for name, addresses in psutil.net_if_addrs().items():
            mac = ""
            ipv4 = ""
            for address in addresses:
                if getattr(psutil, "AF_LINK", object()) == address.family:
                    mac = address.address
                elif socket.AF_INET == address.family:
                    ipv4 = address.address
            adapter_stats = stats.get(name)
            rows.append(
                {
                    "name": name if not mask_sensitive else SystemInfo.mask_text(name),
                    "mac_address": SystemInfo.mask_mac(mac) if mask_sensitive else mac,
                    "ipv4_address": SystemInfo.mask_ip(ipv4) if mask_sensitive else ipv4,
                    "status": "up" if adapter_stats and adapter_stats.isup else "down",
                }
            )
        return rows

    @staticmethod
    def format_uptime(seconds: float) -> str:
        """Format uptime seconds as days, hours, and minutes."""
        minutes = int(seconds // 60)
        days, remainder = divmod(minutes, 1440)
        hours, minutes = divmod(remainder, 60)
        return f"{days}d {hours}h {minutes}m"

    @staticmethod
    def mask_text(value: str) -> str:
        """Partially mask a text value."""
        if len(value) <= 2:
            return "*" * len(value)
        return value[:2] + "*" * max(2, len(value) - 4) + value[-2:]

    @staticmethod
    def mask_ip(value: str) -> str:
        """Mask the host portion of an IPv4 address."""
        parts = value.split(".")
        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.*.*"
        return SystemInfo.mask_text(value) if value else ""

    @staticmethod
    def mask_mac(value: str) -> str:
        """Mask the second half of a MAC address."""
        if not value:
            return ""
        parts = value.replace("-", ":").split(":")
        if len(parts) == 6:
            return ":".join(parts[:3] + ["**", "**", "**"])
        return SystemInfo.mask_text(value)
