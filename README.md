# Overvue

![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Python](https://img.shields.io/badge/python-3.10+-blue.svg)

**Overvue** is a cross-platform system monitoring CLI toolkit that provides real-time insights into your system's performance and resource usage.

## Features

- **Cross-platform**: Works on Windows, macOS, and Linux
- **Real-time monitoring**: Live updates with watch mode
- **Beautiful terminal output**: Rich tables, colors, and progress bars
- **Comprehensive system info**: CPU, RAM, disk, network, and processes
- **System cleaning**: Safe removal of temporary files and cache
- **Duplicate file finder**: Find and reclaim disk space

## Installation

### From PyPI (recommended)
```bash
pip install overvue
```

### From source
```bash
git clone https://github.com/overvue/overvue.git
cd overvue
pip install -e .
```

## Quick Start

```bash
# Show system overview
overvue status

# Watch CPU usage in real-time
overvue cpu --watch

# Find duplicate files in your home directory
overvue disk --dupes --path ~

# Clean temporary files (dry-run by default)
overvue clean

# Show top 10 processes by RAM usage
overvue procs --sort ram --top 10
```

## Commands

| Command | Description | Example |
|---------|-------------|---------|
| `overvue status` | System overview with CPU, RAM, disk, and network | `overvue status` |
| `overvue cpu` | Detailed CPU information and usage | `overvue cpu --watch` |
| `overvue ram` | RAM and swap usage statistics | `overvue ram --watch` |
| `overvue disk` | Disk usage and duplicate file finder | `overvue disk --dupes --min-size 10` |
| `overvue net` | Network interfaces and connections | `overvue net --ports` |
| `overvue procs` | Active processes monitoring | `overvue procs --sort cpu --top 20` |
| `overvue clean` | System cleaning and cache removal | `overvue clean --force` |

### Command Options

#### `overvue cpu`
- `--watch, -w`: Live monitoring mode
- `--interval SECONDS`: Update interval (default: 1)

#### `overvue ram`
- `--watch, -w`: Live monitoring mode

#### `overvue disk`
- `--path PATH`: Directory to analyze (default: system root)
- `--dupes, -d`: Find duplicate files
- `--min-size MB`: Minimum file size for duplicates (default: 1MB)

#### `overvue net`
- `--ports, -p`: Show open ports and processes
- `--watch, -w`: Live monitoring mode

#### `overvue procs`
- `--top N`: Number of processes to show (default: 15)
- `--sort [cpu\|ram\|name]`: Sort criterion (default: cpu)
- `--watch, -w`: Live monitoring mode

#### `overvue clean`
- `--dry-run, -d`: Show what would be cleaned (default behavior)
- `--force, -f`: Actually clean files (requires confirmation)
- `--path PATH`: Additional path to clean

## Examples

### Real-time CPU Monitoring
```bash
overvue cpu --watch --interval 2
```

### Find Large Duplicate Files
```bash
overvue disk --dupes --path ~/Downloads --min-size 50
```

### Network Port Analysis
```bash
overvue net --ports
```

### Process Monitoring
```bash
overvue procs --sort ram --top 10 --watch
```

### Safe System Cleaning
```bash
# First, see what would be cleaned
overvue clean --dry-run

# Actually clean after review
overvue clean --force
```

## Roadmap

### v0.1 (Current)
- Basic system monitoring commands
- Cross-platform compatibility
- Rich terminal output
- System cleaning functionality

### v0.2 (Planned)
- Configuration file support
- Advanced filtering options
- Historical data logging
- Alert thresholds

### v0.3 (Planned)
- JSON/CSV export capabilities
- Remote monitoring
- Plugin system
- Performance graphs

### v1.0 (Future)
- GUI interface (Electron/Tauri)
- Distributed monitoring
- Advanced analytics
- Cloud integration

## Contributing

We welcome contributions! Here's how to get started:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run the test suite: `python -m pytest`
5. Commit your changes: `git commit -am 'Add new feature'`
6. Push to the branch: `git push origin feature-name`
7. Submit a pull request

### Adding a New Module

1. Create a new file in `overvue/modules/`
2. Implement your module following the existing patterns
3. Add the command to `overvue/cli.py`
4. Update this README with documentation
5. Test on all supported platforms

### Development Setup

```bash
git clone https://github.com/overvue/overvue.git
cd overvue
pip install -e ".[dev]"
```

## Requirements

- Python 3.10 or higher
- Supported operating systems: Windows, macOS, Linux

### Dependencies

- `click` - Command line interface framework
- `rich` - Rich text and beautiful formatting in the terminal
- `psutil` - System and process utilities
- `humanize` - Human readable data formatting
- `py-cpuinfo` - CPU information extraction
- `colorama` - Cross-platform colored terminal text

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 📖 [Documentation](https://github.com/overvue/overvue/wiki)
- 🐛 [Issue Tracker](https://github.com/overvue/overvue/issues)
- 💬 [Discussions](https://github.com/overvue/overvue/discussions)

## Acknowledgments

- Thanks to all contributors who make this project possible
- Built with amazing open-source libraries like [Rich](https://github.com/Textualize/rich) and [psutil](https://github.com/giampaolo/psutil)
- Inspired by system monitoring tools across different platforms
