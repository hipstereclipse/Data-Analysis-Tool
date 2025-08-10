#!/usr/bin/env python3
"""
Test installation script
Verifies that all components are properly installed and configured
"""

import sys
import importlib
from pathlib import Path


def test_dependencies():
    """Test that all required dependencies are installed"""
    print("Testing dependencies...")

    required = {
        'pandas': '1.3.0',
        'numpy': '1.21.0',
        'matplotlib': '3.4.0',
        'scipy': '1.7.0',
        'sklearn': '0.24.0',
        'customtkinter': '5.0.0',
        'openpyxl': '3.0.0'
    }

    all_ok = True

    for module_name, min_version in required.items():
        try:
            if module_name == 'sklearn':
                module = importlib.import_module('sklearn')
                version = module.__version__
            else:
                module = importlib.import_module(module_name)
                version = module.__version__ if hasattr(module, '__version__') else 'unknown'

            print(f"  ✓ {module_name:15} {version:10} (required >= {min_version})")

        except ImportError as e:
            print(f"  ✗ {module_name:15} NOT INSTALLED")
            all_ok = False

    return all_ok


def test_modules():
    """Test that all application modules can be imported"""
    print("\nTesting application modules...")

    modules_to_test = [
        'config.constants',
        'models.data_models',
        'models.project_models',
        'ui.components',
        'ui.panels',
        'ui.dialogs',
        'core.file_manager',
        'core.plot_manager',
        'core.annotation_manager',
        'core.project_manager',
        'core.export_manager',
        'analysis.statistical',
        'analysis.vacuum',
        'analysis.data_quality',
        'utils.helpers',
        'utils.validators',
        'app'
    ]

    all_ok = True

    for module_name in modules_to_test:
        try:
            importlib.import_module(module_name)
            print(f"  ✓ {module_name}")
        except ImportError as e:
            print(f"  ✗ {module_name}: {e}")
            all_ok = False

    return all_ok


def test_directories():
    """Test that required directories exist or can be created"""
    print("\nTesting directories...")

    app_dir = Path.home() / '.excel_data_plotter'
    dirs_to_test = [
        app_dir,
        app_dir / 'autosave',
        app_dir / 'temp',
        app_dir / 'logs'
    ]

    all_ok = True

    for dir_path in dirs_to_test:
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"  ✓ {dir_path}")
        except Exception as e:
            print(f"  ✗ {dir_path}: {e}")
            all_ok = False

    return all_ok


def test_matplotlib_backend():
    """Test that matplotlib can use TkAgg backend"""
    print("\nTesting matplotlib backend...")

    try:
        import matplotlib
        matplotlib.use('TkAgg')
        import matplotlib.pyplot as plt

        # Try to create a figure
        fig = plt.figure(figsize=(1, 1))
        plt.close(fig)

        print(f"  ✓ Matplotlib backend: {matplotlib.get_backend()}")
        return True

    except Exception as e:
        print(f"  ✗ Matplotlib backend error: {e}")
        return False


def test_tkinter():
    """Test that tkinter is available"""
    print("\nTesting tkinter...")

    try:
        import tkinter as tk

        # Try to create a root window (but don't show it)
        root = tk.Tk()
        root.withdraw()
        root.destroy()

        print("  ✓ Tkinter is available")
        return True

    except Exception as e:
        print(f"  ✗ Tkinter error: {e}")
        print("    Tkinter may not be installed. On Ubuntu/Debian, try:")
        print("    sudo apt-get install python3-tk")
        return False


def test_customtkinter_theme():
    """Test CustomTkinter theme settings"""
    print("\nTesting CustomTkinter theme...")

    try:
        import customtkinter as ctk

        # Test theme settings
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        print("  ✓ CustomTkinter theme configured")
        return True

    except Exception as e:
        print(f"  ✗ CustomTkinter theme error: {e}")
        return False


def test_data_creation():
    """Test that we can create basic data structures"""
    print("\nTesting data structures...")

    try:
        from models.data_models import FileData, SeriesConfig, PlotConfiguration
        import pandas as pd
        import numpy as np

        # Create sample data
        df = pd.DataFrame({
            'time': pd.date_range('2024-01-01', periods=100, freq='h'),
            'pressure': np.random.exponential(1e-6, 100),
            'temperature': np.random.normal(25, 2, 100)
        })

        # Create FileData object
        file_data = FileData(
            file_id='test123',
            filepath='/tmp/test.csv',
            filename='test.csv',
            data=df
        )

        # Create SeriesConfig object
        series = SeriesConfig(
            name='Test Series',
            file_id='test123',
            x_column='time',
            y_column='pressure'
        )

        # Create PlotConfiguration
        config = PlotConfiguration()

        print(f"  ✓ Created FileData with {file_data.row_count} rows")
        print(f"  ✓ Created SeriesConfig: {series.name}")
        print(f"  ✓ Created PlotConfiguration")

        return True

    except Exception as e:
        print(f"  ✗ Data structure error: {e}")
        return False


def run_all_tests():
    """Run all installation tests"""
    print("=" * 60)
    print("Excel Data Plotter - Installation Test")
    print("=" * 60)

    results = []

    # Run tests
    results.append(("Dependencies", test_dependencies()))
    results.append(("Tkinter", test_tkinter()))
    results.append(("Application Modules", test_modules()))
    results.append(("Directories", test_directories()))
    results.append(("Matplotlib Backend", test_matplotlib_backend()))
    results.append(("CustomTkinter Theme", test_customtkinter_theme()))
    results.append(("Data Structures", test_data_creation()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    all_passed = True
    for test_name, passed in results:
        status = "PASSED" if passed else "FAILED"
        symbol = "✓" if passed else "✗"
        print(f"{symbol} {test_name:25} {status}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n✓ All tests passed! The application is ready to use.")
        print("\nRun the application with:")
        print("  python main.py")
        return 0
    else:
        print("\n✗ Some tests failed. Please install missing dependencies.")
        print("\nTo install all dependencies:")
        print("  pip install -r requirements.txt")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())