"""Main CLI entry point for Overvue."""

import platform
import time
from typing import Optional

import click
import psutil
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .modules import cpu, ram, disk, net, procs, clean
from .utils.display import (
    get_console,
    make_table,
    color_by_percent,
    create_progress_bar,
    section_header,
    bytes_to_human
)

# Import the handler functions directly
from .modules.cpu import handle_cpu_command
from .modules.ram import handle_ram_command
from .modules.disk import handle_disk_command
from .modules.net import handle_net_command
from .modules.procs import handle_procs_command
from .modules.clean import handle_clean_command


@click.group()
@click.version_option(version="0.1.0", prog_name="overvue")
def main():
    """Overvue - Cross-platform system monitoring CLI toolkit."""
    pass


@main.command()
def status():
    """Show general system status overview."""
    console = get_console()
    console.clear()
    section_header("System Status Overview")
    
    # System info
    hostname = platform.node()
    os_info = f"{platform.system()} {platform.release()}"
    python_version = platform.python_version()
    uptime = time.time() - psutil.boot_time()
    uptime_str = f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m"
    
    info_table = make_table("System Information", ["Property", "Value"])
    info_table.add_row("Hostname", hostname)
    info_table.add_row("OS", os_info)
    info_table.add_row("Python", python_version)
    info_table.add_row("Uptime", uptime_str)
    console.print(info_table)
    console.print()
    
    # CPU Status
    cpu_percent = psutil.cpu_percent(interval=0.1)
    cpu_color = color_by_percent(cpu_percent)
    cpu_table = make_table("CPU", ["Metric", "Value"])
    cpu_table.add_row("Usage", f"[{cpu_color}]{create_progress_bar(cpu_percent)}[/{cpu_color}]")
    cpu_table.add_row("Cores", f"{psutil.cpu_count(logical=False)} physical / {psutil.cpu_count(logical=True)} logical")
    console.print(cpu_table)
    
    # RAM Status
    memory = psutil.virtual_memory()
    ram_color = color_by_percent(memory.percent)
    ram_table = make_table("RAM", ["Metric", "Value"])
    ram_table.add_row("Usage", f"[{ram_color}]{create_progress_bar(memory.percent)}[/{ram_color}]")
    ram_table.add_row("Used/Total", f"{bytes_to_human(memory.used)} / {bytes_to_human(memory.total)}")
    console.print(ram_table)
    
    # Disk Status (root partition)
    try:
        disk_usage = psutil.disk_usage('/')
        disk_percent = (disk_usage.used / disk_usage.total) * 100
        disk_color = color_by_percent(disk_percent)
        disk_table = make_table("Disk (Root)", ["Metric", "Value"])
        disk_table.add_row("Usage", f"[{disk_color}]{create_progress_bar(disk_percent)}[/{disk_color}]")
        disk_table.add_row("Used/Total", f"{bytes_to_human(disk_usage.used)} / {bytes_to_human(disk_usage.total)}")
        console.print(disk_table)
    except OSError:
        console.print("[yellow]Disk information not available[/yellow]")
    
    # Network Status
    net_io = psutil.net_io_counters()
    net_table = make_table("Network", ["Metric", "Value"])
    net_table.add_row("Bytes Sent", bytes_to_human(net_io.bytes_sent))
    net_table.add_row("Bytes Received", bytes_to_human(net_io.bytes_recv))
    console.print(net_table)


@main.command()
@click.option('--watch', '-w', is_flag=True, help='Watch mode - updates every second')
@click.option('--interval', default=1, help='Update interval for watch mode (seconds)')
def cpu(watch: bool, interval: int):
    """Show detailed CPU information."""
    handle_cpu_command(watch=watch, interval=interval)


@main.command()
@click.option('--watch', '-w', is_flag=True, help='Watch mode - updates every second')
def ram(watch: bool):
    """Show RAM and swap information."""
    handle_ram_command(watch=watch)


@main.command()
@click.option('--path', '-p', help='Path to analyze (default: system root)')
@click.option('--dupes', '-d', is_flag=True, help='Find duplicate files')
@click.option('--min-size', default=1, help='Minimum size for duplicates in MB')
def disk(path: Optional[str], dupes: bool, min_size: int):
    """Show disk usage and find duplicate files."""
    handle_disk_command(path=path, find_duplicates=dupes, min_size_mb=min_size)


@main.command()
@click.option('--ports', '-p', is_flag=True, help='Show open ports')
@click.option('--watch', '-w', is_flag=True, help='Watch mode - updates every second')
def net(ports: bool, watch: bool):
    """Show network interfaces and connections."""
    handle_net_command(show_ports=ports, watch=watch)


@main.command()
@click.option('--top', '-n', default=15, help='Number of processes to show')
@click.option('--sort', default='cpu', type=click.Choice(['cpu', 'ram', 'name']), help='Sort by criterion')
@click.option('--watch', '-w', is_flag=True, help='Watch mode - updates every second')
def procs(top: int, sort: str, watch: bool):
    """Show active processes."""
    handle_procs_command(sort_by=sort, limit=top, watch=watch)


@main.command()
@click.option('--dry-run', '-d', is_flag=True, default=True, help='Show what would be cleaned (default)')
@click.option('--force', '-f', is_flag=True, help='Actually clean files (requires confirmation)')
@click.option('--path', help='Additional path to clean')
def clean(dry_run: bool, force: bool, path: Optional[str]):
    """Clean temporary files and cache."""
    # Ensure dry-run is the default behavior
    if not dry_run and not force:
        dry_run = True
    
    handle_clean_command(dry_run=dry_run, force=force, additional_path=path)


if __name__ == '__main__':
    main()
