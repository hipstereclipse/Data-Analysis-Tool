"""
core/file_manager.py - File Manager
Handles file operations including loading Excel/CSV files
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple
import logging
import uuid
from tkinter import filedialog
import os

from models.data_models import FileData
from config.constants import FileTypes

logger = logging.getLogger(__name__)


class FileManager:
    """
    Manages file operations
    Handles loading, validating, and processing data files
    """

    def __init__(self):
        """Initialize file manager"""
        self.supported_extensions = ['.xlsx', '.xls', '.xlsm', '.xlsb', '.csv', '.tsv', '.txt']
        self.max_file_size = 500 * 1024 * 1024  # 500 MB

    def load_file(self, filepath: str, sheet_name: Optional[str] = None) -> Optional[FileData]:
        """
        Load a data file

        Args:
            filepath: Path to the file
            sheet_name: Specific sheet for Excel files

        Returns:
            FileData object if successful, None otherwise
        """
        try:
            path = Path(filepath)

            # Validate file
            if not path.exists():
                logger.error(f"File not found: {filepath}")
                return None

            if path.stat().st_size > self.max_file_size:
                logger.error(f"File too large: {filepath}")
                return None

            # Determine file type and load
            ext = path.suffix.lower()

            if ext in ['.xlsx', '.xls', '.xlsm', '.xlsb']:
                file_data = self.load_excel_file(filepath, sheet_name)
            elif ext in ['.csv', '.tsv', '.txt']:
                file_data = self.load_csv_file(filepath)
            else:
                logger.error(f"Unsupported file type: {ext}")
                return None

            return file_data

        except Exception as e:
            logger.error(f"Failed to load file {filepath}: {e}")
            return None

    def load_excel_file(self, filepath: str, sheet_name: Optional[str] = None) -> Optional[FileData]:
        """
        Load an Excel file with comprehensive column name handling

        Args:
            filepath: Path to Excel file
            sheet_name: Specific sheet to load

        Returns:
            FileData object if successful
        """
        try:
            path = Path(filepath)
            logger.info(f"Loading Excel file: {path}")

            # Read Excel file
            excel_file = pd.ExcelFile(filepath)

            # Get all sheets
            sheets = {}

            if sheet_name:
                # Load specific sheet
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                # Immediately ensure column names are strings to prevent integer column issues
                df.columns = [str(col) if col is not None else f"Unnamed_{i}" for i, col in enumerate(df.columns)]
                sheets[sheet_name] = df
                main_df = df
                logger.debug(f"Loaded specific sheet '{sheet_name}' with columns: {list(df.columns)}")
            else:
                # Load all sheets with improved error handling
                for name in excel_file.sheet_names:
                    try:
                        sheet_df = pd.read_excel(excel_file, sheet_name=name)
                        # Ensure column names are strings and handle None/NaN columns
                        sheet_df.columns = [str(col) if col is not None else f"Unnamed_{i}" for i, col in enumerate(sheet_df.columns)]
                        sheets[name] = sheet_df
                        logger.debug(f"Successfully loaded sheet '{name}' with columns: {list(sheet_df.columns)}")
                    except Exception as sheet_error:
                        logger.warning(f"Failed to load sheet '{name}': {sheet_error}")
                        continue

                # Use first successfully loaded sheet as main dataframe
                if sheets:
                    main_df = list(sheets.values())[0]
                    logger.info(f"Using sheet '{list(sheets.keys())[0]}' as main dataframe")
                else:
                    logger.error("No sheets could be loaded from Excel file")
                    return None

            # Double-check main dataframe column names are strings
            if main_df is not None:
                main_df.columns = [str(col) if col is not None else f"Unnamed_{i}" for i, col in enumerate(main_df.columns)]
                logger.debug(f"Final main dataframe columns: {list(main_df.columns)}")

            # Create FileData object
            file_data = FileData(
                filepath=str(path),
                data=main_df,
                filename=path.name
            )
            
            # Set additional properties
            file_data.file_size = path.stat().st_size
            file_data.sheet_name = sheet_name or excel_file.sheet_names[0]
            
            # Store sheets info (if needed for future use)
            file_data.sheets = sheets

            logger.info(f"Successfully loaded Excel file: {path.name} with {len(sheets)} sheet(s)")
            return file_data

        except Exception as e:
            logger.error(f"Failed to load Excel file: {e}")
            return None

            logger.info(f"Loaded Excel file: {path.name} with {len(sheets)} sheet(s)")
            return file_data

        except Exception as e:
            logger.error(f"Failed to load Excel file: {e}")
            return None

    def load_csv_file(self, filepath: str) -> Optional[FileData]:
        """
        Load a CSV file

        Args:
            filepath: Path to CSV file

        Returns:
            FileData object if successful
        """
        try:
            path = Path(filepath)

            # Try to detect delimiter
            with open(filepath, 'r') as f:
                first_line = f.readline()
                if '\t' in first_line:
                    delimiter = '\t'
                elif ',' in first_line:
                    delimiter = ','
                elif ';' in first_line:
                    delimiter = ';'
                else:
                    delimiter = ','

            # Read CSV
            df = pd.read_csv(filepath, delimiter=delimiter)

            # Create FileData object
            file_data = FileData(
                filepath=str(path),
                data=df,
                filename=path.name
            )
            
            # Set additional properties
            file_data.file_size = path.stat().st_size

            logger.info(f"Loaded CSV file: {path.name} with {len(df)} rows")
            return file_data

        except Exception as e:
            logger.error(f"Failed to load CSV file: {e}")
            return None

    def save_dataframe(self, df: pd.DataFrame, filepath: str, **kwargs):
        """
        Save a dataframe to file

        Args:
            df: DataFrame to save
            filepath: Path to save to
            **kwargs: Additional arguments for to_excel/to_csv
        """
        try:
            path = Path(filepath)
            ext = path.suffix.lower()

            if ext in ['.xlsx', '.xls']:
                df.to_excel(filepath, index=False, **kwargs)
            elif ext in ['.csv', '.tsv', '.txt']:
                delimiter = '\t' if ext == '.tsv' else ','
                df.to_csv(filepath, index=False, sep=delimiter, **kwargs)
            else:
                raise ValueError(f"Unsupported file type: {ext}")

            logger.info(f"Saved dataframe to {filepath}")

        except Exception as e:
            logger.error(f"Failed to save dataframe: {e}")
            raise

    def open_file_dialog(self, title: str = "Select File",
                         filetypes: List[Tuple[str, str]] = None) -> Optional[str]:
        """
        Open file selection dialog

        Args:
            title: Dialog title
            filetypes: List of (description, pattern) tuples

        Returns:
            Selected filepath or None
        """
        if not filetypes:
            filetypes = [
                FileTypes.DATA.filedialog_tuple,
                FileTypes.EXCEL.filedialog_tuple,
                FileTypes.CSV.filedialog_tuple,
                FileTypes.ALL.filedialog_tuple
            ]

        filepath = filedialog.askopenfilename(title=title, filetypes=filetypes)
        return filepath if filepath else None

    def open_files_dialog(self, title: str = "Select Files",
                          filetypes: List[Tuple[str, str]] = None) -> List[str]:
        """
        Open multiple file selection dialog

        Args:
            title: Dialog title
            filetypes: List of (description, pattern) tuples

        Returns:
            List of selected filepaths
        """
        if not filetypes:
            filetypes = [
                FileTypes.DATA.filedialog_tuple,
                FileTypes.EXCEL.filedialog_tuple,
                FileTypes.CSV.filedialog_tuple,
                FileTypes.ALL.filedialog_tuple
            ]

        filepaths = filedialog.askopenfilenames(title=title, filetypes=filetypes)
        return list(filepaths) if filepaths else []

    def save_file_dialog(self, title: str = "Save File",
                         defaultextension: str = ".xlsx",
                         filetypes: List[Tuple[str, str]] = None) -> Optional[str]:
        """
        Open save file dialog

        Args:
            title: Dialog title
            defaultextension: Default file extension
            filetypes: List of (description, pattern) tuples

        Returns:
            Selected filepath or None
        """
        if not filetypes:
            filetypes = [
                FileTypes.EXCEL.filedialog_tuple,
                FileTypes.CSV.filedialog_tuple,
                FileTypes.ALL.filedialog_tuple
            ]

        filepath = filedialog.asksaveasfilename(
            title=title,
            defaultextension=defaultextension,
            filetypes=filetypes
        )
        return filepath if filepath else None

    def validate_file(self, filepath: str) -> Tuple[bool, str]:
        """
        Validate a file for loading

        Args:
            filepath: Path to file

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            path = Path(filepath)

            if not path.exists():
                return False, "File does not exist"

            if not path.is_file():
                return False, "Path is not a file"

            if path.stat().st_size == 0:
                return False, "File is empty"

            if path.stat().st_size > self.max_file_size:
                size_mb = path.stat().st_size / (1024 * 1024)
                return False, f"File too large ({size_mb:.1f} MB)"

            ext = path.suffix.lower()
            if ext not in self.supported_extensions:
                return False, f"Unsupported file type: {ext}"

            return True, ""

        except Exception as e:
            return False, str(e)
