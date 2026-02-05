# MoBI Markers

[![Build](https://github.com/iktae-kim/MoBI_Markers/actions/workflows/test.yaml/badge.svg?branch=main)](https://github.com/iktae-kim/MoBI-Markers/actions/workflows/test.yaml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/iktae-kim/MoBI_Markers/branch/main/graph/badge.svg)](https://codecov.io/gh/iktae-kim/MoBI_Markers)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
![stability-experimental](https://img.shields.io/badge/stability-experimental-orange.svg)
[![LGPL--2.1 License](https://img.shields.io/badge/license-LGPL--2.1-blue.svg)](https://github.com/childmindresearch/MoBI_Markers/blob/main/LICENSE)
[![pages](https://img.shields.io/badge/api-docs-blue)](https://iktae-kim.github.io/MoBI_Markers)

A Python GUI application for sending LSL (Lab Streaming Layer) markers used in neuroscience research.

## Features

- **Simple GUI Interface**: Clean and intuitive interface built with PyQt6
- **LSL Stream Integration**: Creates and manages an LSL marker stream
- **Real-time Marker Sending**: Send custom string markers with a single click or Enter key
- **Status Logging**: Real-time status updates and error reporting
- **Cross-platform**: Works on Windows, macOS, and Linux

## Installation

### Prerequisites

- Python 3.12 or higher
- uv package manager

### Install with uv

```bash
# Clone the repository
git clone <repository-url>
cd mobi-marker

# Install with uv (recommended)
uv sync

# Or install in development mode
uv sync --group dev
```

### Install with pip

```bash
pip install -e .
```

## Usage

### Running the GUI Application

After installation, you can run the application in several ways:

```bash
# Using the installed script
mobi-marker

# Or directly with Python
python -m mobi_marker.main

# Or if installed in development mode
uv run mobi-marker
```

### Using the Application

1. **Start the Application**: The LSL stream starts automatically when the application launches
2. **Send Markers**: 
   - Type your marker text in the input field
   - Click "Send Marker" or press Enter
   - The marker will be sent through the LSL stream
3. **Monitor Status**: View real-time status updates in the log area
4. **Clear Log**: Use the "Clear Log" button to clear the status display

### LSL Stream Details

- **Stream Name**: MobiMarkerStream
- **Stream Type**: Markers
- **Channel Count**: 1
- **Data Format**: String
- **Source ID**: mobi_marker_gui_v1

## Development

### Setting up Development Environment

```bash
# Install with development dependencies
uv sync --group dev

# Install pre-commit hooks
uv run pre-commit install
```

### Running Tests

```bash
# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=mobi_marker
```

### Code Quality

```bash
# Run linting
uv run ruff check

# Run type checking
uv run mypy src

# Format code
uv run ruff format
```

## Project Structure

```
mobi-marker/
├── src/
│   └── mobi_marker/
│       ├── __init__.py
│       ├── main.py
│       └── gui.py
├── tests/
├── pyproject.toml
└── README.md
```

## Dependencies

- **PyQt6**: GUI framework
- **pylsl**: Lab Streaming Layer interface

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Troubleshooting

### Common Issues

1. **LSL Stream Not Starting**: 
   - Ensure pylsl is properly installed
   - Check that no other application is using the same stream name

2. **GUI Not Displaying**:
   - Verify PyQt6 installation
   - Check system GUI framework compatibility

3. **Import Errors**:
   - Ensure all dependencies are installed
   - Try running `uv sync` to reinstall dependencies

### Support

For issues and questions, please open an issue on the GitHub repository.
