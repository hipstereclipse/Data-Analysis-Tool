#!/usr/bin/env python3
"""
Data Processing Utilities - Reusable data manipulation functions
Consolidates common data processing patterns
"""

import numpy as np
import pandas as pd
from scipy import stats
from scipy.signal import savgol_filter, find_peaks
from sklearn.linear_model import LinearRegression
from typing import Tuple, List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class DataProcessor:
    """Utility class for common data processing operations"""
    
    @staticmethod
    def handle_missing_data(x_data: np.ndarray, y_data: np.ndarray, 
                           method: str = "drop") -> Tuple[np.ndarray, np.ndarray]:
        """Handle missing data in series
        
        Args:
            x_data: X-axis data array
            y_data: Y-axis data array  
            method: Method to handle missing data ('drop', 'interpolate', 'forward_fill', 'zero_fill')
            
        Returns:
            Tuple of cleaned (x_data, y_data)
        """
        try:
            # Convert to pandas Series for easier handling
            x_series = pd.Series(x_data)
            y_series = pd.Series(y_data)
            
            if method == "drop":
                # Drop rows with NaN in either series
                mask = ~(x_series.isna() | y_series.isna())
                return x_series[mask].values, y_series[mask].values
                
            elif method == "interpolate":
                # Interpolate missing values
                x_filled = x_series.interpolate()
                y_filled = y_series.interpolate()
                return x_filled.values, y_filled.values
                
            elif method == "forward_fill":
                # Forward fill missing values
                x_filled = x_series.fillna(method='ffill')
                y_filled = y_series.fillna(method='ffill')
                return x_filled.values, y_filled.values
                
            elif method == "zero_fill":
                # Fill with zeros
                x_filled = x_series.fillna(0)
                y_filled = y_series.fillna(0)
                return x_filled.values, y_filled.values
                
            else:
                logger.warning(f"Unknown missing data method: {method}, using 'drop'")
                mask = ~(x_series.isna() | y_series.isna())
                return x_series[mask].values, y_series[mask].values
                
        except Exception as e:
            logger.error(f"Error handling missing data: {e}")
            return x_data, y_data
    
    @staticmethod
    def apply_smoothing(y_data: np.ndarray, window_size: int = 5, 
                       poly_order: int = 3) -> np.ndarray:
        """Apply Savitzky-Golay smoothing to data
        
        Args:
            y_data: Y-axis data array
            window_size: Window size for smoothing (must be odd)
            poly_order: Polynomial order for smoothing
            
        Returns:
            Smoothed data array
        """
        try:
            if len(y_data) < window_size:
                return y_data
                
            # Ensure window size is odd and valid
            if window_size % 2 == 0:
                window_size += 1
            window_size = min(window_size, len(y_data))
            poly_order = min(poly_order, window_size - 1)
            
            if window_size >= 3 and poly_order >= 1:
                return savgol_filter(y_data, window_size, poly_order)
            else:
                return y_data
                
        except Exception as e:
            logger.error(f"Error applying smoothing: {e}")
            return y_data
    
    @staticmethod
    def calculate_trend_line(x_data: np.ndarray, y_data: np.ndarray, 
                           trend_type: str = "linear") -> Tuple[np.ndarray, Dict[str, float]]:
        """Calculate trend line for data
        
        Args:
            x_data: X-axis data array
            y_data: Y-axis data array
            trend_type: Type of trend ('linear', 'polynomial')
            
        Returns:
            Tuple of (trend_y_values, trend_stats)
        """
        try:
            if trend_type == "linear":
                # Linear regression
                x_reshaped = x_data.reshape(-1, 1)
                model = LinearRegression()
                model.fit(x_reshaped, y_data)
                
                trend_y = model.predict(x_reshaped)
                
                # Calculate R-squared
                r_squared = model.score(x_reshaped, y_data)
                
                stats_dict = {
                    "slope": model.coef_[0],
                    "intercept": model.intercept_,
                    "r_squared": r_squared
                }
                
                return trend_y, stats_dict
                
            elif trend_type == "polynomial":
                # Polynomial fit (degree 2)
                coeffs = np.polyfit(x_data, y_data, 2)
                trend_y = np.polyval(coeffs, x_data)
                
                # Calculate R-squared
                ss_res = np.sum((y_data - trend_y) ** 2)
                ss_tot = np.sum((y_data - np.mean(y_data)) ** 2)
                r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
                
                stats_dict = {
                    "coefficients": coeffs.tolist(),
                    "r_squared": r_squared
                }
                
                return trend_y, stats_dict
                
            else:
                logger.warning(f"Unknown trend type: {trend_type}")
                return np.array([]), {}
                
        except Exception as e:
            logger.error(f"Error calculating trend line: {e}")
            return np.array([]), {}
    
    @staticmethod
    def detect_outliers(y_data: np.ndarray, method: str = "iqr", 
                       threshold: float = 1.5) -> List[int]:
        """Detect outliers in data
        
        Args:
            y_data: Y-axis data array
            method: Method for outlier detection ('iqr', 'zscore', 'modified_zscore')
            threshold: Threshold for outlier detection
            
        Returns:
            List of outlier indices
        """
        try:
            outliers = []
            
            if method == "iqr":
                # Interquartile Range method
                Q1 = np.percentile(y_data, 25)
                Q3 = np.percentile(y_data, 75)
                IQR = Q3 - Q1
                
                lower_bound = Q1 - threshold * IQR
                upper_bound = Q3 + threshold * IQR
                
                outliers = np.where((y_data < lower_bound) | (y_data > upper_bound))[0].tolist()
                
            elif method == "zscore":
                # Z-score method
                z_scores = np.abs(stats.zscore(y_data))
                outliers = np.where(z_scores > threshold)[0].tolist()
                
            elif method == "modified_zscore":
                # Modified Z-score method
                median = np.median(y_data)
                mad = np.median(np.abs(y_data - median))
                modified_z_scores = 0.6745 * (y_data - median) / mad
                outliers = np.where(np.abs(modified_z_scores) > threshold)[0].tolist()
                
            return outliers
            
        except Exception as e:
            logger.error(f"Error detecting outliers: {e}")
            return []
    
    @staticmethod
    def find_peaks_in_data(y_data: np.ndarray, prominence: float = None, 
                          distance: int = None) -> Tuple[np.ndarray, Dict[str, np.ndarray]]:
        """Find peaks in data
        
        Args:
            y_data: Y-axis data array
            prominence: Required prominence of peaks
            distance: Minimum distance between peaks
            
        Returns:
            Tuple of (peak_indices, peak_properties)
        """
        try:
            # Set default prominence if not provided
            if prominence is None:
                prominence = np.std(y_data) * 0.5
                
            # Find peaks
            peaks, properties = find_peaks(y_data, prominence=prominence, distance=distance)
            
            return peaks, properties
            
        except Exception as e:
            logger.error(f"Error finding peaks: {e}")
            return np.array([]), {}
    
    @staticmethod
    def calculate_basic_statistics(y_data: np.ndarray) -> Dict[str, float]:
        """Calculate basic statistics for data
        
        Args:
            y_data: Y-axis data array
            
        Returns:
            Dictionary of basic statistics
        """
        try:
            stats_dict = {
                "count": len(y_data),
                "mean": np.mean(y_data),
                "median": np.median(y_data),
                "std": np.std(y_data),
                "var": np.var(y_data),
                "min": np.min(y_data),
                "max": np.max(y_data),
                "range": np.max(y_data) - np.min(y_data),
                "q1": np.percentile(y_data, 25),
                "q3": np.percentile(y_data, 75),
                "skewness": stats.skew(y_data),
                "kurtosis": stats.kurtosis(y_data)
            }
            
            return stats_dict
            
        except Exception as e:
            logger.error(f"Error calculating statistics: {e}")
            return {}
    
    @staticmethod
    def normalize_data(y_data: np.ndarray, method: str = "zscore") -> np.ndarray:
        """Normalize data using specified method
        
        Args:
            y_data: Y-axis data array
            method: Normalization method ('zscore', 'minmax', 'robust')
            
        Returns:
            Normalized data array
        """
        try:
            if method == "zscore":
                # Z-score normalization
                return stats.zscore(y_data)
                
            elif method == "minmax":
                # Min-max normalization
                min_val = np.min(y_data)
                max_val = np.max(y_data)
                if max_val != min_val:
                    return (y_data - min_val) / (max_val - min_val)
                else:
                    return y_data
                    
            elif method == "robust":
                # Robust normalization using median and MAD
                median = np.median(y_data)
                mad = np.median(np.abs(y_data - median))
                if mad != 0:
                    return (y_data - median) / mad
                else:
                    return y_data - median
                    
            else:
                logger.warning(f"Unknown normalization method: {method}")
                return y_data
                
        except Exception as e:
            logger.error(f"Error normalizing data: {e}")
            return y_data
    
    @staticmethod
    def resample_data(x_data: np.ndarray, y_data: np.ndarray, 
                     target_points: int) -> Tuple[np.ndarray, np.ndarray]:
        """Resample data to target number of points
        
        Args:
            x_data: X-axis data array
            y_data: Y-axis data array
            target_points: Target number of points
            
        Returns:
            Tuple of resampled (x_data, y_data)
        """
        try:
            if len(y_data) <= target_points:
                return x_data, y_data
                
            # Create new x values
            x_new = np.linspace(x_data[0], x_data[-1], target_points)
            
            # Interpolate y values
            y_new = np.interp(x_new, x_data, y_data)
            
            return x_new, y_new
            
        except Exception as e:
            logger.error(f"Error resampling data: {e}")
            return x_data, y_data


