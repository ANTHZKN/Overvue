"""CPU monitoring module for Overvue."""

import time
import platform
from typing import Optional

import psutil
import cpuinfo
from rich.table import Table

from ..utils.display import (
    get_console,
    make_table,
    color_by_percent,
    create_progress_bar,
    section_header,
    print_warning
)


def get_cpu_info() -> dict:
    """Get detailed CPU information."""
    try:
        cpu_info = cpuinfo.get_cpu_info()
        return {
            'name': cpu_info.get('brand_raw', 'Unknown'),
            'arch': cpu_info.get('arch', 'Unknown'),
            'cores_physical': psutil.cpu_count(logical=False),
            'cores_logical': psutil.cpu_count(logical=True),
        }
    except Exception:
        return {
            'name': platform.processor() or 'Unknown',
            'arch': platform.machine() or 'Unknown',
            'cores_physical': psutil.cpu_count(logical=False),
            'cores_logical': psutil.cpu_count(logical=True),
        }


def get_cpu_usage() -> dict:
    """Get current CPU usage statistics."""
    return {
        'usage_total': psutil.cpu_percent(interval=0.1),
        'usage_per_core': psutil.cpu_percent(percpu=True),
        'freq_current': psutil.cpu_freq().current if psutil.cpu_freq() else None,
        'freq_min': psutil.cpu_freq().min if psutil.cpu_freq() else None,
        'freq_max': psutil.cpu_freq().max if psutil.cpu_freq() else None,
    }


def get_temperature() -> Optional[float]:
    """Get CPU temperature if available."""
    try:
        if hasattr(psutil, 'sensors_temperatures'):
            temps = psutil.sensors_temperatures()
            if temps:
                # Try common CPU temperature sensor names
                for name, entries in temps.items():
                    if any(keyword in name.lower() for keyword in ['cpu', 'core', 'coretemp', 'k10temp']):
                        if entries:
                            return entries[0].current
        return None
    except Exception:
        return None


def display_cpu_info(watch: bool = False, interval: int = 1) -> None:
    """Display CPU information."""
    console = get_console()
    
    while True:
        console.clear()
        section_header("CPU Information")
        
        # Basic CPU info
        cpu_info = get_cpu_info()
        info_table = make_table("", ["Property", "Value"])
        info_table.add_row("CPU Name", cpu_info['name'])
        info_table.add_row("Architecture", cpu_info['arch'])
        info_table.add_row("Physical Cores", str(cpu_info['cores_physical']))
        info_table.add_row("Logical Cores", str(cpu_info['cores_logical']))
        console.print(info_table)
        console.print()
        
        # CPU usage
        usage = get_cpu_usage()
        
        # Total usage with progress bar
        console.print(f"Total Usage: {create_progress_bar(usage['usage_total'])}")
        console.print()
        
        # Per-core usage table
        core_table = make_table("Per-Core Usage", ["Core", "Usage", "Progress"])
        for i, core_usage in enumerate(usage['usage_per_core']):
            color = color_by_percent(core_usage)
            core_table.add_row(
                f"Core {i}",
                f"{core_usage:.1f}%",
                f"[{color}]{create_progress_bar(core_usage, 15)}[/{color}]"
            )
        console.print(core_table)
        console.print()
        
        # Frequency info
        if usage['freq_current']:
            freq_table = make_table("Frequency", ["Current", "Min", "Max"])
            freq_table.add_row(
                f"{usage['freq_current']:.0f} MHz",
                f"{usage['freq_min']:.0f} MHz",
                f"{usage['freq_max']:.0f} MHz"
            )
            console.print(freq_table)
            console.print()
        
        # Temperature
        temp = get_temperature()
        if temp:
            temp_color = color_by_percent((temp / 100) * 100)  # Assuming max 100°C
            console.print(f"Temperature: [{temp_color}]{temp:.1f}°C[/{temp_color}]")
        else:
            print_warning("Temperature information not available on this system")
        
        if not watch:
            break
        
        console.print(f"\n[yellow]Updating every {interval} second(s). Press Ctrl+C to stop.[/yellow]")
        time.sleep(interval)


def handle_cpu_command(watch: bool, interval: int) -> None:
    """Handle the CPU command."""
    try:
        display_cpu_info(watch=watch, interval=interval)
    except KeyboardInterrupt:
        console = get_console()
        console.print("\n[yellow]Stopped monitoring.[/yellow]")
