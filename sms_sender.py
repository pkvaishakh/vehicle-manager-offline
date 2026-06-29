"""
SMS sending module using a local Android SMS gateway server.
"""
import base64
from datetime import datetime
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from threading import Event, Thread
from typing import Callable, Dict, List, Optional

from database import log_message

_last_error: str = ""

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


def _set_last_error(message: str) -> None:
    global _last_error
    _last_error = str(message)


def get_last_error() -> str:
    return _last_error


def sanitize_url(url: str) -> str:
    url = str(url).strip()
    if not url:
        raise ValueError("SMS API URL is required")
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "http://" + url

    parsed = urllib.parse.urlparse(url)
    scheme = parsed.scheme
    netloc = parsed.netloc
    path = parsed.path or "/message"
    if path == "/":
        path = "/message"
    query = f"?{parsed.query}" if parsed.query else ""
    return urllib.parse.urlunparse((scheme, netloc, path, "", parsed.query, ""))


def _normalize_sms_phone(phone: str) -> str:
    phone = str(phone).strip()
    if not phone:
        return phone

    for ch in [" ", "-", "(", ")", "."]:
        phone = phone.replace(ch, "")

    if phone.startswith("00"):
        phone = "+" + phone[2:]

    if phone.startswith("+"):
        return phone

    if phone.startswith("91") and len(phone) == 12 and phone.isdigit():
        return "+" + phone

    if phone.isdigit() and len(phone) == 10:
        return "+91" + phone

    return phone

def format_sms_message(
        vehicle_number: str, 
        owner_name: str, 
        expiry_date: str, 
        custom_message: Optional[str] = None
) -> str:
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
                status = f"ഇന്ന് അവസാനിക്കുന്നു ({formatted_date})"
            elif days_left <= 7:
                status = f"*{days_left}* ദിവസത്തിനുള്ളിൽ അവസാനിക്കുന്നതാണ് ({formatted_date})"
            else:
                status = f"{formatted_date} ന് അവസാനിക്കുന്നു"
    except ValueError:
        status = f"Expiry: *{formatted_date}*"
    
    return (
        f"🚗 *വാഹനപുകപരിശോധനകേന്ദ്രത്തിൽ നിന്നുള്ള അറിയിപ്പ്...*\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"Dear {name},\n\n"
        f"താങ്കളുടെ {vehicle_number} വാഹനത്തിന്റെ "
        f"വാഹനപുക സർട്ടിഫിക്കറ്റ് കാലാവധി {status}.\n\n"
        f"സർക്കാർ അധികാരികളിൽ നിന്നുള്ള നിയമപരമായ "
        f"ശിക്ഷാനടപടികൾ/പിഴ ഒഴിവാക്കുന്നതിനായി, "
        f"കാലാവധി തീരുന്നതിന് മുൻപായി ഞങ്ങളുടെ "
        f"വാഹനപുകപരിശോധനാകേന്ദ്രത്തിൽ നിന്നും "
        f"സർട്ടിഫിക്കറ്റ് പുതുക്കുക.\n\n"
        f"{center_information.get('name', '')}\n"
        f"അഡ്രസ്സ്: {center_information.get('address', '')}\n"
        f"ഫോൺ: {center_information.get('phone', '')}\n"
        f"ലൊക്കേഷൻ: {center_information.get('google_maps', '')}\n"
        f"{center_information.get('working_hours', '')}\n"
    )


def _build_request(
    url: str,
    data: Optional[bytes] = None,
    headers: Optional[Dict[str, str]] = None,
    method: str = "POST",
    username: str = "",
    password: str = "",
) -> urllib.request.Request:
    headers = headers or {}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    if username or password:
        token = base64.b64encode(f"{username}:{password}".encode("utf-8"))
        req.add_header("Authorization", f"Basic {token.decode('ascii')}")
    return req


