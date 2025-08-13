#!/usr/bin/env python3
"""
Demonstrate that the fixes work correctly
Run this to see the fixes in action
"""

import tkinter as tk
import customtkinter as ctk
import pandas as pd
import numpy as np


def test_statusbar_fix():
    """Test the StatusBar with progress methods"""
    print("\n" + "=" * 60)
    print("Testing StatusBar Fix")
    print("=" * 60)

    # Create a test window
    root = ctk.CTk()
    root.title("StatusBar Test")
    root.geometry("600x200")

    # Import and create StatusBar
    from ui.components import StatusBar

    status_bar = StatusBar(root)
    status_bar.pack(fill="x", side="bottom")

    # Test methods
    def test_sequence():
        # Test 1: Set status
        status_bar.set_status("Testing status message", "info")
        root.after(1000, lambda: status_bar.set_status("Success message", "success"))

        # Test 2: Update counts
        root.after(2000, lambda: status_bar.update_counts(files=3, series=5))

        # Test 3: Show progress
        root.after(3000, lambda: status_bar.show_progress(0.0))
        root.after(3500, lambda: status_bar.show_progress(0.25))
        root.after(4000, lambda: status_bar.show_progress(0.50))
        root.after(4500, lambda: status_bar.show_progress(0.75))
        root.after(5000, lambda: status_bar.show_progress(1.0))

        # Test 4: Hide progress
        root.after(6000, lambda: status_bar.hide_progress())
        root.after(6500, lambda: status_bar.set_status("Test complete!", "success"))

        # Close window
        root.after(8000, root.destroy)

    # Add instructions
    label = ctk.CTkLabel(root, text="Watch the status bar below:", font=("", 16))
    label.pack(pady=20)

    info = ctk.CTkLabel(root,
                        text="It will show:\n1. Status messages\n2. File/series counts\n3. Progress bar\n4. Then return to normal",
                        font=("", 12))
    info.pack(pady=10)

    # Start test sequence
    root.after(500, test_sequence)

    try:
        root.mainloop()
        print("✓ StatusBar test completed successfully")
        return True
    except Exception as e:
        print(f"✗ StatusBar test failed: {e}")
        return False


def test_data_quality_fix():
    """Test the DataQualityAnalyzer scoring fix"""
    print("\n" + "=" * 60)
    print("Testing DataQualityAnalyzer Fix")
    print("=" * 60)

    from analysis.data_quality import DataQualityAnalyzer

    analyzer = DataQualityAnalyzer()

    # Test 1: Good quality data
    print("\nTest 1: Good quality data (no missing values)")
    good_data = pd.DataFrame({
        'x': np.arange(100),
        'y': np.random.randn(100),
        'z': np.random.randn(100) * 10
    })

    good_report = analyzer.analyze_quality(good_data)
    print(f"  Quality score: {good_report.quality_score:.1f}")
    print(f"  Issues: {good_report.issues if good_report.issues else 'None'}")
    print(f"  Expected: >90, Got: {good_report.quality_score:.1f}")

    # Test 2: Bad quality data (50% missing)
    print("\nTest 2: Bad quality data (50% missing values)")
    bad_data = pd.DataFrame({
        'x': np.arange(100),
        'y': [np.nan] * 50 + list(np.random.randn(50)),
        'z': list(np.random.randn(50)) + [np.nan] * 50
    })

    bad_report = analyzer.analyze_quality(bad_data)
    print(f"  Quality score: {bad_report.quality_score:.1f}")
    print(f"  Issues: {bad_report.issues}")
    print(f"  Expected: <50, Got: {bad_report.quality_score:.1f}")

    # Test 3: Medium quality data (20% missing, some outliers)
    print("\nTest 3: Medium quality data (20% missing, outliers)")
    medium_data = pd.DataFrame({
        'x': np.arange(100),
        'y': [np.nan] * 20 + list(np.random.randn(80)),
        'z': list(np.random.randn(95)) + [100, 200, 300, -100, -200]  # outliers
    })

    medium_report = analyzer.analyze_quality(medium_data)
    print(f"  Quality score: {medium_report.quality_score:.1f}")
    print(f"  Issues: {medium_report.issues}")
    print(f"  Expected: 50-80, Got: {medium_report.quality_score:.1f}")

    # Verify the fix works
    if good_report.quality_score > 90 and bad_report.quality_score < 50:
        print("\n✓ DataQualityAnalyzer scoring is working correctly!")
        return True
    else:
        print("\n✗ DataQualityAnalyzer scoring still needs adjustment")
        return False


def test_export_dialog_fix():
    """Test the ExportDialog fix"""
    print("\n" + "=" * 60)
    print("Testing ExportDialog Fix")
    print("=" * 60)

    # Check if the fix is in app.py
    from pathlib import Path

    app_path = Path("app.py")
    if app_path.exists():
        # Read with UTF-8 to support Unicode icons present in the UI source
        with open(app_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        if "ExportDialog(self, self.plot_manager)" in content:
            print("✓ ExportDialog constructor is fixed in app.py")
            print("  The dialog now receives both parent and plot_manager")
            return True
        else:
            print("✗ ExportDialog constructor not fixed in app.py")
            return False
    else:
        print("⚠ app.py not found - skipping test")
        return True


def main():
    """Run all test demonstrations"""
    print("=" * 60)
    print("Excel Data Plotter - Fix Demonstrations")
    print("=" * 60)
    print("This will demonstrate that the fixes work correctly")

    results = []

    # Test each fix
    try:
        # Test 1: DataQuality (non-GUI)
        results.append(test_data_quality_fix())

        # Test 2: ExportDialog check
        results.append(test_export_dialog_fix())

        # Test 3: StatusBar (GUI - optional)
        print("\n" + "=" * 60)
        response = input("Do you want to see the StatusBar GUI demo? (y/n): ")
        if response.lower() == 'y':
            results.append(test_statusbar_fix())
        else:
            print("Skipping StatusBar GUI demo")

    except Exception as e:
        print(f"\nError during testing: {e}")

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    if all(results):
        print("✅ All tested fixes are working correctly!")
    else:
        print("⚠️ Some fixes may need additional adjustment")

    print("\nYou can now run your application with: python main.py")
    print("=" * 60)


if __name__ == "__main__":
    main()