#!/usr/bin/env python3
"""
Data quality analysis and validation - ULTRA AGGRESSIVE SCORING
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class QualityReport:
    """Data quality analysis report"""
    total_points: int = 0
    valid_points: int = 0
    missing_points: int = 0
    zeros: List[int] = field(default_factory=list)
    outliers: List[int] = field(default_factory=list)
    duplicates: List[int] = field(default_factory=list)
    gaps: List[int] = field(default_factory=list)
    noise_level: float = 0.0
    quality_score: float = 100.0
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)

    completeness: float = 0.0
    consistency: float = 0.0
    validity: float = 0.0


class DataQualityAnalyzer:
    """Analyzes data quality and identifies issues"""

    def __init__(self):
        self.config = {
            'zero_threshold': 1e-10,
            'outlier_method': 'iqr',
            'outlier_threshold': 3.0,
            'duplicate_threshold': 1e-6,
            'gap_threshold': 10,
            'noise_window': 50
        }

    def analyze_quality(self, data: pd.DataFrame) -> QualityReport:
        """Analyze quality of DataFrame data - ULTRA AGGRESSIVE SCORING"""
        report = QualityReport()

        if isinstance(data, pd.DataFrame):
            # Get numeric columns
            numeric_cols = data.select_dtypes(include=[np.number]).columns

            if len(numeric_cols) == 0:
                report.total_points = len(data)
                report.valid_points = 0
                report.missing_points = len(data)
                report.issues.append("No numeric columns found")
                report.quality_score = 0
                return report

            # Analyze all numeric columns for issues
            total_cells = 0
            total_missing = 0
            total_zeros = 0
            total_outliers = 0
            total_duplicates = 0

            for col in numeric_cols:
                col_data = data[col]
                total_cells += len(col_data)

                # Count missing values
                missing = col_data.isna().sum()
                total_missing += missing

                # Count zeros
                zeros = (col_data == 0).sum()
                total_zeros += zeros

                # Detect outliers using IQR
                valid_data = col_data.dropna()
                if len(valid_data) > 0:
                    q1 = valid_data.quantile(0.25)
                    q3 = valid_data.quantile(0.75)
                    iqr = q3 - q1
                    if iqr > 0:
                        lower = q1 - 1.5 * iqr
                        upper = q3 + 1.5 * iqr
                        outliers = ((valid_data < lower) | (valid_data > upper)).sum()
                        total_outliers += outliers

                # Count duplicates
                duplicates = col_data.duplicated().sum()
                total_duplicates += duplicates

            # Calculate percentages
            missing_pct = (total_missing / total_cells) * 100 if total_cells > 0 else 0
            zeros_pct = (total_zeros / total_cells) * 100 if total_cells > 0 else 0
            outliers_pct = (total_outliers / total_cells) * 100 if total_cells > 0 else 0
            duplicates_pct = (total_duplicates / total_cells) * 100 if total_cells > 0 else 0

            # ULTRA AGGRESSIVE SCORING - Ensure bad data fails
            score = 100.0

            # ULTRA HEAVY penalty for missing data
            if missing_pct > 0:
                # 3 points per percent for first 25%, then 1 point per percent
                if missing_pct <= 25:
                    penalty = missing_pct * 3.0
                else:
                    penalty = 75 + (missing_pct - 25) * 1.0
                score -= min(90, penalty)
                report.issues.append(f"{missing_pct:.1f}% missing values")

            # ULTRA HEAVY penalty for duplicates
            if duplicates_pct > 5:
                # 2 points per percent over 5%
                penalty = (duplicates_pct - 5) * 2.0
                score -= min(50, penalty)
                report.issues.append(f"{duplicates_pct:.1f}% duplicate values")
            elif duplicates_pct > 0:
                # Still penalize small amounts
                score -= duplicates_pct * 0.5
                if duplicates_pct > 1:
                    report.issues.append(f"{duplicates_pct:.1f}% duplicate values")

            # Penalty for zeros
            if zeros_pct > 10:
                penalty = (zeros_pct - 10) * 0.5
                score -= min(15, penalty)
                report.issues.append(f"{zeros_pct:.1f}% zero values")

            # Penalty for outliers
            if outliers_pct > 5:
                penalty = (outliers_pct - 5) * 1.0
                score -= min(15, penalty)
                report.issues.append(f"{outliers_pct:.1f}% outliers")

            # Ensure score doesn't go below 0
            score = max(0, score)

            # Fill report
            report.total_points = total_cells
            report.valid_points = total_cells - total_missing
            report.missing_points = total_missing
            report.quality_score = score

            # Add statistics
            report.statistics = {
                'missing_pct': missing_pct,
                'zeros_pct': zeros_pct,
                'outliers_pct': outliers_pct,
                'duplicates_pct': duplicates_pct
            }

            # Add recommendations based on score
            if score < 50:
                report.recommendations.append("Data quality is poor - consider cleaning before analysis")
            elif score < 70:
                report.recommendations.append("Data quality is moderate - review problematic areas")
            elif score < 90:
                report.recommendations.append("Data quality is good - minor issues detected")
            else:
                report.recommendations.append("Data quality is excellent")

        else:
            # Handle Series data
            series_data = pd.Series(data) if not isinstance(data, pd.Series) else data

            total = len(series_data)
            missing = series_data.isna().sum()
            missing_pct = (missing / total) * 100 if total > 0 else 0

            # Ultra aggressive for Series too
            score = 100.0
            if missing_pct > 0:
                if missing_pct <= 25:
                    penalty = missing_pct * 3.0
                else:
                    penalty = 75 + (missing_pct - 25) * 1.0
                score -= min(95, penalty)
            score = max(0, score)

            report.total_points = total
            report.valid_points = total - missing
            report.missing_points = missing
            report.quality_score = score

            if missing_pct > 0:
                report.issues.append(f"{missing_pct:.1f}% missing values")

        return report
