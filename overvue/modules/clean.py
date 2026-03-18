"""System cleaning module for Overvue."""

import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional

from ..utils.display import (
    get_console,
    section_header,
    bytes_to_human,
    print_warning,
    print_success,
    print_error
)


def get_temp_directories() -> List[Path]:
    """Get platform-specific temporary directories."""
    system = platform.system().lower()
    temp_dirs = []
    
    if system == "windows":
        temp_dirs.extend([
            Path(os.environ.get("TEMP", "C:\\Windows\\Temp")),
            Path(os.environ.get("TMP", "C:\\Windows\\Temp")),
            Path("C:\\Windows\\Temp"),
        ])
    else:  # Linux/Mac
        temp_dirs.extend([
            Path("/tmp"),
            Path(os.environ.get("TMPDIR", "/tmp")),
            Path.home() / ".cache",
        ])
    
    return [d for d in temp_dirs if d.exists()]


def get_python_cache_dirs(base_path: Optional[Path] = None) -> List[Path]:
    """Get Python cache directories."""
    cache_dirs = []
    
    if base_path:
        search_paths = [base_path]
    else:
        search_paths = [Path.cwd()] + list(Path.cwd().parents)
    
    for path in search_paths:
        try:
            # Find __pycache__ directories
            for pycache in path.rglob("__pycache__"):
                if pycache.is_dir():
                    cache_dirs.append(pycache)
            
            # Find .pyc files
            for pyc_file in path.rglob("*.pyc"):
                if pyc_file.is_file():
                    cache_dirs.append(pyc_file)
                    
        except (OSError, PermissionError):
            continue
    
    return cache_dirs


def get_pip_cache_dir() -> Optional[Path]:
    """Get pip cache directory."""
    try:
        result = subprocess.run(
            ["pip", "cache", "dir"],
            capture_output=True,
            text=True,
            check=True
        )
        cache_dir = result.stdout.strip()
        return Path(cache_dir) if cache_dir else None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def get_system_junk_files() -> List[Path]:
    """Get system-specific junk files."""
    junk_files = []
    system = platform.system().lower()
    
    if system == "windows":
        # Thumbs.db files
        home = Path.home()
        for thumbs_db in home.rglob("Thumbs.db"):
            if thumbs_db.is_file():
                junk_files.append(thumbs_db)
    elif system == "darwin":  # macOS
        # .DS_Store files
        home = Path.home()
        for ds_store in home.rglob(".DS_Store"):
            if ds_store.is_file():
                junk_files.append(ds_store)
    
    return junk_files


def calculate_directory_size(path: Path) -> int:
    """Calculate total size of a directory."""
    total_size = 0
    
    try:
        if path.is_file():
            return path.stat().st_size
        elif path.is_dir():
            for item in path.rglob("*"):
                if item.is_file():
                    try:
                        total_size += item.stat().st_size
                    except (OSError, PermissionError):
                        continue
    except (OSError, PermissionError):
        pass
    
    return total_size


def scan_cleanable_items(additional_path: Optional[str] = None) -> Tuple[List[Tuple[str, Path, int]], int]:
    """Scan for cleanable items and return list with sizes."""
    cleanable = []
    total_size = 0
    
    # Temporary directories
    section_header("Scanning temporary directories...")
    for temp_dir in get_temp_directories():
        size = calculate_directory_size(temp_dir)
        if size > 0:
            cleanable.append(("Temp Directory", temp_dir, size))
            total_size += size
    
    # Python cache
    section_header("Scanning Python cache...")
    for cache_item in get_python_cache_dirs():
        size = calculate_directory_size(cache_item)
        if size > 0:
            cleanable.append(("Python Cache", cache_item, size))
            total_size += size
    
    # Pip cache
    section_header("Scanning pip cache...")
    pip_cache = get_pip_cache_dir()
    if pip_cache and pip_cache.exists():
        size = calculate_directory_size(pip_cache)
        if size > 0:
            cleanable.append(("Pip Cache", pip_cache, size))
            total_size += size
    
    # System junk files
    section_header("Scanning system junk files...")
    for junk_file in get_system_junk_files():
        size = calculate_directory_size(junk_file)
        if size > 0:
            cleanable.append(("System Junk", junk_file, size))
            total_size += size
    
    # Additional path
    if additional_path:
        additional = Path(additional_path)
        if additional.exists():
            section_header(f"Scanning {additional_path}...")
            size = calculate_directory_size(additional)
            if size > 0:
                cleanable.append(("Additional Path", additional, size))
                total_size += size
    
    return cleanable, total_size


def delete_item(path: Path) -> bool:
    """Delete a file or directory safely."""
    try:
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)
        return True
    except (OSError, PermissionError):
        return False


def display_clean_results(cleanable: List[Tuple[str, Path, int]], total_size: int, dry_run: bool = True) -> None:
    """Display cleaning results."""
    console = get_console()
    
    if not cleanable:
        console.print("[green]No items to clean.[/green]")
        return
    
    table_title = "Items to Clean" if dry_run else "Items Cleaned"
    table = make_table(table_title, ["Type", "Path", "Size"])
    
    for item_type, path, size in cleanable:
        # Truncate long paths
        path_str = str(path)
        if len(path_str) > 60:
            path_str = "..." + path_str[-57:]
        
        table.add_row(item_type, path_str, bytes_to_human(size))
    
    console.print(table)
    console.print()
    console.print(f"[bold]Total space: {'to be freed' if dry_run else 'freed'}: {bytes_to_human(total_size)}[/bold]")


def handle_clean_command(dry_run: bool, force: bool, additional_path: Optional[str]) -> None:
    """Handle the clean command."""
    console = get_console()
    
    # Safety check: force is required for actual cleaning
    if not dry_run and not force:
        print_error("Use --force to actually delete files. Default is --dry-run.")
        return
    
    console.clear()
    section_header("System Cleaning")
    
    # Scan for cleanable items
    cleanable, total_size = scan_cleanable_items(additional_path)
    
    if not cleanable:
        print_success("System is already clean!")
        return
    
    # Display what would be cleaned
    display_clean_results(cleanable, total_size, dry_run=True)
    
    if dry_run:
        console.print("\n[yellow]This was a dry run. No files were deleted.[/yellow]")
        console.print("[yellow]Use --force to actually delete these files.[/yellow]")
        return
    
    # Ask for confirmation
    console.print(f"\n[red]WARNING: This will permanently delete {len(cleanable)} items![/red]")
    console.print(f"[red]Total space to be freed: {bytes_to_human(total_size)}[/red]")
    
    response = input("Are you sure? [y/N]: ").strip().lower()
    if response not in ['y', 'yes']:
        console.print("[yellow]Operation cancelled.[/yellow]")
        return
    
    # Actually clean
    console.print("\n[red]Cleaning...[/red]")
    successful_cleaned = []
    failed_cleaned = []
    cleaned_size = 0
    
    for item_type, path, size in cleanable:
        if delete_item(path):
            successful_cleaned.append((item_type, path, size))
            cleaned_size += size
        else:
            failed_cleaned.append((item_type, path, size))
    
    # Display results
    if successful_cleaned:
        display_clean_results(successful_cleaned, cleaned_size, dry_run=False)
        print_success(f"Successfully cleaned {len(successful_cleaned)} items!")
    
    if failed_cleaned:
        console.print("\n[red]Failed to clean some items:[/red]")
        for item_type, path, size in failed_cleaned:
            console.print(f"  [red]✗[/red] {item_type}: {path}")
    
    if failed_cleaned:
        print_warning(f"Failed to clean {len(failed_cleaned)} items. Check permissions.")
