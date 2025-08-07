# !/usr/bin/env python3
"""
Data validation utilities
"""

import logging
from pathlib import Path
from typing import List, Optional, Any
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def validate_file_size(filepath: Path, max_size_mb: float) -> bool:
    """
    Validate file size

    Args:
        filepath: Path to file
        max_size_mb: Maximum size in megabytes

    Returns:
        True if file size is acceptable
    """
    file_size_mb = filepath.stat().st_size / (1024 * 1024)
    return file_size_mb <= max_size_mb


def validate_dataframe(df: pd.DataFrame) -> None:
    """
    Validate dataframe for basic requirements

    Args:
        df: DataFrame to validate

    Raises:
        ValueError: If validation fails
    """
    if df.empty:
        raise ValueError("DataFrame is empty")

    if len(df.columns) == 0:
        raise ValueError("DataFrame has no columns")

    if len(df) == 0:
        raise ValueError("DataFrame has no rows")

    # Check for at least one numeric column
    numeric_columns = df.select_dtypes(include=[np.number]).columns
    if len(numeric_columns) == 0:
        logger.warning("DataFrame has no numeric columns")


def validate_series_config(series: Any, file_data: Any) -> List[str]:
    """
    Validate series configuration

    Args:
        series: Series configuration
        file_data: Associated file data

    Returns:
        List of validation errors
    """
    errors = []

    if not series.name:
        errors.append("Series name is required")

    if not series.file_id:
        errors.append("File ID is required")

    if not file_data:
        errors.append("File data not found")
        return errors

    # Check columns exist
    df = file_data.dataframe

    if series.x_column != 'Index' and series.x_column not in df.columns:
        errors.append(f"X column '{series.x_column}' not found in file")

    if series.y_column not in df.columns:
        errors.append(f"Y column '{series.y_column}' not found in file")

    # Check data range
    if series.start_index < 0:
        errors.append("Start index cannot be negative")

    if series.end_index and series.end_index <= series.start_index:
        errors.append("End index must be greater than start index")

    if series.end_index and series.end_index > len(df):
        errors.append(f"End index ({series.end_index}) exceeds data length ({len(df)})")

    return errors


def validate_plot_config(config: dict) -> List[str]:
    """
    Validate plot configuration

    Args:
        config: Plot configuration dictionary

    Returns:
        List of validation errors
    """
    errors = []

    # Check required fields
    if not config.get('title'):
        logger.warning("Plot title is empty")

    # Check numeric ranges
    if config.get('fig_width', 0) <= 0:
        errors.append("Figure width must be positive")

    if config.get('fig_height', 0) <= 0:
        errors.append("Figure height must be positive")

    if config.get('dpi', 0) <= 0:
        errors.append("DPI must be positive")

    # Check alpha values
    alpha = config.get('grid_alpha', 1.0)
    if not 0 <= alpha <= 1:
        errors.append("Grid alpha must be between 0 and 1")

    return errors


def validate_data_range(
        start: int,
        end: Optional[int],
        data_length: int
) -> tuple:
    """
    Validate and adjust data range

    Args:
        start: Start index
        end: End index (None for full range)
        data_length: Total data length

    Returns:
        Tuple of (valid_start, valid_end)
    """
    # Ensure start is valid
    start = max(0, min(start, data_length - 1))

    # Ensure end is valid
    if end is None:
        end = data_length
    else:
        end = max(start + 1, min(end, data_length))

    return start, end


def validate_color(color: str) -> bool:
    """
    Validate color string

    Args:
        color: Color string (hex or name)

    Returns:
        True if valid color
    """
    import matplotlib.colors as mcolors

    try:
        mcolors.to_rgb(color)
        return True
    except:
        return False


def validate_export_path(filepath: Path, overwrite: bool = False) -> List[str]:
    """
    Validate export file path

    Args:
        filepath: Target file path
        overwrite: Whether overwriting is allowed

    Returns:
        List of validation errors
    """
    errors = []

    # Check parent directory exists
    if not filepath.parent.exists():
        errors.append(f"Directory does not exist: {filepath.parent}")

    # Check write permissions
    if filepath.parent.exists() and not os.access(filepath.parent, os.W_OK):
        errors.append(f"No write permission for directory: {filepath.parent}")

    # Check if file exists
    if filepath.exists() and not overwrite:
        errors.append(f"File already exists: {filepath}")

    # Check extension
    valid_extensions = {'.png', '.pdf', '.svg', '.jpg', '.xlsx', '.csv', '.txt', '.json'}
    if filepath.suffix.lower() not in valid_extensions:
        errors.append(f"Unsupported file extension: {filepath.suffix}")

    return errors


def validate_analysis_data(data: np.ndarray, min_points: int = 2) -> List[str]:
    """
    Validate data for analysis

    Args:
        data: Data array
        min_points: Minimum required data points

    Returns:
        List of validation errors
    """
    errors = []

    if len(data) < min_points:
        errors.append(f"Insufficient data points (need at least {min_points})")

    # Check for all NaN
    if np.all(np.isnan(data)):
        errors.append("All data values are NaN")

    # Check for all same value
    unique_values = np.unique(data[~np.isnan(data)])
    if len(unique_values) == 1:
        errors.append("All data values are identical")

    # Check for infinite values
    if np.any(np.isinf(data)):
        errors.append("Data contains infinite values")

    return errors

