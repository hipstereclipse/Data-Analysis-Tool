#!/usr/bin/env python3
"""
file_manager.py - File input/output operations for Excel Data Plotter
Handles loading, saving, and exporting data files
"""

import os  # For file path operations
import json  # For JSON file handling
import pandas as pd  # For Excel/CSV operations
from datetime import datetime  # For timestamps
from tkinter import filedialog, messagebox  # For file dialogs
import traceback  # For error reporting

from models import FileData, SeriesConfig, ProjectData  # Import data models
from constants import FileTypes, AppConfig  # Import constants


class FileManager:
    """
    Manages all file operations for the application
    Provides methods for loading, saving, and exporting data
    """

    @staticmethod
    def load_excel_file(filepath):
        """
        Load an Excel file into a pandas DataFrame

        Args:
            filepath (str): Path to Excel file

        Returns:
            pd.DataFrame: Loaded data

        Raises:
            Exception: If file cannot be loaded
        """
        try:
            # Check if file exists
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"File not found: {filepath}")

            # Determine file extension
            _, ext = os.path.splitext(filepath.lower())

            # Load based on extension
            if ext in ['.xlsx', '.xlsm', '.xlsb']:
                # Modern Excel format
                df = pd.read_excel(filepath, engine='openpyxl')
            elif ext == '.xls':
                # Legacy Excel format
                df = pd.read_excel(filepath, engine='xlrd')
            else:
                # Try auto-detection
                df = pd.read_excel(filepath)

            # Validate DataFrame
            if df.empty:
                raise ValueError("File contains no data")

            return df

        except Exception as e:
            # Re-raise with more context
            raise Exception(f"Failed to load Excel file '{filepath}': {str(e)}")

    @staticmethod
    def load_csv_file(filepath, **kwargs):
        """
        Load a CSV file into a pandas DataFrame

        Args:
            filepath (str): Path to CSV file
            **kwargs: Additional pandas read_csv arguments

        Returns:
            pd.DataFrame: Loaded data

        Raises:
            Exception: If file cannot be loaded
        """
        try:
            # Check if file exists
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"File not found: {filepath}")

            # Default CSV reading parameters
            params = {
                'encoding': 'utf-8',  # Default encoding
                'na_values': ['NA', 'N/A', 'null', 'NULL', ''],  # Null value indicators
                'keep_default_na': True,  # Keep default NaN recognition
                'parse_dates': True,  # Try to parse dates
                'infer_datetime_format': True,  # Infer date formats
            }

            # Update with any provided kwargs
            params.update(kwargs)

            # Load CSV file
            df = pd.read_csv(filepath, **params)

            # Validate DataFrame
            if df.empty:
                raise ValueError("File contains no data")

            return df

        except UnicodeDecodeError:
            # Try alternative encodings
            encodings = ['latin-1', 'iso-8859-1', 'cp1252']
            for encoding in encodings:
                try:
                    params['encoding'] = encoding
                    df = pd.read_csv(filepath, **params)
                    return df
                except:
                    continue

            # If all encodings fail
            raise Exception(f"Failed to load CSV file '{filepath}': Unable to detect encoding")

        except Exception as e:
            # Re-raise with more context
            raise Exception(f"Failed to load CSV file '{filepath}': {str(e)}")

    @staticmethod
    def load_file(filepath):
        """
        Load any supported file type

        Args:
            filepath (str): Path to file

        Returns:
            FileData: Loaded file data object

        Raises:
            Exception: If file cannot be loaded
        """
        # Get file extension
        _, ext = os.path.splitext(filepath.lower())

        try:
            # Load based on file type
            if ext == '.csv':
                df = FileManager.load_csv_file(filepath)
            elif ext in ['.xlsx', '.xls', '.xlsm', '.xlsb']:
                df = FileManager.load_excel_file(filepath)
            else:
                raise ValueError(f"Unsupported file type: {ext}")

            # Create FileData object
            file_data = FileData(filepath, df)

            return file_data

        except Exception as e:
            raise Exception(f"Failed to load file: {str(e)}")

    @staticmethod
    def save_project(project_data, filepath):
        """
        Save project configuration to JSON file

        Args:
            project_data (ProjectData): Project data to save
            filepath (str): Path to save file

        Raises:
            Exception: If save fails
        """
        try:
            # Update last modified time
            project_data.last_modified = datetime.now().isoformat()

            # Convert to dictionary for JSON serialization
            save_data = {
                'version': project_data.version,
                'creation_date': project_data.creation_date,
                'last_modified': project_data.last_modified,
                'files': project_data.files,
                'series': project_data.series,
                'annotations': project_data.annotations,
                'plot_config': project_data.plot_config,
                'window_state': project_data.window_state
            }

            # Create backup if file exists
            if os.path.exists(filepath):
                backup_path = filepath + '.backup'
                try:
                    os.rename(filepath, backup_path)
                except:
                    pass  # Ignore backup errors

            # Write to file with pretty formatting
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)

            # Delete backup after successful save
            backup_path = filepath + '.backup'
            if os.path.exists(backup_path):
                try:
                    os.remove(backup_path)
                except:
                    pass  # Ignore cleanup errors

        except Exception as e:
            # Try to restore backup if save failed
            backup_path = filepath + '.backup'
            if os.path.exists(backup_path):
                try:
                    os.rename(backup_path, filepath)
                except:
                    pass

            raise Exception(f"Failed to save project: {str(e)}")

    @staticmethod
    def load_project(filepath):
        """
        Load project configuration from JSON file

        Args:
            filepath (str): Path to project file

        Returns:
            ProjectData: Loaded project data

        Raises:
            Exception: If load fails
        """
        try:
            # Check if file exists
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"Project file not found: {filepath}")

            # Load JSON data
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Create ProjectData object
            project = ProjectData()

            # Populate project data
            project.version = data.get('version', '1.0')
            project.creation_date = data.get('creation_date')
            project.last_modified = data.get('last_modified')
            project.files = data.get('files', [])
            project.series = data.get('series', [])
            project.annotations = data.get('annotations', [])
            project.plot_config = data.get('plot_config', project.plot_config)
            project.window_state = data.get('window_state', project.window_state)

            return project

        except json.JSONDecodeError as e:
            raise Exception(f"Invalid project file format: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to load project: {str(e)}")

    @staticmethod
    def export_dataframe_to_excel(df, filepath, sheet_name='Sheet1'):
        """
        Export DataFrame to Excel file

        Args:
            df (pd.DataFrame): Data to export
            filepath (str): Output file path
            sheet_name (str): Excel sheet name

        Raises:
            Exception: If export fails
        """
        try:
            # Create Excel writer with modern engine
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # Write DataFrame to sheet
                df.to_excel(writer, sheet_name=sheet_name, index=False)

                # Get workbook and worksheet
                workbook = writer.book
                worksheet = writer.sheets[sheet_name]

                # Auto-adjust column widths
                for column in df.columns:
                    column_width = max(
                        df[column].astype(str).map(len).max(),  # Max data width
                        len(str(column))  # Column name width
                    )
                    # Limit width to reasonable maximum
                    column_width = min(column_width + 2, 50)

                    # Get column letter
                    col_idx = df.columns.get_loc(column)
                    col_letter = chr(65 + col_idx) if col_idx < 26 else 'AA'

                    # Set column width
                    worksheet.column_dimensions[col_letter].width = column_width

        except Exception as e:
            raise Exception(f"Failed to export to Excel: {str(e)}")

    @staticmethod
    def export_dataframe_to_csv(df, filepath):
        """
        Export DataFrame to CSV file

        Args:
            df (pd.DataFrame): Data to export
            filepath (str): Output file path

        Raises:
            Exception: If export fails
        """
        try:
            # Export to CSV with UTF-8 encoding
            df.to_csv(filepath, index=False, encoding='utf-8')

        except Exception as e:
            raise Exception(f"Failed to export to CSV: {str(e)}")

    @staticmethod
    def export_series_data(series_list, loaded_files, filepath):
        """
        Export multiple series to a single Excel file

        Args:
            series_list (dict): Dictionary of series configurations
            loaded_files (dict): Dictionary of loaded file data
            filepath (str): Output file path

        Raises:
            Exception: If export fails
        """
        try:
            # Create Excel writer
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # Export each series to a separate sheet
                for series_id, series in series_list.items():
                    # Get file data
                    file_data = loaded_files.get(series.file_id)
                    if not file_data:
                        continue

                    # Extract series data range
                    start_idx = max(0, series.start_index)
                    end_idx = min(len(file_data.df), series.end_index or len(file_data.df))
                    data_slice = file_data.df.iloc[start_idx:end_idx]

                    # Select relevant columns
                    if series.x_column == 'Index':
                        # Create index column
                        export_df = data_slice[[series.y_column]].copy()
                        export_df.insert(0, 'Index', range(start_idx, end_idx))
                    else:
                        # Use specified columns
                        cols = [series.x_column, series.y_column]
                        # Filter for existing columns
                        cols = [c for c in cols if c in data_slice.columns]
                        export_df = data_slice[cols].copy()

                    # Create valid sheet name (Excel limit is 31 chars)
                    sheet_name = series.name[:31]
                    # Remove invalid characters
                    for char in ['/', '\\', '?', '*', '[', ']', ':']:
                        sheet_name = sheet_name.replace(char, '_')

                    # Write to Excel
                    export_df.to_excel(writer, sheet_name=sheet_name, index=False)

        except Exception as e:
            raise Exception(f"Failed to export series data: {str(e)}")

    @staticmethod
    def export_plot_image(figure, filepath, dpi=300, bbox_inches='tight'):
        """
        Export matplotlib figure to image file

        Args:
            figure: Matplotlib figure object
            filepath (str): Output file path
            dpi (int): Dots per inch resolution
            bbox_inches: Bounding box setting

        Raises:
            Exception: If export fails
        """
        try:
            # Save figure with specified settings
            figure.savefig(
                filepath,
                dpi=dpi,
                bbox_inches=bbox_inches,
                facecolor=figure.get_facecolor(),
                edgecolor='none'
            )

        except Exception as e:
            raise Exception(f"Failed to export plot: {str(e)}")

    @staticmethod
    def import_series_config(filepath):
        """
        Import series configuration from JSON file

        Args:
            filepath (str): Path to configuration file

        Returns:
            list: List of series configuration dictionaries

        Raises:
            Exception: If import fails
        """
        try:
            # Load JSON file
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Validate format
            if 'series' not in data:
                raise ValueError("Invalid configuration file: missing 'series' key")

            # Return series list
            return data['series']

        except json.JSONDecodeError as e:
            raise Exception(f"Invalid configuration file format: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to import configuration: {str(e)}")

    @staticmethod
    def validate_file_access(filepath, mode='r'):
        """
        Validate file access permissions

        Args:
            filepath (str): Path to check
            mode (str): Access mode ('r' for read, 'w' for write)

        Returns:
            bool: True if accessible, False otherwise
        """
        try:
            if mode == 'r':
                # Check read access
                return os.path.exists(filepath) and os.access(filepath, os.R_OK)
            elif mode == 'w':
                # Check write access to directory
                directory = os.path.dirname(filepath) or '.'
                return os.access(directory, os.W_OK)
            else:
                return False

        except:
            return False

    @staticmethod
    def get_file_info(filepath):
        """
        Get information about a file

        Args:
            filepath (str): Path to file

        Returns:
            dict: File information dictionary
        """
        try:
            # Get file stats
            stats = os.stat(filepath)

            # Build info dictionary
            info = {
                'path': filepath,
                'name': os.path.basename(filepath),
                'directory': os.path.dirname(filepath),
                'extension': os.path.splitext(filepath)[1],
                'size_bytes': stats.st_size,
                'size_mb': stats.st_size / (1024 * 1024),
                'modified_time': datetime.fromtimestamp(stats.st_mtime),
                'created_time': datetime.fromtimestamp(stats.st_ctime),
                'readable': os.access(filepath, os.R_OK),
                'writable': os.access(filepath, os.W_OK)
            }

            return info

        except Exception as e:
            return {'error': str(e)}