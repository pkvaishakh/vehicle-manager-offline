"""
WhatsApp message sender module
Supports: WhatsApp Desktop App with AUTO-SEND (no manual clicking)
Uses pyautogui to automatically press Enter/Send
"""
import urllib.parse
import webbrowser
import subprocess
import time
import threading
import os
import sys
import platform
from datetime import datetime

# Try import center_information
try:
    from center_information import center_information
except ImportError:
    center_information = {
        "name": "Vehicle Pollution Testing Center",
        "address": "",
        "phone": "",
        "google_maps": ""
    }

# Try import pyautogui for auto-send
try:
    import pyautogui
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.5
    HAS_AUTOGUI = True
except ImportError:
    HAS_AUTOGUI = False
    print("⚠️ pyautogui not installed. Auto-send disabled.")
    print("   Install with: pip install pyautogui")


def find_whatsapp_exe():
    """
    Find WhatsApp Desktop executable on the PC
    Returns path if found, None otherwise
    """
    possible_paths = []

    if platform.system() == "Windows":
        local_app = os.environ.get("LOCALAPPDATA", "")
        if local_app:
            whatsapp_dir = os.path.join(local_app, "WhatsApp")
            if os.path.exists(whatsapp_dir):
                for root, dirs, files in os.walk(whatsapp_dir):
                    for f in files:
                        if f.lower() == "whatsapp.exe":
                            possible_paths.append(os.path.join(root, f))

        prog_dirs = [
            os.environ.get("PROGRAMFILES", "C:\\Program Files"),
            os.environ.get("PROGRAMFILES(X86)",
                           "C:\\Program Files (x86)"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""),
                         "Programs"),
        ]

        for prog_dir in prog_dirs:
            if prog_dir:
                wp_path = os.path.join(
                    prog_dir, "WhatsApp", "WhatsApp.exe")
                if os.path.exists(wp_path):
                    possible_paths.append(wp_path)

        user_profile = os.environ.get("USERPROFILE", "")
        if user_profile:
            extra_paths = [
                os.path.join(user_profile, "AppData", "Local",
                             "WhatsApp", "WhatsApp.exe"),
                os.path.join(user_profile, "AppData", "Local",
                             "Programs", "WhatsApp", "WhatsApp.exe"),
            ]
            for p in extra_paths:
                if os.path.exists(p):
                    possible_paths.append(p)

        try:
            result = subprocess.run(
                ["where", "WhatsApp"],
                capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    if line.strip():
                        possible_paths.append(line.strip())
        except Exception:
            pass

    elif platform.system() == "Darwin":
        mac_paths = [
            "/Applications/WhatsApp.app",
            os.path.expanduser("~/Applications/WhatsApp.app"),
        ]
        for p in mac_paths:
            if os.path.exists(p):
                possible_paths.append(p)

    elif platform.system() == "Linux":
        try:
            result = subprocess.run(
                ["which", "whatsapp-nativefier"],
                capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                possible_paths.append(result.stdout.strip())
        except Exception:
            pass

        linux_paths = [
            "/snap/bin/whatsapp-for-linux",
            "/usr/bin/whatsapp-for-linux",
        ]
        for p in linux_paths:
            if os.path.exists(p):
                possible_paths.append(p)

    for path in possible_paths:
        if os.path.exists(path):
            return path

    # Attempt to find Microsoft Store (WindowsApps) install of WhatsApp
    # (Store apps are often installed to a protected folder and not detected
    # by the usual install paths or `where` command.)
    if platform.system() == "Windows":
        windows_apps_paths = [
            os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "WindowsApps"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WindowsApps"),
        ]
        for base in windows_apps_paths:
            if not base or not os.path.isdir(base):
                continue
            try:
                for root, dirs, files in os.walk(base):
                    for f in files:
                        if f.lower().startswith("whatsapp") and f.lower().endswith(".exe"):
                            candidate = os.path.join(root, f)
                            if os.path.exists(candidate):
                                return candidate
            except PermissionError:
                # Some WindowsApps folders are protected; ignore and continue.
                continue
            except Exception:
                continue

    return None


def is_whatsapp_installed():
    """Check if WhatsApp Desktop is installed"""
    return find_whatsapp_exe() is not None


def get_whatsapp_status():
    """Get detailed WhatsApp installation status"""
    exe_path = find_whatsapp_exe()
    status = {
        "installed": exe_path is not None,
        "path": exe_path,
        "auto_send": HAS_AUTOGUI,
        "method": "desktop" if exe_path else "protocol",
    }

    if exe_path and HAS_AUTOGUI:
        status["message"] = (
            f"✅ WhatsApp Desktop FOUND\n"
            f"✅ Auto-Send ENABLED (pyautogui installed)\n"
            f"Path: {exe_path}")
    elif exe_path:
        status["message"] = (
            f"✅ WhatsApp Desktop FOUND\n"
            f"⚠️ Auto-Send DISABLED (install pyautogui)\n"
            f"Path: {exe_path}")
    elif HAS_AUTOGUI:
        status["message"] = (
            f"⚠️ WhatsApp Desktop NOT FOUND\n"
            f"✅ pyautogui installed\n"
            f"Will use whatsapp:// protocol")
    else:
        status["message"] = (
            f"⚠️ WhatsApp Desktop NOT FOUND\n"
            f"⚠️ Auto-Send DISABLED\n"
            f"Install: pip install pyautogui")

    return status


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
            status = f"{formatted_date} ന് അവസാനിച്ചിരിക്കുന്നു"
        else:
            days_left = (exp - today).days
            if days_left == 0:
                status = f"ഇന്ന് അവസാനിക്കുന്നു *{formatted_date}*"
            elif days_left <= 7:
                status = (
                    f"*{days_left}* ദിവസത്തിനുള്ളിൽ "
                    f"അവസാനിക്കുന്നതാണ് *{formatted_date}*")
            else:
                status = f"*{formatted_date}* ന് അവസാനിക്കുന്നു"
    except ValueError:
        status = f"Expiry: *{formatted_date}*"

    message = (
        f"🚗 *വാഹനപുകപരിശോധനകേന്ദ്രത്തിൽ നിന്നുള്ള അറിയിപ്പ്...*\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"Dear *{name}*,\n\n"
        f"താങ്കളുടെ *{vehicle_number}* വാഹനത്തിന്റെ "
        f"വാഹനപുക സർട്ടിഫിക്കറ്റ് കാലാവധി {status}.\n\n"
        f"സർക്കാർ അധികാരികളിൽ നിന്നുള്ള നിയമപരമായ "
        f"ശിക്ഷാനടപടികൾ/പിഴ ഒഴിവാക്കുന്നതിനായി, "
        f"കാലാവധി തീരുന്നതിന് മുൻപായി ഞങ്ങളുടെ "
        f"വാഹനപുകപരിശോധനാകേന്ദ്രത്തിൽ നിന്നും "
        f"സർട്ടിഫിക്കറ്റ് പുതുക്കുക.\n\n"
        f"*{center_information.get('name', '')}*\n"
        f"അഡ്രസ്സ്: {center_information.get('address', '')}\n"
        f"ഫോൺ: {center_information.get('phone', '')}\n"
        f"ലൊക്കേഷൻ : {center_information.get('google_maps', '')}\n"
        f"{center_information.get('working_hours', '')}\n"
    )
    
    return message


def clean_phone_number(phone):
    """Clean and format phone number"""
    phone = str(phone).strip().replace(" ", "").replace(
        "-", "").replace("(", "").replace(")", "")

    if phone.startswith("+"):
        phone = phone[1:]

    if len(phone) == 10 and phone.isdigit():
        phone = "91" + phone

    return phone


def wait_for_whatsapp_ready(timeout=15):
    """
    Wait for WhatsApp window to be ready and message loaded
    Returns True if ready, False if timeout
    """
    if not HAS_AUTOGUI:
        return False

    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            # Check if WhatsApp window is in foreground
            if platform.system() == "Windows":
                import ctypes
                hwnd = ctypes.windll.user32.GetForegroundWindow()
                length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
                buff = ctypes.create_unicode_buffer(length + 1)
                ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
                window_title = buff.value.lower()

                if "whatsapp" in window_title:
                    return True
            else:
                # For Mac/Linux just wait
                time.sleep(3)
                return True

        except Exception:
            pass

        time.sleep(1)

    # Timeout - assume it's ready anyway
    return True


def auto_press_enter(wait_time=8):
    """
    Wait for WhatsApp to load the chat, then press Enter to send
    """
    if not HAS_AUTOGUI:
        return False

    try:
        # Wait for WhatsApp to open and load the chat
        time.sleep(wait_time)

        # Press Enter to send the message
        pyautogui.press('enter')

        # Small delay to confirm sent
        time.sleep(1)

        return True

    except Exception as e:
        print(f"Auto-send error: {e}")
        return False


def send_and_auto_enter(phone, message, method="protocol",
                        exe_path=None, wait_time=8):
    """
    Open WhatsApp with message AND automatically press Enter to send
    
    Flow:
    1. Open WhatsApp with pre-filled message
    2. Wait for WhatsApp to load (wait_time seconds + buffer)
    3. Press Enter automatically to send (with retry logic)
    """
    phone = clean_phone_number(phone)
    encoded_message = urllib.parse.quote(message)

    opened = False

    # Step 1: Open WhatsApp with message
    if method in ("auto", "protocol", "desktop"):
        protocol_url = (
            f"whatsapp://send?phone={phone}&text={encoded_message}")
        try:
            if platform.system() == "Windows":
                os.startfile(protocol_url)
                opened = True
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", protocol_url])
                opened = True
            elif platform.system() == "Linux":
                subprocess.Popen(["xdg-open", protocol_url])
                opened = True
        except Exception:
            pass

    # Fallback to exe if protocol failed
    if not opened and exe_path and os.path.exists(exe_path):
        try:
            wa_url = (f"https://api.whatsapp.com/send?"
                      f"phone={phone}&text={encoded_message}")
            subprocess.Popen([exe_path, wa_url])
            opened = True
        except Exception:
            pass

    # Last resort: browser
    if not opened and method in ("auto", "browser"):
        try:
            url = f"https://wa.me/{phone}?text={encoded_message}"
            webbrowser.open(url)
            opened = True
        except Exception:
            pass

    if not opened:
        return False, "Could not open WhatsApp"

    # Step 2: Wait and auto-send with IMPROVED timing
    if HAS_AUTOGUI:
        # Add extra buffer time (2-3s) to ensure message field is fully rendered
        # This prevents draft state issues
        total_wait = max(wait_time + 2, 10)  # Minimum 10s total wait

        # Wait for WhatsApp to load the chat with message
        time.sleep(total_wait)
        wait_for_whatsapp_ready(timeout=5)

        try:
            # First attempt: press Enter (default send behavior)
            pyautogui.press('enter')
            time.sleep(0.5)

            # Fallback attempt: use Ctrl+Enter in case "Enter key sends" is disabled
            pyautogui.hotkey('ctrl', 'enter')
            time.sleep(0.5)

            # One more Enter to be safe
            pyautogui.press('enter')

            # Wait to confirm send completed
            time.sleep(1.5)
            return True, "Message sent automatically ✅"
        except Exception as e:
            return True, f"Opened but auto-send failed: {e}"
    else:
        return True, "Opened (auto-send unavailable - install pyautogui)"


def send_via_desktop_exe(phone, message, exe_path=None):
    """Send using desktop exe"""
    phone = clean_phone_number(phone)
    encoded_message = urllib.parse.quote(message)

    protocol_url = (
        f"whatsapp://send?phone={phone}&text={encoded_message}")

    try:
        if platform.system() == "Windows":
            os.startfile(protocol_url)
            return True, "Opened via whatsapp:// protocol"
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", protocol_url])
            return True, "Opened via whatsapp:// protocol"
        elif platform.system() == "Linux":
            subprocess.Popen(["xdg-open", protocol_url])
            return True, "Opened via whatsapp:// protocol"
    except Exception:
        pass

    if exe_path and os.path.exists(exe_path):
        try:
            wa_url = (f"https://api.whatsapp.com/send?"
                      f"phone={phone}&text={encoded_message}")
            subprocess.Popen([exe_path, wa_url])
            return True, f"Opened via exe: {exe_path}"
        except Exception as e:
            return False, f"Exe launch failed: {str(e)}"

    return False, "No method available"


def send_via_protocol(phone, message):
    """Send using whatsapp:// protocol"""
    phone = clean_phone_number(phone)
    encoded_message = urllib.parse.quote(message)
    url = f"whatsapp://send?phone={phone}&text={encoded_message}"

    try:
        if platform.system() == "Windows":
            os.startfile(url)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", url])
        else:
            subprocess.Popen(["xdg-open", url])
        return True, "Opened WhatsApp Desktop"
    except Exception as e:
        return False, str(e)


def send_via_browser(phone, message):
    """Fallback: Send using web browser"""
    phone = clean_phone_number(phone)
    encoded_message = urllib.parse.quote(message)
    url = f"https://wa.me/{phone}?text={encoded_message}"

    try:
        webbrowser.open(url)
        return True, "Opened in browser"
    except Exception as e:
        return False, str(e)


def send_whatsapp_message(phone, message, method="auto",
                          exe_path=None, auto_send=True,
                          wait_time=8, callback=None):
    """
    Send WhatsApp message - with optional auto-send

    Parameters:
        phone       - Phone number
        message     - Message text
        method      - "auto", "desktop", "protocol", "browser"
        exe_path    - Custom WhatsApp.exe path
        auto_send   - If True, automatically press Enter to send
        wait_time   - Seconds to wait before pressing Enter
        callback    - Optional callback function
    """
    # Use auto-send if enabled and pyautogui available
    if auto_send and HAS_AUTOGUI:
        success, result_msg = send_and_auto_enter(
            phone, message, method, exe_path, wait_time)
        if callback:
            callback(success, result_msg)
        return success

    # Manual mode (just open, don't auto-send)
    success = False
    result_msg = ""

    if method == "auto":
        if not exe_path:
            exe_path = find_whatsapp_exe()

        if exe_path:
            success, result_msg = send_via_desktop_exe(
                phone, message, exe_path)
            if success:
                if callback:
                    callback(True, result_msg)
                return True

        success, result_msg = send_via_protocol(phone, message)
        if success:
            if callback:
                callback(True, result_msg)
            return True

        success, result_msg = send_via_browser(phone, message)
        if callback:
            callback(success, result_msg)
        return success

    elif method == "desktop":
        if not exe_path:
            exe_path = find_whatsapp_exe()
        success, result_msg = send_via_desktop_exe(
            phone, message, exe_path)

    elif method == "protocol":
        success, result_msg = send_via_protocol(phone, message)

    elif method == "browser":
        success, result_msg = send_via_browser(phone, message)

    if callback:
        callback(success, result_msg)
    return success


def bulk_send_messages(vehicles, custom_message=None, delay=10,
                       method="auto", auto_send=True,
                       wait_time=8, progress_callback=None):
    """
    Send messages to multiple vehicles with auto-send

    Parameters:
        vehicles           - List of vehicle dicts
        custom_message     - Optional custom template
        delay              - Seconds between each message (MINIMUM, auto-adjusted)
        method             - Sending method
        auto_send          - Auto press Enter to send
        wait_time          - Wait time before pressing Enter
        progress_callback  - Progress update function
    """
    def _send():
        total = len(vehicles)
        success_count = 0
        failed_count = 0
        exe_path = find_whatsapp_exe() if method in (
            "auto", "desktop") else None

        # Auto-adjust delay to ensure enough time for send to complete
        # Minimum delay between messages should be wait_time + 3 seconds buffer
        effective_delay = max(delay, wait_time + 3) if auto_send else delay

        for i, vehicle in enumerate(vehicles):
            msg = format_message(
                vehicle["vehicle_number"],
                vehicle.get("owner_name", ""),
                vehicle["expiry_date"],
                custom_message
            )

            try:
                if auto_send and HAS_AUTOGUI:
                    success, result_msg = send_and_auto_enter(
                        vehicle["phone"], msg, method,
                        exe_path, wait_time)
                else:
                    success = send_whatsapp_message(
                        vehicle["phone"], msg,
                        method=method, exe_path=exe_path,
                        auto_send=False)
                    result_msg = "Opened"

                if success:
                    success_count += 1
                    try:
                        from database import log_message
                        log_message(
                            vehicle["id"],
                            vehicle["vehicle_number"],
                            vehicle["phone"],
                            msg)
                    except Exception:
                        pass
                else:
                    failed_count += 1

            except Exception as e:
                failed_count += 1

            if progress_callback:
                progress_callback(
                    i + 1, total, success_count, failed_count,
                    vehicle["vehicle_number"])

            # Wait between messages (auto-adjusted for auto-send)
            if i < total - 1:
                time.sleep(effective_delay)

        if progress_callback:
            progress_callback(
                total, total, success_count, failed_count, "DONE")

    thread = threading.Thread(target=_send, daemon=True)
    thread.start()
    return thread