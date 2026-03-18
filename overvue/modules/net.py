"""Network monitoring module for Overvue."""

import socket
import time
from typing import Dict, List, Tuple, Optional

import psutil
import platform
from rich.table import Table

from ..utils.display import (
    get_console,
    make_table,
    section_header,
    bytes_to_human,
    print_warning
)


def get_network_interfaces() -> List[Dict]:
    """Get network interface information."""
    interfaces = []
    
    net_if_addrs = psutil.net_if_addrs()
    net_if_stats = psutil.net_if_stats()
    
    for interface_name, addresses in net_if_addrs.items():
        interface_info = {
            'name': interface_name,
            'is_up': net_if_stats[interface_name].isup if interface_name in net_if_stats else False,
            'speed': net_if_stats[interface_name].speed if interface_name in net_if_stats else 0,
            'mtu': net_if_stats[interface_name].mtu if interface_name in net_if_stats else 0,
            'addresses': []
        }
        
        for addr in addresses:
            if addr.family == psutil.AF_LINK:  # MAC address
                interface_info['mac'] = addr.address
            elif addr.family == socket.AF_INET:  # IPv4
                interface_info['ipv4'] = addr.address
                interface_info['netmask'] = addr.netmask
            elif addr.family == socket.AF_INET6:  # IPv6
                interface_info['ipv6'] = addr.address
        
        interfaces.append(interface_info)
    
    return interfaces


def get_network_io() -> Dict:
    """Get network I/O statistics."""
    return psutil.net_io_counters()


def get_network_connections() -> List[Dict]:
    """Get active network connections."""
    connections = []
    
    try:
        for conn in psutil.net_connections(kind='inet'):
            if conn.status == 'LISTEN':
                connections.append({
                    'local_address': conn.laddr,
                    'remote_address': conn.raddr,
                    'status': conn.status,
                    'pid': conn.pid,
                    'family': conn.type if hasattr(conn, 'type') else 'Unknown',
                })
    except (psutil.AccessDenied, psutil.NoSuchProcess):
        pass
    
    return connections


def get_top_network_processes(limit: int = 5) -> List[Tuple[str, int, int, int]]:
    """Get top processes by network usage."""
    try:
        # Get network I/O per process
        process_network = []
        
        for proc in psutil.process_iter(['pid', 'name', 'io_counters']):
            try:
                pid = proc.info['pid']
                name = proc.info['name']
                
                if proc.info['io_counters']:
                    io_counters = proc.info['io_counters']
                    bytes_sent = io_counters.write_bytes if hasattr(io_counters, 'write_bytes') else 0
                    bytes_recv = io_counters.read_bytes if hasattr(io_counters, 'read_bytes') else 0
                    
                    total_bytes = bytes_sent + bytes_recv
                    if total_bytes > 0:
                        process_network.append((name, pid, bytes_sent, bytes_recv))
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        # Sort by total bytes
        process_network.sort(key=lambda x: x[2] + x[3], reverse=True)
        return process_network[:limit]
        
    except Exception:
        return []


def display_network_info(show_ports: bool = False, watch: bool = False) -> None:
    """Display network information."""
    console = get_console()
    
    while True:
        console.clear()
        section_header("Network Information")
        
        # Network interfaces
        interfaces = get_network_interfaces()
        
        if interfaces:
            interface_table = make_table("Network Interfaces", ["Interface", "Status", "IP", "MAC", "Speed"])
            
            for interface in interfaces:
                status = "[green]Up[/green]" if interface['is_up'] else "[red]Down[/red]"
                ip = interface.get('ipv4', 'N/A')
                mac = interface.get('mac', 'N/A')
                speed = f"{interface['speed']} Mbps" if interface['speed'] > 0 else "N/A"
                
                interface_table.add_row(
                    interface['name'],
                    status,
                    ip,
                    mac,
                    speed
                )
            
            console.print(interface_table)
        else:
            print_warning("No network interfaces found")
        
        console.print()
        
        # Network I/O
        net_io = get_network_io()
        io_table = make_table("Network I/O", ["Metric", "Value"])
        io_table.add_row("Bytes Sent", bytes_to_human(net_io.bytes_sent))
        io_table.add_row("Bytes Received", bytes_to_human(net_io.bytes_recv))
        io_table.add_row("Packets Sent", f"{net_io.packets_sent:,}")
        io_table.add_row("Packets Received", f"{net_io.packets_recv:,}")
        
        if net_io.errin > 0 or net_io.errout > 0:
            io_table.add_row("Errors In", f"{net_io.errin:,}")
            io_table.add_row("Errors Out", f"{net_io.errout:,}")
        
        console.print(io_table)
        
        # Show ports if requested
        if show_ports:
            console.print()
            section_header("Open Ports")
            
            connections = get_network_connections()
            
            if connections:
                ports_table = make_table("Listening Ports", ["Port", "Protocol", "Address", "PID", "Process"])
                
                for conn in connections:
                    if conn['local_address']:
                        port = conn['local_address'].port
                        address = conn['local_address'].ip
                        
                        # Get process name
                        process_name = "Unknown"
                        if conn['pid']:
                            try:
                                proc = psutil.Process(conn['pid'])
                                process_name = proc.name()
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                pass
                        
                        protocol = "TCP"  # We're only getting TCP connections
                        ports_table.add_row(str(port), protocol, address, str(conn['pid']), process_name)
                
                console.print(ports_table)
            else:
                print_warning("No listening ports found or access denied")
        
        # Top network processes
        console.print()
        top_processes = get_top_network_processes(5)
        
        if top_processes:
            proc_table = make_table("Top 5 Network Processes", ["Process", "PID", "Sent", "Received", "Total"])
            
            for name, pid, sent, recv in top_processes:
                total = sent + recv
                proc_table.add_row(
                    name,
                    str(pid),
                    bytes_to_human(sent),
                    bytes_to_human(recv),
                    bytes_to_human(total)
                )
            
            console.print(proc_table)
        else:
            print_warning("Network process information not available on this system")
        
        if not watch:
            break
        
        console.print(f"\n[yellow]Updating every 1 second. Press Ctrl+C to stop.[/yellow]")
        time.sleep(1)


def handle_net_command(show_ports: bool, watch: bool) -> None:
    """Handle the network command."""
    try:
        display_network_info(show_ports=show_ports, watch=watch)
    except KeyboardInterrupt:
        console = get_console()
        console.print("\n[yellow]Stopped monitoring.[/yellow]")
