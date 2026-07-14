--------------------------------
To Run Project
--------------------------------
1- Install dependencies
    pip install -r requirements.txt

2- Run setup first:
    python setup.py

3- Launch the app:
    python main.py
    
----------------
Developer Setup
----------------
- Use a virtual environment: `python -m venv .venv`
- Activate it before installing packages
- Install optional packages for full features:
  pip install tkcalendar pyautogui babel pyinstaller

---------------------------------------------------------------------------------------------------------------------
Feature	Description
--------------------------------------------------------------------------------------------------------------------
Dashboard	Stats cards showing total, active, expired, expiring soon, created today, renewed today, messages sent
Add/Renew	Auto-detects existing vehicle numbers and renews instead of duplicating
CRUD	Full Create, Read, Update, Delete operations with confirmation dialogs
Filters	Filter by vehicle number, phone, owner name, status (Active/Expired/Expiring Soon)
WhatsApp	Individual and bulk WhatsApp messaging via wa.me links with customizable templates
Import/Export	CSV and JSON import/export with sample template download
Color-coded rows	Red for expired, yellow for expiring soon, white for active
Message logging	All sent messages are logged in the database
Right-click menu	Context menu on vehicle list for quick actions


-------------------------------------------------
Convert Python Tkinter App to EXE
-------------------------------------------------
Step 1: Install PyInstaller
    pip install pyinstaller

Build Commands
----------------------------------------
Option 1: Use Build Script (Recommended)
    python build.py

Option 2: Manual PyInstaller Command
    pyinstaller --onefile --noconsole --name=VehicleManager --add-data "pages;pages" --hidden-import=tkcalendar --hidden-import=babel.numbers --hidden-import=babel.dates --hidden-import=pyautogui --hidden-import=sqlite3 --clean --noconfirm main.py

Option 3: With Icon
    python build_icon.py
    python build.py

option 4:
    .\.venv\Scripts\pyinstaller.exe --clean --onefile --windowed --icon app_icon.ico --name VehicleManager main.py

Important: 32-bit vs 64-bit builds
- Build the EXE with the same Python architecture as the target PC.
- 64-bit Python produces a 64-bit EXE and only runs on 64-bit Windows.
- 32-bit Python produces a 32-bit EXE and can run on both 32-bit and 64-bit Windows.
- You cannot build a 32-bit EXE using only a 64-bit Python interpreter.
  PyInstaller always bundles the current Python runtime architecture.

How to build a 32-bit EXE
1) Install or use a 32-bit Python distribution on your build machine.
2) Create a 32-bit virtual environment:
    C:\Path\To\Python32\python.exe -m venv .venv32
3) Activate the 32-bit environment:
    .venv32\Scripts\activate
4) Install requirements inside that environment:
    python -m pip install -r requirements.txt
5) Build the EXE from that environment:
    python build.py

To support both architectures:
1) Build a 32-bit EXE with 32-bit Python/PyInstaller for older or 32-bit Windows.
2) Build a 64-bit EXE with 64-bit Python/PyInstaller for modern 64-bit Windows.
3) Distribute both EXEs when you need to support both target machines.

-------------------------------------------------
✅ To “start fresh” (clear caches + rebuild)
-------------------------------------------------
1) Delete old PyInstaller build outputs (cache + exe)
    rmdir /s /q build
    rmdir /s /q dist
    del /q *.spec

2) Delete Python bytecode caches (optional but cleanest)
    del /s /q *.pyc
    rmdir /s /q __pycache__

    ✅ This removes:
    build (PyInstaller temporary build cache)
    dist (previous EXE outputs)
    any old *.spec files

    ✅ This removes all .pyc files and __pycache__ folders so Python will recompile everything.

    ✅ This removes 
    all .pyc files and __pycache__ folders so Python will recompile everything.