def _try_request(
    url: str,
    data: Optional[bytes],
    headers: Dict[str, str],
    method: str,
    username: str,
    password: str,
    timeout: int = 10,
) -> bool:
    req = _build_request(url, data=data, headers=headers,
                         method=method,
                         username=username,
                         password=password)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            code = resp.getcode()
            if 200 <= code < 300:
                if code == 202:
                    print("[SMS DEBUG] Success response 202 Accepted")
                return True
            _set_last_error(f"HTTP {code}: {resp.read().decode('utf-8', errors='ignore')}" if hasattr(resp, 'read') else f"HTTP {code}")
            return False
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read().decode('utf-8', errors='ignore')
        except Exception:
            body = ""
        _set_last_error(f"HTTPError {exc.code}: {body}")
        print(f"[SMS DEBUG] HTTPError {exc.code}: {body}")
        return False
    except urllib.error.URLError as exc:
        _set_last_error(f"URLError: {exc.reason}")
        print(f"[SMS DEBUG] URLError: {exc.reason}")
        return False
    except Exception as exc:
        _set_last_error(f"Exception: {exc}")
        print(f"[SMS DEBUG] Exception: {exc}")
        return False


def ping_sms_server(api_url: str,
                    username: str = "",
                    password: str = "",
                    timeout: int = 5) -> bool:
    try:
        url = sanitize_url(api_url)
    except ValueError:
        return False

    req = _build_request(url, data=None, headers={}, method="GET",
                         username=username, password=password)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return 200 <= resp.getcode() < 500
    except urllib.error.HTTPError as exc:
        return exc.code in (401, 403, 404, 405)
    except urllib.error.URLError:
        return False
    except Exception:
        return False


def send_sms_message(
    phone: str,
    message: str,
    api_url: str,
    username: str = "",
    password: str = "",
    timeout: int = 15,
) -> bool:
    if not phone or not message or not api_url:
        return False

    api_url = sanitize_url(api_url)
    phone_clean = _normalize_sms_phone(phone)
    payload = {
        "textMessage": {
            "text": message,
        },
        "phoneNumbers": [phone_clean],
    }

    json_data = json.dumps(payload).encode("utf-8")
    print(f"[SMS DEBUG] POST {api_url} payload={json.dumps(payload, ensure_ascii=False)}")

    if _try_request(api_url, json_data,
                    {"Content-Type": "application/json"},
                    "POST", username, password, timeout):
        return True

    _set_last_error("SMS request failed for JSON payload")
    return False


def bulk_send_messages(
    vehicles: List[Dict],
    custom_message: Optional[str],
    delay: int,
    api_url: str,
    username: str = "",
    password: str = "",
    timeout: int = 15,
    progress_callback: Optional[Callable[[int, int, int, int, str, str], None]] = None,
    stop_event: Optional[Event] = None,
) -> Thread:
    def _send_thread():
        total = len(vehicles)
        success = 0
        failed = 0
        current = 0

        for vehicle in vehicles:
            if stop_event and stop_event.is_set():
                break
            current += 1
            message = format_sms_message(
                vehicle.get("vehicle_number", ""),
                vehicle.get("owner_name", ""),
                vehicle.get("expiry_date", ""),
                custom_message,
            )
            ok = send_sms_message(
                vehicle.get("phone", ""),
                message,
                api_url,
                username=username,
                password=password,
                timeout=timeout,
            )
            if ok:
                success += 1
                vehicle_id = vehicle.get("id") or vehicle.get("vehicle_id")
                log_message(
                    vehicle_id,
                    vehicle.get("vehicle_number", ""),
                    vehicle.get("phone", ""),
                    message,
                )
                error_message = ""
            else:
                failed += 1
                error_message = get_last_error()

            if progress_callback:
                progress_callback(current, total, success, failed,
                                  vehicle.get("vehicle_number", ""),
                                  error_message)

            if current < total:
                for _ in range(max(1, delay)):
                    if stop_event and stop_event.is_set():
                        break
                    time.sleep(1)
                if stop_event and stop_event.is_set():
                    break

        if progress_callback:
            progress_callback(total, total, success, failed, "DONE", "")

    thread = Thread(target=_send_thread, daemon=True)
    thread.start()
    return thread
