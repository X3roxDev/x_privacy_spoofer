"""MAC address generation and supported Windows adapter testing mode."""

from __future__ import annotations

import re
import secrets
import subprocess

import psutil

from modules.admin_utils import AdminUtils, OperationResult
from modules.backup_manager import BackupManager


class MacManager:
    """Generate and optionally apply locally administered MAC addresses."""

    MAC_PATTERN = re.compile(r"^(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$|^[0-9A-Fa-f]{12}$")

    @staticmethod
    def generate() -> str:
        """Generate a locally administered unicast MAC address."""
        first_octet = (secrets.randbits(8) & 0xFC) | 0x02
        octets = [first_octet] + [secrets.randbits(8) for _ in range(5)]
        return ":".join(f"{octet:02X}" for octet in octets)

    @classmethod
    def validate(cls, mac_address: str) -> bool:
        """Validate a MAC address and require local-admin unicast bits."""
        if not cls.MAC_PATTERN.fullmatch(mac_address.strip()):
            return False
        compact = cls.compact(mac_address)
        first = int(compact[:2], 16)
        is_unicast = (first & 0x01) == 0
        is_locally_administered = (first & 0x02) == 0x02
        return is_unicast and is_locally_administered

    @staticmethod
    def compact(mac_address: str) -> str:
        """Return a MAC address without separators."""
        return mac_address.replace(":", "").replace("-", "").upper()

    @staticmethod
    def pretty(mac_address: str) -> str:
        """Return a colon-separated MAC address."""
        compact = MacManager.compact(mac_address)
        return ":".join(compact[index : index + 2] for index in range(0, 12, 2))

    @staticmethod
    def list_adapters() -> list[dict[str, str]]:
        """List network adapters with MAC addresses."""
        stats = psutil.net_if_stats()
        adapters: list[dict[str, str]] = []
        for name, addresses in psutil.net_if_addrs().items():
            mac = ""
            for address in addresses:
                if getattr(psutil, "AF_LINK", object()) == address.family:
                    mac = address.address
                    break
            if not mac or mac == "00:00:00:00:00:00":
                continue
            adapter_stats = stats.get(name)
            adapters.append(
                {
                    "name": name,
                    "mac_address": mac,
                    "status": "up" if adapter_stats and adapter_stats.isup else "down",
                    "speed_mbps": str(adapter_stats.speed if adapter_stats else 0),
                }
            )
        return adapters

    @staticmethod
    def get_network_address_registry_value(adapter_name: str) -> str:
        """Read the adapter NetworkAddress advanced property when available."""
        if not AdminUtils.is_windows():
            return ""
        command = [
            "powershell.exe",
            "-NoProfile",
            "-Command",
            (
                "& { param($Name) "
                "try { "
                "  $p = Get-NetAdapterAdvancedProperty -Name $Name -RegistryKeyword 'NetworkAddress' -ErrorAction Stop; "
                "  [string]$p.RegistryValue "
                "} catch { '' } "
                "}"
            ),
            adapter_name,
        ]
        try:
            completed = subprocess.run(command, capture_output=True, text=True, timeout=30, check=False)
        except (subprocess.SubprocessError, OSError):
            return ""
        return completed.stdout.strip()

    @classmethod
    def apply_adapter_mac(
        cls,
        adapter_name: str,
        mac_address: str,
        backup_manager: BackupManager,
    ) -> OperationResult:
        """Apply a MAC address through supported Windows adapter advanced settings."""
        if not AdminUtils.is_windows():
            return OperationResult(False, "Adapter MAC testing mode is supported only on Windows.")
        if not AdminUtils.is_admin():
            return OperationResult(False, "Administrator privileges are required to change adapter settings.")
        if not cls.validate(mac_address):
            return OperationResult(False, "Invalid MAC. It must be locally administered and unicast.")

        adapters = {adapter["name"]: adapter for adapter in cls.list_adapters()}
        if adapter_name not in adapters:
            return OperationResult(False, "Selected adapter was not found.")

        previous_registry_value = cls.get_network_address_registry_value(adapter_name)
        backup_manager.create_backup(
            change_type="mac_address",
            original_hostname=None,
            selected_network_adapter=adapter_name,
            previous_mac_config={
                "display_mac_address": adapters[adapter_name]["mac_address"],
                "network_address_registry_value": previous_registry_value,
            },
            notes=f"Preparing to set adapter {adapter_name} test MAC to {cls.pretty(mac_address)}.",
        )

        compact = cls.compact(mac_address)
        set_result = cls._set_network_address(adapter_name, compact)
        if not set_result.success:
            return set_result

        restart_result = cls.restart_adapter(adapter_name)
        if not restart_result.success:
            return OperationResult(
                False,
                "MAC value was set, but the selected adapter could not be restarted.",
                restart_result.details,
            )

        return OperationResult(True, "Adapter MAC testing value applied and selected adapter restarted.")

    @classmethod
    def restore_from_backup(cls, backup: dict[str, object]) -> OperationResult:
        """Restore adapter MAC configuration from a backup."""
        adapter_name = str(backup.get("selected_network_adapter") or "").strip()
        previous_config = backup.get("previous_mac_config")
        if not isinstance(previous_config, dict) or not adapter_name:
            return OperationResult(False, "This backup does not contain adapter MAC settings.")
        if not AdminUtils.is_windows():
            return OperationResult(False, "Adapter restore is supported only on Windows.")
        if not AdminUtils.is_admin():
            return OperationResult(False, "Administrator privileges are required to restore adapter settings.")

        previous_value = str(previous_config.get("network_address_registry_value") or "").strip()
        result = cls._restore_network_address(adapter_name, previous_value)
        if not result.success:
            return result

        restart_result = cls.restart_adapter(adapter_name)
        if not restart_result.success:
            return OperationResult(
                False,
                "MAC configuration was restored, but the selected adapter could not be restarted.",
                restart_result.details,
            )
        return OperationResult(True, "Adapter MAC configuration restored and selected adapter restarted.")

    @staticmethod
    def _set_network_address(adapter_name: str, registry_value: str) -> OperationResult:
        command = [
            "powershell.exe",
            "-NoProfile",
            "-Command",
            (
                "& { param($Name, $Value) "
                "Set-NetAdapterAdvancedProperty -Name $Name -RegistryKeyword 'NetworkAddress' "
                "-RegistryValue $Value -NoRestart -ErrorAction Stop "
                "}"
            ),
            adapter_name,
            registry_value,
        ]
        return MacManager._run_powershell(command, "Could not set adapter NetworkAddress property.")

    @staticmethod
    def _restore_network_address(adapter_name: str, previous_value: str) -> OperationResult:
        command = [
            "powershell.exe",
            "-NoProfile",
            "-Command",
            (
                "& { param($Name, $Value) "
                "if ([string]::IsNullOrWhiteSpace($Value)) { "
                "  try { Reset-NetAdapterAdvancedProperty -Name $Name -RegistryKeyword 'NetworkAddress' "
                "    -NoRestart -ErrorAction Stop } "
                "  catch { Set-NetAdapterAdvancedProperty -Name $Name -RegistryKeyword 'NetworkAddress' "
                "    -RegistryValue '' -NoRestart -ErrorAction Stop } "
                "} else { "
                "  Set-NetAdapterAdvancedProperty -Name $Name -RegistryKeyword 'NetworkAddress' "
                "    -RegistryValue $Value -NoRestart -ErrorAction Stop "
                "} "
                "}"
            ),
            adapter_name,
            previous_value,
        ]
        return MacManager._run_powershell(command, "Could not restore adapter NetworkAddress property.")

    @staticmethod
    def restart_adapter(adapter_name: str) -> OperationResult:
        """Restart only the selected adapter."""
        command = [
            "powershell.exe",
            "-NoProfile",
            "-Command",
            (
                "& { param($Name) "
                "Disable-NetAdapter -Name $Name -Confirm:$false -ErrorAction Stop; "
                "Start-Sleep -Seconds 2; "
                "Enable-NetAdapter -Name $Name -Confirm:$false -ErrorAction Stop "
                "}"
            ),
            adapter_name,
        ]
        return MacManager._run_powershell(command, "Could not restart selected adapter.")

    @staticmethod
    def _run_powershell(command: list[str], failure_message: str) -> OperationResult:
        try:
            completed = subprocess.run(command, capture_output=True, text=True, timeout=120, check=False)
        except (subprocess.SubprocessError, OSError) as exc:
            return OperationResult(False, failure_message, str(exc))

        if completed.returncode != 0:
            return OperationResult(False, failure_message, completed.stderr.strip())
        return OperationResult(True, "PowerShell command completed successfully.")
