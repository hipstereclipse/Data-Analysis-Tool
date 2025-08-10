#!/usr/bin/env python3
"""
Project Refactoring Script
Automates the renaming and consolidation of files according to the refactoring plan
"""

import os
import shutil
import re
from pathlib import Path
from typing import Dict, List, Tuple

class ProjectRefactorer:
    """Handles the systematic refactoring of the project structure"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.backup_dir = self.project_root / "refactoring_backup"
        
        # Define file mappings: old_name -> new_name
        self.file_mappings = {
            # Enhanced/Fixed files to unified versions
            "ui/enhanced_series_dialog_fixed.py": "DELETE",  # Already consolidated into series_dialog.py
            "ui/enhanced_series_dialog.py": "DELETE",  # Already consolidated
            "ui/smart_series_dialog.py": "DELETE",  # Consolidated into series_dialog.py
            "ui/modern_annotation_dialog.py": "DELETE",  # Consolidated into annotation_dialog.py
            "ui/enhanced_multi_series_analysis.py": "ui/multi_series_analysis.py",
            "core/enhanced_plot_manager.py": "DELETE",  # Consolidated into plot_manager.py
            "app_enhanced.py": "DELETE",  # Will merge best features into app.py
            
            # Rename existing files to remove versioning/subjective naming
            "ui/dialogs.py": "ui/legacy_dialogs.py",  # Keep as legacy reference
        }
        
        # Define import update patterns
        self.import_patterns = [
            # Enhanced imports to unified imports
            (r"from ui\.enhanced_series_dialog_fixed import", "from ui.series_dialog import"),
            (r"from ui\.enhanced_series_dialog import", "from ui.series_dialog import"),
            (r"from ui\.smart_series_dialog import", "from ui.series_dialog import"),
            (r"from ui\.modern_annotation_dialog import", "from ui.annotation_dialog import"),
            (r"from ui\.enhanced_multi_series_analysis import", "from ui.multi_series_analysis import"),
            (r"from core\.enhanced_plot_manager import", "from core.plot_manager import"),
            
            # Class name updates
            (r"SeriesDialog", "SeriesDialog"),
            (r"SeriesDialog", "SeriesDialog"),
            (r"AnnotationDialog", "AnnotationDialog"),
            (r"MultiSeriesAnalysisDialog", "MultiSeriesAnalysisDialog"),
            (r"PlotManager", "PlotManager"),
            
            # Function name updates
            (r"show_series_dialog", "show_series_dialog"),
            (r"show_multi_series_analysis", "show_multi_series_analysis"),
        ]
    
    def create_backup(self):
        """Create backup of current project state"""
        print("Creating backup...")
        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)
        shutil.copytree(self.project_root, self.backup_dir, ignore=shutil.ignore_patterns("refactoring_backup"))
        print(f"Backup created at: {self.backup_dir}")
    
    def rename_files(self):
        """Rename and consolidate files according to mappings"""
        print("Renaming and consolidating files...")
        
        for old_path, new_path in self.file_mappings.items():
            old_file = self.project_root / old_path
            
            if not old_file.exists():
                print(f"Warning: {old_file} not found, skipping...")
                continue
            
            if new_path == "DELETE":
                print(f"Deleting: {old_file}")
                old_file.unlink()
            else:
                new_file = self.project_root / new_path
                new_file.parent.mkdir(parents=True, exist_ok=True)
                print(f"Moving: {old_file} -> {new_file}")
                shutil.move(str(old_file), str(new_file))
    
    def update_imports(self):
        """Update import statements in all Python files"""
        print("Updating import statements...")
        
        for py_file in self.project_root.rglob("*.py"):
            if "refactoring_backup" in str(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                # Apply all import pattern replacements
                for old_pattern, new_pattern in self.import_patterns:
                    content = re.sub(old_pattern, new_pattern, content)
                
                # Write back if changes were made
                if content != original_content:
                    with open(py_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"Updated imports in: {py_file}")
                    
            except Exception as e:
                print(f"Error updating {py_file}: {e}")
    
    def update_main_app(self):
        """Update main application files to use unified components"""
        print("Updating main application files...")
        
        app_file = self.project_root / "app.py"
        if app_file.exists():
            try:
                with open(app_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Update imports at the top
                import_updates = [
                    "from ui.series_dialog import show_series_dialog",
                    "from ui.annotation_dialog import show_annotation_dialog", 
                    "from ui.multi_series_analysis import show_multi_series_analysis",
                    "from core.ui_factory import UIFactory",
                    "from core.data_utils import DataProcessor, DataValidator"
                ]
                
                # Find the import section and add our imports
                import_section = re.search(r'(# Import.*?\n\n)', content, re.DOTALL)
                if import_section:
                    new_imports = "\n".join(import_updates) + "\n\n"
                    content = content.replace(import_section.group(1), 
                                            import_section.group(1) + new_imports)
                
                with open(app_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
                print(f"Updated main application: {app_file}")
                
            except Exception as e:
                print(f"Error updating main app: {e}")
    
    def clean_unused_imports(self):
        """Remove unused import statements"""
        print("Cleaning unused imports...")
        
        # Patterns for imports that should be removed
        remove_patterns = [
            r"from ui\.enhanced_.*? import.*?\n",
            r"from ui\.smart_.*? import.*?\n", 
            r"from ui\.modern_.*? import.*?\n",
            r"from core\.enhanced_.*? import.*?\n",
        ]
        
        for py_file in self.project_root.rglob("*.py"):
            if "refactoring_backup" in str(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                # Remove unused import patterns
                for pattern in remove_patterns:
                    content = re.sub(pattern, "", content)
                
                # Write back if changes were made
                if content != original_content:
                    with open(py_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"Cleaned imports in: {py_file}")
                    
            except Exception as e:
                print(f"Error cleaning imports in {py_file}: {e}")
    
    def generate_summary_report(self):
        """Generate a summary report of the refactoring"""
        print("\n" + "="*60)
        print("REFACTORING SUMMARY REPORT")
        print("="*60)
        
        # Count Python files
        py_files = list(self.project_root.rglob("*.py"))
        py_files = [f for f in py_files if "refactoring_backup" not in str(f)]
        
        print(f"Total Python files: {len(py_files)}")
        
        # List major components
        print("\nMajor Components:")
        major_files = [
            "app.py",
            "main.py", 
            "ui/series_dialog.py",
            "ui/annotation_dialog.py",
            "ui/multi_series_analysis.py",
            "core/plot_manager.py",
            "core/ui_factory.py",
            "core/data_utils.py"
        ]
        
        for file_path in major_files:
            full_path = self.project_root / file_path
            status = "✓ EXISTS" if full_path.exists() else "✗ MISSING"
            print(f"  {file_path}: {status}")
        
        print("\nRefactoring Benefits:")
        print("  • Eliminated redundant 'enhanced', 'modern', 'smart' prefixes")
        print("  • Consolidated duplicate functionality")
        print("  • Standardized naming conventions")
        print("  • Created reusable UI and data utilities")
        print("  • Reduced technical debt")
        
        print(f"\nBackup location: {self.backup_dir}")
        print("="*60)
    
    def run_full_refactoring(self):
        """Run the complete refactoring process"""
        print("Starting project refactoring...")
        print("="*60)
        
        try:
            # Step 1: Create backup
            self.create_backup()
            
            # Step 2: Rename and consolidate files
            self.rename_files()
            
            # Step 3: Update import statements
            self.update_imports()
            
            # Step 4: Update main application
            self.update_main_app()
            
            # Step 5: Clean unused imports
            self.clean_unused_imports()
            
            # Step 6: Generate summary
            self.generate_summary_report()
            
            print("\n✓ Refactoring completed successfully!")
            print("Please test the application and verify all functionality works correctly.")
            
        except Exception as e:
            print(f"\n✗ Refactoring failed: {e}")
            print(f"You can restore from backup at: {self.backup_dir}")


def main():
    """Main refactoring entry point"""
    # Get the project root directory
    current_dir = Path(__file__).parent
    project_root = current_dir
    
    print("Excel Data Plotter - Project Refactoring Tool")
    print("="*50)
    print(f"Project root: {project_root}")
    
    # Auto-confirm for automated refactoring
    print("\nProceeding with automated refactoring...")
    
    # Run refactoring
    refactorer = ProjectRefactorer(str(project_root))
    refactorer.run_full_refactoring()


if __name__ == "__main__":
    main()
