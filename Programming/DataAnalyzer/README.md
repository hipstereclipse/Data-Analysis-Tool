# README.md

# Professional Excel Data Plotter - Vacuum Analysis Edition

A comprehensive data visualization and analysis tool designed for multi-file Excel/CSV data processing with specialized vacuum system analysis capabilities.

## Features

### Core Functionality
- **Multi-File Support**: Load and manage multiple Excel/CSV files simultaneously
- **Flexible Series Configuration**: Create custom data series from any combination of files and columns
- **Advanced Plotting**: Multiple plot types with extensive customization options
- **Real-time Preview**: See changes instantly as you configure series

### Data Processing
- **Smart Data Handling**: Automatic detection of datetime columns and data types
- **Missing Data Management**: Multiple interpolation and filling methods
- **Data Smoothing**: Savitzky-Golay and other smoothing algorithms
- **Outlier Detection**: Statistical methods for identifying anomalies

### Vacuum Analysis Tools
- **Pump-down Analysis**: Exponential fitting and time constant calculation
- **Leak Rate Calculation**: Pressure rise analysis with flow regime detection
- **Outgassing Analysis**: Surface-specific outgassing rate calculations
- **Base Pressure Analysis**: Ultimate pressure and stability metrics
- **Gas Species Estimation**: Intelligent gas type identification based on pressure

### Visualization Features
- **Interactive Annotations**: Add text, arrows, and shapes to plots
- **Trend Lines**: Linear, polynomial, exponential, and logarithmic fits
- **Statistical Overlays**: Mean lines, standard deviation bands, confidence intervals
- **Customizable Appearance**: Full control over colors, styles, and formatting

### Project Management
- **Save/Load Projects**: Preserve complete analysis sessions
- **Export Options**: Multiple formats (PNG, PDF, SVG, Excel, CSV)
- **Report Generation**: Automated analysis reports with plots and statistics
- **Recent Projects**: Quick access to previously saved work

## Installation

### Prerequisites
- Python 3.7 or higher
- pip package manager

### Install from Source

```bash
# Clone the repository
git clone https://github.com/yourusername/excel-data-plotter.git
cd excel-data-plotter

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### Install as Package

```bash
# Install directly
pip install .

# Or install in development mode
pip install -e .

# Run the application
excel-plotter
```

## Quick Start

1. **Launch the Application**
   ```bash
   python main.py
   ```

2. **Load Data Files**
   - Click "Add Files" or use File → Add Files
   - Select one or more Excel/CSV files
   - Files appear in the Files panel

3. **Create Data Series**
   - In the Series panel, configure:
     - Select source file
     - Choose X and Y columns
     - Set data range (optional)
     - Click "Add Series"

4. **Configure Plot**
   - Use the Config panel to set:
     - Plot title and labels
     - Axis scales and limits
     - Grid and legend options

5. **Analyze Data**
   - Use Analysis menu for:
     - Statistical analysis
     - Vacuum-specific calculations
     - Data quality reports

6. **Export Results**
   - File → Export Plot for images
   - File → Export Data for spreadsheets
   - Analysis → Save Report for comprehensive documentation

## Usage Examples

### Basic Time Series Plot
```python
# Load time-stamped pressure data
# Select DateTime column as X
# Select Pressure column as Y
# Apply logarithmic Y scale for vacuum data
```

### Pump-down Curve Analysis
1. Load pump-down data file
2. Create series with Time vs Pressure
3. Analysis → Vacuum Analysis
4. Select "Pump-down Analysis"
5. View exponential fit and time constants

### Multi-File Comparison
1. Load multiple experimental runs
2. Create series from each file
3. Use different colors/styles
4. Add annotations for key events
5. Export comparison plot

## Project Structure

```
excel_data_plotter/
├── main.py                     # Application entry point
├── app.py                      # Main application window
├── config/
│   ├── constants.py            # Application constants
│   └── settings.py             # User settings
├── models/
│   ├── data_models.py          # Data structures
│   └── project_models.py       # Project management
├── ui/
│   ├── components.py           # Reusable UI components
│   ├── dialogs.py              # Dialog windows
│   └── panels.py               # Main UI panels
├── core/
│   ├── file_manager.py         # File operations
│   ├── plot_manager.py         # Plotting engine
│   ├── annotation_manager.py   # Annotation system
│   ├── project_manager.py      # Project persistence
│   └── export_manager.py       # Export functionality
├── analysis/
│   ├── statistical.py          # Statistical analysis
│   ├── vacuum.py               # Vacuum-specific analysis
│   └── data_quality.py         # Data validation
├── utils/
│   ├── helpers.py              # Helper functions
│   └── validators.py           # Validation utilities
└── tests/                      # Unit tests

```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+N | New Project |
| Ctrl+O | Open Project |
| Ctrl+S | Save Project |
| Ctrl+Shift+O | Add Files |
| Ctrl+Shift+N | Add Series |
| F5 | Refresh Plot |
| Ctrl+E | Export Plot |
| Ctrl+G | Toggle Grid |
| Ctrl+L | Toggle Legend |
| Ctrl+T | Toggle Theme |
| F1 | Show Help |

## Configuration

### Plot Defaults
Edit `config/constants.py` to change default settings:
- Figure size and DPI
- Color schemes
- Grid styles
- Font sizes

### Vacuum Analysis Parameters
Customize vacuum-specific settings:
- Pressure unit conversions
- Gas molecular weights
- Leak rate classifications
- Outgassing thresholds

## Troubleshooting

### Common Issues

**Issue**: Plot not updating
- **Solution**: Press F5 or click Refresh Plot

**Issue**: Cannot load Excel file
- **Solution**: Ensure openpyxl is installed: `pip install openpyxl`

**Issue**: Missing data in plot
- **Solution**: Check data range settings and missing data handling method

**Issue**: Vacuum analysis fails
- **Solution**: Ensure pressure data is positive and in correct units

### Error Logs
Logs are stored in: `~/.excel_data_plotter/logs/app.log`

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with CustomTkinter for modern UI
- Uses Matplotlib for powerful plotting
- Scipy and Scikit-learn for analysis
- Pandas for data manipulation

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing documentation
- Review closed issues for solutions

## Version History

### v5.0.0 (Current)
- Complete refactor with modular architecture
- Enhanced vacuum analysis tools
- Improved annotation system
- Better project management

### v4.0.0
- Added multi-file support
- Implemented series configuration
- Basic vacuum analysis

### v3.0.0
- Initial release
- Single file plotting
- Basic analysis tools

---
