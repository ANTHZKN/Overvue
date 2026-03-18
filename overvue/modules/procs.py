"""Process monitoring module for Overvue."""

import time
from typing import List, Dict, Tuple

import psutil
from rich.table import Table

from ..utils.display import (
    get_console,
    make_table,
    color_by_percent,
    section_header,
    bytes_to_human
)


def get_processes(sort_by: str = "cpu", limit: int = 15) -> List[Dict]:
    """Get sorted list of processes."""
    processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_info', 'status']):
        try:
            pinfo = proc.info
            
            # Get CPU percentage (non-blocking)
            cpu_percent = proc.cpu_percent(interval=0.1)
            
            # Get memory in MB
            memory_mb = 0
            if pinfo['memory_info']:
                memory_mb = pinfo['memory_info'].rss / (1024 * 1024)
            
            processes.append({
                'pid': pinfo['pid'],
                'name': pinfo['name'] or 'Unknown',
                'username': pinfo['username'] or 'Unknown',
                'cpu_percent': cpu_percent,
                'memory_mb': memory_mb,
                'status': pinfo['status'] or 'Unknown',
            })
            
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    
    # Sort processes
    if sort_by == "cpu":
        processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
    elif sort_by == "ram":
        processes.sort(key=lambda x: x['memory_mb'], reverse=True)
    elif sort_by == "name":
        processes.sort(key=lambda x: x['name'].lower())
    
    return processes[:limit]


def display_processes(sort_by: str = "cpu", limit: int = 15, watch: bool = False) -> None:
    """Display process information."""
    console = get_console()
    
    while True:
        console.clear()
        section_header(f"Top {limit} Processes (sorted by {sort_by})")
        
        processes = get_processes(sort_by=sort_by, limit=limit)
        
        if processes:
            table = make_table("Processes", ["PID", "Name", "User", "CPU%", "RAM (MB)", "Status"])
            
            for proc in processes:
                # Color coding for high resource usage
                name = proc['name']
                cpu_str = f"{proc['cpu_percent']:.1f}"
                ram_str = f"{proc['memory_mb']:.1f}"
                
                # Highlight high CPU usage
                if proc['cpu_percent'] > 50:
                    cpu_str = f"[red]{cpu_str}[/red]"
                
                # Highlight high RAM usage (>1GB)
                if proc['memory_mb'] > 1024:
                    ram_str = f"[red]{ram_str}[/red]"
                
                # Color status
                status_color = {
                    'running': 'green',
                    'sleeping': 'yellow',
                    'stopped': 'red',
                    'zombie': 'red',
                    'dead': 'red',
                }.get(proc['status'].lower(), 'white')
                
                status = f"[{status_color}]{proc['status']}[/{status_color}]"
                
                table.add_row(
                    str(proc['pid']),
                    name,
                    proc['username'],
                    cpu_str,
                    ram_str,
                    status
                )
            
            console.print(table)
        else:
            console.print("[yellow]No processes found or access denied.[/yellow]")
        
        if not watch:
            break
        
        console.print(f"\n[yellow]Updating every 1 second. Press Ctrl+C to stop.[/yellow]")
        time.sleep(1)


def handle_procs_command(sort_by: str, limit: int, watch: bool) -> None:
    """Handle the processes command."""
    try:
        display_processes(sort_by=sort_by, limit=limit, watch=watch)
    except KeyboardInterrupt:
        console = get_console()
        console.print("\n[yellow]Stopped monitoring.[/yellow]")
