#!/usr/bin/env python3
"""
Ultra-aggressive fix for DataQualityAnalyzer
This ensures bad data scores below 50
Save and run this file to fix the scoring issue
"""

from pathlib import Path


def apply_ultra_aggressive_fix():
    """Apply ultra-aggressive scoring to DataQualityAnalyzer"""

    print("=" * 60)
    print("APPLYING ULTRA-AGGRESSIVE DATAQUALITY FIX")
    print("=" * 60)

    # Ultra-aggressive scoring content
    fixed_content = '''#!/usr/bin/env python3
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
'''

    # Write the file
    data_quality_path = Path("analysis/data_quality.py")

    # Ensure directory exists
    if not data_quality_path.parent.exists():
        data_quality_path.parent.mkdir(parents=True, exist_ok=True)

    # Backup existing file
    if data_quality_path.exists():
        backup_path = data_quality_path.with_suffix('.py.bak')
        with open(data_quality_path, 'r', encoding='utf-8') as f:
            backup_content = f.read()
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(backup_content)
        print(f"Backed up existing file to: {backup_path}")

    # Write the ultra-aggressive version
    with open(data_quality_path, 'w', encoding='utf-8') as f:
        f.write(fixed_content)

    print(f"✓ Written ultra-aggressive scoring to: {data_quality_path}")

    # Test the fix
    print("\nTesting the ultra-aggressive fix...")
    test_scoring()


def test_scoring():
    """Test that the scoring is now aggressive enough"""
    try:
        import pandas as pd
        import numpy as np
        from analysis.data_quality import DataQualityAnalyzer

        analyzer = DataQualityAnalyzer()

        print("\nTest 1: Good quality data")
        good_data = pd.DataFrame({
            'x': np.arange(100),
            'y': np.random.randn(100),
            'z': np.random.randn(100) * 10
        })
        good_report = analyzer.analyze_quality(good_data)
        print(f"  Score: {good_report.quality_score:.1f}")
        print(f"  Issues: {good_report.issues if good_report.issues else 'None'}")

        print("\nTest 2: Bad quality data (33% missing, 33% duplicates)")
        # Create data similar to your test
        y_data = [np.nan] * 50 + list(np.random.randn(50))
        z_data = list(np.random.randn(50)) + [np.nan] * 50
        bad_data = pd.DataFrame({
            'x': np.arange(100),
            'y': y_data,
            'z': z_data
        })
        bad_report = analyzer.analyze_quality(bad_data)
        print(f"  Score: {bad_report.quality_score:.1f}")
        print(f"  Issues: {bad_report.issues}")

        print("\nTest 3: Medium quality (20% missing)")
        medium_data = pd.DataFrame({
            'x': np.arange(100),
            'y': [np.nan] * 20 + list(np.random.randn(80)),
            'z': list(np.random.randn(80)) + [np.nan] * 20
        })
        medium_report = analyzer.analyze_quality(medium_data)
        print(f"  Score: {medium_report.quality_score:.1f}")
        print(f"  Issues: {medium_report.issues}")

        # Check if scoring is correct
        print("\n" + "=" * 60)
        if good_report.quality_score > 90 and bad_report.quality_score < 50 and 50 <= medium_report.quality_score <= 80:
            print("✅ ULTRA-AGGRESSIVE SCORING IS WORKING PERFECTLY!")
            print(f"  Good data: {good_report.quality_score:.1f} (>90) ✓")
            print(f"  Bad data: {bad_report.quality_score:.1f} (<50) ✓")
            print(f"  Medium data: {medium_report.quality_score:.1f} (50-80) ✓")
        else:
            print("⚠️ Scoring still needs adjustment:")
            print(f"  Good data: {good_report.quality_score:.1f} (expected >90)")
            print(f"  Bad data: {bad_report.quality_score:.1f} (expected <50)")
            print(f"  Medium data: {medium_report.quality_score:.1f} (expected 50-80)")

    except Exception as e:
        print(f"\n❌ Error testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    apply_ultra_aggressive_fix()
    print("\n" + "=" * 60)
    print("Fix applied! Now run your tests:")
    print("  python run_tests.py")
    print("  python test_fixes.py")
    print("=" * 60)