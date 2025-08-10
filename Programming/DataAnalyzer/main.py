# !/usr/bin/env python3
"""
Excel Data Plotter - Main Entry Point
Professional multi-file data visualization and analysis tool
"""

import sys
import logging
from pathlib import Path

# Create necessary directories
app_dir = Path.home() / '.excel_data_plotter'
app_dir.mkdir(exist_ok=True)
(app_dir / 'logs').mkdir(exist_ok=True)
(app_dir / 'temp').mkdir(exist_ok=True)
(app_dir / 'autosave').mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(app_dir / 'logs' / 'app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Main application entry point"""
    try:
        logger.info("Starting Excel Data Plotter...")

        # Import here to avoid issues if dependencies are missing
        from app import ExcelDataPlotter

        # Create and run application
        app = ExcelDataPlotter()
        app.mainloop()

        logger.info("Application closed normally")

    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        print(f"\nError: Missing required dependency - {e}")
        print("\nPlease install all requirements:")
        print("  pip install -r requirements.txt")
        sys.exit(1)

    except Exception as e:
        logger.exception("Unexpected error occurred")
        print(f"\nUnexpected error: {e}")
        print("\nPlease check the log file at:")
        print(f"  {app_dir / 'logs' / 'app.log'}")
        sys.exit(1)


if __name__ == "__main__":
    main()