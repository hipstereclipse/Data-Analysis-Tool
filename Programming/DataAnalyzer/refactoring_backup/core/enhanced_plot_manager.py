#!/usr/bin/env python3
"""
Enhanced Plot Manager with multi-series support and advanced styling
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from scipy import stats, signal
from typing import Dict, List, Optional, Any, Tuple
import logging

from models.data_models import SeriesConfig, FileData
from ui.theme_manager import theme_manager

logger = logging.getLogger(__name__)

class EnhancedPlotManager:
    """Enhanced plot manager with multi-series support and advanced styling"""
    
    def __init__(self, figure: Figure):
        self.figure = figure
        self.axes = None
        self.series_plots = {}  # Store plot objects for each series
        self.series_configs = {}  # Store series configurations
        self.loaded_files = {}  # Store file data
        self.outlier_points = {}  # Store outlier points for highlighting
        self.annotation_manager = None
        
        # Plot settings
        self.auto_scale = True
        self.show_grid = True
        self.show_legend = True
        self.legend_location = "best"
        
        # Initialize figure
        self.setup_figure()
        
    def setup_figure(self):
        """Setup the figure with proper theming"""
        self.figure.clear()
        self.axes = self.figure.add_subplot(111)
        
        # Apply theme
        theme_manager.configure_matplotlib_figure(self.figure, self.axes)
        
        # Set default labels
        self.axes.set_xlabel("X-Axis")
        self.axes.set_ylabel("Y-Axis")
        self.axes.set_title("Data Plot")
        
    def add_series(self, series_id: str, series_config: SeriesConfig, file_data: FileData):
        """Add a series to the plot"""
        try:
            self.series_configs[series_id] = series_config
            self.loaded_files[series_config.file_id] = file_data
            
            # Get and process data
            x_data, y_data = self.get_series_data(series_config, file_data)
            
            if len(x_data) == 0 or len(y_data) == 0:
                logger.warning(f"No data for series {series_id}")
                return False
                
            # Process data according to configuration
            x_processed, y_processed, outliers = self.process_series_data(
                x_data, y_data, series_config
            )
            
            # Store outliers for highlighting
            if len(outliers) > 0:
                self.outlier_points[series_id] = outliers
                
            # Create the main plot
            plot_objects = self.create_series_plot(
                x_processed, y_processed, series_config
            )
            
            self.series_plots[series_id] = plot_objects
            
            # Handle outliers if configured to highlight
            if series_config.outlier_handling == "highlight" and len(outliers) > 0:
                self.highlight_outliers(series_id, x_data, y_data, outliers, series_config)
                
            logger.info(f"Added series {series_id} with {len(x_processed)} points")
            return True
            
        except Exception as e:
            logger.error(f"Error adding series {series_id}: {e}")
            return False
            
    def create_series_plot(self, x_data, y_data, config: SeriesConfig) -> Dict[str, Any]:
        """Create plot objects for a series"""
        plot_objects = {}
        
        # Determine plot style
        line_style = config.line_style if config.line_style != "none" else ""
        marker = config.marker if config.marker not in [None, "none"] else ""
        
        # Main line/scatter plot
        if config.plot_type == "scatter":
            scatter = self.axes.scatter(
                x_data, y_data,
                c=config.color,
                s=config.marker_size**2,  # matplotlib uses area
                alpha=config.alpha,
                marker=marker if marker else "o",
                label=config.legend_label or config.name,
                zorder=config.z_order
            )
            plot_objects["main"] = scatter
            
        elif config.plot_type == "bar":
            bars = self.axes.bar(
                x_data, y_data,
                color=config.color,
                alpha=config.alpha,
                label=config.legend_label or config.name,
                zorder=config.z_order
            )
            plot_objects["main"] = bars
            
        elif config.plot_type == "step":
            line = self.axes.step(
                x_data, y_data,
                color=config.color,
                linewidth=config.line_width,
                alpha=config.alpha,
                label=config.legend_label or config.name,
                zorder=config.z_order,
                where='post'
            )
            plot_objects["main"] = line[0]
            
        else:  # Default to line plot
            line = self.axes.plot(
                x_data, y_data,
                color=config.color,
                linestyle=line_style,
                marker=marker,
                linewidth=config.line_width,
                markersize=config.marker_size,
                markeredgecolor=config.marker_edge_color if config.marker_edge_color != "auto" else config.color,
                markeredgewidth=config.marker_edge_width,
                alpha=config.alpha,
                label=config.legend_label or config.name,
                zorder=config.z_order
            )[0]
            plot_objects["main"] = line
            
        # Add fill between if requested
        if config.fill_between:
            fill_color = config.fill_color if config.fill_color != "auto" else config.color
            fill = self.axes.fill_between(
                x_data, y_data,
                alpha=config.fill_alpha,
                color=fill_color,
                zorder=config.z_order - 1
            )
            plot_objects["fill"] = fill
            
        # Add error bars if requested
        if config.error_bars and hasattr(config, 'error_data'):
            error_color = config.error_color if config.error_color != "auto" else config.color
            errorbar = self.axes.errorbar(
                x_data, y_data, yerr=config.error_data,
                color=error_color,
                alpha=config.error_alpha,
                capsize=3,
                capthick=1,
                zorder=config.z_order
            )
            plot_objects["errorbar"] = errorbar
            
        # Add trendline if requested
        if config.show_trendline and len(x_data) > 1:
            try:
                trendline = self.add_trendline(x_data, y_data, config)
                if trendline:
                    plot_objects["trendline"] = trendline
            except Exception as e:
                logger.warning(f"Could not add trendline: {e}")
                
        return plot_objects
        
    def add_trendline(self, x_data, y_data, config: SeriesConfig):
        """Add trendline to the plot"""
        try:
            # Remove NaN values for fitting
            mask = ~(np.isnan(x_data) | np.isnan(y_data))
            x_clean = x_data[mask]
            y_clean = y_data[mask]
            
            if len(x_clean) < 2:
                return None
                
            # Fit linear regression
            slope, intercept, r_value, p_value, std_err = stats.linregress(x_clean, y_clean)
            
            # Create trendline
            trend_x = np.array([x_clean.min(), x_clean.max()])
            trend_y = slope * trend_x + intercept
            
            # Plot trendline
            trendline = self.axes.plot(
                trend_x, trend_y,
                color=config.color,
                linestyle='--',
                alpha=0.7,
                linewidth=max(1.0, config.line_width - 0.5),
                label=f'{config.name} Trend (R²={r_value**2:.3f})',
                zorder=config.z_order + 1
            )[0]
            
            return trendline
            
        except Exception as e:
            logger.error(f"Error adding trendline: {e}")
            return None
            
    def highlight_outliers(self, series_id: str, x_data, y_data, outlier_indices, config: SeriesConfig):
        """Highlight outlier points"""
        try:
            if len(outlier_indices) == 0:
                return
                
            outlier_x = x_data[outlier_indices]
            outlier_y = y_data[outlier_indices]
            
            # Create outlier scatter plot
            outlier_plot = self.axes.scatter(
                outlier_x, outlier_y,
                c=config.outlier_color,
                s=(config.marker_size * 1.5)**2,
                marker='x',
                alpha=0.8,
                zorder=config.z_order + 2,
                label=f'{config.name} Outliers'
            )
            
            # Store outlier plot
            if series_id not in self.series_plots:
                self.series_plots[series_id] = {}
            self.series_plots[series_id]["outliers"] = outlier_plot
            
        except Exception as e:
            logger.error(f"Error highlighting outliers: {e}")
            
    def get_series_data(self, config: SeriesConfig, file_data: FileData) -> Tuple[np.ndarray, np.ndarray]:
        """Extract data from file according to series configuration"""
        try:
            # Get data slice
            start_idx = config.start_index or 0
            end_idx = config.end_index or len(file_data.data)
            data_slice = file_data.data.iloc[start_idx:end_idx]
            
            # Get X data
            if config.x_column == "Index":
                x_data = np.arange(len(data_slice))
            else:
                x_data = data_slice[config.x_column].values
                # Convert to numeric if needed
                if pd.api.types.is_object_dtype(x_data):
                    x_data = pd.to_numeric(x_data, errors='coerce')
                    
            # Get Y data
            y_data = data_slice[config.y_column].values
            if pd.api.types.is_object_dtype(y_data):
                y_data = pd.to_numeric(y_data, errors='coerce')
                
            return x_data, y_data
            
        except Exception as e:
            logger.error(f"Error getting series data: {e}")
            return np.array([]), np.array([])
            
    def process_series_data(self, x_data, y_data, config: SeriesConfig) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Process data according to series configuration"""
        outlier_indices = np.array([])
        
        try:
            # Handle missing data
            if config.missing_data_method == "skip":
                mask = ~(pd.isna(x_data) | pd.isna(y_data))
                x_clean = x_data[mask]
                y_clean = y_data[mask]
            elif config.missing_data_method == "interpolate":
                # Simple linear interpolation
                df = pd.DataFrame({'x': x_data, 'y': y_data})
                df = df.interpolate(method='linear')
                x_clean = df['x'].values
                y_clean = df['y'].values
            elif config.missing_data_method == "zero":
                x_clean = np.nan_to_num(x_data, nan=0.0)
                y_clean = np.nan_to_num(y_data, nan=0.0)
            else:
                x_clean = x_data
                y_clean = y_data
                
            # Detect outliers
            if len(y_clean) > 3:
                outlier_indices = self.detect_outliers(y_clean, config.outlier_threshold)
                
                # Handle outliers based on configuration
                if config.outlier_handling == "remove" and len(outlier_indices) > 0:
                    keep_mask = np.ones(len(y_clean), dtype=bool)
                    keep_mask[outlier_indices] = False
                    x_clean = x_clean[keep_mask]
                    y_clean = y_clean[keep_mask]
                    outlier_indices = np.array([])  # Clear since we removed them
                    
                elif config.outlier_handling == "clamp" and len(outlier_indices) > 0:
                    # Clamp outliers to threshold values
                    median_val = np.nanmedian(y_clean)
                    std_val = np.nanstd(y_clean)
                    upper_limit = median_val + config.outlier_threshold * std_val
                    lower_limit = median_val - config.outlier_threshold * std_val
                    y_clean = np.clip(y_clean, lower_limit, upper_limit)
                    outlier_indices = np.array([])  # Clear since we clamped them
                    
            # Apply smoothing if requested
            if config.smooth_line and len(y_clean) > config.smooth_window:
                y_clean = self.apply_smoothing(y_clean, config.smooth_window)
                
            # Apply decimation if requested
            if config.data_decimation and config.decimation_factor > 1:
                step = config.decimation_factor
                x_clean = x_clean[::step]
                y_clean = y_clean[::step]
                # Adjust outlier indices
                if len(outlier_indices) > 0:
                    outlier_indices = outlier_indices[outlier_indices % step == 0] // step
                    
            return x_clean, y_clean, outlier_indices
            
        except Exception as e:
            logger.error(f"Error processing series data: {e}")
            return x_data, y_data, outlier_indices
            
    def detect_outliers(self, data: np.ndarray, threshold: float) -> np.ndarray:
        """Detect outliers using Z-score method"""
        try:
            # Remove NaN values for calculation
            clean_data = data[~np.isnan(data)]
            if len(clean_data) < 3:
                return np.array([])
                
            # Calculate Z-scores
            z_scores = np.abs(stats.zscore(clean_data, nan_policy='omit'))
            outlier_mask = z_scores > threshold
            
            # Map back to original indices
            clean_indices = np.where(~np.isnan(data))[0]
            outlier_indices = clean_indices[outlier_mask]
            
            return outlier_indices
            
        except Exception as e:
            logger.error(f"Error detecting outliers: {e}")
            return np.array([])
            
    def apply_smoothing(self, data: np.ndarray, window_size: int) -> np.ndarray:
        """Apply smoothing to data"""
        try:
            if window_size <= 1 or len(data) <= window_size:
                return data
                
            # Use Savitzky-Golay filter for smoothing
            if len(data) > window_size:
                # Ensure odd window size
                if window_size % 2 == 0:
                    window_size += 1
                    
                # Apply filter
                smoothed = signal.savgol_filter(data, window_size, 3)
                return smoothed
            else:
                # Fallback to simple moving average
                return pd.Series(data).rolling(window=window_size, center=True).mean().values
                
        except Exception as e:
            logger.warning(f"Error applying smoothing, using moving average: {e}")
            # Fallback to simple moving average
            return pd.Series(data).rolling(window=window_size, center=True).mean().fillna(data).values
            
    def remove_series(self, series_id: str):
        """Remove a series from the plot"""
        try:
            if series_id in self.series_plots:
                # Remove all plot objects for this series
                plot_objects = self.series_plots[series_id]
                for plot_obj in plot_objects.values():
                    if hasattr(plot_obj, 'remove'):
                        plot_obj.remove()
                    elif hasattr(plot_obj, 'set_visible'):
                        plot_obj.set_visible(False)
                        
                del self.series_plots[series_id]
                
            if series_id in self.series_configs:
                del self.series_configs[series_id]
                
            if series_id in self.outlier_points:
                del self.outlier_points[series_id]
                
            logger.info(f"Removed series {series_id}")
            
        except Exception as e:
            logger.error(f"Error removing series {series_id}: {e}")
            
    def update_series(self, series_id: str, series_config: SeriesConfig):
        """Update an existing series"""
        try:
            if series_id in self.series_configs:
                # Remove old series
                self.remove_series(series_id)
                
                # Add updated series
                file_data = self.loaded_files.get(series_config.file_id)
                if file_data:
                    self.add_series(series_id, series_config, file_data)
                    
        except Exception as e:
            logger.error(f"Error updating series {series_id}: {e}")
            
    def refresh_plot(self):
        """Refresh the entire plot"""
        try:
            # Clear axes but keep data
            self.axes.clear()
            
            # Reapply theme
            theme_manager.configure_matplotlib_figure(self.figure, self.axes)
            
            # Re-add all series
            for series_id, config in self.series_configs.items():
                file_data = self.loaded_files.get(config.file_id)
                if file_data:
                    # Get data and create plot
                    x_data, y_data = self.get_series_data(config, file_data)
                    if len(x_data) > 0 and len(y_data) > 0:
                        x_processed, y_processed, outliers = self.process_series_data(x_data, y_data, config)
                        plot_objects = self.create_series_plot(x_processed, y_processed, config)
                        self.series_plots[series_id] = plot_objects
                        
                        # Handle outliers
                        if config.outlier_handling == "highlight" and len(outliers) > 0:
                            self.highlight_outliers(series_id, x_data, y_data, outliers, config)
                            
            # Update plot elements
            self.update_plot_elements()
            
        except Exception as e:
            logger.error(f"Error refreshing plot: {e}")
            
    def update_plot_elements(self):
        """Update plot elements like legend, grid, etc."""
        try:
            # Update grid
            if self.show_grid:
                self.axes.grid(True, alpha=0.3)
            else:
                self.axes.grid(False)
                
            # Update legend
            if self.show_legend and len(self.series_configs) > 0:
                handles, labels = self.axes.get_legend_handles_labels()
                if handles:
                    legend = self.axes.legend(
                        handles, labels,
                        loc=self.legend_location,
                        fancybox=True,
                        shadow=True,
                        framealpha=0.9
                    )
                    # Style legend for dark theme
                    if theme_manager.current_theme == "dark":
                        legend.get_frame().set_facecolor('#2b2b2b')
                        legend.get_frame().set_edgecolor('#555555')
                        for text in legend.get_texts():
                            text.set_color('white')
                            
            # Auto-scale if enabled
            if self.auto_scale:
                self.axes.autoscale()
                
            # Tight layout
            self.figure.tight_layout()
            
        except Exception as e:
            logger.error(f"Error updating plot elements: {e}")
            
    def set_axis_labels(self, xlabel: str = None, ylabel: str = None, title: str = None):
        """Set axis labels and title"""
        if xlabel:
            self.axes.set_xlabel(xlabel)
        if ylabel:
            self.axes.set_ylabel(ylabel)
        if title:
            self.axes.set_title(title)
            
    def set_axis_limits(self, xlim: Tuple[float, float] = None, ylim: Tuple[float, float] = None):
        """Set axis limits"""
        if xlim:
            self.axes.set_xlim(xlim)
        if ylim:
            self.axes.set_ylim(ylim)
            
    def export_plot(self, filename: str, dpi: int = 300, format: str = 'png'):
        """Export plot to file"""
        try:
            self.figure.savefig(
                filename,
                dpi=dpi,
                format=format,
                bbox_inches='tight',
                facecolor=self.figure.get_facecolor(),
                edgecolor='none'
            )
            logger.info(f"Plot exported to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting plot: {e}")
            return False
            
    def get_series_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all series"""
        info = {}
        for series_id, config in self.series_configs.items():
            file_data = self.loaded_files.get(config.file_id)
            if file_data:
                x_data, y_data = self.get_series_data(config, file_data)
                info[series_id] = {
                    "name": config.name,
                    "file": file_data.filename,
                    "x_column": config.x_column,
                    "y_column": config.y_column,
                    "points": len(y_data),
                    "color": config.color,
                    "visible": config.visible,
                    "has_outliers": series_id in self.outlier_points and len(self.outlier_points[series_id]) > 0
                }
        return info
