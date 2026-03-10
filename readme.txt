--------------------------------
To Run Project
--------------------------------
1- Install Dependencies
pip install -r requirements.txt
or
pip install tkcalendar
pip install pyautogui
pip install babel
pip install pyinstaller

2-Run setup first:
python setup.py

3-Launch the app:
python main.py


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


=============================================================
Final Project Structure
=============================================================
vehicle_manager/
├── main.py                    ← Entry point
├── app.py                     ← Main app class
├── database.py                ← Database operations
├── styles.py                  ← Theme/colors
├── whatsapp_sender.py         ← WhatsApp messaging
├── import_export.py           ← CSV/JSON import/export
├── center_information.py      ← Your business info
├── build.py                   ← Build script
├── build_icon.py              ← Icon generator
├── setup.py                   ← First-time setup
├── requirements.txt           ← Dependencies
├── pages/
│   ├── __init__.py
│   ├── dashboard.py
│   ├── vehicles.py
│   ├── add_vehicle.py
│   └── whatsapp.py
│
├── dist/                      ← OUTPUT
│   └── VehicleManager.exe     ← YOUR EXE FILE
│
└── build/                     ← Temp (can delete)


========================================================================================================
def format_message(vehicle_number, owner_name, expiry_date,
                   custom_message=None):
    """Format a reminder message"""
    if custom_message:
        msg = custom_message
        msg = msg.replace("{vehicle_number}", vehicle_number)
        msg = msg.replace("{owner_name}",
                          owner_name if owner_name else "Sir/Madam")
        msg = msg.replace("{expiry_date}", expiry_date)
        return msg

    name = owner_name if owner_name else "Sir/Madam"

    try:
        exp_date = datetime.strptime(expiry_date, "%Y-%m-%d")
        formatted_date = exp_date.strftime("%d-%b-%Y")
    except ValueError:
        formatted_date = expiry_date

    today = datetime.now().date()
    try:
        exp = datetime.strptime(expiry_date, "%Y-%m-%d").date()
        if exp < today:
            status = f"⚠️ *EXPIRED* on {formatted_date}"
        else:
            days_left = (exp - today).days
            if days_left == 0:
                status = f"⚠️ *EXPIRES TODAY* ({formatted_date})"
            elif days_left <= 7:
                status = (f"⚠️ Expires in *{days_left} days* "
                          f"({formatted_date})")
            else:
                status = f"Expires on *{formatted_date}*"
    except ValueError:
        status = f"Expiry: {formatted_date}"

    message = (
        f"🚗 *Vehicle Renewal Reminder*\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"Dear *{name}*,\n\n"
        f"This is a reminder for your vehicle:\n\n"
        f"🔢 Vehicle No: *{vehicle_number}*\n"
        f"📅 {status}\n\n"
        f"Please renew your vehicle registration/insurance "
        f"at the earliest.\n\n"
        f"Thank you! 🙏"
    )
    return message