#!/usr/bin/env python3
"""
utils/validators.py - Fixed validation utilities
Adds missing validate_file_size function and other validators
"""

import os
import re
from typing import Tuple, Any, Optional
import numpy as np
import pandas as pd
from pathlib import Path


def validate_file_size(filepath: str, max_size_mb: float = 500) -> Tuple[bool, str]:
    """
    Validate file size is within acceptable limits
    
    Args:
        filepath: Path to file
        max_size_mb: Maximum file size in MB
        
    Returns:
        Tuple of (is_valid, message)
    """
    try:
        path = Path(filepath)
        
        if not path.exists():
            return False, f"File not found: {filepath}"
        
        size_mb = path.stat().st_size / (1024 * 1024)
        
        if size_mb > max_size_mb:
            return False, f"File too large: {size_mb:.1f} MB (max: {max_size_mb} MB)"
        
        return True, f"File size OK: {size_mb:.1f} MB"
        
    except Exception as e:
        return False, f"Error checking file size: {str(e)}"


def validate_dataframe(df: pd.DataFrame) -> Tuple[bool, str]:
    """
    Validate a pandas DataFrame
    
    Args:
        df: DataFrame to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if df is None:
        return False, "DataFrame is None"
    
    if df.empty:
        return False, "DataFrame is empty"
    
    if len(df.columns) == 0:
        return False, "No columns in DataFrame"
    
    # Check for numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) == 0:
        return False, "No numeric columns found"
    
    return True, ""


def validate_data_range(data: np.ndarray, min_val: float = None, 
                       max_val: float = None) -> Tuple[bool, str]:
    """
    Validate data is within specified range
    
    Args:
        data: Data array
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(data) == 0:
        return False, "Empty data array"
    
    clean_data = data[~np.isnan(data)]
    
    if len(clean_data) == 0:
        return False, "All values are NaN"
    
    data_min = np.min(clean_data)
    data_max = np.max(clean_data)
    
    if min_val is not None and data_min < min_val:
        return False, f"Data contains values below minimum ({data_min:.2e} < {min_val:.2e})"
    
    if max_val is not None and data_max > max_val:
        return False, f"Data contains values above maximum ({data_max:.2e} > {max_val:.2e})"
    
    return True, ""


def validate_positive_number(value: Any, allow_zero: bool = False) -> Tuple[bool, str]:
    """
    Validate that a value is a positive number
    
    Args:
        value: Value to validate
        allow_zero: Whether zero is allowed
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        num = float(value)
        
        if np.isnan(num) or np.isinf(num):
            return False, "Value is NaN or infinite"
        
        if allow_zero:
            if num < 0:
                return False, "Value must be non-negative"
        else:
            if num <= 0:
                return False, "Value must be positive"
        
        return True, ""
        
    except (TypeError, ValueError):
        return False, "Value is not a number"


def validate_color(color: str) -> Tuple[bool, str]:
    """
    Validate a color string (hex or name)
    
    Args:
        color: Color string to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not color:
        return False, "Empty color string"
    
    # Check hex color
    if color.startswith('#'):
        hex_pattern = r'^#(?:[0-9a-fA-F]{3}){1,2}$'
        if re.match(hex_pattern, color):
            return True, ""
        else:
            return False, "Invalid hex color format"
    
    # Check named colors (basic set)
    valid_colors = {
        'red', 'green', 'blue', 'yellow', 'orange', 'purple',
        'cyan', 'magenta', 'black', 'white', 'gray', 'grey',
        'brown', 'pink', 'lime', 'navy', 'teal', 'olive'
    }
    
    if color.lower() in valid_colors:
        return True, ""
    
    return False, f"Unknown color: {color}"


