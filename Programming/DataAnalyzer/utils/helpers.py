# !/usr/bin/env python3
"""
Helper utility functions
"""

import os
import re
import hashlib
from pathlib import Path
from typing import List, Optional, Any, Union
import numpy as np
import pandas as pd
from datetime import datetime, timedelta


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string
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
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    elif seconds < 86400:
        hours = seconds / 3600
        return f"{hours:.1f}h"
    else:
        days = seconds / 86400
        return f"{days:.1f}d"


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize filename for safe file system usage

    Args:
        filename: Original filename
        max_length: Maximum allowed length

    Returns:
        Sanitized filename
    """
    # Remove invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')

    # Remove control characters
    filename = re.sub(r'[\x00-\x1f\x7f]', '', filename)

    # Remove leading/trailing spaces and dots
    filename = filename.strip('. ')

    # Truncate if too long
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        max_name_length = max_length - len(ext)
        filename = name[:max_name_length] + ext

    # Ensure filename is not empty
    if not filename:
        filename = "unnamed"

    return filename


def generate_unique_id(prefix: str = "") -> str:
    """
    Generate unique identifier

    Args:
        prefix: Optional prefix for ID

    Returns:
        Unique ID string
    """
    import uuid
    unique_id = str(uuid.uuid4())[:8]

    if prefix:
        return f"{prefix}_{unique_id}"
    return unique_id


def detect_datetime_column(data: Union[pd.Series, np.ndarray]) -> bool:
    """
    Check if data contains datetime values

    Args:
        data: Data to check

    Returns:
        True if datetime data detected
    """
    if isinstance(data, pd.Series):
        if pd.api.types.is_datetime64_any_dtype(data):
            return True

        # Sample check for string dates
        sample = data.dropna().head(20)
        if len(sample) == 0:
            return False

        try:
            pd.to_datetime(sample, errors='coerce')
            success_rate = pd.to_datetime(sample, errors='coerce').notna().sum() / len(sample)
            return success_rate > 0.8
        except:
            return False

    return False


def convert_to_datetime(data: Union[pd.Series, np.ndarray]) -> pd.Series:
    """
    Convert data to datetime if possible

    Args:
        data: Data to convert

    Returns:
        Converted datetime series or original
    """
    if isinstance(data, pd.Series):
        if pd.api.types.is_datetime64_any_dtype(data):
            return data

        try:
            converted = pd.to_datetime(data, errors='coerce')
            if converted.notna().sum() / len(data.dropna()) > 0.8:
                return converted
        except:
            pass

    return pd.Series(data)


def detect_datetime_axis(axis_data: Any) -> bool:
    """
    Check if axis contains datetime data

    Args:
        axis_data: Axis data to check

    Returns:
        True if datetime axis
    """
    try:
        if hasattr(axis_data, '__iter__'):
            sample = list(axis_data)[:10]
            for item in sample:
                if isinstance(item, (datetime, pd.Timestamp)):
                    return True
    except:
        pass

    return False


def interpolate_missing_data(
        x_data: np.ndarray,
        y_data: np.ndarray,
        method: str = 'linear'
) -> tuple:
    """
    Interpolate missing data points

    Args:
        x_data: X-axis data
        y_data: Y-axis data
        method: Interpolation method

    Returns:
        Tuple of (x_data, y_data) with interpolated values
    """
    # Create mask for valid data
    mask = ~(np.isnan(x_data) | np.isnan(y_data))

    if np.sum(mask) < 2:
        return x_data, y_data

    # Interpolate
    from scipy.interpolate import interp1d

    try:
        f = interp1d(x_data[mask], y_data[mask], kind=method, fill_value='extrapolate')
        y_interpolated = f(x_data)
        return x_data, y_interpolated
    except:
        return x_data, y_data


def generate_color_sequence(n_colors: int) -> List[str]:
    """
    Generate a sequence of distinct colors

    Args:
        n_colors: Number of colors needed

    Returns:
        List of hex color codes
    """
    import matplotlib.cm as cm
    import matplotlib.colors as mcolors

    if n_colors <= 12:
        # Use predefined palette for small numbers
        base_colors = [
            '#3B82F6', '#10B981', '#F59E0B', '#EF4444',
            '#8B5CF6', '#EC4899', '#14B8A6', '#F97316',
            '#6366F1', '#84CC16', '#06B6D4', '#A855F7'
        ]
        return base_colors[:n_colors]
    else:
        # Generate colors from colormap
        cmap = cm.get_cmap('tab20')
        colors = []
        for i in range(n_colors):
            color = cmap(i / n_colors)
            hex_color = mcolors.to_hex(color)
            colors.append(hex_color)
        return colors


def calculate_aspect_ratio(width: int, height: int) -> float:
    """
    Calculate aspect ratio

    Args:
        width: Width in pixels
        height: Height in pixels

    Returns:
        Aspect ratio
    """
    if height == 0:
        return 1.0
    return width / height


def estimate_sample_rate(time_data: Union[pd.Series, np.ndarray]) -> float:
    """
    Estimate sampling rate from time data

    Args:
        time_data: Time series data

    Returns:
        Estimated sample rate in Hz
    """
    if len(time_data) < 2:
        return 1.0

    # Calculate time differences
    if isinstance(time_data, pd.Series):
        if pd.api.types.is_datetime64_any_dtype(time_data):
            diffs = time_data.diff().dropna()
            median_diff = diffs.median()
            if hasattr(median_diff, 'total_seconds'):
                seconds = median_diff.total_seconds()
            else:
                seconds = float(median_diff)
        else:
            diffs = np.diff(time_data)
            seconds = np.median(diffs)
    else:
        diffs = np.diff(time_data)
        seconds = np.median(diffs)

    if seconds > 0:
        return 1.0 / seconds
    return 1.0


def create_backup(filepath: Path, max_backups: int = 3):
    """
    Create backup of file

    Args:
        filepath: File to backup
        max_backups: Maximum number of backups to keep
    """
    if not filepath.exists():
        return

    # Create backup directory
    backup_dir = filepath.parent / "backups"
    backup_dir.mkdir(exist_ok=True)

    # Generate backup name with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{filepath.stem}_{timestamp}{filepath.suffix}"
    backup_path = backup_dir / backup_name

    # Copy file
    import shutil
    shutil.copy2(filepath, backup_path)

    # Clean old backups
    backups = sorted(backup_dir.glob(f"{filepath.stem}_*{filepath.suffix}"))
    if len(backups) > max_backups:
        for old_backup in backups[:-max_backups]:
            old_backup.unlink()


def calculate_hash(filepath: Path) -> str:
    """
    Calculate file hash for integrity checking

    Args:
        filepath: File to hash

    Returns:
        SHA256 hash string
    """
    sha256_hash = hashlib.sha256()

    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)

    return sha256_hash.hexdigest()

