"""
Build script to convert the application to .exe
Run: python build.py
"""
import subprocess
import sys
import os
import shutil


def build_exe():
    print("=" * 60)
    print("🔨 Building Vehicle Management System - EXE")
    print("=" * 60)

    # Step 1: Install required packages
    print("\n📦 Step 1: Installing dependencies...")

    requirements_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
    if os.path.exists(requirements_path):
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "-r", requirements_path])
            print("  ✅ Installed requirements.txt")
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Failed to install requirements.txt (exit {e.returncode})")
            print("  Please fix the error above, then rerun: ")
            print(f"    {sys.executable} -m pip install -r requirements.txt")
            sys.exit(1)
    else:
        print("  ⚠️ requirements.txt not found. Installing a minimal set of packages.")
        packages = ["pyinstaller", "tkcalendar", "pyautogui"]

        for pkg in packages:
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", pkg])
                print(f"  ✅ {pkg}")
            except subprocess.CalledProcessError as e:
                print(f"  ❌ {pkg} failed to install (exit {e.returncode})")
                print("  Please check your network/permissions, then run:")
                print(f"    {sys.executable} -m pip install {pkg}")
                sys.exit(1)

    # Step 2: Check for icon file
    icon_file = None
    icon_candidates = [
        "app_icon.ico",
        "icon.ico",
        "logo.ico",
        "vehicle.ico",
        "app.ico",
    ]

    # Check all possible icon filenames
    for name in icon_candidates:
        if os.path.exists(name):
            icon_file = name
            break

    # Also search for ANY .ico file in current directory
    if not icon_file:
        for f in os.listdir("."):
            if f.lower().endswith(".ico"):
                icon_file = f
                break

    if icon_file:
        print(f"\n🎨 Icon found: {icon_file}")
    else:
        print("\n⚠️ No .ico file found. Building without custom icon.")
        print("   Place your .ico file in the project folder and rebuild.")

    # Step 3: Clean old builds
    print("\n🧹 Step 2: Cleaning old builds...")
    for folder in ["build", "dist"]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"  Removed: {folder}/")

    for f in os.listdir("."):
        if f.endswith(".spec"):
            os.remove(f)
            print(f"  Removed: {f}")

    # Step 4: Build EXE
    print("\n🔨 Step 3: Building EXE (2-5 minutes)...")
    print("   Please wait...\n")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "main.py",
        "--name=VehicleManager",
        "--onefile",
        "--noconsole",

        # Data files
        "--add-data", f"database.py{os.pathsep}.",
        "--add-data", f"app.py{os.pathsep}.",
        "--add-data", f"styles.py{os.pathsep}.",
        "--add-data", f"whatsapp_sender.py{os.pathsep}.",
        "--add-data", f"import_export.py{os.pathsep}.",
        "--add-data", f"center_information.py{os.pathsep}.",
        "--add-data", f"pages{os.pathsep}pages",

        # Hidden imports
        "--hidden-import=tkcalendar",
        "--hidden-import=babel.numbers",
        "--hidden-import=babel.dates",
        "--hidden-import=pyautogui",
        "--hidden-import=reportlab",
        "--hidden-import=sqlite3",
        "--hidden-import=csv",
        "--hidden-import=json",
        "--hidden-import=calendar",
        "--hidden-import=threading",
        "--hidden-import=urllib.parse",
        "--hidden-import=webbrowser",
        "--hidden-import=subprocess",
        "--hidden-import=ctypes",
        "--hidden-import=platform",

        # Ensure required package data is collected (prevents missing resources in onefile builds)
        "--collect-all", "reportlab",
        "--collect-all", "pyautogui",
        "--collect-all", "tkcalendar",

        # Exclude unnecessary
        "--exclude-module=matplotlib",
        "--exclude-module=numpy",
        "--exclude-module=pandas",
        "--exclude-module=scipy",
        "--exclude-module=PIL",
        "--exclude-module=PyQt5",
        "--exclude-module=PyQt6",
        "--exclude-module=wx",

        "--noconfirm",
        "--clean",
    ]

    # ✅ ADD ICON IF FOUND
    if icon_file:
        cmd.insert(cmd.index("--noconsole") + 1,
                   f"--icon={icon_file}")

    try:
        subprocess.check_call(cmd)

        print("\n" + "=" * 60)
        print("✅ BUILD SUCCESSFUL!")
        print("=" * 60)

        exe_path = os.path.join("dist", "VehicleManager.exe")
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"\n📁 EXE: {os.path.abspath(exe_path)}")
            print(f"📊 Size: {size_mb:.1f} MB")
            if icon_file:
                print(f"🎨 Icon: {icon_file} ✅")
            print(f"\n💡 Double-click dist/VehicleManager.exe to run")

    except subprocess.CalledProcessError as e:
        print(f"\n❌ BUILD FAILED: {e}")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")


if __name__ == "__main__":
    build_exe()