def validate_series_config(config: dict, file_data: Any) -> Tuple[bool, str]:
    """
    Validate a series configuration
    
    Args:
        config: Series configuration dictionary
        file_data: Associated file data
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check required fields
    required_fields = ['name', 'x_column', 'y_column']
    for field in required_fields:
        if field not in config or not config[field]:
            return False, f"Missing required field: {field}"
    
    # Validate columns exist
    if file_data and hasattr(file_data, 'data'):
        df = file_data.data
        
        if config['x_column'] not in df.columns:
            return False, f"X column '{config['x_column']}' not found"
        
        if config['y_column'] not in df.columns:
            return False, f"Y column '{config['y_column']}' not found"
    
    # Validate color if present
    if 'color' in config:
        valid, msg = validate_color(config['color'])
        if not valid:
            return False, f"Invalid color: {msg}"
    
    # Validate numeric fields
    numeric_fields = ['line_width', 'marker_size', 'alpha']
    for field in numeric_fields:
        if field in config:
            valid, msg = validate_positive_number(config[field], allow_zero=(field == 'alpha'))
            if not valid:
                return False, f"Invalid {field}: {msg}"
    
    return True, ""


def validate_plot_config(config: dict) -> Tuple[bool, str]:
    """
    Validate plot configuration
    
    Args:
        config: Plot configuration dictionary
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check figure size
    if 'figure_size' in config:
        width, height = config['figure_size']
        if width <= 0 or height <= 0:
            return False, "Figure size must be positive"
    
    # Check DPI
    if 'dpi' in config:
        if config['dpi'] <= 0:
            return False, "DPI must be positive"
    
    # Check limits
    for axis in ['x', 'y']:
        min_key = f'{axis}_min'
        max_key = f'{axis}_max'
        
        if min_key in config and max_key in config:
            if config[min_key] >= config[max_key]:
                return False, f"{axis} min must be less than max"
    
    return True, ""


def validate_export_path(path: str, format: str = None) -> Tuple[bool, str]:
    """
    Validate an export file path
    
    Args:
        path: Export file path
        format: Expected file format
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not path:
        return False, "Empty file path"
    
    # Check parent directory exists
    parent_dir = os.path.dirname(path)
    if parent_dir and not os.path.exists(parent_dir):
        return False, f"Directory does not exist: {parent_dir}"
    
    # Check file extension matches format
    if format:
        ext = os.path.splitext(path)[1].lower().lstrip('.')
        if ext != format.lower():
            return False, f"File extension '{ext}' does not match format '{format}'"
    
    # Check write permissions
    try:
        if os.path.exists(path):
            if not os.access(path, os.W_OK):
                return False, "No write permission for file"
        elif parent_dir:
            if not os.access(parent_dir, os.W_OK):
                return False, "No write permission for directory"
    except Exception as e:
        return False, f"Permission check failed: {str(e)}"
    
    return True, ""


def validate_analysis_data(data: np.ndarray, analysis_type: str) -> Tuple[bool, str]:
    """
    Validate data for specific analysis type
    
    Args:
        data: Data array
        analysis_type: Type of analysis to perform
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(data) == 0:
        return False, "Empty data array"
    
    clean_data = data[~np.isnan(data)]
    
    if len(clean_data) == 0:
        return False, "All values are NaN"
    
    # Check based on analysis type
    if analysis_type == 'fft':
        if len(clean_data) < 4:
            return False, "FFT requires at least 4 data points"
        
    elif analysis_type == 'correlation':
        if len(clean_data) < 2:
            return False, "Correlation requires at least 2 data points"
        
    elif analysis_type == 'vacuum':
        if np.any(clean_data < 0):
            return False, "Vacuum analysis requires positive pressure values"
        
    elif analysis_type == 'statistics':
        if len(clean_data) < 1:
            return False, "Statistics requires at least 1 data point"
    
    return True, ""


def validate_export_format(format: str) -> Tuple[bool, str]:
    """
    Validate an export format
    
    Args:
        format: Format string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    valid_formats = ['png', 'pdf', 'svg', 'jpg', 'jpeg', 'tiff', 'eps',
                     'xlsx', 'xls', 'csv', 'json', 'html']
    
    format_lower = format.lower().lstrip('.')
    
    if format_lower not in valid_formats:
        return False, f"Unsupported format: {format}"
    
    return True, ""


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing invalid characters
    
    Args:
        filename: Filename to sanitize
        
    Returns:
        Sanitized filename
    """
    # Remove invalid characters
    invalid_chars = r'<>:"/\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove control characters
    filename = ''.join(char for char in filename if ord(char) >= 32)
    
    # Limit length
    max_length = 200
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        filename = name[:max_length - len(ext)] + ext
    
    return filename