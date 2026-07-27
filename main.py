"""X Privacy Spoofer terminal application."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from config import RESTRICTED_FEATURE_MESSAGE, RESTRICTED_KEYWORDS, ensure_directories
from modules.admin_utils import AdminUtils
from modules.backup_manager import BackupManager
from modules.console_ui import ConsoleUI
from modules.export_manager import ExportManager
from modules.hostname_manager import HostnameManager
from modules.identifier_generator import IdentifierGenerator
from modules.logger import AppLogger
from modules.mac_manager import MacManager
from modules.profile_generator import ProfileGenerator
from modules.system_info import SystemInfo
from modules.user_agent_generator import UserAgentGenerator


class XPrivacySpooferApp:
    """Interactive Windows privacy and testing terminal app."""

    def __init__(self) -> None:
        ensure_directories()
        self.ui = ConsoleUI()
        self.logger = AppLogger.get_logger()
        self.backups = BackupManager()
        self.exports = ExportManager()
        self.last_profile: dict[str, Any] | None = None

    def run(self) -> None:
        """Run the main menu loop."""
        self.logger.info("Application start")
        while True:
            self.ui.clear()
            self.ui.header()
            self.ui.menu()
            choice = self.ui.prompt("Select option").strip()

            if self._is_restricted_request(choice):
                self.ui.restricted(RESTRICTED_FEATURE_MESSAGE)
                self.logger.warning("Restricted feature request blocked")
                self.ui.pause()
                continue

            handlers = {
                "1": self.generate_profile,
                "2": self.hostname_menu,
                "3": self.mac_menu,
                "4": self.user_agent_menu,
                "5": self.identifier_menu,
                "6": self.system_info_menu,
                "7": self.create_manual_backup,
                "8": self.restore_menu,
                "9": self.export_profile_menu,
                "10": self.view_logs,
                "0": self.exit_app,
            }
            handler = handlers.get(choice)
            if handler is None:
                self.ui.error("Unknown option.")
                self.ui.pause()
                continue
            handler()

    def generate_profile(self) -> None:
        """Generate and display a fictional test profile."""
        self.ui.clear()
        self.ui.header()
        self.ui.spinner("Generating fictional test profile")
        self.last_profile = ProfileGenerator.generate()
        self.logger.info("Generated fictional profile")
        self.ui.dict_table("Generated Fake Device Profile", self.last_profile)
        if self.ui.confirm("Export this profile now?", default=False):
            self._export_data(self.last_profile)
        self.ui.pause()

    def hostname_menu(self) -> None:
        """Generate, copy, apply, or restore hostnames."""
        generated = HostnameManager.generate()
        while True:
            self.ui.clear()
            self.ui.header()
            self.ui.dict_table(
                "Hostname Generator",
                {
                    "generated_hostname": generated,
                    "current_hostname": HostnameManager.current_hostname(),
                    "administrator": AdminUtils.is_admin(),
                },
            )
            self.ui.console.print("[1] Generate new hostname")
            self.ui.console.print("[2] Copy generated hostname")
            self.ui.console.print("[3] Apply generated hostname")
            self.ui.console.print("[4] Restore hostname from backup")
            self.ui.console.print("[0] Back")
            choice = self.ui.prompt("Select option").strip()

            if choice == "1":
                generated = HostnameManager.generate()
                self.logger.info("Generated hostname preview")
            elif choice == "2":
                self._show_result(AdminUtils.copy_to_clipboard(generated))
            elif choice == "3":
                self._confirm_and_apply_hostname(generated)
            elif choice == "4":
                self.restore_menu(filter_type="hostname")
            elif choice == "0":
                return
            elif self._is_restricted_request(choice):
                self.ui.restricted(RESTRICTED_FEATURE_MESSAGE)
                self.logger.warning("Restricted feature request blocked in hostname menu")
            else:
                self.ui.error("Unknown option.")
            self.ui.pause()

    def _confirm_and_apply_hostname(self, hostname: str) -> None:
        if not HostnameManager.validate(hostname):
            self.ui.error("Generated hostname did not pass validation.")
            return
        self.ui.warning("This will request a supported Windows hostname change.")
        self.ui.warning("A backup will be created first. A Windows restart is required afterward.")
        if not self.ui.confirm(f"Apply hostname {hostname}?", default=False):
            self.logger.info("Hostname apply cancelled")
            return
        result = HostnameManager.apply_hostname(hostname, self.backups)
        self._show_result(result)
        self.logger.info("Hostname apply attempted: %s", result.success)

    def mac_menu(self) -> None:
        """Generate, copy, test-apply, or restore MAC addresses."""
        generated = MacManager.generate()
        while True:
            self.ui.clear()
            self.ui.header()
            self.ui.dict_table(
                "MAC Address Generator",
                {
                    "generated_mac": generated,
                    "type": "locally administered unicast",
                    "adapter_testing_mode": "optional supported Windows adapter settings",
                    "administrator": AdminUtils.is_admin(),
                },
            )
            self.ui.console.print("[1] Generate new MAC")
            self.ui.console.print("[2] Copy generated MAC")
            self.ui.console.print("[3] View adapters")
            self.ui.console.print("[4] Apply to selected adapter for testing")
            self.ui.console.print("[5] Restore adapter MAC from backup")
            self.ui.console.print("[0] Back")
            choice = self.ui.prompt("Select option").strip()

            if choice == "1":
                generated = MacManager.generate()
                self.logger.info("Generated locally administered MAC preview")
            elif choice == "2":
                self._show_result(AdminUtils.copy_to_clipboard(generated))
            elif choice == "3":
                self._show_adapters()
            elif choice == "4":
                self._confirm_and_apply_mac(generated)
            elif choice == "5":
                self.restore_menu(filter_type="mac_address")
            elif choice == "0":
                return
            elif self._is_restricted_request(choice):
                self.ui.restricted(RESTRICTED_FEATURE_MESSAGE)
                self.logger.warning("Restricted feature request blocked in MAC menu")
            else:
                self.ui.error("Unknown option.")
            self.ui.pause()

    def _show_adapters(self) -> None:
        adapters = MacManager.list_adapters()
        if not adapters:
            self.ui.warning("No adapters with MAC addresses were detected.")
            return
        rows = [
            (index + 1, adapter["name"], adapter["mac_address"], adapter["status"], adapter["speed_mbps"])
            for index, adapter in enumerate(adapters)
        ]
        self.ui.rows_table("Detected Network Adapters", ("#", "Name", "MAC", "Status", "Speed Mbps"), rows)

    def _confirm_and_apply_mac(self, mac_address: str) -> None:
        adapters = MacManager.list_adapters()
        if not adapters:
            self.ui.warning("No adapters with MAC addresses were detected.")
            return

        rows = [
            (index + 1, adapter["name"], adapter["mac_address"], adapter["status"], adapter["speed_mbps"])
            for index, adapter in enumerate(adapters)
        ]
        self.ui.rows_table("Choose Adapter", ("#", "Name", "Current MAC", "Status", "Speed Mbps"), rows)
        selected = self.ui.prompt("Adapter number").strip()
        if not selected.isdigit() or not 1 <= int(selected) <= len(adapters):
            self.ui.error("Invalid adapter selection.")
            return

        adapter_name = adapters[int(selected) - 1]["name"]
        if not MacManager.validate(mac_address):
            self.ui.error("Generated MAC did not pass local-admin unicast validation.")
            return

        self.ui.warning("This will change only the selected adapter's supported NetworkAddress setting.")
        self.ui.warning("The selected adapter will be disabled and re-enabled after the backup is created.")
        if not self.ui.confirm(f"Apply {mac_address} to adapter {adapter_name}?", default=False):
            self.logger.info("MAC apply cancelled")
            return

        result = MacManager.apply_adapter_mac(adapter_name, mac_address, self.backups)
        self._show_result(result)
        self.logger.info("MAC apply attempted: %s", result.success)

    def user_agent_menu(self) -> None:
        """Generate, copy, and export browser User-Agent values."""
        data = UserAgentGenerator.generate_all()
        while True:
            self.ui.clear()
            self.ui.header()
            self.ui.dict_table("Browser User-Agent Generator", data)
            self.ui.console.print("[1] Regenerate")
            self.ui.console.print("[2] Copy Chrome")
            self.ui.console.print("[3] Copy Edge")
            self.ui.console.print("[4] Copy Firefox")
            self.ui.console.print("[5] Export User-Agents")
            self.ui.console.print("[0] Back")
            choice = self.ui.prompt("Select option").strip()

            if choice == "1":
                data = UserAgentGenerator.generate_all()
                self.logger.info("Generated browser User-Agent values")
            elif choice in {"2", "3", "4"}:
                key = {"2": "Google Chrome", "3": "Microsoft Edge", "4": "Mozilla Firefox"}[choice]
                self._show_result(AdminUtils.copy_to_clipboard(data[key]))
            elif choice == "5":
                self._export_data(data)
            elif choice == "0":
                return
            else:
                self.ui.error("Unknown option.")
            self.ui.pause()

    def identifier_menu(self) -> None:
        """Generate and export fictional identifiers."""
        data = IdentifierGenerator.generate()
        while True:
            self.ui.clear()
            self.ui.header()
            self.ui.dict_table("Fictional Test Identifiers", data)
            self.ui.console.print("[1] Regenerate")
            self.ui.console.print("[2] Export identifiers")
            self.ui.console.print("[0] Back")
            choice = self.ui.prompt("Select option").strip()

            if choice == "1":
                data = IdentifierGenerator.generate()
                self.logger.info("Generated fictional identifiers")
            elif choice == "2":
                self._export_data(data)
            elif choice == "0":
                return
            else:
                self.ui.error("Unknown option.")
            self.ui.pause()

    def system_info_menu(self) -> None:
        """Display read-only system identity information with masking controls."""
        while True:
            self.ui.clear()
            self.ui.header()
            self.ui.console.print("[1] Mask sensitive values")
            self.ui.console.print("[2] Show full local values")
            self.ui.console.print("[0] Back")
            choice = self.ui.prompt("Select option", default="1").strip()
            if choice == "0":
                return
            if choice not in {"1", "2"}:
                self.ui.error("Unknown option.")
                self.ui.pause()
                continue

            mask_sensitive = choice == "1"
            info = SystemInfo.collect(mask_sensitive=mask_sensitive)
            adapters = info.pop("network_adapters", [])
            self.ui.dict_table("Current System Identity", info)
            if isinstance(adapters, list):
                rows = [
                    (
                        adapter.get("name", ""),
                        adapter.get("mac_address", ""),
                        adapter.get("ipv4_address", ""),
                        adapter.get("status", ""),
                    )
                    for adapter in adapters
                    if isinstance(adapter, dict)
                ]
                self.ui.rows_table("Network Adapters", ("Name", "MAC", "IPv4", "Status"), rows)
            self.logger.info("Viewed current system identity with masking=%s", mask_sensitive)
            self.ui.pause()

    def create_manual_backup(self) -> None:
        """Create a manual snapshot backup of restorable supported settings."""
        self.ui.clear()
        self.ui.header()
        path = self.backups.create_backup(
            change_type="manual",
            original_hostname=HostnameManager.current_hostname(),
            selected_network_adapter=None,
            previous_mac_config=None,
            notes="Manual snapshot created from the backup menu.",
        )
        self.logger.info("Manual backup created")
        self.ui.success(f"Backup created: {path.name}")
        self.ui.pause()

    def restore_menu(self, filter_type: str | None = None) -> None:
        """Restore supported settings from a validated backup."""
        self.ui.clear()
        self.ui.header()
        backup_paths = self.backups.list_backups()
        records: list[tuple[Path, dict[str, Any]]] = []
        for path in backup_paths:
            try:
                record = self.backups.load_backup(path)
            except (OSError, ValueError) as exc:
                self.logger.error("Invalid backup skipped: %s", exc)
                continue
            if filter_type and record.get("change_type") != filter_type:
                continue
            records.append((path, record))

        if not records:
            self.ui.warning("No matching valid backups found.")
            return

        rows = [
            (
                index + 1,
                path.name,
                record.get("change_type", ""),
                record.get("date_time", ""),
                record.get("selected_network_adapter") or record.get("original_hostname") or "",
            )
            for index, (path, record) in enumerate(records)
        ]
        self.ui.rows_table("Available Backups", ("#", "File", "Type", "Date", "Target"), rows)
        selected = self.ui.prompt("Backup number").strip()
        if not selected.isdigit() or not 1 <= int(selected) <= len(records):
            self.ui.error("Invalid backup selection.")
            return

        path, record = records[int(selected) - 1]
        change_type = str(record.get("change_type"))
        if change_type == "manual":
            self.ui.warning("Manual snapshots are records only and do not perform a restore action.")
            return

        self.ui.warning(f"Restore will use validated backup file: {path.name}")
        if not self.ui.confirm("Continue with restore?", default=False):
            self.logger.info("Restore cancelled")
            return

        if change_type == "hostname":
            result = HostnameManager.restore_from_backup(record, self.backups)
        elif change_type == "mac_address":
            result = MacManager.restore_from_backup(record)
        else:
            self.ui.error("Backup change type is not supported.")
            return

        self._show_result(result)
        self.logger.info("Restore attempted for %s: %s", change_type, result.success)

    def export_profile_menu(self) -> None:
        """Export the most recent generated profile."""
        self.ui.clear()
        self.ui.header()
        if self.last_profile is None:
            self.ui.warning("No generated profile is available yet.")
            if not self.ui.confirm("Generate a new fake device profile now?", default=True):
                return
            self.last_profile = ProfileGenerator.generate()
            self.logger.info("Generated fictional profile for export")
        self._export_data(self.last_profile)
        self.ui.pause()

    def _export_data(self, data: dict[str, Any]) -> None:
        export_format = self.ui.prompt("Export format", default="json").strip().lower()
        try:
            path = self.exports.export(data, export_format)
        except (OSError, ValueError) as exc:
            self.ui.error(f"Export failed: {exc}")
            self.logger.error("Export failed: %s", exc)
            return
        self.ui.success(f"Export saved: {path.name}")
        self.logger.info("Export saved in %s format", export_format)

    def view_logs(self) -> None:
        """Show the most recent local application log lines."""
        self.ui.clear()
        self.ui.header()
        log_path = Path("logs") / "x_privacy_spoofer.log"
        absolute_log_path = Path(__file__).resolve().parent / log_path
        if not absolute_log_path.exists():
            self.ui.warning("No log file exists yet.")
            self.ui.pause()
            return

        lines = absolute_log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-30:]
        self.ui.rows_table("Recent Logs", ("#", "Entry"), ((index + 1, line) for index, line in enumerate(lines)))
        self.ui.pause()

    def exit_app(self) -> None:
        """Exit the application."""
        self.logger.info("Application exit")
        self.ui.success("Session ended.")
        raise SystemExit(0)

    def _show_result(self, result: Any) -> None:
        if result.success:
            self.ui.success(result.message)
        else:
            self.ui.error(result.message)
        if result.details:
            self.ui.console.print(f"[dim]{result.details}[/dim]")

    @staticmethod
    def _is_restricted_request(choice: str) -> bool:
        lowered = choice.lower()
        return any(keyword in lowered for keyword in RESTRICTED_KEYWORDS)


def main() -> int:
    """Application entry point."""
    app = XPrivacySpooferApp()
    try:
        app.run()
    except KeyboardInterrupt:
        app.logger.info("Application interrupted by user")
        app.ui.warning("\nInterrupted by user.")
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
