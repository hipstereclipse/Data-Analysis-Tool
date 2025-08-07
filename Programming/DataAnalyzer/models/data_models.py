#!/usr/bin/env python3
"""
Core data models
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np


@dataclass
class FileData:
    """Represents a loaded data file"""
    filepath: str
    dataframe: pd.DataFrame
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    filename: str = field(init=False)
    load_time: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Post-initialization processing"""
        from pathlib import Path
        self.filename = Path(self.filepath).name
        self._analyze_data()

    def _analyze_data(self):
        """Analyze dataframe and store metadata"""
        self.metadata = {
            'rows': len(self.dataframe),
            'columns': len(self.dataframe.columns),
            'memory_usage': self.dataframe.memory_usage(deep=True).sum(),
            'dtypes': self.dataframe.dtypes.to_dict(),
            'has_datetime': self._has_datetime_columns(),
            'has_numeric': self._has_numeric_columns(),
            'null_counts': self.dataframe.isnull().sum().to_dict()
        }

    def _has_datetime_columns(self) -> bool:
        """Check if dataframe has datetime columns"""
        return any(pd.api.types.is_datetime64_any_dtype(dtype)
                   for dtype in self.dataframe.dtypes)

    def _has_numeric_columns(self) -> bool:
        """Check if dataframe has numeric columns"""
        return any(pd.api.types.is_numeric_dtype(dtype)
                   for dtype in self.dataframe.dtypes)

    def get_numeric_columns(self) -> List[str]:
        """Get list of numeric column names"""
        return [col for col in self.dataframe.columns
                if pd.api.types.is_numeric_dtype(self.dataframe[col])]

    def get_datetime_columns(self) -> List[str]:
        """Get list of datetime column names"""
        return [col for col in self.dataframe.columns
                if pd.api.types.is_datetime64_any_dtype(self.dataframe[col])]

    def get_column_stats(self, column: str) -> Dict[str, Any]:
        """Get statistics for a specific column"""
        if column not in self.dataframe.columns:
            return {}

        data = self.dataframe[column].dropna()

        if pd.api.types.is_numeric_dtype(data):
            return {
                'mean': float(data.mean()),
                'median': float(data.median()),
                'std': float(data.std()),
                'min': float(data.min()),
                'max': float(data.max()),
                'q1': float(data.quantile(0.25)),
                'q3': float(data.quantile(0.75))
            }
        else:
            return {
                'unique': int(data.nunique()),
                'most_common': data.mode().iloc[0] if not data.mode().empty else None,
                'type': str(data.dtype)
            }


@dataclass
class SeriesConfig:
    """Configuration for a data series"""
    name: str
    file_id: str
    x_column: str
    y_column: str

    # Data range
    start_index: int = 0
    end_index: Optional[int] = None

    # Visual properties
    color: Optional[str] = None
    line_style: str = '-'
    line_width: float = 1.5
    marker: Optional[str] = None
    marker_size: float = 6
    alpha: float = 1.0

    # Display options
    visible: bool = True
    show_in_legend: bool = True
    legend_label: Optional[str] = None

    # Data processing
    missing_data_method: str = 'drop'
    smoothing_enabled: bool = False
    smoothing_window: int = 5

    # Trend line
    show_trendline: bool = False
    trend_type: str = 'linear'
    trend_order: int = 2

    # Analysis features
    show_statistics: bool = False
    show_peaks: bool = False
    peak_prominence: float = 0.1

    # Metadata
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Post-initialization setup"""
        if not self.legend_label:
            self.legend_label = self.name

    def get_data(self, file_data: 'FileData') -> tuple:
        """Extract x and y data from file"""
        df = file_data.dataframe

        # Apply index range
        start = self.start_index
        end = self.end_index if self.end_index else len(df)
        df_slice = df.iloc[start:end]

        # Get x data
        if self.x_column == 'Index':
            x_data = np.arange(start, end)
        else:
            x_data = df_slice[self.x_column].values

        # Get y data
        y_data = df_slice[self.y_column].values

        return x_data, y_data

    def validate(self, file_data: 'FileData') -> List[str]:
        """Validate series configuration"""
        errors = []

        if self.x_column != 'Index' and self.x_column not in file_data.dataframe.columns:
            errors.append(f"X column '{self.x_column}' not found")

        if self.y_column not in file_data.dataframe.columns:
            errors.append(f"Y column '{self.y_column}' not found")

        if self.start_index < 0:
            errors.append("Start index cannot be negative")

        if self.end_index and self.end_index <= self.start_index:
            errors.append("End index must be greater than start index")

        return errors


@dataclass
class AnnotationConfig:
    """Configuration for plot annotations"""
    type: str  # 'line', 'region', 'text', 'arrow', 'point'
    label: str = ""

    # Visual properties
    color: str = "red"
    alpha: float = 0.7
    line_width: float = 2
    line_style: str = "-"

    # Position data (varies by type)
    x_data: Optional[Any] = None
    y_data: Optional[Any] = None
    x_end: Optional[Any] = None
    y_end: Optional[Any] = None

    # Text properties
    text: Optional[str] = None
    fontsize: int = 10

    # Metadata
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    visible: bool = True
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class AnalysisResult:
    """Results from data analysis"""
    analysis_type: str
    series_id: str
    timestamp: datetime = field(default_factory=datetime.now)

    # Results storage
    statistics: Dict[str, float] = field(default_factory=dict)
    data: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Visualization data
    figure_data: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'analysis_type': self.analysis_type,
            'series_id': self.series_id,
            'timestamp': self.timestamp.isoformat(),
            'statistics': self.statistics,
            'metadata': self.metadata
        }