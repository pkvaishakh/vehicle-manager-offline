"""
Vehicle Management System - Main Entry Point
Handles both normal Python and PyInstaller EXE execution
"""
import os
import sys


def get_base_path():
    """Get the base path - works for both dev and PyInstaller exe"""
    if getattr(sys, 'frozen', False):
        # Running as compiled EXE
        return os.path.dirname(sys.executable)
    else:
        # Running as Python script
        return os.path.dirname(os.path.abspath(__file__))


def setup_paths():
    """Setup paths for the application"""
    base = get_base_path()

    # Change working directory to exe location
    # so database.db is created next to the exe
    os.chdir(base)

    # Add base path to Python path for imports
    if base not in sys.path:
        sys.path.insert(0, base)

    # For PyInstaller bundled files
    if getattr(sys, 'frozen', False):
        bundle_dir = getattr(sys, '_MEIPASS', base)
        if bundle_dir not in sys.path:
            sys.path.insert(0, bundle_dir)


# Setup paths BEFORE importing anything else
setup_paths()

from app import VehicleManagementApp


if __name__ == "__main__":
    app = VehicleManagementApp()
    app.run()