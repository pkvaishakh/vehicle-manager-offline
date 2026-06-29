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
 
-------------------------------------------------
✅ To “start fresh” (clear caches + rebuild)
-------------------------------------------------
1) Delete old PyInstaller build outputs (cache + exe)
    rmdir /s /q build
    rmdir /s /q dist
    del /q *.spec

    ✅ This removes:
    build (PyInstaller temporary build cache)
    dist (previous EXE outputs)
    any old *.spec files 

2) Delete Python bytecode caches (optional but cleanest) 
    del /s /q *.pyc
    rmdir /s /q __pycache__

    ✅ This removes 
    all .pyc files and __pycache__ folders so Python will recompile everything.


