#!/usr/bin/env python3
"""
utils/helpers.py - Helper utility functions
Complete implementation with all missing functions
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Optional, Tuple, Any, Union
import colorsys
import hashlib
import json
from datetime import datetime, timedelta
import logging
import re
import shutil
import uuid

logger = logging.getLogger(__name__)


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted string (e.g., "2h 30m 15s")
    """
    if seconds < 0:
        return "0s"

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")

    return " ".join(parts)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing invalid characters

    Args:
        filename: Filename to sanitize

    Returns:
        Sanitized filename
    """
    # Remove invalid characters for Windows/Unix
    invalid_chars = r'<>:"/\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')

    # Remove control characters
    filename = ''.join(char for char in filename if ord(char) >= 32)

    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')

    # Limit length
    max_length = 200
    if len(filename) > max_length:
        name, ext = Path(filename).stem, Path(filename).suffix
        filename = name[:max_length - len(ext)] + ext

    # Ensure filename is not empty
    if not filename:
        filename = "unnamed"

    return filename


def generate_unique_id() -> str:
    """
    Generate a unique identifier

    Returns:
        Unique ID string
    """
    return str(uuid.uuid4())


def generate_color_sequence(n: int, start_hue: float = 0.0) -> List[str]:
    """
    Generate a sequence of distinct colors

    Args:
        n: Number of colors to generate
        start_hue: Starting hue value (0-1)

    Returns:
        List of hex color strings
    """
    colors = []
    golden_ratio = 0.618033988749895

    for i in range(n):
        hue = (start_hue + i * golden_ratio) % 1.0
        # Use high saturation and medium lightness for vibrant colors
        rgb = colorsys.hsv_to_rgb(hue, 0.8, 0.85)
        hex_color = '#{:02x}{:02x}{:02x}'.format(
            int(rgb[0] * 255),
            int(rgb[1] * 255),
            int(rgb[2] * 255)
        )
        colors.append(hex_color)

    return colors


def detect_datetime_column(series: pd.Series, sample_size: int = 100) -> bool:
    """
    Detect if a column contains datetime data

    Args:
        series: Pandas series to check
        sample_size: Number of rows to sample

    Returns:
        True if likely datetime column
    """
    # Already datetime
    if pd.api.types.is_datetime64_any_dtype(series):
        return True

    # Sample the data
    sample = series.dropna().head(sample_size)

    if len(sample) == 0:
        return False

    # Try to convert to datetime
    try:
        pd.to_datetime(sample)
        return True
    except:
        pass

    # Check for common datetime patterns
    datetime_patterns = [
        r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
        r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
        r'\d{2}\.\d{2}\.\d{4}',  # DD.MM.YYYY
        r'\d{4}/\d{2}/\d{2}',  # YYYY/MM/DD
    ]

    sample_str = str(sample.iloc[0]) if len(sample) > 0 else ""
    for pattern in datetime_patterns:
        if re.match(pattern, sample_str):
            return True

    return False


def convert_to_datetime(series: pd.Series, format: Optional[str] = None) -> pd.Series:
    """
    Convert a series to datetime

    Args:
        series: Series to convert
        format: Optional datetime format string

    Returns:
        Converted datetime series
    """
    try:
        if format:
            return pd.to_datetime(series, format=format)
        else:
            return pd.to_datetime(series, infer_datetime_format=True)
    except Exception as e:
        logger.warning(f"Failed to convert to datetime: {e}")
        return series


def detect_datetime_axis(df: pd.DataFrame) -> Optional[str]:
    """
    Detect which column is likely a datetime axis

    Args:
        df: DataFrame to analyze

    Returns:
        Column name if found, None otherwise
    """
    for col in df.columns:
        if detect_datetime_column(df[col]):
            return col

    # Check for common time column names
    time_names = ['time', 'date', 'datetime', 'timestamp', 'ts', 't']
    for col in df.columns:
        if col.lower() in time_names:
            if detect_datetime_column(df[col]):
                return col

    return None


def interpolate_missing_data(data: Union[pd.Series, np.ndarray],
                             method: str = 'linear') -> Union[pd.Series, np.ndarray]:
    """
    Interpolate missing data points

    Args:
        data: Data with missing values
        method: Interpolation method ('linear', 'cubic', 'nearest', etc.)

    Returns:
        Data with interpolated values
    """
    if isinstance(data, np.ndarray):
        # Convert to pandas for interpolation
        series = pd.Series(data)
        interpolated = series.interpolate(method=method)
        return interpolated.values
    else:
        return data.interpolate(method=method)


def calculate_aspect_ratio(width: float, height: float) -> float:
    """
    Calculate aspect ratio

    Args:
        width: Width value
        height: Height value

    Returns:
        Aspect ratio (width/height)
    """
    if height == 0:
        return 1.0
    return width / height


def estimate_sample_rate(time_data: Union[pd.Series, np.ndarray]) -> float:
    """
    Estimate the sample rate from time data

    Args:
        time_data: Time series data

    Returns:
        Estimated sample rate in Hz
    """
    if len(time_data) < 2:
        return 1.0

    # Convert to numpy array if needed
    if isinstance(time_data, pd.Series):
        time_data = time_data.values

    # Calculate differences
    if np.issubdtype(time_data.dtype, np.datetime64):
        # Convert datetime to seconds
        time_data = pd.to_datetime(time_data)
        diffs = np.diff(time_data) / pd.Timedelta(seconds=1)
    else:
        diffs = np.diff(time_data)

    # Get median difference (more robust than mean)
    median_diff = np.median(diffs[diffs > 0]) if any(diffs > 0) else 1.0

    # Calculate sample rate
    sample_rate = 1.0 / median_diff if median_diff > 0 else 1.0

    return sample_rate


def create_backup(filepath: str, backup_dir: Optional[str] = None) -> Optional[str]:
    """
    Create a backup of a file

    Args:
        filepath: Path to file to backup
        backup_dir: Optional backup directory

    Returns:
        Path to backup file if successful, None otherwise
    """
    try:
        source = Path(filepath)
        if not source.exists():
            return None

        # Determine backup directory
        if backup_dir:
            backup_path = Path(backup_dir)
        else:
            backup_path = source.parent / "backups"

        # Create backup directory if needed
        backup_path.mkdir(parents=True, exist_ok=True)

        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_path / f"{source.stem}_{timestamp}{source.suffix}"

        # Copy file
        shutil.copy2(source, backup_file)

        return str(backup_file)

    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        return None


def calculate_hash(data: Union[str, bytes, pd.DataFrame]) -> str:
    """
    Calculate SHA256 hash of data

    Args:
        data: Data to hash

    Returns:
        Hex string of hash
    """
    hasher = hashlib.sha256()

    if isinstance(data, str):
        hasher.update(data.encode('utf-8'))
    elif isinstance(data, bytes):
        hasher.update(data)
    elif isinstance(data, pd.DataFrame):
        hasher.update(data.to_json().encode('utf-8'))
    else:
        hasher.update(str(data).encode('utf-8'))

    return hasher.hexdigest()


def smooth_data(data: np.ndarray, window_size: int = 5,
                method: str = 'mean') -> np.ndarray:
    """
    Smooth data using various methods

    Args:
        data: Data to smooth
        window_size: Size of smoothing window
        method: Smoothing method ('mean', 'median', 'gaussian')

    Returns:
        Smoothed data
    """
    if len(data) < window_size:
        return data

    if method == 'mean':
        # Moving average
        kernel = np.ones(window_size) / window_size
        return np.convolve(data, kernel, mode='same')

    elif method == 'median':
        # Median filter
        from scipy.signal import medfilt
        return medfilt(data, kernel_size=window_size)

    elif method == 'gaussian':
        # Gaussian smoothing
        from scipy.ndimage import gaussian_filter1d
        sigma = window_size / 4
        return gaussian_filter1d(data, sigma)

    else:
        return data


def parse_range_string(range_str: str, max_value: int) -> Tuple[int, int]:
    """
    Parse a range string like "1:100" or "50:" into start and end indices

    Args:
        range_str: Range string
        max_value: Maximum valid value

    Returns:
        Tuple of (start, end) indices
    """
    if not range_str or range_str.strip() == '':
        return 0, max_value

    parts = range_str.split(':')

    if len(parts) == 1:
        # Single value
        try:
            val = int(parts[0])
            return val, val + 1
        except:
            return 0, max_value

    elif len(parts) == 2:
        # Range
        try:
            start = int(parts[0]) if parts[0] else 0
            end = int(parts[1]) if parts[1] else max_value
            return start, end
        except:
            return 0, max_value

    else:
        return 0, max_value


def format_timedelta(td: pd.Timedelta) -> str:
    """
    Format a timedelta in human-readable format

    Args:
        td: Timedelta to format

    Returns:
        Formatted string
    """
    total_seconds = td.total_seconds()

    if total_seconds < 60:
        return f"{total_seconds:.1f} seconds"
    elif total_seconds < 3600:
        minutes = total_seconds / 60
        return f"{minutes:.1f} minutes"
    elif total_seconds < 86400:
        hours = total_seconds / 3600
        return f"{hours:.1f} hours"
    else:
        days = total_seconds / 86400
        return f"{days:.1f} days"


def safe_divide(numerator: float, denominator: float,
                default: float = 0.0) -> float:
    """
    Safely divide two numbers

    Args:
        numerator: Numerator
        denominator: Denominator
        default: Default value if division fails

    Returns:
        Result of division or default
    """
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except:
        return default


def create_time_index(start: Union[str, datetime],
                      periods: int,
                      freq: str = 'h') -> pd.DatetimeIndex:
    """
    Create a time index for data

    Args:
        start: Start time
        periods: Number of periods
        freq: Frequency string

    Returns:
        DatetimeIndex
    """
    if isinstance(start, str):
        start = pd.to_datetime(start)

    return pd.date_range(start=start, periods=periods, freq=freq)


def resample_data(df: pd.DataFrame, time_column: str,
                  freq: str = '1H', method: str = 'mean') -> pd.DataFrame:
    """
    Resample time series data

    Args:
        df: DataFrame with time series
        time_column: Name of time column
        freq: Target frequency
        method: Aggregation method

    Returns:
        Resampled DataFrame
    """
    # Set time column as index
    df_resampled = df.set_index(time_column)

    # Resample based on method
    if method == 'mean':
        return df_resampled.resample(freq).mean()
    elif method == 'sum':
        return df_resampled.resample(freq).sum()
    elif method == 'max':
        return df_resampled.resample(freq).max()
    elif method == 'min':
        return df_resampled.resample(freq).min()
    elif method == 'first':
        return df_resampled.resample(freq).first()
    elif method == 'last':
        return df_resampled.resample(freq).last()
    else:
        return df_resampled.resample(freq).mean()