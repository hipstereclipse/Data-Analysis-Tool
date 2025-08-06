#!/usr/bin/env python3
"""
plot_manager.py - Plot creation and management for Excel Data Plotter
Handles all plotting operations including series rendering and styling
"""

import numpy as np  # For numerical operations
import pandas as pd  # For data manipulation
import matplotlib.pyplot as plt  # For plotting
from matplotlib.figure import Figure  # For figure creation
import matplotlib.dates as mdates  # For date formatting
from scipy.signal import savgol_filter  # For data smoothing
from sklearn.linear_model import LinearRegression  # For trend lines

from constants import PlotTypes, MissingDataMethods, TrendTypes  # Import constants
from analysis_tools import DataAnalysisTools, VacuumAnalysisTools  # Import analysis tools


class PlotManager:
    """
    Manages plot creation, updating, and configuration
    Handles all matplotlib operations for the application
    """

    def __init__(self):
        """Initialize plot manager"""
        # Current figure and axes
        self.figure = None  # Matplotlib figure object
        self.axes = None  # Matplotlib axes object

        # Plot configuration
        self.plot_config = {
            'title': 'Data Analysis',
            'xlabel': 'X Axis',
            'ylabel': 'Y Axis',
            'grid': True,
            'legend': True
        }

    def create_figure(self, width=14, height=9, dpi=100):
        """
        Create a new matplotlib figure

        Args:
            width (float): Figure width in inches
            height (float): Figure height in inches
            dpi (int): Dots per inch resolution

        Returns:
            Figure: Created matplotlib figure
        """
        # Create new figure with specified dimensions
        self.figure = Figure(figsize=(width, height), dpi=dpi)

        # Set figure background color
        self.figure.patch.set_facecolor('white')

        # Create axes
        self.axes = self.figure.add_subplot(111)

        return self.figure

    def clear_plot(self):
        """Clear the current plot"""
        if self.axes:
            # Clear axes content
            self.axes.clear()

    def plot_series(self, series_config, x_data, y_data, plot_type='line'):
        """
        Plot a single data series

        Args:
            series_config: SeriesConfig object with display settings
            x_data: X-axis data array
            y_data: Y-axis data array
            plot_type (str): Type of plot to create
        """
        # Ensure axes exists
        if not self.axes:
            self.create_figure()

        # Handle missing data according to configuration
        y_data = self.handle_missing_data(y_data, series_config.missing_data_method)

        # Apply smoothing if requested
        if series_config.smoothing and series_config.smooth_factor > 0:
            y_data = self.apply_smoothing(y_data, series_config.smooth_factor)

        # Plot based on type
        if plot_type == PlotTypes.LINE:
            self.plot_line(x_data, y_data, series_config)
        elif plot_type == PlotTypes.SCATTER:
            self.plot_scatter(x_data, y_data, series_config)
        elif plot_type == PlotTypes.BAR:
            self.plot_bar(x_data, y_data, series_config)
        elif plot_type == PlotTypes.AREA:
            self.plot_area(x_data, y_data, series_config)
        else:
            # Default to line plot
            self.plot_line(x_data, y_data, series_config)

        # Add trend line if requested
        if series_config.show_trendline:
            self.add_trendline(x_data, y_data, series_config)

        # Add statistics box if requested
        if series_config.show_statistics:
            self.add_statistics_box(y_data, series_config)

        # Mark peaks if requested
        if series_config.show_peaks:
            self.mark_peaks(x_data, y_data, series_config)

    def plot_line(self, x_data, y_data, series_config):
        """
        Create a line plot

        Args:
            x_data: X-axis data
            y_data: Y-axis data
            series_config: Series configuration
        """
        # Plot line with specified style
        line = self.axes.plot(
            x_data,  # X values
            y_data,  # Y values
            color=series_config.color,  # Line color
            linestyle=series_config.line_style,  # Line style (solid, dashed, etc.)
            linewidth=series_config.line_width,  # Line thickness
            marker=series_config.marker if series_config.marker else None,  # Point markers
            markersize=series_config.marker_size,  # Marker size
            alpha=series_config.alpha,  # Transparency
            label=series_config.legend_label if series_config.show_in_legend else ""  # Legend label
        )

        # Fill area under curve if requested
        if series_config.fill_area:
            self.axes.fill_between(
                x_data,  # X values
                y_data,  # Y values
                alpha=series_config.alpha * 0.3,  # Lighter transparency for fill
                color=series_config.color  # Fill color
            )

    def plot_scatter(self, x_data, y_data, series_config):
        """
        Create a scatter plot

        Args:
            x_data: X-axis data
            y_data: Y-axis data
            series_config: Series configuration
        """
        # Create scatter plot
        self.axes.scatter(
            x_data,  # X values
            y_data,  # Y values
            color=series_config.color,  # Point color
            s=series_config.marker_size ** 2,  # Size (squared for area)
            marker=series_config.marker if series_config.marker else 'o',  # Marker style
            alpha=series_config.alpha,  # Transparency
            label=series_config.legend_label if series_config.show_in_legend else ""  # Legend label
        )

    def plot_bar(self, x_data, y_data, series_config):
        """
        Create a bar plot

        Args:
            x_data: X-axis data
            y_data: Y-axis data
            series_config: Series configuration
        """
        # Create bar plot
        self.axes.bar(
            x_data,  # X positions
            y_data,  # Bar heights
            color=series_config.color,  # Bar color
            alpha=series_config.alpha,  # Transparency
            label=series_config.legend_label if series_config.show_in_legend else ""  # Legend label
        )

    def plot_area(self, x_data, y_data, series_config):
        """
        Create an area plot

        Args:
            x_data: X-axis data
            y_data: Y-axis data
            series_config: Series configuration
        """
        # Create filled area plot
        self.axes.fill_between(
            x_data,  # X values
            y_data,  # Y values
            color=series_config.color,  # Fill color
            alpha=series_config.alpha,  # Transparency
            label=series_config.legend_label if series_config.show_in_legend else ""  # Legend label
        )

    def handle_missing_data(self, data, method):
        """
        Handle missing data according to specified method

        Args:
            data: Data array with potential NaN values
            method (str): Method for handling missing data

        Returns:
            Processed data array
        """
        # Convert to pandas Series for easier manipulation
        series = pd.Series(data)

        if method == MissingDataMethods.DROP:
            # Remove NaN values
            return series.dropna()
        elif method == MissingDataMethods.FILL_ZERO:
            # Replace NaN with zero
            return series.fillna(0)
        elif method == MissingDataMethods.FORWARD_FILL:
            # Forward fill (use previous valid value)
            return series.fillna(method='ffill')
        elif method == MissingDataMethods.INTERPOLATE:
            # Interpolate missing values
            return series.interpolate()
        else:
            # Return unchanged
            return series

    def apply_smoothing(self, data, smooth_factor):
        """
        Apply smoothing to data

        Args:
            data: Input data array
            smooth_factor (int): Smoothing strength (0-100)

        Returns:
            Smoothed data array
        """
        # Skip if no smoothing or insufficient data
        if smooth_factor == 0 or len(data) < 5:
            return data

        # Calculate window size based on smooth factor
        window_size = max(5, int(len(data) * smooth_factor / 100))

        # Ensure odd window size
        if window_size % 2 == 0:
            window_size += 1

        # Limit window size to data length
        window_size = min(window_size, len(data))

        try:
            # Apply Savitzky-Golay filter
            smoothed = savgol_filter(
                data,  # Input data
                window_size,  # Window length
                min(3, window_size - 1)  # Polynomial order
            )
            return smoothed
        except:
            # Return original if smoothing fails
            return data

    def add_trendline(self, x_data, y_data, series_config):
        """
        Add a trend line to the plot

        Args:
            x_data: X-axis data
            y_data: Y-axis data
            series_config: Series configuration with trend settings
        """
        try:
            # Convert to numeric arrays
            x_numeric = pd.to_numeric(x_data, errors='coerce')
            y_numeric = pd.to_numeric(y_data, errors='coerce')

            # Remove NaN values
            valid_mask = ~(x_numeric.isna() | y_numeric.isna())
            if valid_mask.sum() < 2:
                return  # Not enough data for trend

            x_valid = x_numeric[valid_mask].values
            y_valid = y_numeric[valid_mask].values

            # Create trend based on type
            if series_config.trend_type == TrendTypes.LINEAR:
                self.add_linear_trend(x_valid, y_valid, series_config)
            elif series_config.trend_type == TrendTypes.POLYNOMIAL:
                self.add_polynomial_trend(x_valid, y_valid, series_config)
            elif series_config.trend_type == TrendTypes.MOVING_AVERAGE:
                self.add_moving_average(x_valid, y_valid, series_config)

        except Exception as e:
            print(f"Failed to add trendline: {e}")

    def add_linear_trend(self, x_data, y_data, series_config):
        """
        Add linear regression trend line

        Args:
            x_data: X-axis numeric data
            y_data: Y-axis numeric data
            series_config: Series configuration
        """
        # Reshape for sklearn
        x_reshaped = x_data.reshape(-1, 1)

        # Fit linear regression
        model = LinearRegression()
        model.fit(x_reshaped, y_data)

        # Create trend line points
        x_trend = np.array([x_data.min(), x_data.max()]).reshape(-1, 1)
        y_trend = model.predict(x_trend)

        # Calculate R-squared
        r_squared = model.score(x_reshaped, y_data)

        # Plot trend line
        self.axes.plot(
            x_trend.flatten(),  # X points
            y_trend,  # Y points
            color=series_config.color,  # Same color as series
            linestyle='--',  # Dashed line
            linewidth=series_config.line_width * 0.8,  # Slightly thinner
            alpha=series_config.alpha * 0.7,  # Slightly transparent
            label=f"{series_config.name} trend (R²={r_squared:.3f})"  # Label with R²
        )

    def add_polynomial_trend(self, x_data, y_data, series_config):
        """
        Add polynomial trend line

        Args:
            x_data: X-axis numeric data
            y_data: Y-axis numeric data
            series_config: Series configuration
        """
        # Get polynomial degree
        degree = series_config.trend_params.get('degree', 2)

        # Fit polynomial
        coeffs = np.polyfit(x_data, y_data, degree)
        poly = np.poly1d(coeffs)

        # Create smooth trend line
        x_trend = np.linspace(x_data.min(), x_data.max(), 100)
        y_trend = poly(x_trend)

        # Plot trend line
        self.axes.plot(
            x_trend,  # X points
            y_trend,  # Y points
            color=series_config.color,  # Same color as series
            linestyle='--',  # Dashed line
            linewidth=series_config.line_width * 0.8,  # Slightly thinner
            alpha=series_config.alpha * 0.7,  # Slightly transparent
            label=f"{series_config.name} poly{degree}"  # Label with degree
        )

    def add_moving_average(self, x_data, y_data, series_config):
        """
        Add moving average line

        Args:
            x_data: X-axis data
            y_data: Y-axis data
            series_config: Series configuration
        """
        # Get window size
        window = series_config.trend_params.get('window', 20)

        # Calculate moving average
        ma = pd.Series(y_data).rolling(window=window, center=True).mean()

        # Plot moving average
        self.axes.plot(
            x_data,  # X points
            ma,  # Moving average values
            color=series_config.color,  # Same color as series
            linestyle='--',  # Dashed line
            linewidth=series_config.line_width * 0.8,  # Slightly thinner
            alpha=series_config.alpha * 0.7,  # Slightly transparent
            label=f"{series_config.name} MA({window})"  # Label with window size
        )

    def add_statistics_box(self, y_data, series_config):
        """
        Add statistics text box to plot

        Args:
            y_data: Y-axis data
            series_config: Series configuration
        """
        # Calculate statistics
        stats = DataAnalysisTools.calculate_statistics(y_data)

        # Create text for box
        stats_text = f"{series_config.name}\n"
        stats_text += f"Mean: {stats['mean']:.3e}\n"
        stats_text += f"Std: {stats['std']:.3e}\n"
        stats_text += f"Min: {stats['min']:.3e}\n"
        stats_text += f"Max: {stats['max']:.3e}"

        # Create text box properties
        props = dict(
            boxstyle='round',  # Rounded corners
            facecolor='wheat',  # Background color
            alpha=0.5  # Transparency
        )

        # Add text box to plot (upper left corner)
        self.axes.text(
            0.02,  # X position (2% from left)
            0.98,  # Y position (98% from bottom)
            stats_text,  # Text content
            transform=self.axes.transAxes,  # Use axes coordinates
            fontsize=9,  # Font size
            verticalalignment='top',  # Align to top
            bbox=props  # Box properties
        )

    def mark_peaks(self, x_data, y_data, series_config):
        """
        Mark peaks and valleys on the plot

        Args:
            x_data: X-axis data
            y_data: Y-axis data
            series_config: Series configuration
        """
        # Calculate prominence for peak detection
        data_range = np.max(y_data) - np.min(y_data)
        prominence = series_config.peak_prominence * data_range

        # Find peaks and valleys
        peak_results = DataAnalysisTools.find_peaks_and_valleys(
            np.array(x_data),
            np.array(y_data),
            prominence
        )

        # Mark peaks with upward triangles
        if len(peak_results['peaks']['indices']) > 0:
            self.axes.scatter(
                peak_results['peaks']['x_values'],  # X positions
                peak_results['peaks']['y_values'],  # Y positions
                marker='^',  # Upward triangle
                s=100,  # Size
                color='red',  # Color
                zorder=5,  # Draw order (on top)
                label=f'{series_config.name} peaks'  # Legend label
            )

        # Mark valleys with downward triangles
        if len(peak_results['valleys']['indices']) > 0:
            self.axes.scatter(
                peak_results['valleys']['x_values'],  # X positions
                peak_results['valleys']['y_values'],  # Y positions
                marker='v',  # Downward triangle
                s=100,  # Size
                color='blue',  # Color
                zorder=5,  # Draw order (on top)
                label=f'{series_config.name} valleys'  # Legend label
            )

    def configure_axes(self, config):
        """
        Configure plot axes with labels, scales, and styling

        Args:
            config (dict): Configuration dictionary
        """
        if not self.axes:
            return

        # Set title
        self.axes.set_title(
            config.get('title', 'Data Analysis'),  # Title text
            fontsize=config.get('title_size', 16),  # Font size
            fontweight='bold',  # Bold text
            pad=20  # Padding from plot
        )

        # Set axis labels
        self.axes.set_xlabel(
            config.get('xlabel', 'X Axis'),  # X label text
            fontsize=config.get('xlabel_size', 12)  # Font size
        )
        self.axes.set_ylabel(
            config.get('ylabel', 'Y Axis'),  # Y label text
            fontsize=config.get('ylabel_size', 12)  # Font size
        )

        # Configure grid
        if config.get('show_grid', True):
            self.axes.grid(
                True,  # Enable grid
                linestyle=config.get('grid_style', '-'),  # Line style
                alpha=config.get('grid_alpha', 0.3),  # Transparency
                which='both'  # Major and minor gridlines
            )
            self.axes.set_axisbelow(True)  # Draw grid below data

        # Configure legend
        if config.get('show_legend', True):
            # Get legend handles and labels
            handles, labels = self.axes.get_legend_handles_labels()

            # Filter out empty labels
            filtered = [(h, l) for h, l in zip(handles, labels) if l]

            if filtered:
                handles, labels = zip(*filtered)
                # Create legend
                self.axes.legend(
                    handles,  # Plot elements
                    labels,  # Labels
                    loc='best',  # Automatic positioning
                    frameon=True,  # Show frame
                    fancybox=True,  # Rounded corners
                    shadow=True,  # Drop shadow
                    fontsize=10  # Font size
                )

        # Set log scales if requested
        if config.get('log_scale_x', False):
            self.axes.set_xscale('log')  # Logarithmic X axis
        if config.get('log_scale_y', False):
            self.axes.set_yscale('log')  # Logarithmic Y axis

        # Set axis limits if specified
        if 'x_min' in config and 'x_max' in config:
            try:
                self.axes.set_xlim(float(config['x_min']), float(config['x_max']))
            except:
                pass  # Ignore invalid limits

        if 'y_min' in config and 'y_max' in config:
            try:
                self.axes.set_ylim(float(config['y_min']), float(config['y_max']))
            except:
                pass  # Ignore invalid limits

        # Apply tight layout
        self.figure.tight_layout()

    def format_datetime_axis(self):
        """Format X-axis for datetime data"""
        if not self.axes:
            return

        # Set date formatter
        self.axes.xaxis.set_major_formatter(
            mdates.DateFormatter('%Y-%m-%d %H:%M')  # Date format
        )

        # Set date locator
        self.axes.xaxis.set_major_locator(
            mdates.AutoDateLocator()  # Automatic date tick spacing
        )

        # Rotate labels for better readability
        self.figure.autofmt_xdate()

    def apply_theme(self, dark_mode=False):
        """
        Apply color theme to plot

        Args:
            dark_mode (bool): Whether to use dark theme
        """
        if dark_mode:
            # Dark theme colors
            plt.style.use('dark_background')
        else:
            # Light theme colors
            plt.style.use('seaborn-v0_8-whitegrid')

    def get_figure(self):
        """
        Get the current matplotlib figure

        Returns:
            Figure: Current figure or None
        """
        return self.figure

    def get_axes(self):
        """
        Get the current matplotlib axes

        Returns:
            Axes: Current axes or None
        """
        return self.axes