class DataValidator:
    """Utility class for data validation"""
    
    @staticmethod
    def validate_numeric_data(data: np.ndarray) -> Tuple[bool, str]:
        """Validate that data is numeric and suitable for plotting
        
        Args:
            data: Data array to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if len(data) == 0:
                return False, "Data array is empty"
                
            if not np.issubdtype(data.dtype, np.number):
                return False, "Data is not numeric"
                
            if np.all(np.isnan(data)):
                return False, "All data values are NaN"
                
            finite_count = np.sum(np.isfinite(data))
            if finite_count < 2:
                return False, f"Only {finite_count} finite values found (need at least 2)"
                
            return True, ""
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    @staticmethod
    def validate_data_compatibility(x_data: np.ndarray, y_data: np.ndarray) -> Tuple[bool, str]:
        """Validate that x and y data are compatible for plotting
        
        Args:
            x_data: X-axis data array
            y_data: Y-axis data array
            
        Returns:
            Tuple of (is_compatible, error_message)
        """
        try:
            # Check if arrays have same length
            if len(x_data) != len(y_data):
                return False, f"Data length mismatch: X has {len(x_data)} points, Y has {len(y_data)} points"
                
            # Validate both arrays individually
            x_valid, x_error = DataValidator.validate_numeric_data(x_data)
            if not x_valid:
                return False, f"X-data validation failed: {x_error}"
                
            y_valid, y_error = DataValidator.validate_numeric_data(y_data)
            if not y_valid:
                return False, f"Y-data validation failed: {y_error}"
                
            return True, ""
            
        except Exception as e:
            return False, f"Compatibility check error: {str(e)}"
