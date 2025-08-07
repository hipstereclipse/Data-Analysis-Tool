#!/usr/bin/env python3
"""
Project save/load functionality
"""

import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import pickle
import gzip

from models.project_models import Project
from models.data_models import FileData, SeriesConfig, AnnotationConfig

logger = logging.getLogger(__name__)


class ProjectManager:
    """Manages project persistence"""

    def __init__(self):
        self.current_project_path: Optional[Path] = None
        self.autosave_enabled = False
        self.compression_enabled = True

    def save_project(self, project: Project, filepath: str):
        """
        Save project to file

        Args:
            project: Project object to save
            filepath: Target file path
        """
        filepath = Path(filepath)

        # Ensure .edp extension
        if filepath.suffix != '.edp':
            filepath = filepath.with_suffix('.edp')

        try:
            # Prepare project data
            project_dict = self._project_to_dict(project)

            # Add metadata
            project_dict['metadata'] = {
                'version': project.version,
                'created_at': project.created_at.isoformat(),
                'modified_at': datetime.now().isoformat(),
                'application': 'Excel Data Plotter',
                'app_version': '5.0.0'
            }

            # Save with compression if enabled
            if self.compression_enabled:
                with gzip.open(filepath, 'wt', encoding='utf-8') as f:
                    json.dump(project_dict, f, indent=2)
            else:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(project_dict, f, indent=2)

            self.current_project_path = filepath
            logger.info(f"Project saved to: {filepath}")

        except Exception as e:
            logger.error(f"Failed to save project: {e}")
            raise

    def load_project(self, filepath: str) -> Project:
        """
        Load project from file

        Args:
            filepath: Project file path

        Returns:
            Loaded Project object
        """
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"Project file not found: {filepath}")

        try:
            # Try to load with compression first
            try:
                with gzip.open(filepath, 'rt', encoding='utf-8') as f:
                    project_dict = json.load(f)
            except:
                # Fallback to uncompressed
                with open(filepath, 'r', encoding='utf-8') as f:
                    project_dict = json.load(f)

            # Create Project object
            project = self._dict_to_project(project_dict)

            self.current_project_path = filepath
            logger.info(f"Project loaded from: {filepath}")

            return project

        except Exception as e:
            logger.error(f"Failed to load project: {e}")
            raise

    def _project_to_dict(self, project: Project) -> Dict[str, Any]:
        """Convert Project object to dictionary"""
        return {
            'name': project.name,
            'description': project.description,
            'files': self._serialize_files(project.files),
            'series': self._serialize_series(project.series),
            'annotations': self._serialize_annotations(project.annotations),
            'config': project.config
        }

    def _dict_to_project(self, data: Dict[str, Any]) -> Project:
        """Convert dictionary to Project object"""
        project = Project(
            name=data.get('name', 'Untitled'),
            description=data.get('description', '')
        )

        # Restore files
        project.files = self._deserialize_files(data.get('files', {}))

        # Restore series
        project.series = self._deserialize_series(data.get('series', {}))

        # Restore annotations
        project.annotations = self._deserialize_annotations(data.get('annotations', {}))

        # Restore config
        project.config = data.get('config', {})

        # Restore metadata if available
        if 'metadata' in data:
            metadata = data['metadata']
            if 'created_at' in metadata:
                project.created_at = datetime.fromisoformat(metadata['created_at'])
            if 'version' in metadata:
                project.version = metadata['version']

        return project

    def _serialize_files(self, files: Dict[str, FileData]) -> Dict[str, Any]:
        """Serialize file data for saving"""
        serialized = {}

        for file_id, file_data in files.items():
            # Save file reference and minimal data
            serialized[file_id] = {
                'id': file_id,
                'filepath': file_data.filepath,
                'filename': file_data.filename,
                'load_time': file_data.load_time.isoformat(),
                'metadata': file_data.metadata,
                # Option to embed small datasets
                'embedded': False
            }

            # For small files, optionally embed data
            if file_data.metadata['rows'] < 1000:
                serialized[file_id]['embedded'] = True
                serialized[file_id]['data'] = file_data.dataframe.to_dict('records')

        return serialized

    def _deserialize_files(self, data: Dict[str, Any]) -> Dict[str, FileData]:
        """Deserialize file data"""
        import pandas as pd

        files = {}

        for file_id, file_dict in data.items():
            filepath = file_dict['filepath']

            # Check if data is embedded
            if file_dict.get('embedded') and 'data' in file_dict:
                # Use embedded data
                df = pd.DataFrame(file_dict['data'])
                file_data = FileData(filepath, df)
            else:
                # Load from file path
                if Path(filepath).exists():
                    from core.file_manager import FileManager
                    fm = FileManager()
                    try:
                        file_data = fm.load_file(filepath)
                    except Exception as e:
                        logger.warning(f"Could not load file {filepath}: {e}")
                        # Create placeholder
                        df = pd.DataFrame()
                        file_data = FileData(filepath, df)
                else:
                    logger.warning(f"File not found: {filepath}")
                    # Create placeholder
                    df = pd.DataFrame()
                    file_data = FileData(filepath, df)

            # Restore ID and metadata
            file_data.id = file_id
            if 'load_time' in file_dict:
                file_data.load_time = datetime.fromisoformat(file_dict['load_time'])

            files[file_id] = file_data

        return files

    def _serialize_series(self, series: Dict[str, SeriesConfig]) -> Dict[str, Any]:
        """Serialize series configurations"""
        serialized = {}

        for series_id, series_config in series.items():
            serialized[series_id] = {
                'id': series_id,
                'name': series_config.name,
                'file_id': series_config.file_id,
                'x_column': series_config.x_column,
                'y_column': series_config.y_column,
                'start_index': series_config.start_index,
                'end_index': series_config.end_index,
                'color': series_config.color,
                'line_style': series_config.line_style,
                'line_width': series_config.line_width,
                'marker': series_config.marker,
                'marker_size': series_config.marker_size,
                'alpha': series_config.alpha,
                'visible': series_config.visible,
                'show_in_legend': series_config.show_in_legend,
                'legend_label': series_config.legend_label,
                'missing_data_method': series_config.missing_data_method,
                'smoothing_enabled': series_config.smoothing_enabled,
                'smoothing_window': series_config.smoothing_window,
                'show_trendline': series_config.show_trendline,
                'trend_type': series_config.trend_type,
                'trend_order': series_config.trend_order,
                'show_statistics': series_config.show_statistics,
                'show_peaks': series_config.show_peaks,
                'peak_prominence': series_config.peak_prominence
            }

        return serialized

    def _deserialize_series(self, data: Dict[str, Any]) -> Dict[str, SeriesConfig]:
        """Deserialize series configurations"""
        series = {}

        for series_id, series_dict in data.items():
            series_config = SeriesConfig(
                name=series_dict['name'],
                file_id=series_dict['file_id'],
                x_column=series_dict['x_column'],
                y_column=series_dict['y_column']
            )

            # Restore all properties
            series_config.id = series_id
            for key, value in series_dict.items():
                if hasattr(series_config, key):
                    setattr(series_config, key, value)

            series[series_id] = series_config

        return series

    def _serialize_annotations(self, annotations: Dict[str, AnnotationConfig]) -> List[Dict[str, Any]]:
        """Serialize annotations"""
        serialized = []

        for ann_id, ann in annotations.items():
            serialized.append({
                'id': ann_id,
                'type': ann.type,
                'label': ann.label,
                'color': ann.color,
                'alpha': ann.alpha,
                'line_width': ann.line_width,
                'line_style': ann.line_style,
                'x_data': ann.x_data,
                'y_data': ann.y_data,
                'x_end': ann.x_end,
                'y_end': ann.y_end,
                'text': ann.text,
                'fontsize': ann.fontsize,
                'visible': ann.visible
            })

        return serialized

    def _deserialize_annotations(self, data: List[Dict[str, Any]]) -> Dict[str, AnnotationConfig]:
        """Deserialize annotations"""
        annotations = {}

        for ann_dict in data:
            ann = AnnotationConfig(
                type=ann_dict['type'],
                label=ann_dict.get('label', ''),
                color=ann_dict.get('color', 'red'),
                alpha=ann_dict.get('alpha', 0.7),
                line_width=ann_dict.get('line_width', 2),
                line_style=ann_dict.get('line_style', '-'),
                x_data=ann_dict.get('x_data'),
                y_data=ann_dict.get('y_data'),
                x_end=ann_dict.get('x_end'),
                y_end=ann_dict.get('y_end'),
                text=ann_dict.get('text'),
                fontsize=ann_dict.get('fontsize', 10),
                visible=ann_dict.get('visible', True)
            )

            if 'id' in ann_dict:
                ann.id = ann_dict['id']
                annotations[ann.id] = ann
            else:
                annotations[ann.id] = ann

        return annotations

    def export_project_summary(self, project: Project, filepath: str):
        """Export project summary as text"""
        filepath = Path(filepath)

        summary = []
        summary.append(f"PROJECT SUMMARY: {project.name}")
        summary.append("=" * 60)
        summary.append(f"Created: {project.created_at}")
        summary.append(f"Description: {project.description}")
        summary.append("")

        summary.append("FILES:")
        summary.append("-" * 40)
        for file_data in project.files.values():
            summary.append(f"  • {file_data.filename}")
            summary.append(f"    Path: {file_data.filepath}")
            summary.append(f"    Size: {file_data.metadata['rows']} × {file_data.metadata['columns']}")
        summary.append("")

        summary.append("SERIES:")
        summary.append("-" * 40)
        for series in project.series.values():
            file_name = "Unknown"
            if series.file_id in project.files:
                file_name = project.files[series.file_id].filename

            summary.append(f"  • {series.name}")
            summary.append(f"    File: {file_name}")
            summary.append(f"    Data: {series.x_column} vs {series.y_column}")
            summary.append(f"    Visible: {series.visible}")
        summary.append("")

        summary.append("ANNOTATIONS:")
        summary.append("-" * 40)
        summary.append(f"  Total: {len(project.annotations)}")

        # Write summary
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("\n".join(summary))

        logger.info(f"Project summary exported to: {filepath}")
