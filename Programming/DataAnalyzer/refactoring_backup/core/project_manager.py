#!/usr/bin/env python3
"""
core/project_manager.py - Project Manager
Handles project saving, loading, and management
"""

import json
import pickle
from pathlib import Path
from typing import Optional, Dict, List
import logging
from datetime import datetime
import uuid

from models.project_models import Project, ProjectMetadata, RecentProjects
from models.data_models import FileData, SeriesConfig, AnnotationConfig, PlotConfiguration
from core.file_manager import FileManager

logger = logging.getLogger(__name__)


class ProjectManager:
    """
    Manages project operations including saving and loading
    """

    def __init__(self):
        """Initialize project manager"""
        self.file_manager = FileManager()
        self.recent_projects = RecentProjects()
        self.current_project: Optional[Project] = None
        self.project_modified = False

    def create_new_project(self, name: str = "Untitled Project") -> Project:
        """
        Create a new project

        Args:
            name: Project name

        Returns:
            New Project object
        """
        project = Project(
            project_id=str(uuid.uuid4())[:8],
            name=name,
            created_date=datetime.now(),
            modified_date=datetime.now()
        )

        self.current_project = project
        self.project_modified = False

        logger.info(f"Created new project: {name}")
        return project

    def save_project(self, project: Project, filepath: str) -> bool:
        """
        Save project to file

        Args:
            project: Project to save
            filepath: Path to save file

        Returns:
            True if successful
        """
        try:
            path = Path(filepath)

            # Ensure .edp extension
            if path.suffix.lower() != '.edp':
                path = path.with_suffix('.edp')

            # Update modified date
            project.update_modified_date()

            # Create project data dictionary
            project_data = project.to_dict()

            # Save file data separately (in same directory)
            data_dir = path.parent / f"{path.stem}_data"
            data_dir.mkdir(exist_ok=True)

            # Save each file's data
            for file_id, file_data in project.files.items():
                data_file = data_dir / f"{file_id}.pkl"
                with open(data_file, 'wb') as f:
                    pickle.dump(file_data, f)

            # Save project metadata
            with open(path, 'w') as f:
                json.dump(project_data, f, indent=2)

            # Update recent projects
            metadata = ProjectMetadata.from_project(project, str(path))
            self.recent_projects.add_project(metadata)

            self.project_modified = False
            logger.info(f"Saved project to {path}")

            return True

        except Exception as e:
            logger.error(f"Failed to save project: {e}")
            return False

    def load_project(self, filepath: str) -> Optional[Project]:
        """
        Load project from file

        Args:
            filepath: Path to project file

        Returns:
            Project object if successful
        """
        try:
            path = Path(filepath)

            if not path.exists():
                logger.error(f"Project file not found: {filepath}")
                return None

            # Load project metadata
            with open(path, 'r') as f:
                project_data = json.load(f)

            # Create project from data
            project = Project.from_dict(project_data)

            # Load file data
            data_dir = path.parent / f"{path.stem}_data"

            if data_dir.exists():
                for file_ref in project_data.get('file_references', {}).values():
                    file_id = file_ref['file_id']
                    data_file = data_dir / f"{file_id}.pkl"

                    if data_file.exists():
                        with open(data_file, 'rb') as f:
                            file_data = pickle.load(f)
                            project.files[file_id] = file_data
                    else:
                        # Try to reload from original path
                        original_path = file_ref['filepath']
                        if Path(original_path).exists():
                            file_data = self.file_manager.load_file(original_path)
                            if file_data:
                                file_data.file_id = file_id
                                project.files[file_id] = file_data

            # Update recent projects
            metadata = ProjectMetadata.from_project(project, str(path))
            self.recent_projects.add_project(metadata)

            self.current_project = project
            self.project_modified = False

            logger.info(f"Loaded project from {path}")
            return project

        except Exception as e:
            logger.error(f"Failed to load project: {e}")
            return None

    def export_project(self, project: Project, filepath: str,
                       include_data: bool = True) -> bool:
        """
        Export project to a portable format

        Args:
            project: Project to export
            filepath: Path to export file
            include_data: Whether to include data files

        Returns:
            True if successful
        """
        try:
            import zipfile

            path = Path(filepath)

            # Ensure .zip extension for export
            if path.suffix.lower() != '.zip':
                path = path.with_suffix('.zip')

            with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Save project metadata
                project_data = project.to_dict()
                zipf.writestr('project.json', json.dumps(project_data, indent=2))

                # Save data files if requested
                if include_data:
                    for file_id, file_data in project.files.items():
                        # Save as CSV for portability
                        csv_data = file_data.data.to_csv(index=False)
                        zipf.writestr(f"data/{file_id}.csv", csv_data)

                # Save summary
                summary = project.get_summary()
                zipf.writestr('README.txt', summary)

            logger.info(f"Exported project to {path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export project: {e}")
            return False

    def import_project(self, filepath: str) -> Optional[Project]:
        """
        Import project from exported format

        Args:
            filepath: Path to exported project file

        Returns:
            Project object if successful
        """
        try:
            import zipfile

            path = Path(filepath)

            with zipfile.ZipFile(path, 'r') as zipf:
                # Load project metadata
                project_json = zipf.read('project.json').decode('utf-8')
                project_data = json.loads(project_json)

                # Create project
                project = Project.from_dict(project_data)

                # Load data files
                for name in zipf.namelist():
                    if name.startswith('data/') and name.endswith('.csv'):
                        file_id = Path(name).stem
                        csv_data = zipf.read(name).decode('utf-8')

                        # Create DataFrame from CSV
                        import io
                        df = pd.read_csv(io.StringIO(csv_data))

                        # Create FileData object
                        file_ref = project_data['file_references'].get(file_id, {})
                        file_data = FileData(
                            file_id=file_id,
                            filepath="imported",
                            filename=file_ref.get('filename', f"file_{file_id}"),
                            data=df
                        )

                        project.files[file_id] = file_data

            logger.info(f"Imported project from {path}")
            return project

        except Exception as e:
            logger.error(f"Failed to import project: {e}")
            return None

    def get_recent_projects(self) -> List[ProjectMetadata]:
        """Get list of recent projects"""
        return self.recent_projects.get_recent()

    def clear_recent_projects(self):
        """Clear recent projects list"""
        self.recent_projects.clear()

    def autosave_project(self, project: Project) -> bool:
        """
        Autosave project to temporary location

        Args:
            project: Project to autosave

        Returns:
            True if successful
        """
        try:
            # Create autosave directory
            autosave_dir = Path.home() / '.excel_data_plotter' / 'autosave'
            autosave_dir.mkdir(parents=True, exist_ok=True)

            # Create autosave filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            autosave_file = autosave_dir / f"autosave_{project.project_id}_{timestamp}.edp"

            # Save project
            success = self.save_project(project, str(autosave_file))

            if success:
                # Clean old autosaves (keep last 5)
                autosaves = sorted(autosave_dir.glob(f"autosave_{project.project_id}_*.edp"))
                if len(autosaves) > 5:
                    for old_file in autosaves[:-5]:
                        try:
                            old_file.unlink()
                            # Also remove data directory
                            data_dir = old_file.parent / f"{old_file.stem}_data"
                            if data_dir.exists():
                                import shutil
                                shutil.rmtree(data_dir)
                        except:
                            pass

            return success

        except Exception as e:
            logger.error(f"Failed to autosave project: {e}")
            return False

    def recover_autosave(self, project_id: str) -> Optional[Project]:
        """
        Recover project from autosave

        Args:
            project_id: Project ID to recover

        Returns:
            Recovered project if found
        """
        try:
            autosave_dir = Path.home() / '.excel_data_plotter' / 'autosave'

            if not autosave_dir.exists():
                return None

            # Find most recent autosave
            autosaves = sorted(autosave_dir.glob(f"autosave_{project_id}_*.edp"))

            if autosaves:
                latest = autosaves[-1]
                logger.info(f"Recovering from autosave: {latest}")
                return self.load_project(str(latest))

            return None

        except Exception as e:
            logger.error(f"Failed to recover autosave: {e}")
            return None

    def mark_modified(self):
        """Mark current project as modified"""
        self.project_modified = True
        if self.current_project:
            self.current_project.update_modified_date()

    def is_modified(self) -> bool:
        """Check if current project has unsaved changes"""
        return self.project_modified

