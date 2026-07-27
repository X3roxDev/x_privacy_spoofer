"""Rich-powered terminal interface components."""

from __future__ import annotations

import time
from collections.abc import Iterable

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table
from rich.text import Text

from config import APP_BANNER, APP_REPOSITORY, APP_VERSION, BACKUP_DIR, EXPORT_DIR, LOG_DIR
from modules.admin_utils import AdminUtils


class ConsoleUI:
    """Reusable terminal UI helpers."""

    def __init__(self) -> None:
        self.console = Console(highlight=False)

    def clear(self) -> None:
        """Clear the terminal viewport and scrollback buffer."""
        self.console.file.write("\x1b[2J\x1b[3J\x1b[H")
        self.console.file.flush()

    def header(self) -> None:
        """Render the application header."""
        self.console.print(Text(APP_BANNER, style="bold white"))
        self.console.print("Windows Privacy & Testing Tool")
        self.console.print(f"GitHub: {APP_REPOSITORY}")
        self.console.print("[dim]" + "=" * 110 + "[/dim]")
        self._status_line()
        self.console.print()

    def menu(self) -> None:
        """Render the main menu."""
        options = (
            ("1", "Generate fake device profile"),
            ("2", "Generate random hostname"),
            ("3", "Generate random MAC address"),
            ("4", "Generate browser User-Agent"),
            ("5", "Generate test identifiers"),
            ("6", "View current system identity"),
            ("7", "Create backup"),
            ("8", "Restore original settings"),
            ("9", "Export profile"),
            ("10", "View logs"),
            ("0", "Exit"),
        )
        self.console.print("[bold white]Menu[/bold white]")
        for key, label in options:
            self.console.print(f"   [bold white][{key}][/bold white] [white]{label}[/white]")
        self.console.print()

    def prompt(self, message: str, default: str | None = None) -> str:
        """Prompt for user input."""
        suffix = f" [{default}]" if default is not None else ""
        value = self.console.input(f"[bold cyan]{message}{suffix}> [/bold cyan]")
        if value == "" and default is not None:
            return default
        return value

    def confirm(self, message: str, default: bool = False) -> bool:
        """Prompt for confirmation."""
        return Confirm.ask(f"[bold white]{message}[/bold white]", default=default)

    def pause(self, message: str = "Press Enter to continue") -> None:
        """Pause until the user presses Enter."""
        self.console.input(f"\n[dim]{message}[/dim]")

    def info(self, message: str) -> None:
        """Display an informational status."""
        self.console.print(f"[white][*][/white] {message}")

    def success(self, message: str) -> None:
        """Display a success status."""
        self.console.print(f"[bold green][+][/bold green] {message}")

    def warning(self, message: str) -> None:
        """Display a warning status."""
        self.console.print(f"[bold yellow][!][/bold yellow] {message}")

    def error(self, message: str) -> None:
        """Display an error status."""
        self.console.print(f"[bold red][-][/bold red] {message}")

    def restricted(self, message: str) -> None:
        """Display a restricted feature warning."""
        self.console.print(Panel(message, title="Restricted", border_style="red", box=box.ASCII))

    def spinner(self, message: str, seconds: float = 0.8) -> None:
        """Show a short loading animation."""
        with self.console.status(f"[white]{message}[/white]", spinner="dots"):
            time.sleep(seconds)

    def dict_table(self, title: str, data: dict[str, object]) -> None:
        """Render a dictionary as a two-column table."""
        table = Table(title=title, box=None, show_edge=False, pad_edge=False)
        table.add_column("Field", style="bold white", no_wrap=True)
        table.add_column("Value", style="white")
        for key, value in data.items():
            table.add_row(str(key).replace("_", " ").title(), self._format_value(value))
        self.console.print(table)

    def rows_table(self, title: str, columns: Iterable[str], rows: Iterable[Iterable[object]]) -> None:
        """Render row data as a table."""
        table = Table(title=title, box=None, show_edge=False, pad_edge=False)
        for column in columns:
            table.add_column(column, style="bold white")
        for row in rows:
            table.add_row(*(self._format_value(value) for value in row))
        self.console.print(table)

    def _status_line(self) -> None:
        """Render compact counters in the screenshot-inspired style."""
        backups = self._count_files(BACKUP_DIR, "*.json")
        exports = self._count_files(EXPORT_DIR, "*.*")
        logs = self._count_files(LOG_DIR, "*.log")
        admin = "Yes" if AdminUtils.is_admin() else "No"
        self.console.print(
            "[bold green]Backups:[/bold green] "
            f"{backups}   "
            "[bold yellow]Exports:[/bold yellow] "
            f"{exports}   "
            "[bold red]Logs:[/bold red] "
            f"{logs}   "
            "[bold cyan]Admin:[/bold cyan] "
            f"{admin}   "
            "[bold magenta]v[/bold magenta] "
            f"{APP_VERSION}"
        )

    @staticmethod
    def _count_files(directory: object, pattern: str) -> int:
        try:
            return sum(1 for path in directory.glob(pattern) if path.is_file())  # type: ignore[attr-defined]
        except OSError:
            return 0

    @staticmethod
    def _format_value(value: object) -> str:
        if isinstance(value, (dict, list, tuple)):
            return str(value)
        return "" if value is None else str(value)
