#!/usr/bin/env python3
"""
main.py - Entry point for Excel Data Plotter application
Initializes and launches the main application window
pip install pandas matplotlib openpyxl xlrd seaborn scipy scikit-learn customtkinter pillow
"""

import sys  # For system operations
import os  # For file operations
import traceback  # For error reporting
import logging  # For logging system
from datetime import datetime  # For timestamps


# Configure logging before importing other modules
def setup_logging():
    """
    Configure application logging
    Creates log file and sets up logging format
    """
    # Create logs directory if it doesn't exist
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Create log filename with timestamp
    log_filename = os.path.join(
        log_dir,
        f'excel_plotter_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
    )

    # Configure logging format
    logging.basicConfig(
        level=logging.INFO,  # Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Log format
        handlers=[
            logging.FileHandler(log_filename),  # Write to file
            logging.StreamHandler(sys.stdout)  # Also print to console
        ]
    )

    return logging.getLogger(__name__)


# Setup logging
logger = setup_logging()


def check_dependencies():
    """
    Check if all required dependencies are installed

    Returns:
        bool: True if all dependencies available, False otherwise
    """
    required_packages = {
        'pandas': 'pandas',
        'numpy': 'numpy',
        'matplotlib': 'matplotlib',
        'customtkinter': 'customtkinter',
        'openpyxl': 'openpyxl',
        'xlrd': 'xlrd',
        'scipy': 'scipy',
        'sklearn': 'scikit-learn',
        'PIL': 'Pillow'
    }

    missing_packages = []

    # Check each required package
    for import_name, package_name in required_packages.items():
        try:
            __import__(import_name)
            logger.info(f"✓ {package_name} is installed")
        except ImportError:
            missing_packages.append(package_name)
            logger.error(f"✗ {package_name} is not installed")

    # Report missing packages
    if missing_packages:
        logger.error(f"\nMissing packages: {', '.join(missing_packages)}")
        logger.error(f"Install with: pip install {' '.join(missing_packages)}")
        return False

    return True


def main():
    """
    Main function - application entry point
    Initializes and runs the Excel Data Plotter application
    """
    try:
        # Print startup banner
        print("\n" + "=" * 60)
        print("EXCEL DATA PLOTTER v4.2")
        print("Vacuum Analysis Edition")
        print("=" * 60 + "\n")

        logger.info("Starting Excel Data Plotter application")

        # Check dependencies
        logger.info("Checking dependencies...")
        if not check_dependencies():
            logger.error("Missing required dependencies. Please install them and try again.")
            input("\nPress Enter to exit...")
            sys.exit(1)

        # Import application class after dependency check
        logger.info("Importing application modules...")
        from app import ExcelDataPlotter

        # Create application instance
        logger.info("Creating application window...")
        app = ExcelDataPlotter()

        # Configure window icon if available
        try:
            icon_path = 'assets/icon.ico'
            if os.path.exists(icon_path):
                app.wm_iconbitmap(icon_path)
                logger.info(f"Window icon set from {icon_path}")
        except Exception as e:
            logger.warning(f"Could not set window icon: {e}")

        # Configure window properties
        app.title("Excel Data Plotter - Vacuum Analysis Edition")

        # Center window on screen
        app.update_idletasks()  # Update window to get accurate dimensions
        width = app.winfo_width()
        height = app.winfo_height()
        x = (app.winfo_screenwidth() // 2) - (width // 2)
        y = (app.winfo_screenheight() // 2) - (height // 2)
        app.geometry(f'{width}x{height}+{x}+{y}')

        logger.info("Application window configured")

        # Run application main loop
        logger.info("Starting application main loop")
        app.mainloop()

        logger.info("Application closed normally")

    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        logger.info("Application interrupted by user")
        print("\nApplication interrupted by user")
        sys.exit(0)

    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Critical error: {e}")
        logger.error(traceback.format_exc())

        # Show error dialog if possible
        try:
            import tkinter as tk
            from tkinter import messagebox

            # Create hidden root window
            root = tk.Tk()
            root.withdraw()

            # Show error message
            messagebox.showerror(
                "Critical Error",
                f"An unexpected error occurred:\n\n{str(e)}\n\n"
                "Please check the log file for details."
            )

            root.destroy()

        except:
            # Fallback to console error
            print(f"\nCritical error: {e}")
            print("Please check the log file for details.")
            traceback.print_exc()

        input("\nPress Enter to exit...")
        sys.exit(1)


def run_with_profiling():
    """
    Run application with performance profiling
    Useful for optimization and debugging
    """
    import cProfile
    import pstats

    logger.info("Running with profiling enabled")

    # Create profiler
    profiler = cProfile.Profile()

    # Run main function with profiling
    profiler.enable()
    main()
    profiler.disable()

    # Save profiling results
    stats_file = f'profile_{datetime.now().strftime("%Y%m%d_%H%M%S")}.stats'
    profiler.dump_stats(stats_file)

    # Print top 20 time-consuming functions
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)

    logger.info(f"Profiling results saved to {stats_file}")


if __name__ == "__main__":
    """
    Script entry point
    Run main function when script is executed directly
    """
    # Check for command line arguments
    if len(sys.argv) > 1:
        # Check for special run modes
        if '--profile' in sys.argv:
            # Run with profiling
            run_with_profiling()
        elif '--debug' in sys.argv:
            # Set debug logging level
            logging.getLogger().setLevel(logging.DEBUG)
            logger.debug("Debug mode enabled")
            main()
        elif '--help' in sys.argv:
            # Show help information
            print("\nExcel Data Plotter - Command Line Options")
            print("-" * 40)
            print("  --profile   Run with performance profiling")
            print("  --debug     Enable debug logging")
            print("  --help      Show this help message")
            print()
        else:
            # Unknown argument, run normally
            main()
    else:
        # Normal execution
        main()