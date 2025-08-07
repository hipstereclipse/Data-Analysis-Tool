#!/usr/bin/env python3
"""
Unit tests for data models
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

from models.data_models import FileData, SeriesConfig, AnnotationConfig
from models.project_models import Project


class TestFileData(unittest.TestCase):
    """Test FileData model"""

    def setUp(self):
        """Set up test data"""
        self.df = pd.DataFrame({
            'x': np.arange(100),
            'y': np.random.randn(100),
            'z': np.random.randn(100)
        })
        self.filepath = "test.csv"

    def test_file_data_creation(self):
        """Test FileData creation"""
        file_data = FileData(self.filepath, self.df)

        self.assertEqual(file_data.filepath, self.filepath)
        self.assertEqual(file_data.filename, "test.csv")
        self.assertIsNotNone(file_data.id)
        self.assertTrue(isinstance(file_data.load_time, datetime))

    def test_metadata_analysis(self):
        """Test metadata analysis"""
        file_data = FileData(self.filepath, self.df)

        self.assertEqual(file_data.metadata['rows'], 100)
        self.assertEqual(file_data.metadata['columns'], 3)
        self.assertTrue(file_data.metadata['has_numeric'])

    def test_get_numeric_columns(self):
        """Test numeric column detection"""
        file_data = FileData(self.filepath, self.df)
        numeric_cols = file_data.get_numeric_columns()

        self.assertEqual(len(numeric_cols), 3)
        self.assertIn('x', numeric_cols)
        self.assertIn('y', numeric_cols)


class TestSeriesConfig(unittest.TestCase):
    """Test SeriesConfig model"""

    def test_series_creation(self):
        """Test SeriesConfig creation"""
        series = SeriesConfig(
            name="Test Series",
            file_id="file123",
            x_column="x",
            y_column="y"
        )

        self.assertEqual(series.name, "Test Series")
        self.assertEqual(series.file_id, "file123")
        self.assertEqual(series.x_column, "x")
        self.assertEqual(series.y_column, "y")
        self.assertIsNotNone(series.id)

    def test_series_defaults(self):
        """Test default values"""
        series = SeriesConfig(
            name="Test",
            file_id="file123",
            x_column="x",
            y_column="y"
        )

        self.assertEqual(series.start_index, 0)
        self.assertIsNone(series.end_index)
        self.assertTrue(series.visible)
        self.assertTrue(series.show_in_legend)
        self.assertEqual(series.line_style, '-')
        self.assertEqual(series.line_width, 1.5)

    def test_get_data(self):
        """Test data extraction"""
        df = pd.DataFrame({
            'x': np.arange(10),
            'y': np.arange(10, 20)
        })
        file_data = FileData("test.csv", df)

        series = SeriesConfig(
            name="Test",
            file_id=file_data.id,
            x_column="x",
            y_column="y",
            start_index=2,
            end_index=8
        )

        x_data, y_data = series.get_data(file_data)

        self.assertEqual(len(x_data), 6)
        self.assertEqual(x_data[0], 2)
        self.assertEqual(y_data[0], 12)


class TestProject(unittest.TestCase):
    """Test Project model"""

    def test_project_creation(self):
        """Test Project creation"""
        project = Project(
            name="Test Project",
            description="Test description"
        )

        self.assertEqual(project.name, "Test Project")
        self.assertEqual(project.description, "Test description")
        self.assertIsInstance(project.files, dict)
        self.assertIsInstance(project.series, dict)
        self.assertIsInstance(project.annotations, dict)

    def test_add_file(self):
        """Test adding file to project"""
        project = Project()
        df = pd.DataFrame({'x': [1, 2, 3]})
        file_data = FileData("test.csv", df)

        project.add_file(file_data)

        self.assertIn(file_data.id, project.files)
        self.assertEqual(project.files[file_data.id], file_data)

    def test_add_series(self):
        """Test adding series to project"""
        project = Project()
        series = SeriesConfig(
            name="Test",
            file_id="file123",
            x_column="x",
            y_column="y"
        )

        project.add_series(series)

        self.assertIn(series.id, project.series)
        self.assertEqual(project.series[series.id], series)

    def test_project_statistics(self):
        """Test project statistics"""
        project = Project()

        # Add some data
        df = pd.DataFrame({'x': np.arange(10), 'y': np.arange(10)})
        file_data = FileData("test.csv", df)
        project.add_file(file_data)

        series = SeriesConfig(
            name="Test",
            file_id=file_data.id,
            x_column="x",
            y_column="y"
        )
        project.add_series(series)

        stats = project.get_statistics()

        self.assertEqual(stats['file_count'], 1)
        self.assertEqual(stats['series_count'], 1)
        self.assertEqual(stats['total_rows'], 10)


if __name__ == '__main__':
    unittest.main()