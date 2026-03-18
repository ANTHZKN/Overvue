"""Display utilities for Overvue using Rich."""

from typing import List, Optional
import humanize
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn
from rich.text import Text


def get_console() -> Console:
    """Get a Rich Console instance with consistent styling."""
    return Console()


def make_table(title: str, columns: List[str]) -> Table:
    """Create a Rich Table with consistent styling."""
    table = Table(title=title, show_header=True, header_style="bold magenta")
    table.box_style = "round"
    
    for column in columns:
        table.add_column(column, style="cyan", no_wrap=False)
    
    return table


def color_by_percent(value: float) -> str:
    """Return color based on percentage value."""
    if value >= 90:
        return "red"
    elif value >= 70:
        return "yellow"
    else:
        return "green"


def bytes_to_human(bytes_value: int) -> str:
    """Format bytes to human readable format using humanize."""
    return humanize.naturalsize(bytes_value, binary=True)


def section_header(title: str) -> None:
    """Print a styled section header using Rich Panel."""
    console = get_console()
    panel = Panel(
        Text(title, style="bold white"),
        border_style="blue",
        padding=(0, 1)
    )
    console.print(panel)


def create_progress_bar(percentage: float, width: int = 20) -> str:
    """Create a simple progress bar representation."""
    filled = int(width * percentage / 100)
    bar = "█" * filled + "░" * (width - filled)
    color = color_by_percent(percentage)
    return f"[{color}]{bar}[/{color}] {percentage:.1f}%"


def print_warning(message: str) -> None:
    """Print a warning message in yellow."""
    console = get_console()
    console.print(f"[yellow]{message}[/yellow]")


def print_error(message: str) -> None:
    """Print an error message in red."""
    console = get_console()
    console.print(f"[red]{message}[/red]")


def print_success(message: str) -> None:
    """Print a success message in green."""
    console = get_console()
    console.print(f"[green]{message}[/green]")
