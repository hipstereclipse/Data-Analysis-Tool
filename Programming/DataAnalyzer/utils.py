#!/usr/bin/env python3
"""
utils.py - Utility functions for Excel Data Plotter
Contains helper functions used throughout the application
"""

import os  # For file operations
import re  # For regular expressions
import pandas as pd  # For data manipulation
import numpy as np  # For numerical operations
from datetime import datetime, timedelta  # For date operations
import platform  # For system information
import psutil  # For system resources (optional)


def format_file_size(size_bytes):
    """
    Format file size in bytes to human-readable format

    Args:
        size_bytes (int): Size in bytes

    Returns:
        str: Formatted size string (e.g., "1.5 MB")
    """
    # Define size units
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            # Return formatted size with appropriate unit
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    # For very large files
    return f"{size_bytes:.1f} PB"


def sanitize_filename(filename, max_length=255):
    """
    Sanitize filename for safe file system usage

    Args:
        filename (str): Original filename
        max_length (int): Maximum allowed length

    Returns:
        str: Sanitized filename
    """
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')

    # Remove control characters
    filename = re.sub(r'[\x00-\x1f\x7f]', '', filename)

    # Remove leading/trailing spaces and dots
    filename = filename.strip('. ')

    # Truncate if too long
    if len(filename) > max_length:
        # Keep extension if present
        name, ext = os.path.splitext(filename)
        max_name_length = max_length - len(ext)
        filename = name[:max_name_length] + ext

    # Ensure filename is not empty
    if not filename:
        filename = "unnamed"

    return filename


def validate_excel_sheet_name(name):
    """
    Validate and sanitize Excel sheet name

    Args:
        name (str): Proposed sheet name

    Returns:
        str: Valid sheet name (max 31 chars, no invalid characters)
    """
    # Excel sheet name limitations
    max_length = 31
    invalid_chars = ['/', '\\', '?', '*', '[', ']', ':']

    # Replace invalid characters
    for char in invalid_chars:
        name = name.replace(char, '_')

    # Truncate if too long
    if len(name) > max_length:
        name = name[:max_length]

    # Ensure not empty
    if not name:
        name = "Sheet1"

    return name


def detect_datetime_column(data_series):
    """
    Detect if a data series contains datetime values

    Args:
        data_series: Pandas Series or array-like data

    Returns:
        bool: True if datetime data detected
    """
    try:
        # Check if already datetime type
        if pd.api.types.is_datetime64_any_dtype(data_series):
            return True

        # Sample first few non-null values
        sample = pd.Series(data_series).dropna().head(20)

        if len(sample) == 0:
            return False

        # Try to convert to datetime
        converted = pd.to_datetime(sample, errors='coerce', infer_datetime_format=True)

        # Check success rate
        success_rate = converted.notna().sum() / len(sample)

        # Consider datetime if >80% successful conversion
        return success_rate > 0.8

    except Exception:
        return False


def convert_to_datetime(data_series):
    """
    Convert data series to datetime if possible

    Args:
        data_series: Input data

    Returns:
        Converted datetime series or original if conversion fails
    """
    try:
        # Return if already datetime
        if pd.api.types.is_datetime64_any_dtype(data_series):
            return data_series

        # Attempt conversion
        converted = pd.to_datetime(data_series, errors='coerce', infer_datetime_format=True)

        # Check if conversion was successful
        if converted.notna().sum() / len(data_series.dropna()) > 0.8:
            return converted
        else:
            return data_series

    except Exception:
        return data_series


def detect_data_type(data_series):
    """
    Detect the type of data in a series

    Args:
        data_series: Pandas Series or array

    Returns:
        str: Data type ('numeric', 'datetime', 'categorical', 'text')
    """
    # Convert to pandas Series for analysis
    series = pd.Series(data_series)

    # Remove null values for analysis
    non_null = series.dropna()

    if len(non_null) == 0:
        return 'empty'

    # Check for datetime
    if pd.api.types.is_datetime64_any_dtype(series) or detect_datetime_column(series):
        return 'datetime'

    # Check for numeric
    try:
        pd.to_numeric(non_null)
        return 'numeric'
    except:
        pass

    # Check for categorical (limited unique values)
    unique_ratio = len(non_null.unique()) / len(non_null)
    if unique_ratio < 0.05:  # Less than 5% unique values
        return 'categorical'

    # Default to text
    return 'text'


