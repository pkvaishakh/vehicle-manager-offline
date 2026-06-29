"""
WhatsApp message sender module - OPTIMIZED VERSION
High-performance bulk messaging with intelligent session management
"""
import urllib.parse
import time
import threading
import os
from datetime import datetime
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

# PyAutoGUI Configuration
try:
    import pyautogui
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.3  # Reduced from 0.5
    HAS_AUTOGUI = True
except ImportError:
    pyautogui = None
    HAS_AUTOGUI = False

# Import center_information safely
try:
    from center_information import center_information
except ImportError:
    center_information = {
        "name": "Vehicle Pollution Testing Center",
        "address": "",
        "phone": "",
        "google_maps": "",
        "working_hours": ""
    }


# ============================================================================
# ENUMS & DATA CLASSES
# ============================================================================

class SendProfile(Enum):
    """Send profile types"""
    FAST = "fast"
    STANDARD = "standard"
    SLOW_PC = "slow_pc"
    MAX_RELIABILITY = "max_reliability"


@dataclass
class ProfileConfig:
    """Configuration for send profiles"""
    initial_wait: int
    enter_retries: int
    retry_base_wait: int
    message_buffer: int
    launch_gap: int
    post_send_settle: int


@dataclass
class SendResult:
    """Result of a message send operation"""
    success: bool
    message: str
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


# ============================================================================
# CONFIGURATION
# ============================================================================

SEND_PROFILES: Dict[SendProfile, ProfileConfig] = {
    SendProfile.FAST: ProfileConfig(
        initial_wait=8,
        enter_retries=2,
        retry_base_wait=1,
        message_buffer=3,
        launch_gap=2,
        post_send_settle=2
    ),
    SendProfile.STANDARD: ProfileConfig(
        initial_wait=12,
        enter_retries=3,
        retry_base_wait=2,
        message_buffer=5,
        launch_gap=4,
        post_send_settle=3
    ),
    SendProfile.SLOW_PC: ProfileConfig(
        initial_wait=18,
        enter_retries=4,
        retry_base_wait=3,
        message_buffer=8,
        launch_gap=6,
        post_send_settle=4
    ),
    SendProfile.MAX_RELIABILITY: ProfileConfig(
        initial_wait=25,
        enter_retries=5,
        retry_base_wait=4,
        message_buffer=10,
        launch_gap=8,
        post_send_settle=5
    )
}


# ============================================================================
# SESSION MANAGER
# ============================================================================

