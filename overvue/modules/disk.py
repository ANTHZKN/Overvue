"""Disk monitoring module for Overvue."""

import hashlib
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import psutil
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..utils.display import (
    get_console,
    make_table,
    color_by_percent,
    create_progress_bar,
    section_header,
    bytes_to_human,
    print_warning
)


def get_disk_partitions() -> List[Dict]:
    """Get all disk partitions with usage information."""
    partitions = []
    
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
            partitions.append({
                'device': part.device,
                'mountpoint': part.mountpoint,
                'fstype': part.fstype,
                'total': usage.total,
                'used': usage.used,
                'free': usage.free,
                'percent': (usage.used / usage.total) * 100,
            })
        except (OSError, PermissionError):
            # Skip partitions that can't be accessed
            continue
    
    return partitions


def calculate_file_hash(filepath: Path, chunk_size: int = 8192) -> str:
    """Calculate MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except (OSError, PermissionError):
        return ""


def find_duplicate_files(search_path: str, min_size_mb: int = 1) -> Dict[str, List[Path]]:
    """Find duplicate files in the given path."""
    path = Path(search_path)
    if not path.exists():
        return {}
    
    min_size_bytes = min_size_mb * 1024 * 1024
    hash_map = {}
    
    console = get_console()
    
    # Walk through directory and hash files
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("Scanning files...", total=None)
        
        for root, dirs, files in os.walk(path):
            for file in files:
                file_path = Path(root) / file
                
                try:
                    # Skip files smaller than minimum size
                    if file_path.stat().st_size < min_size_bytes:
                        continue
                    
                    file_hash = calculate_file_hash(file_path)
                    if file_hash:
                        if file_hash not in hash_map:
                            hash_map[file_hash] = []
                        hash_map[file_hash].append(file_path)
                        
                except (OSError, PermissionError):
                    continue
            
            progress.update(task, description=f"Scanning {root}...")
    
    # Filter to only include duplicates
    duplicates = {hash_val: paths for hash_val, paths in hash_map.items() if len(paths) > 1}
    return duplicates


def display_disk_info(path: str = None, find_duplicates: bool = False, min_size_mb: int = 1) -> None:
    """Display disk information."""
    console = get_console()
    section_header("Disk Information")
    
    # Display partitions
    partitions = get_disk_partitions()
    
    if partitions:
        table = make_table("Disk Partitions", ["Device", "Mountpoint", "FS Type", "Total", "Used", "Free", "Usage"])
        
        for part in partitions:
            usage_color = color_by_percent(part['percent'])
            table.add_row(
                part['device'],
                part['mountpoint'],
                part['fstype'],
                bytes_to_human(part['total']),
                bytes_to_human(part['used']),
                bytes_to_human(part['free']),
                f"[{usage_color}]{create_progress_bar(part['percent'], 10)}[/{usage_color}]"
            )
        
        console.print(table)
    else:
        print_warning("No disk partitions found or accessible")
    
    # Find duplicates if requested
    if find_duplicates:
        console.print()
        section_header(f"Duplicate Files (min: {min_size_mb}MB)")
        
        search_path = path or str(Path.home())
        duplicates = find_duplicate_files(search_path, min_size_mb)
        
        if duplicates:
            total_recoverable = 0
            dup_table = make_table("Duplicate Files", ["Hash", "Size", "Count", "Paths"])
            
            for file_hash, paths in duplicates.items():
                file_size = paths[0].stat().st_size
                recoverable_space = file_size * (len(paths) - 1)
                total_recoverable += recoverable_space
                
                # Truncate hash for display
                short_hash = file_hash[:8] + "..."
                
                # Show first few paths, truncate if too many
                paths_str = ", ".join(str(p) for p in paths[:3])
                if len(paths) > 3:
                    paths_str += f" ... and {len(paths) - 3} more"
                
                dup_table.add_row(
                    short_hash,
                    bytes_to_human(file_size),
                    str(len(paths)),
                    paths_str
                )
            
            console.print(dup_table)
            console.print()
            console.print(f"[green]Total recoverable space: {bytes_to_human(total_recoverable)}[/green]")
        else:
            console.print("[green]No duplicate files found.[/green]")


def handle_disk_command(path: Optional[str], find_duplicates: bool, min_size_mb: int) -> None:
    """Handle the disk command."""
    try:
        display_disk_info(path=path, find_duplicates=find_duplicates, min_size_mb=min_size_mb)
    except KeyboardInterrupt:
        console = get_console()
        console.print("\n[yellow]Operation cancelled.[/yellow]")
