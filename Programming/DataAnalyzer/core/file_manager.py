#!/usr/bin/env python3
"""
File management operations
"""

import logging
from pathlib import Path
from typing import List, Optional, Union
import pandas as pd
import numpy as np
from tkinter import filedialog
import json

from models.data_models import FileData
from config.constants import AppConfig, FileTypes
from utils.validators import validate_file_size, validate_dataframe

logger = logging.getLogger(__name__)


class FileManager:
    """Handles all file operations"""

    def __init__(self):
        self.supported_extensions = {
            '.xlsx', '.xls', '.xlsm', '.csv', '.tsv'
        }
        self.encoding_options = ['utf-8', 'latin1', 'cp1252']

    def select_files(self) -> List[str]:
        """Open file selection dialog"""
        filetypes = [
            (FileTypes.EXCEL.description, " ".join(FileTypes.EXCEL.extensions)),
            (FileTypes.CSV.description, " ".join(FileTypes.CSV.extensions)),
            ("All Files", "*.*")
        ]

        files = filedialog.askopenfilenames(
            title="Select Data Files",
            filetypes=filetypes
        )

        return list(files)

    def open_file_dialog(self, title: str, filetypes: List[tuple]) -> Optional[str]:
        """Open single file dialog"""
        return filedialog.askopenfilename(
            title=title,
            filetypes=filetypes
        )

    def save_file_dialog(self, title: str, filetypes: List[tuple]) -> Optional[str]:
        """Save file dialog"""
        return filedialog.asksaveasfilename(
            title=title,
            filetypes=filetypes,
            defaultextension=filetypes[0][1].split('*')[1]
        )

    def load_file(self, filepath: Union[str, Path]) -> FileData:
        """Load a data file"""
        filepath = Path(filepath)

        # Validate file
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        if not validate_file_size(filepath, AppConfig.MAX_FILE_SIZE_MB):
            raise ValueError(f"File too large (max {AppConfig.MAX_FILE_SIZE_MB}MB)")

        # Load based on extension
        ext = filepath.suffix.lower()

        if ext in ['.xlsx', '.xls', '.xlsm']:
            df = self._load_excel(filepath)
        elif ext in ['.csv', '.tsv']:
            df = self._load_csv(filepath)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

        # Validate dataframe
        validate_dataframe(df)

        # Clean and prepare dataframe
        df = self._prepare_dataframe(df)

        logger.info(f"Loaded file: {filepath.name} ({len(df)} rows, {len(df.columns)} columns)")

        return FileData(str(filepath), df)

    def _load_excel(self, filepath: Path) -> pd.DataFrame:
        """Load Excel file"""
        try:
            # Try to read with openpyxl engine first
            excel_file = pd.ExcelFile(filepath, engine='openpyxl')

            # If multiple sheets, use first with data
            if len(excel_file.sheet_names) > 1:
                for sheet in excel_file.sheet_names:
                    df = pd.read_excel(excel_file, sheet_name=sheet)
                    if not df.empty:
                        logger.info(f"Using sheet: {sheet}")
                        return df

            # Default to first sheet
            return pd.read_excel(excel_file, sheet_name=0)

        except Exception as e:
            # Fallback to default engine
            logger.warning(f"Openpyxl failed, trying default: {e}")
            return pd.read_excel(filepath)

    def _load_csv(self, filepath: Path) -> pd.DataFrame:
        """Load CSV file with encoding detection"""
        # Try different encodings
        for encoding in self.encoding_options:
            try:
                return pd.read_csv(
                    filepath,
                    encoding=encoding,
                    sep=None,  # Auto-detect separator
                    engine='python',
                    on_bad_lines='skip'
                )
            except UnicodeDecodeError:
                continue

        # If all encodings fail, use latin1 (accepts all bytes)
        return pd.read_csv(filepath, encoding='latin1', on_bad_lines='skip')

    def _prepare_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and prepare dataframe"""
        # Remove completely empty rows and columns
        df = df.dropna(how='all')
        df = df.dropna(axis=1, how='all')

        # Clean column names
        df.columns = [self._clean_column_name(col) for col in df.columns]

        # Convert obvious datetime columns
        for col in df.columns:
            if self._is_datetime_column(df[col]):
                try:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                except:
                    pass

        # Convert obvious numeric columns
        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                    # Try numeric conversion
                    numeric = pd.to_numeric(df[col], errors='coerce')
                    if numeric.notna().sum() / len(df) > 0.5:  # >50% valid
                        df[col] = numeric
                except:
                    pass

        return df

    def _clean_column_name(self, name: str) -> str:
        """Clean column name"""
        if pd.isna(name):
            return "Unnamed"

        name = str(name).strip()
        # Remove problematic characters
        for char in ['\\n', '\\r', '\\t']:
            name = name.replace(char, ' ')

        # Collapse multiple spaces
        while '  ' in name:
            name = name.replace('  ', ' ')

        return name if name else "Unnamed"

    def _is_datetime_column(self, series: pd.Series) -> bool:
        """Check if series contains datetime data"""
        if pd.api.types.is_datetime64_any_dtype(series):
            return True

        # Sample check for string dates
        sample = series.dropna().head(10)
        if len(sample) == 0:
            return False

        try:
            pd.to_datetime(sample, errors='coerce')
            return True
        except:
            return False

    def export_dataframe(self, df: pd.DataFrame, filepath: Union[str, Path]):
        """Export dataframe to file"""
        filepath = Path(filepath)
        ext = filepath.suffix.lower()

        if ext == '.csv':
            df.to_csv(filepath, index=False)
        elif ext in ['.xlsx', '.xls']:
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Data')
        else:
            raise ValueError(f"Unsupported export format: {ext}")

        logger.info(f"Exported data to: {filepath}")