def find_header_row(dataframe, max_rows=20):
    """
    Attempt to auto-detect header row in dataframe

    Args:
        dataframe: Pandas DataFrame
        max_rows: Maximum rows to check

    Returns:
        int: Best guess for header row index
    """
    best_row = 0
    max_non_numeric = 0

    # Check first few rows
    for i in range(min(max_rows, len(dataframe))):
        row = dataframe.iloc[i]

        # Count non-numeric values
        non_numeric_count = 0
        for val in row:
            try:
                float(val)
            except:
                non_numeric_count += 1

        # Track row with most non-numeric values (likely headers)
        if non_numeric_count > max_non_numeric:
            max_non_numeric = non_numeric_count
            best_row = i

    return best_row


def interpolate_missing_data(x_data, y_data, method='linear'):
    """
    Interpolate missing data points

    Args:
        x_data: X-axis values
        y_data: Y-axis values with potential NaN
        method: Interpolation method

    Returns:
        tuple: (x_clean, y_interpolated)
    """
    # Create dataframe for easier handling
    df = pd.DataFrame({'x': x_data, 'y': y_data})

    # Remove rows where both x and y are NaN
    df = df.dropna(subset=['x'])

    # Interpolate y values
    df['y'] = df['y'].interpolate(method=method)

    return df['x'].values, df['y'].values


def calculate_sampling_rate(time_data):
    """
    Calculate sampling rate from time series data

    Args:
        time_data: Array of time values

    Returns:
        float: Sampling rate in Hz
    """
    try:
        # Convert to datetime if needed
        if not pd.api.types.is_datetime64_any_dtype(time_data):
            time_data = pd.to_datetime(time_data)

        # Calculate time differences
        time_diffs = pd.Series(time_data).diff().dropna()

        # Get median time difference (robust to outliers)
        median_diff = time_diffs.median()

        # Convert to seconds
        if hasattr(median_diff, 'total_seconds'):
            seconds = median_diff.total_seconds()
        else:
            seconds = float(median_diff)

        # Calculate frequency (Hz)
        if seconds > 0:
            return 1.0 / seconds
        else:
            return 1.0

    except Exception:
        return 1.0  # Default to 1 Hz


def generate_color_sequence(n_colors):
    """
    Generate a sequence of distinct colors

    Args:
        n_colors (int): Number of colors needed

    Returns:
        list: List of hex color codes
    """
    # Base colors to cycle through
    base_colors = [
        '#1f77b4',  # Blue
        '#ff7f0e',  # Orange
        '#2ca02c',  # Green
        '#d62728',  # Red
        '#9467bd',  # Purple
        '#8c564b',  # Brown
        '#e377c2',  # Pink
        '#7f7f7f',  # Gray
        '#bcbd22',  # Olive
        '#17becf'  # Cyan
    ]

    colors = []

    # Cycle through base colors
    for i in range(n_colors):
        colors.append(base_colors[i % len(base_colors)])

    return colors


def format_number(value, precision=3):
    """
    Format number for display with appropriate notation

    Args:
        value: Numeric value
        precision: Number of significant digits

    Returns:
        str: Formatted number string
    """
    try:
        value = float(value)

        # Use scientific notation for very large or small numbers
        if abs(value) >= 1e6 or (abs(value) < 1e-3 and value != 0):
            return f"{value:.{precision}e}"
        else:
            return f"{value:.{precision}f}"

    except (ValueError, TypeError):
        return str(value)


def create_time_series_index(start_date, n_points, frequency='1H'):
    """
    Create a time series index for data without timestamps

    Args:
        start_date: Starting datetime
        n_points: Number of data points
        frequency: Pandas frequency string (e.g., '1H' for hourly)

    Returns:
        pd.DatetimeIndex: DateTime index
    """
    # Parse start date if string
    if isinstance(start_date, str):
        start_date = pd.to_datetime(start_date)

    # Create date range
    return pd.date_range(start=start_date, periods=n_points, freq=frequency)


