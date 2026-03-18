"""RAM monitoring module for Overvue."""

import time
from typing import List, Tuple

import psutil
from rich.table import Table

from ..utils.display import (
    get_console,
    make_table,
    color_by_percent,
    create_progress_bar,
    section_header,
    bytes_to_human
)


def get_memory_info() -> dict:
    """Get memory information."""
    virtual = psutil.virtual_memory()
    swap = psutil.swap_memory()
    
    return {
        'virtual': {
            'total': virtual.total,
            'used': virtual.used,
            'available': virtual.available,
            'percent': virtual.percent,
        },
        'swap': {
            'total': swap.total,
            'used': swap.used,
            'free': swap.free,
            'percent': swap.percent,
        }
    }


def get_top_ram_processes(limit: int = 5) -> List[Tuple[str, int, float]]:
    """Get top processes by RAM usage."""
    processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
        try:
            pid = proc.info['pid']
            name = proc.info['name']
            memory_mb = proc.info['memory_info'].rss / (1024 * 1024)  # Convert to MB
            processes.append((name, pid, memory_mb))
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    
    # Sort by memory usage and return top N
    processes.sort(key=lambda x: x[2], reverse=True)
    return processes[:limit]


def display_ram_info(watch: bool = False) -> None:
    """Display RAM information."""
    console = get_console()
    
    while True:
        console.clear()
        section_header("RAM Information")
        
        memory = get_memory_info()
        
        # Virtual Memory
        virtual = memory['virtual']
        console.print("Virtual Memory:")
        console.print(f"  Total: {bytes_to_human(virtual['total'])}")
        console.print(f"  Used: {bytes_to_human(virtual['used'])}")
        console.print(f"  Available: {bytes_to_human(virtual['available'])}")
        console.print(f"  Usage: {create_progress_bar(virtual['percent'])}")
        console.print()
        
        # Swap Memory
        swap = memory['swap']
        console.print("Swap Memory:")
        console.print(f"  Total: {bytes_to_human(swap['total'])}")
        console.print(f"  Used: {bytes_to_human(swap['used'])}")
        console.print(f"  Free: {bytes_to_human(swap['free'])}")
        console.print(f"  Usage: {create_progress_bar(swap['percent'])}")
        console.print()
        
        # Top RAM-consuming processes
        top_processes = get_top_ram_processes(5)
        if top_processes:
            proc_table = make_table("Top 5 RAM-Consuming Processes", ["Process", "PID", "Memory (MB)"])
            
            for name, pid, memory_mb in top_processes:
                # Highlight processes using more than 1GB
                if memory_mb > 1024:
                    name = f"[red]{name}[/red]"
                    memory_mb = f"[red]{memory_mb:.1f}[/red]"
                else:
                    memory_mb = f"{memory_mb:.1f}"
                
                proc_table.add_row(name, str(pid), memory_mb)
            
            console.print(proc_table)
        
        if not watch:
            break
        
        console.print("\n[yellow]Updating every 1 second. Press Ctrl+C to stop.[/yellow]")
        time.sleep(1)


def handle_ram_command(watch: bool) -> None:
    """Handle the RAM command."""
    try:
        display_ram_info(watch=watch)
    except KeyboardInterrupt:
        console = get_console()
        console.print("\n[yellow]Stopped monitoring.[/yellow]")