class WhatsAppSessionManager:
    """Manages WhatsApp session state with thread safety"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._session_active = False
        self._last_launch = 0.0
        self._exe_path = None
        self._initialized = True
    
    @property
    def is_active(self) -> bool:
        with self._lock:
            return self._session_active
    
    def activate(self):
        with self._lock:
            self._session_active = True
    
    def deactivate(self):
        with self._lock:
            self._session_active = False
    
    def wait_for_launch_gap(self, min_gap: float = 4.0):
        """Wait until safe to launch"""
        with self._lock:
            now = time.time()
            elapsed = now - self._last_launch
            if elapsed < min_gap:
                time.sleep(min_gap - elapsed)
            self._last_launch = time.time()
    
    def get_exe_path(self) -> Optional[str]:
        """Get cached WhatsApp executable path"""
        if self._exe_path is None:
            self._exe_path = self._find_whatsapp_exe()
        return self._exe_path
    
    @staticmethod
    def _find_whatsapp_exe() -> Optional[str]:
        """Find WhatsApp Desktop executable on Windows"""
        search_paths = [
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "WhatsApp"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "WhatsApp"),
            os.path.join(os.environ.get("PROGRAMFILES", ""), "WhatsApp"),
            os.path.join(os.environ.get("PROGRAMFILES(X86)", ""), "WhatsApp"),
        ]

        for base_path in search_paths:
            if not base_path or not os.path.exists(base_path):
                continue

            exe_direct = os.path.join(base_path, "WhatsApp.exe")
            if os.path.exists(exe_direct):
                return exe_direct

            try:
                for root, _, files in os.walk(base_path):
                    if root.count(os.sep) - base_path.count(os.sep) > 2:
                        continue
                    if "WhatsApp.exe" in files:
                        return os.path.join(root, "WhatsApp.exe")
            except (PermissionError, OSError):
                continue

        return None


# Global session manager instance
session_manager = WhatsAppSessionManager()

    
# ============================================================================
# MESSAGE FORMATTING
# ============================================================================

class MessageFormatter:
    """Formats WhatsApp messages"""
    
    @staticmethod
    def format_message(vehicle_number: str, owner_name: str, 
                      expiry_date: str, custom_message: Optional[str] = None) -> str:
        """Format reminder message"""
        if custom_message:
            msg = custom_message
            msg = msg.replace("{vehicle_number}", vehicle_number)
            msg = msg.replace("{owner_name}", owner_name or "Sir/Madam")
            msg = msg.replace("{expiry_date}", expiry_date)
            return msg
        
        name = owner_name or "Sir/Madam"
        
        # Format date
        try:
            exp_date = datetime.strptime(expiry_date, "%Y-%m-%d")
            formatted_date = exp_date.strftime("%d-%b-%Y")
        except ValueError:
            formatted_date = expiry_date
        
        # Calculate status
        today = datetime.now().date()
        try:
            exp = datetime.strptime(expiry_date, "%Y-%m-%d").date()
            if exp < today:
                status = f"{formatted_date} ന് അവസാനിച്ചിരിക്കുന്നു"
            else:
                days_left = (exp - today).days
                if days_left == 0:
                    status = f"ഇന്ന് അവസാനിക്കുന്നു (*{formatted_date}*)"
                elif days_left <= 7:
                    status = f"*{days_left}* ദിവസത്തിനുള്ളിൽ അവസാനിക്കുന്നതാണ് (*{formatted_date}*)"
                else:
                    status = f"*{formatted_date}* ന് അവസാനിക്കുന്നു"
        except ValueError:
            status = f"Expiry: *{formatted_date}*"
        
        return (
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
            f"ലൊക്കേഷൻ: {center_information.get('google_maps', '')}\n"
            f"{center_information.get('working_hours', '')}\n"
        )
    
    @staticmethod
    def clean_phone_number(phone: str) -> str:
        """Clean and format phone number"""
        phone = str(phone).strip()
        
        # Remove common separators
        for char in [" ", "-", "(", ")", "."]:
            phone = phone.replace(char, "")
        
        # Remove + prefix
        if phone.startswith("+"):
            phone = phone[1:]
        
        # Add country code for Indian numbers
        if len(phone) == 10 and phone.isdigit():
            phone = "91" + phone
        
        return phone


# ============================================================================
# MESSAGE SENDER
# ============================================================================

class WhatsAppSender:
    """Handles WhatsApp message sending"""
    
    def __init__(self, profile: SendProfile = SendProfile.STANDARD):
        self.profile = SEND_PROFILES[profile]
        self.formatter = MessageFormatter()
    
    def ensure_session_active(self) -> bool:
        """Ensure a WhatsApp Desktop session is active on Windows"""
        if not HAS_AUTOGUI:
            return False
        
        if session_manager.is_active:
            return True
        
        session_manager.wait_for_launch_gap(self.profile.launch_gap)
        
        protocol_url = "whatsapp://send?phone=1&text="
        
        try:
            os.startfile(protocol_url)
        except Exception as e:
            print(f"Failed to open WhatsApp: {e}")
            return False
        
        time.sleep(2)
        
        session_manager.activate()
        return True
    
    def open_chat(self, phone: str, message: str) -> bool:
        """Open chat window with a pre-filled message"""
        phone_clean = self.formatter.clean_phone_number(phone)
        encoded_message = urllib.parse.quote(message)
        protocol_url = f"whatsapp://send?phone={phone_clean}&text={encoded_message}"
        
        session_manager.wait_for_launch_gap(self.profile.launch_gap)
        
        try:
            os.startfile(protocol_url)
        except Exception as e:
            print(f"Failed to open chat: {e}")
            return False
        
        time.sleep(0.2)
        
        return True
    
    def send_message_auto(self) -> bool:
        """Send message using Enter key"""
        if not HAS_AUTOGUI:
            print("Auto-send not available (pyautogui not installed)")
            return False
        
        for attempt in range(self.profile.enter_retries):
            try:
                pyautogui.press('space')
                time.sleep(0.1)
                pyautogui.press('enter')
                time.sleep(self.profile.post_send_settle)
                return True
                
            except Exception as e:
                print(f"Send attempt {attempt + 1} failed: {e}")
                if attempt < self.profile.enter_retries - 1:
                    time.sleep(self.profile.retry_base_wait)
                continue
        
        return False
    
    def send_single(self, phone: str,
                    message: str,
                    auto_send: bool = True,
                    wait_time_override: Optional[int] = None) -> SendResult:
        """Send a single message"""
        try:
            if auto_send and HAS_AUTOGUI:
                if not self.ensure_session_active():
                    return SendResult(False, "Could not activate WhatsApp session")
                
                if not self.open_chat(phone, message):
                    return SendResult(False, "Could not open chat")
                
                wait_time = self.profile.initial_wait
                if wait_time_override is not None:
                    try:
                        wait_time = max(wait_time, int(wait_time_override))
                    except (TypeError, ValueError):
                        wait_time = self.profile.initial_wait

                time.sleep(wait_time)
                
                if self.send_message_auto():
                    return SendResult(True, "Message sent successfully")
                else:
                    return SendResult(True, "Opened (manual send needed)")
            
            else:
                # Manual send mode
                if self.open_chat(phone, message):
                    return SendResult(True, "Opened for manual send")
                else:
                    return SendResult(False, "Could not open WhatsApp")
                    
        except Exception as e:
            return SendResult(False, f"Error: {str(e)}")


# ============================================================================
# BULK SENDER
# ============================================================================

class BulkMessageSender:
    """Handles bulk message sending with optimization"""
    
    def __init__(self, profile: SendProfile = SendProfile.STANDARD):
        self.sender = WhatsAppSender(profile)
        self.profile = SEND_PROFILES[profile]
        self.formatter = MessageFormatter()
        self._stop_requested = False
    
    def stop(self):
        """Request bulk send to stop"""
        self._stop_requested = True
    
    def send_bulk(self, 
                  vehicles: List[Dict],
                  custom_message: Optional[str] = None,
                  delay: int = 20,
                  auto_send: bool = True,
                  wait_time: Optional[int] = None,
                  progress_callback: Optional[Callable] = None) -> Dict:
        """
        Send messages to multiple vehicles
        
        Returns:
            Dict with 'success_count', 'failed_count', 'results'
        """
        total = len(vehicles)
        success_count = 0
        failed_count = 0
        results = []
        
        print(f"\n{'='*60}")
        print(f"Starting Bulk Send: {total} messages")
        print(f"Profile: {self.sender.profile}")
        print(f"Auto-send: {auto_send}")
        print(f"{'='*60}\n")
        
        for i, vehicle in enumerate(vehicles):
            if self._stop_requested:
                print("\n⚠️ Bulk send stopped by user")
                break
            
            # Format message
            msg = self.formatter.format_message(
                vehicle["vehicle_number"],
                vehicle.get("owner_name", ""),
                vehicle["expiry_date"],
                custom_message
            )
            
            # Send message
            result = self.sender.send_single(
                vehicle["phone"],
                msg,
                auto_send=auto_send,
                wait_time_override=wait_time
            )
            
            # Update counters
            if result.success:
                success_count += 1
                print(f"✅ [{i+1}/{total}] {vehicle['vehicle_number']}: {result.message}")
                
                # Log to database
                try:
                    from database import log_message
                    log_message(
                        vehicle["id"],
                        vehicle["vehicle_number"],
                        vehicle["phone"],
                        msg
                    )
                except Exception as e:
                    print(f"   Warning: Could not log to database: {e}")
            else:
                failed_count += 1
                print(f"❌ [{i+1}/{total}] {vehicle['vehicle_number']}: {result.message}")
            
            results.append({
                "vehicle": vehicle,
                "result": result
            })
            
            # Progress callback
            if progress_callback:
                try:
                    progress_callback(
                        i + 1, total, success_count, failed_count,
                        vehicle["vehicle_number"]
                    )
                except Exception as e:
                    print(f"Progress callback error: {e}")
            
            # Wait between messages
            if i < total - 1 and not self._stop_requested:
                wait_time = max(delay, self.profile.initial_wait + self.profile.message_buffer)
                print(f"   ⏳ Waiting {wait_time}s before next message...\n")
                time.sleep(wait_time)
        
        # Deactivate session
        session_manager.deactivate()
        
        # Final summary
        print(f"\n{'='*60}")
        print(f"Bulk Send Complete")
        print(f"Success: {success_count}/{total}")
        print(f"Failed: {failed_count}/{total}")
        print(f"{'='*60}\n")
        
        if progress_callback:
            try:
                progress_callback(total, total, success_count, failed_count, "DONE")
            except Exception:
                pass
        
        return {
            "success_count": success_count,
            "failed_count": failed_count,
            "results": results
        }


# ============================================================================
# PUBLIC API FUNCTIONS
# ============================================================================

def get_whatsapp_status() -> Dict:
    """Get WhatsApp installation and capability status"""
    exe_path = session_manager.get_exe_path()
    
    status = {
        "installed": exe_path is not None,
        "path": exe_path,
        "auto_send": HAS_AUTOGUI,
        "method": "desktop" if exe_path else "protocol",
    }
    
    if exe_path and HAS_AUTOGUI:
        status["message"] = (
            f"✅ WhatsApp Desktop FOUND\n"
            f"✅ Auto-Send ENABLED\n"
            f"Path: {exe_path}"
        )
    elif exe_path:
        status["message"] = (
            f"✅ WhatsApp Desktop FOUND\n"
            f"⚠️ Auto-Send DISABLED (install pyautogui)\n"
            f"Path: {exe_path}"
        )
    else:
        status["message"] = (
            f"⚠️ WhatsApp Desktop NOT FOUND\n"
            f"{'✅' if HAS_AUTOGUI else '⚠️'} pyautogui {'installed' if HAS_AUTOGUI else 'not installed'}"
        )
    
    return status


def is_whatsapp_installed() -> bool:
    """Check if WhatsApp Desktop is installed"""
    return session_manager.get_exe_path() is not None


def send_whatsapp_message(phone: str,
                          message: str,
                          method: str = "auto",
                          auto_send: bool = True,
                          wait_time: int = 12,
                          send_profile: str = "standard",
                          exe_path: Optional[str] = None,
                          callback: Optional[Callable] = None) -> bool:
    """Send a single WhatsApp message"""
    try:
        profile = SendProfile(send_profile)
    except ValueError:
        profile = SendProfile.STANDARD
    
    _ = method, exe_path

    sender = WhatsAppSender(profile)
    result = sender.send_single(
        phone,
        message,
        auto_send,
        wait_time_override=wait_time
    )
    
    if callback:
        callback(result.success, result.message)
    
    return result.success


def bulk_send_messages(vehicles: List[Dict],
                      custom_message: Optional[str] = None,
                      delay: int = 20,
                      method: str = "auto",
                      auto_send: bool = True,
                      wait_time: int = 12,
                      progress_callback: Optional[Callable] = None,
                      send_profile: str = "standard") -> threading.Thread:
    """
    Send messages to multiple vehicles in a background thread
    
    Args:
        vehicles: List of vehicle dicts with keys: id, vehicle_number, owner_name, expiry_date, phone
        custom_message: Optional custom message template
        delay: Delay between messages in seconds
        method: Send method (unused, kept for compatibility)
        auto_send: Whether to auto-send or just open
        wait_time: Minimum wait time before sending
        progress_callback: Callback function(current, total, success, failed, vehicle_number)
        send_profile: Profile name (fast/standard/slow_pc/max_reliability)
    
    Returns:
        Thread object (started)
    """
    try:
        profile = SendProfile(send_profile)
    except ValueError:
        profile = SendProfile.STANDARD
    
    bulk_sender = BulkMessageSender(profile)
    
    def _send_thread():
        bulk_sender.send_bulk(
            vehicles=vehicles,
            custom_message=custom_message,
            delay=delay,
            auto_send=auto_send,
            wait_time=wait_time,
            progress_callback=progress_callback
        )
    
    thread = threading.Thread(target=_send_thread, daemon=True)
    thread.start()
    return thread


# Backward compatibility aliases
format_message = MessageFormatter.format_message
clean_phone_number = MessageFormatter.clean_phone_number
find_whatsapp_exe = lambda: session_manager.get_exe_path()
get_send_profile_config = lambda profile: SEND_PROFILES.get(
    SendProfile(profile) if isinstance(profile, str) else profile,
    SEND_PROFILES[SendProfile.STANDARD]
)
