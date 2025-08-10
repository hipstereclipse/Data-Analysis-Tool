#!/usr/bin/env python3
"""
Plot Manager - Unified plotting operations
Consolidated from plot_manager.py and enhanced_plot_manager.py
Handles all plotting operations including series rendering and styling
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.dates as mdates
import logging
from typing import Dict, List, Optional, Tuple, Any

from config.constants import PlotTypes, MissingDataMethods, TrendTypes
from models.data_models import SeriesConfig, PlotConfiguration, FileData
from core.data_utils import DataProcessor, DataValidator

logger = logging.getLogger(__name__)


class PlotManager:
    """
    Unified plot manager with multi-series support and advanced styling
    Handles all matplotlib operations for the application
    """

    def __init__(self, figure: Optional[Figure] = None):
        """Initialize plot manager"""
        # Current figure and axes
        self.figure: Optional[Figure] = figure
        self.axes: Optional[plt.Axes] = None
        self.canvas: Optional[FigureCanvasTkAgg] = None
        self.toolbar: Optional[NavigationToolbar2Tk] = None

        # Secondary y-axis if needed
        self.axes2: Optional[plt.Axes] = None

        # Plot configuration
        self.plot_config = PlotConfiguration()

        # Track plotted series for updates
        self.plotted_series: Dict[str, Any] = {}
        self.series_configs: Dict[str, SeriesConfig] = {}
        self.loaded_files: Dict[str, FileData] = {}

        # Color cycle
        self.color_cycle = plt.cm.get_cmap('tab10')
        self.color_index = 0
        
        # Plot settings
        self.auto_scale = True
        self.show_grid = True
        self.show_legend = True
        self.legend_location = "best"

        # Initialize figure if provided
        if self.figure:
            self.setup_figure()

    def setup_figure(self):
        """Setup the figure with proper configuration"""
        if self.figure:
            self.figure.clear()
            self.axes = self.figure.add_subplot(111)
            
            # Apply default styling
            self.axes.set_xlabel("X-Axis")
            self.axes.set_ylabel("Y-Axis")
            self.axes.grid(self.show_grid, alpha=0.3)

    def set_figure(self, figure: Figure):
        """Set the figure to be managed"""
        self.figure = figure
        self.setup_figure()

    def add_series(self, series_id: str, series_config: SeriesConfig, file_data: FileData):
        """Add a series to the plot"""
        try:
            # Store references
            self.series_configs[series_id] = series_config
            self.loaded_files[series_config.file_id] = file_data
            
            # Get data
            x_data, y_data = self._get_series_data(series_config, file_data)
            
            # Validate data
            is_valid, error_msg = DataValidator.validate_data_compatibility(x_data, y_data)
            if not is_valid:
                logger.error(f"Invalid data for series {series_id}: {error_msg}")
                return False
            
            # Apply processing
            x_data, y_data = self._process_series_data(x_data, y_data, series_config)
            
            # Plot the series
            plot_objects = self._plot_series(x_data, y_data, series_config)
            
            # Store plot objects for updates
            self.plotted_series[series_id] = {
                'config': series_config,
                'file_data': file_data,
                'plot_objects': plot_objects,
                'x_data': x_data,
                'y_data': y_data
            }
            
            # Update plot
            self._update_plot_appearance()
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding series {series_id}: {e}")
            return False

    def remove_series(self, series_id: str):
        """Remove a series from the plot"""
        try:
            if series_id in self.plotted_series:
                # Remove plot objects
                plot_objects = self.plotted_series[series_id]['plot_objects']
                for obj in plot_objects:
                    if obj in self.axes.lines:
                        obj.remove()
                    elif hasattr(obj, 'remove'):
                        obj.remove()
                
                # Remove from tracking
                del self.plotted_series[series_id]
                if series_id in self.series_configs:
                    del self.series_configs[series_id]
                
                # Update plot
                self._update_plot_appearance()
                
                return True
                
        except Exception as e:
            logger.error(f"Error removing series {series_id}: {e}")
            return False

    def update_series(self, series_id: str, series_config: SeriesConfig):
        """Update an existing series"""
        try:
            if series_id in self.plotted_series:
                # Remove old series
                self.remove_series(series_id)
                
                # Add updated series
                file_data = self.plotted_series.get(series_id, {}).get('file_data')
                if file_data:
                    return self.add_series(series_id, series_config, file_data)
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating series {series_id}: {e}")
            return False

    def clear_plot(self):
        """Clear all series from the plot"""
        try:
            if self.axes:
                self.axes.clear()
                self.plotted_series.clear()
                self.series_configs.clear()
                self.setup_figure()
                
        except Exception as e:
            logger.error(f"Error clearing plot: {e}")

    def refresh_plot(self):
        """Refresh the entire plot"""
        try:
            if not self.axes:
                return
                
            # Store current series
            current_series = self.plotted_series.copy()
            
            # Clear and rebuild
            self.axes.clear()
            self.setup_figure()
            self.plotted_series.clear()
            
            # Re-add all series
            for series_id, series_data in current_series.items():
                self.add_series(
                    series_id,
                    series_data['config'],
                    series_data['file_data']
                )
                
        except Exception as e:
            logger.error(f"Error refreshing plot: {e}")

    def _get_series_data(self, series_config: SeriesConfig, file_data: FileData) -> Tuple[np.ndarray, np.ndarray]:
        """Get data arrays for a series"""
        try:
            # Get data slice
            start_idx = series_config.start_index or 0
            end_idx = series_config.end_index or len(file_data.data)
            data_slice = file_data.data.iloc[start_idx:end_idx]
            
            # Get X data
            if series_config.x_column == "Index":
                x_data = np.arange(len(data_slice))
            else:
                x_data = data_slice[series_config.x_column].values
                if pd.api.types.is_object_dtype(x_data):
                    x_data = pd.to_numeric(x_data, errors='coerce')
                    
            # Get Y data
            y_data = data_slice[series_config.y_column].values
            if pd.api.types.is_object_dtype(y_data):
                y_data = pd.to_numeric(y_data, errors='coerce')
                
            return x_data, y_data
            
        except Exception as e:
            logger.error(f"Error getting series data: {e}")
            return np.array([]), np.array([])

    def _process_series_data(self, x_data: np.ndarray, y_data: np.ndarray, 
                           series_config: SeriesConfig) -> Tuple[np.ndarray, np.ndarray]:
        """Apply data processing to series"""
        try:
            # Handle missing data
            missing_method = getattr(series_config, 'missing_data_method', 'drop')
            x_data, y_data = DataProcessor.handle_missing_data(x_data, y_data, missing_method)
            
            # Apply smoothing
            if getattr(series_config, 'smoothing', False):
                window = getattr(series_config, 'smoothing_window', 5)
                y_data = DataProcessor.apply_smoothing(y_data, window)
            
            return x_data, y_data
            
        except Exception as e:
            logger.error(f"Error processing series data: {e}")
            return x_data, y_data

    def _plot_series(self, x_data: np.ndarray, y_data: np.ndarray, 
                    series_config: SeriesConfig) -> List[Any]:
        """Plot a series and return plot objects"""
        plot_objects = []
        
        try:
            plot_type = series_config.plot_type or "line"
            color = series_config.color or self._get_next_color()
            label = series_config.name if self.show_legend else ""
            
            if plot_type == "line":
                line = self.axes.plot(
                    x_data, y_data,
                    color=color,
                    linestyle=series_config.line_style or "-",
                    linewidth=series_config.line_width or 1.0,
                    alpha=series_config.alpha or 1.0,
                    label=label
                )[0]
                plot_objects.append(line)
                
            elif plot_type == "scatter":
                scatter = self.axes.scatter(
                    x_data, y_data,
                    color=color,
                    marker=series_config.marker or "o",
                    s=(series_config.marker_size or 6.0) ** 2,
                    alpha=series_config.alpha or 1.0,
                    label=label
                )
                plot_objects.append(scatter)
                
            elif plot_type == "both":
                line = self.axes.plot(
                    x_data, y_data,
                    color=color,
                    linestyle=series_config.line_style or "-",
                    linewidth=series_config.line_width or 1.0,
                    marker=series_config.marker or "o",
                    markersize=series_config.marker_size or 6.0,
                    alpha=series_config.alpha or 1.0,
                    label=label
                )[0]
                plot_objects.append(line)
                
            elif plot_type == "bar":
                bars = self.axes.bar(
                    x_data, y_data,
                    color=color,
                    alpha=series_config.alpha or 1.0,
                    label=label
                )
                plot_objects.extend(bars)
                
            elif plot_type == "area":
                area = self.axes.fill_between(
                    x_data, y_data,
                    color=color,
                    alpha=series_config.alpha or 1.0,
                    label=label
                )
                plot_objects.append(area)
                
            elif plot_type == "step":
                line = self.axes.step(
                    x_data, y_data,
                    color=color,
                    linewidth=series_config.line_width or 1.0,
                    alpha=series_config.alpha or 1.0,
                    label=label
                )[0]
                plot_objects.append(line)
            
            return plot_objects
            
        except Exception as e:
            logger.error(f"Error plotting series: {e}")
            return []

    def _update_plot_appearance(self):
        """Update plot appearance and styling"""
        try:
            if not self.axes:
                return
                
            # Update grid
            self.axes.grid(self.show_grid, alpha=0.3)
            
            # Update legend
            if self.show_legend and any(line.get_label() and not line.get_label().startswith('_') 
                                      for line in self.axes.get_lines()):
                self.axes.legend(loc=self.legend_location)
            
            # Auto-scale if enabled
            if self.auto_scale:
                self.axes.relim()
                self.axes.autoscale()
            
            # Refresh canvas if available
            if self.canvas:
                self.canvas.draw()
                
        except Exception as e:
            logger.error(f"Error updating plot appearance: {e}")

    def _get_next_color(self) -> str:
        """Get the next color from the color cycle"""
        color = self.color_cycle(self.color_index % 10)
        self.color_index += 1
        return f"#{int(color[0]*255):02x}{int(color[1]*255):02x}{int(color[2]*255):02x}"

    def set_plot_config(self, config: PlotConfiguration):
        """Set plot configuration"""
        self.plot_config = config
        self._apply_plot_config()

    def _apply_plot_config(self):
        """Apply plot configuration to axes"""
        try:
            if not self.axes:
                return
                
            # Apply titles and labels
            if self.plot_config.title:
                self.axes.set_title(self.plot_config.title)
            if self.plot_config.x_label:
                self.axes.set_xlabel(self.plot_config.x_label)
            if self.plot_config.y_label:
                self.axes.set_ylabel(self.plot_config.y_label)
            
            # Apply grid settings
            self.show_grid = self.plot_config.show_grid
            self.axes.grid(self.show_grid, alpha=0.3)
            
            # Apply legend settings
            self.show_legend = self.plot_config.show_legend
            self.legend_location = self.plot_config.legend_location or "best"
            
            # Refresh appearance
            self._update_plot_appearance()
            
        except Exception as e:
            logger.error(f"Error applying plot config: {e}")

    def export_plot(self, filename: str, **kwargs):
        """Export plot to file"""
        try:
            if self.figure:
                self.figure.savefig(filename, **kwargs)
                return True
            return False
        except Exception as e:
            logger.error(f"Error exporting plot: {e}")
            return False

    def get_plot_statistics(self) -> Dict[str, Any]:
        """Get statistics about the current plot"""
        try:
            stats = {
                'num_series': len(self.plotted_series),
                'series_names': [config.name for config in self.series_configs.values()],
                'data_points': sum(len(data['y_data']) for data in self.plotted_series.values()),
                'plot_config': self.plot_config.__dict__ if self.plot_config else {}
            }
            return stats
        except Exception as e:
            logger.error(f"Error getting plot statistics: {e}")
            return {}

    def create_figure(self, parent_widget=None, width: float = 14, height: float = 9, dpi: int = 100) -> Tuple[
        Figure, FigureCanvasTkAgg, NavigationToolbar2Tk]:
        """
        Create a new matplotlib figure with canvas and toolbar

        Args:
            parent_widget: Parent tkinter widget for canvas
            width: Figure width in inches
            height: Figure height in inches
            dpi: Dots per inch resolution

        Returns:
            Tuple of (figure, canvas, toolbar)
        """
        # Close existing figure if any
        if self.figure:
            plt.close(self.figure)

        # Create new figure
        self.figure = Figure(figsize=(width, height), dpi=dpi, tight_layout=True)
        self.figure.patch.set_facecolor('white')

        # Create axes
        self.axes = self.figure.add_subplot(111)
        self.axes2 = None  # Reset secondary axis

        # Create canvas if parent widget provided
        if parent_widget:
            self.canvas = FigureCanvasTkAgg(self.figure, master=parent_widget)
            self.canvas.draw()

            # Create toolbar
            self.toolbar = NavigationToolbar2Tk(self.canvas, parent_widget)
            self.toolbar.update()

        # Reset tracking
        self.plotted_series.clear()
        self.color_index = 0

        return self.figure, self.canvas, self.toolbar

    def clear_plot(self):
        """Clear the current plot"""
        if self.axes:
            self.axes.clear()
        if self.axes2:
            self.axes2.clear()
            self.axes2 = None

        self.plotted_series.clear()
        self.color_index = 0

        if self.canvas:
            self.canvas.draw()

    def plot_series(self, series_config: SeriesConfig, file_data: FileData,
                    x_data: pd.Series = None, y_data: pd.Series = None) -> bool:
        """
        Plot a single data series

        Args:
            series_config: SeriesConfig object with display settings
            file_data: FileData object containing the data
            x_data: Optional pre-processed X data
            y_data: Optional pre-processed Y data

        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure axes exists
            if not self.axes:
                logger.warning("No axes available for plotting")
                return False

            # Get data if not provided
            if x_data is None or y_data is None:
                x_data, y_data = self.prepare_series_data(series_config, file_data)
                if x_data is None or y_data is None:
                    return False

            # Handle missing data
            x_data, y_data = self.handle_missing_data(
                x_data, y_data, series_config.missing_data_method
            )

            # Apply smoothing if requested
            if series_config.smoothing and series_config.smooth_factor > 0:
                y_data = self.apply_smoothing(y_data, series_config.smooth_factor)

            # Determine which axis to use
            ax = self.axes
            if series_config.y_axis == "right":
                if not self.axes2:
                    self.axes2 = self.axes.twinx()
                ax = self.axes2

            # Plot based on type
            plot_obj = None
            plot_type = series_config.plot_type.lower()

            if plot_type == "line":
                plot_obj = ax.plot(
                    x_data, y_data,
                    color=series_config.color,
                    linestyle=series_config.line_style,
                    linewidth=series_config.line_width,
                    marker=series_config.marker_style if series_config.marker_style else None,
                    markersize=series_config.marker_size,
                    alpha=series_config.alpha,
                    label=series_config.name,
                    zorder=series_config.z_order,
                    visible=series_config.visible
                )[0]

            elif plot_type == "scatter":
                plot_obj = ax.scatter(
                    x_data, y_data,
                    color=series_config.color,
                    marker=series_config.marker_style if series_config.marker_style else 'o',
                    s=series_config.marker_size ** 2,
                    alpha=series_config.alpha,
                    label=series_config.name,
                    zorder=series_config.z_order,
                    visible=series_config.visible
                )

            elif plot_type == "bar":
                plot_obj = ax.bar(
                    range(len(x_data)), y_data,
                    color=series_config.color,
                    alpha=series_config.alpha,
                    label=series_config.name,
                    zorder=series_config.z_order,
                    visible=series_config.visible
                )
                # Set x-tick labels for bar chart
                ax.set_xticks(range(len(x_data)))
                ax.set_xticklabels(x_data, rotation=45, ha='right')

            elif plot_type == "area":
                plot_obj = ax.fill_between(
                    x_data, y_data, 0,
                    color=series_config.color,
                    alpha=series_config.alpha * 0.5,
                    label=series_config.name,
                    zorder=series_config.z_order,
                    visible=series_config.visible
                )

            elif plot_type == "step":
                plot_obj = ax.step(
                    x_data, y_data,
                    color=series_config.color,
                    linewidth=series_config.line_width,
                    alpha=series_config.alpha,
                    label=series_config.name,
                    where='mid',
                    zorder=series_config.z_order,
                    visible=series_config.visible
                )[0]

            elif plot_type == "both":
                # Line with markers
                plot_obj = ax.plot(
                    x_data, y_data,
                    color=series_config.color,
                    linestyle=series_config.line_style,
                    linewidth=series_config.line_width,
                    marker=series_config.marker_style if series_config.marker_style else 'o',
                    markersize=series_config.marker_size,
                    alpha=series_config.alpha,
                    label=series_config.name,
                    zorder=series_config.z_order,
                    visible=series_config.visible
                )[0]

            # Add trend line if requested
            if series_config.show_trend:
                self.add_trend_line(ax, x_data, y_data, series_config)

            # Add statistics overlays if requested
            if series_config.show_mean:
                mean_val = np.nanmean(y_data)
                ax.axhline(mean_val, color=series_config.color, linestyle='--',
                           alpha=0.5, linewidth=1, label=f'{series_config.name} Mean')

            if series_config.show_std:
                mean_val = np.nanmean(y_data)
                std_val = np.nanstd(y_data)
                ax.fill_between(ax.get_xlim(), mean_val - std_val, mean_val + std_val,
                                color=series_config.color, alpha=0.1, label=f'{series_config.name} ±σ')

            # Store reference
            self.plotted_series[series_config.series_id] = {
                'plot_obj': plot_obj,
                'series_config': series_config,
                'axis': ax
            }

            # Format datetime axis if needed
            if isinstance(x_data.iloc[0] if hasattr(x_data, 'iloc') else x_data[0],
                          (pd.Timestamp, np.datetime64)):
                self.format_datetime_axis(ax)

            return True

        except Exception as e:
            logger.error(f"Error plotting series {series_config.name}: {e}")
            return False

    def prepare_series_data(self, series_config: SeriesConfig, file_data: FileData) -> Tuple[
        Optional[pd.Series], Optional[pd.Series]]:
        """
        Prepare data for plotting from series configuration

        Args:
            series_config: Series configuration
            file_data: File data containing the dataframe

        Returns:
            Tuple of (x_data, y_data) or (None, None) if error
        """
        try:
            df = file_data.data

            # Apply row range if specified
            start_row = series_config.start_row if series_config.start_row is not None else 0
            end_row = series_config.end_row if series_config.end_row is not None else len(df)

            # Handle negative indices
            if start_row < 0:
                start_row = len(df) + start_row
            if end_row < 0:
                end_row = len(df) + end_row

            # Slice dataframe
            df_slice = df.iloc[start_row:end_row]

            # Get x and y data
            if series_config.x_column and series_config.x_column in df_slice.columns:
                x_data = df_slice[series_config.x_column]
            else:
                # Use index if no x column specified
                x_data = pd.Series(df_slice.index)

            if series_config.y_column and series_config.y_column in df_slice.columns:
                y_data = df_slice[series_config.y_column]
            else:
                logger.error(f"Y column '{series_config.y_column}' not found")
                return None, None

            # Convert to numeric if possible
            if not pd.api.types.is_numeric_dtype(y_data):
                y_data = pd.to_numeric(y_data, errors='coerce')

            # Try to convert x to datetime if it looks like dates
            if not pd.api.types.is_numeric_dtype(x_data) and not pd.api.types.is_datetime64_any_dtype(x_data):
                try:
                    x_data = pd.to_datetime(x_data, errors='coerce')
                except:
                    pass

            return x_data, y_data

        except Exception as e:
            logger.error(f"Error preparing series data: {e}")
            return None, None

    def handle_missing_data(self, x_data: pd.Series, y_data: pd.Series,
                            method: str) -> Tuple[pd.Series, pd.Series]:
        """
        Handle missing data according to specified method

        Args:
            x_data: X-axis data
            y_data: Y-axis data
            method: Method for handling missing data

        Returns:
            Tuple of cleaned (x_data, y_data)
        """
        if method == MissingDataMethods.DROP.value:
            # Drop rows with NaN values
            mask = ~(x_data.isna() | y_data.isna())
            return x_data[mask], y_data[mask]

        elif method == MissingDataMethods.INTERPOLATE.value:
            # Linear interpolation
            y_data = y_data.interpolate(method='linear')

        elif method == MissingDataMethods.FORWARD_FILL.value:
            # Forward fill
            y_data = y_data.fillna(method='ffill')

        elif method == MissingDataMethods.BACKWARD_FILL.value:
            # Backward fill
            y_data = y_data.fillna(method='bfill')

        elif method == MissingDataMethods.ZERO.value:
            # Fill with zeros
            y_data = y_data.fillna(0)

        elif method == MissingDataMethods.MEAN.value:
            # Fill with mean
            y_data = y_data.fillna(y_data.mean())

        elif method == MissingDataMethods.MEDIAN.value:
            # Fill with median
            y_data = y_data.fillna(y_data.median())

        return x_data, y_data

    def apply_smoothing(self, data: pd.Series, smooth_factor: int) -> pd.Series:
        """
        Apply Savitzky-Golay smoothing to data

        Args:
            data: Data to smooth
            smooth_factor: Smoothing window size (must be odd)

        Returns:
            Smoothed data
        """
        try:
            # Ensure window size is odd and at least 3
            window = max(3, smooth_factor)
            if window % 2 == 0:
                window += 1

            # Don't smooth if not enough data points
            if len(data) <= window:
                return data

            # Apply Savitzky-Golay filter
            smoothed = savgol_filter(data.fillna(method='linear'),
                                     window_length=window,
                                     polyorder=min(3, window - 1))

            return pd.Series(smoothed, index=data.index)

        except Exception as e:
            logger.warning(f"Smoothing failed: {e}, returning original data")
            return data

    def add_trend_line(self, ax: plt.Axes, x_data: pd.Series, y_data: pd.Series,
                       series_config: SeriesConfig):
        """
        Add trend line to plot

        Args:
            ax: Matplotlib axes
            x_data: X-axis data
            y_data: Y-axis data
            series_config: Series configuration
        """
        try:
            # Convert to numeric values for fitting
            if pd.api.types.is_datetime64_any_dtype(x_data):
                x_numeric = np.arange(len(x_data))
            else:
                x_numeric = np.array(x_data)

            y_numeric = np.array(y_data)

            # Remove NaN values
            mask = ~(np.isnan(x_numeric) | np.isnan(y_numeric))
            x_clean = x_numeric[mask]
            y_clean = y_numeric[mask]

            if len(x_clean) < 2:
                return

            trend_type = series_config.trend_type
            trend_color = series_config.trend_color or series_config.color
            trend_style = series_config.trend_style or '--'
            trend_width = series_config.trend_width or 1.0

            if trend_type == TrendTypes.LINEAR.value:
                # Linear regression
                z = np.polyfit(x_clean, y_clean, 1)
                p = np.poly1d(z)
                trend_y = p(x_numeric)

                ax.plot(x_data, trend_y, color=trend_color, linestyle=trend_style,
                        linewidth=trend_width, alpha=0.7,
                        label=f'{series_config.name} Linear Trend')

            elif trend_type == TrendTypes.POLYNOMIAL.value:
                # Polynomial fit (degree 2)
                z = np.polyfit(x_clean, y_clean, 2)
                p = np.poly1d(z)
                trend_y = p(x_numeric)

                ax.plot(x_data, trend_y, color=trend_color, linestyle=trend_style,
                        linewidth=trend_width, alpha=0.7,
                        label=f'{series_config.name} Polynomial Trend')

            elif trend_type == TrendTypes.EXPONENTIAL.value:
                # Exponential fit
                # y = a * exp(b * x)
                # log(y) = log(a) + b * x
                y_positive = y_clean[y_clean > 0]
                x_positive = x_clean[y_clean > 0]

                if len(y_positive) > 1:
                    z = np.polyfit(x_positive, np.log(y_positive), 1)
                    trend_y = np.exp(z[1]) * np.exp(z[0] * x_numeric)

                    ax.plot(x_data, trend_y, color=trend_color, linestyle=trend_style,
                            linewidth=trend_width, alpha=0.7,
                            label=f'{series_config.name} Exponential Trend')

            elif trend_type == TrendTypes.LOGARITHMIC.value:
                # Logarithmic fit
                # y = a * log(x) + b
                x_positive = x_clean[x_clean > 0]
                y_positive = y_clean[x_clean > 0]

                if len(x_positive) > 1:
                    z = np.polyfit(np.log(x_positive), y_positive, 1)

                    # Only plot for positive x values
                    x_plot = x_numeric[x_numeric > 0]
                    trend_y = z[0] * np.log(x_plot) + z[1]

                    # Need to map back to original x_data indices
                    ax.plot(x_data[x_numeric > 0], trend_y, color=trend_color,
                            linestyle=trend_style, linewidth=trend_width, alpha=0.7,
                            label=f'{series_config.name} Logarithmic Trend')

            elif trend_type == TrendTypes.MOVING_AVERAGE.value:
                # Moving average
                window = min(20, len(y_clean) // 4)
                if window > 1:
                    ma = pd.Series(y_numeric).rolling(window=window, center=True).mean()
                    ax.plot(x_data, ma, color=trend_color, linestyle=trend_style,
                            linewidth=trend_width, alpha=0.7,
                            label=f'{series_config.name} Moving Average')

        except Exception as e:
            logger.warning(f"Failed to add trend line: {e}")

    def apply_plot_configuration(self, config: PlotConfiguration):
        """
        Apply plot configuration to current figure

        Args:
            config: PlotConfiguration object
        """
        if not self.axes:
            return

        self.plot_config = config

        # Set title
        self.axes.set_title(config.title, fontsize=config.title_size,
                            fontweight=config.title_weight)

        # Set labels
        self.axes.set_xlabel(config.xlabel, fontsize=config.xlabel_size)
        self.axes.set_ylabel(config.ylabel, fontsize=config.ylabel_size)

        # Set scale
        if config.log_scale_x:
            self.axes.set_xscale('log')
        else:
            self.axes.set_xscale('linear')

        if config.log_scale_y:
            self.axes.set_yscale('log')
        else:
            self.axes.set_yscale('linear')

        # Set limits if not auto
        if not config.x_auto_scale and config.x_min is not None and config.x_max is not None:
            self.axes.set_xlim(config.x_min, config.x_max)

        if not config.y_auto_scale and config.y_min is not None and config.y_max is not None:
            self.axes.set_ylim(config.y_min, config.y_max)

        # Configure grid
        self.axes.grid(config.show_grid, linestyle=config.grid_style,
                       alpha=config.grid_alpha, color=config.grid_color)

        # Configure legend
        if config.show_legend and self.axes.get_legend_handles_labels()[0]:
            self.axes.legend(loc=config.legend_location,
                             frameon=config.legend_frameon,
                             fancybox=config.legend_fancybox,
                             shadow=config.legend_shadow,
                             ncol=config.legend_ncol,
                             fontsize=config.legend_fontsize)

        # Apply to secondary axis if exists
        if self.axes2:
            self.axes2.grid(False)  # Don't double grid
            if config.show_legend and self.axes2.get_legend_handles_labels()[0]:
                self.axes2.legend(loc='upper right')

        # Set margins
        self.figure.subplots_adjust(
            left=config.margin_left,
            right=config.margin_right,
            top=config.margin_top,
            bottom=config.margin_bottom
        )

        # Redraw canvas
        if self.canvas:
            self.canvas.draw()

    def format_datetime_axis(self, ax: plt.Axes):
        """
        Format datetime axis with appropriate date formatter

        Args:
            ax: Matplotlib axes with datetime data
        """
        try:
            # Get x-axis limits
            xlim = ax.get_xlim()

            # Calculate date range in days
            if isinstance(xlim[0], (int, float)):
                # Matplotlib date numbers
                date_range = xlim[1] - xlim[0]
            else:
                date_range = (xlim[1] - xlim[0]).days if hasattr(xlim[1] - xlim[0], 'days') else 1

            # Choose appropriate formatter based on range
            if date_range < 1:
                # Less than a day - show hours and minutes
                formatter = mdates.DateFormatter('%H:%M')
                locator = mdates.HourLocator(interval=1)
            elif date_range < 7:
                # Less than a week - show day and time
                formatter = mdates.DateFormatter('%m/%d %H:%M')
                locator = mdates.DayLocator()
            elif date_range < 30:
                # Less than a month - show day
                formatter = mdates.DateFormatter('%m/%d')
                locator = mdates.DayLocator(interval=2)
            elif date_range < 365:
                # Less than a year - show month/day
                formatter = mdates.DateFormatter('%m/%d')
                locator = mdates.MonthLocator()
            else:
                # More than a year - show year/month
                formatter = mdates.DateFormatter('%Y-%m')
                locator = mdates.YearLocator()

            ax.xaxis.set_major_formatter(formatter)
            ax.xaxis.set_major_locator(locator)

            # Rotate labels for better readability
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

        except Exception as e:
            logger.warning(f"Failed to format datetime axis: {e}")

    def update_series_visibility(self, series_id: str, visible: bool):
        """
        Update visibility of a plotted series

        Args:
            series_id: Series identifier
            visible: Whether series should be visible
        """
        if series_id in self.plotted_series:
            plot_obj = self.plotted_series[series_id]['plot_obj']
            if hasattr(plot_obj, 'set_visible'):
                plot_obj.set_visible(visible)
            elif hasattr(plot_obj, '__iter__'):
                # For bar plots and other collections
                for item in plot_obj:
                    if hasattr(item, 'set_visible'):
                        item.set_visible(visible)

            if self.canvas:
                self.canvas.draw()

    def highlight_data_point(self, series_id: str, point_index: int):
        """
        Highlight a specific data point

        Args:
            series_id: Series identifier
            point_index: Index of point to highlight
        """
        if series_id in self.plotted_series:
            series_info = self.plotted_series[series_id]
            ax = series_info['axis']
            config = series_info['series_config']

            # Add a marker at the specified point
            # Implementation depends on having access to the original data
            # This is a placeholder for the highlighting logic

            if self.canvas:
                self.canvas.draw()

    def export_figure(self, filepath: str, dpi: int = 300):
        """
        Export figure to file

        Args:
            filepath: Path to save file
            dpi: Resolution for raster formats
        """
        if self.figure:
            self.figure.savefig(filepath, dpi=dpi, bbox_inches='tight')
            logger.info(f"Figure exported to {filepath}")

    def get_figure_size(self) -> Tuple[float, float]:
        """Get current figure size in inches"""
        if self.figure:
            return self.figure.get_size_inches()
        return (14, 9)

    def set_figure_size(self, width: float, height: float):
        """Set figure size in inches"""
        if self.figure:
            self.figure.set_size_inches(width, height)
            if self.canvas:
                self.canvas.draw()