def estimate_memory_usage(dataframe):
    """
    Estimate memory usage of a DataFrame

    Args:
        dataframe: Pandas DataFrame

    Returns:
        dict: Memory usage information
    """
    # Get memory usage in bytes
    memory_bytes = dataframe.memory_usage(deep=True).sum()

    # Get per-column memory
    column_memory = {}
    for col in dataframe.columns:
        column_memory[col] = dataframe[col].memory_usage(deep=True)

    return {
        'total': format_file_size(memory_bytes),
        'total_bytes': memory_bytes,
        'per_column': column_memory,
        'rows': len(dataframe),
        'columns': len(dataframe.columns)
    }


def get_system_info():
    """
    Get system information for diagnostics

    Returns:
        dict: System information
    """
    info = {
        'platform': platform.platform(),
        'python_version': platform.python_version(),
        'processor': platform.processor(),
        'architecture': platform.architecture()[0]
    }

    # Try to get memory info (requires psutil)
    try:
        import psutil
        memory = psutil.virtual_memory()
        info['memory_total'] = format_file_size(memory.total)
        info['memory_available'] = format_file_size(memory.available)
        info['memory_percent'] = f"{memory.percent}%"
    except ImportError:
        pass

    return info


def validate_data_range(start_idx, end_idx, data_length):
    """
    Validate and adjust data range indices

    Args:
        start_idx: Starting index
        end_idx: Ending index
        data_length: Total length of data

    Returns:
        tuple: (valid_start, valid_end)
    """
    # Ensure start is non-negative
    start = max(0, start_idx if start_idx is not None else 0)

    # Ensure end doesn't exceed data length
    end = min(data_length, end_idx if end_idx is not None else data_length)

    # Ensure start < end
    if start >= end:
        start = max(0, end - 1)

    return start, end


def merge_dataframes_on_time(df1, df2, time_column='timestamp', method='outer'):
    """
    Merge two dataframes based on time column

    Args:
        df1: First DataFrame
        df2: Second DataFrame
        time_column: Name of time column
        method: Merge method ('inner', 'outer', 'left', 'right')

    Returns:
        pd.DataFrame: Merged DataFrame
    """
    # Ensure time columns are datetime
    if time_column in df1.columns:
        df1[time_column] = pd.to_datetime(df1[time_column])
    if time_column in df2.columns:
        df2[time_column] = pd.to_datetime(df2[time_column])

    # Sort by time
    df1 = df1.sort_values(time_column)
    df2 = df2.sort_values(time_column)

    # Merge
    merged = pd.merge(df1, df2, on=time_column, how=method)

    return merged


def resample_time_series(df, time_column, frequency='1H', method='mean'):
    """
    Resample time series data to new frequency

    Args:
        df: DataFrame with time series
        time_column: Name of time column
        frequency: Target frequency
        method: Aggregation method

    Returns:
        pd.DataFrame: Resampled DataFrame
    """
    # Set time column as index
    df_resampled = df.set_index(time_column)

    # Resample based on method
    if method == 'mean':
        df_resampled = df_resampled.resample(frequency).mean()
    elif method == 'sum':
        df_resampled = df_resampled.resample(frequency).sum()
    elif method == 'max':
        df_resampled = df_resampled.resample(frequency).max()
    elif method == 'min':
        df_resampled = df_resampled.resample(frequency).min()
    else:
        df_resampled = df_resampled.resample(frequency).mean()

    # Reset index
    df_resampled = df_resampled.reset_index()

    return df_resampled


def calculate_date_range(dates):
    """
    Calculate the range of dates in a series

    Args:
        dates: Series of date values

    Returns:
        dict: Date range information
    """
    try:
        # Convert to datetime
        dates = pd.to_datetime(dates)

        # Calculate range
        min_date = dates.min()
        max_date = dates.max()
        duration = max_date - min_date

        return {
            'start': min_date,
            'end': max_date,
            'duration_days': duration.days,
            'duration_hours': duration.total_seconds() / 3600,
            'duration_str': str(duration)
        }

    except Exception:
        return None


def create_backup_filename(original_filename):
    """
    Create a backup filename with timestamp

    Args:
        original_filename (str): Original file path

    Returns:
        str: Backup filename with timestamp
    """
    # Get file parts
    directory = os.path.dirname(original_filename)
    basename = os.path.basename(original_filename)
    name, ext = os.path.splitext(basename)

    # Add timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"{name}_backup_{timestamp}{ext}"

    # Combine path
    return os.path.join(directory, backup_name)