"""
WhatsApp Messaging Page - Auto-send support with date filters
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import os
import calendar as cal_module
from styles import COLORS, FONTS
from database import (get_all_vehicles, get_expired_vehicles,
                      get_expiring_soon_vehicles, log_message)
from whatsapp_sender import (
    format_message, send_whatsapp_message, bulk_send_messages,
    get_whatsapp_status, find_whatsapp_exe, is_whatsapp_installed,
    HAS_AUTOGUI, SEND_PROFILES
)
from datetime import date, datetime, timedelta

# Try importing tkcalendar
try:
    from tkcalendar import Calendar
    HAS_CALENDAR = True
except ImportError:
    HAS_CALENDAR = False


class WhatsAppPage:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.sending = False
        self.filter_date_from_value = None
        self.filter_date_to_value = None
        self.active_calendar_popup = None
        self.build()

    def build(self):
        canvas = tk.Canvas(self.parent, bg=COLORS["bg"],
                           highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.parent, orient="vertical",
                                  command=canvas.yview)
        self.scroll_frame = tk.Frame(canvas, bg=COLORS["bg"])

        self.scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(event):
            try:
                if canvas.winfo_exists():
                    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except (tk.TclError, AttributeError):
                # Canvas destroyed - silently ignore
                pass
        
        try:
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
        except Exception:
            pass

        self.build_status_section()
        self.build_method_section()
        self.build_quick_send()
        self.build_template()
        self.build_bulk_send()
        self.build_progress()

    # =============================================
    # STATUS SECTION
    # =============================================

    def build_status_section(self):
        card = tk.Frame(self.scroll_frame, bg=COLORS["bg_card"],
                        highlightbackground=COLORS["border"],
                        highlightthickness=1)
        card.pack(fill="x", pady=(0, 15), padx=5)

        inner = tk.Frame(card, bg=COLORS["bg_card"])
        inner.pack(fill="x", padx=20, pady=15)

        header = tk.Frame(inner, bg=COLORS["bg_card"])
        header.pack(fill="x", pady=(0, 10))

        tk.Label(header, text="💻 WhatsApp & Auto-Send Status",
                 font=FONTS["subheading"],
                 bg=COLORS["bg_card"], fg=COLORS["text"]).pack(side="left")

        refresh_btn = tk.Label(
            header, text="🔄 Re-detect", font=FONTS["small_bold"],
            bg=COLORS["primary"], fg="white",
            padx=10, pady=3, cursor="hand2")
        refresh_btn.pack(side="right")
        refresh_btn.bind("<Button-1>", lambda e: self.refresh_status())

        self.status_frame = tk.Frame(inner, bg=COLORS["bg_card"])
        self.status_frame.pack(fill="x")
        self.show_status_info()

    def show_status_info(self):
        for w in self.status_frame.winfo_children():
            w.destroy()

        status = get_whatsapp_status()

        row1 = tk.Frame(self.status_frame, bg=COLORS["bg_card"])
        row1.pack(fill="x", pady=2)

        if status["installed"]:
            tk.Label(row1, text="✅ WhatsApp Desktop: FOUND",
                     font=FONTS["body_bold"], bg=COLORS["bg_card"],
                     fg=COLORS["success"]).pack(anchor="w")
            tk.Label(row1, text=f"   Path: {status['path']}",
                     font=FONTS["small"], bg=COLORS["bg_card"],
                     fg=COLORS["text_secondary"]).pack(anchor="w")
        else:
            tk.Label(row1, text="⚠️ WhatsApp Desktop: NOT DETECTED",
                     font=FONTS["body_bold"], bg=COLORS["bg_card"],
                     fg=COLORS["warning"]).pack(anchor="w")
            tk.Label(row1, text="   Will use whatsapp:// protocol (should still work)",
                     font=FONTS["small"], bg=COLORS["bg_card"],
                     fg=COLORS["text_secondary"]).pack(anchor="w")

        row2 = tk.Frame(self.status_frame, bg=COLORS["bg_card"])
        row2.pack(fill="x", pady=(5, 2))

        if HAS_AUTOGUI:
            tk.Label(row2,
                     text="✅ Auto-Send: ENABLED (pyautogui installed)",
                     font=FONTS["body_bold"], bg=COLORS["bg_card"],
                     fg=COLORS["success"]).pack(anchor="w")
        else:
            tk.Label(row2, text="❌ Auto-Send: DISABLED",
                     font=FONTS["body_bold"], bg=COLORS["bg_card"],
                     fg=COLORS["danger"]).pack(anchor="w")

            install_frame = tk.Frame(row2, bg=COLORS["bg_card"])
            install_frame.pack(anchor="w", pady=(3, 0))

            tk.Label(install_frame, text="   Install: ",
                     font=FONTS["small"], bg=COLORS["bg_card"],
                     fg=COLORS["text_secondary"]).pack(side="left")

            install_btn = tk.Label(
                install_frame, text="📦 pip install pyautogui",
                font=FONTS["small_bold"], bg=COLORS["primary"],
                fg="white", padx=10, pady=2, cursor="hand2")
            install_btn.pack(side="left")
            install_btn.bind("<Button-1>",
                             lambda e: self.install_pyautogui())

    # =============================================
    # METHOD SECTION
    # =============================================

    def build_method_section(self):
        card = tk.Frame(self.scroll_frame, bg=COLORS["bg_card"],
                        highlightbackground=COLORS["border"],
                        highlightthickness=1)
        card.pack(fill="x", pady=(0, 15), padx=5)

        inner = tk.Frame(card, bg=COLORS["bg_card"])
        inner.pack(fill="x", padx=20, pady=15)

        tk.Label(inner, text="⚙️ Sending Settings",
                 font=FONTS["subheading"], bg=COLORS["bg_card"],
                 fg=COLORS["text"]).pack(anchor="w", pady=(0, 10))

        # Method
        method_frame = tk.Frame(inner, bg=COLORS["bg_card"])
        method_frame.pack(fill="x", pady=(0, 10))

        tk.Label(method_frame, text="Method:",
                 font=FONTS["small_bold"],
                 bg=COLORS["bg_card"]).pack(side="left")

        self.method_var = tk.StringVar(value="auto")
        for text, value in [("Auto", "auto"),
                            ("Desktop Protocol", "protocol"),
                            ("Desktop Exe", "desktop"),
                            ("Browser", "browser")]:
            ttk.Radiobutton(method_frame, text=text,
                            variable=self.method_var,
                            value=value).pack(side="left", padx=(10, 0))

        # Auto-send toggle
        auto_frame = tk.Frame(inner, bg=COLORS["bg_card"])
        auto_frame.pack(fill="x", pady=(5, 10))

        self.auto_send_var = tk.BooleanVar(value=HAS_AUTOGUI)
        auto_check = ttk.Checkbutton(
            auto_frame,
            text="🚀 Auto-Send (automatically press Enter)",
            variable=self.auto_send_var)
        auto_check.pack(side="left")
        if not HAS_AUTOGUI:
            auto_check.configure(state="disabled")
            tk.Label(auto_frame, text="  (install pyautogui)",
                     font=FONTS["small"], bg=COLORS["bg_card"],
                     fg=COLORS["danger"]).pack(side="left")

        # Wait time
        wait_frame = tk.Frame(inner, bg=COLORS["bg_card"])
        wait_frame.pack(fill="x", pady=(0, 10))

        wait_label_frame = tk.Frame(wait_frame, bg=COLORS["bg_card"])
        wait_label_frame.pack(fill="x", pady=(0, 3))
        
        tk.Label(wait_label_frame, text="⏱️ Wait before send (seconds):",
                 font=FONTS["small_bold"],
                 bg=COLORS["bg_card"]).pack(side="left")

        self.wait_time_var = tk.IntVar(value=15)
        ttk.Spinbox(wait_frame, from_=15, to=30,
                     textvariable=self.wait_time_var,
                     width=5, font=FONTS["input"]).pack(
            side="left", padx=(10, 5))

        tk.Label(wait_frame, text="(min 10s - prevents drafts)",
                 font=FONTS["small"],
                 bg=COLORS["bg_card"], fg=COLORS["text_secondary"]).pack(side="left")

        profile_frame = tk.Frame(inner, bg=COLORS["bg_card"])
        profile_frame.pack(fill="x", pady=(0, 10))

        tk.Label(profile_frame, text="Reliability profile:",
                 font=FONTS["small_bold"],
                 bg=COLORS["bg_card"]).pack(side="left")

        self.send_profile_var = tk.StringVar(value="slow_pc")
        profile_values = list(SEND_PROFILES.keys())
        self.profile_combo = ttk.Combobox(
            profile_frame,
            textvariable=self.send_profile_var,
            values=profile_values,
            state="readonly",
            width=18)
        self.profile_combo.pack(side="left", padx=(10, 5))

        tk.Label(
            profile_frame,
            text="standard = faster, slow_pc = safer, max_reliability = slowest",
            font=FONTS["small"],
            bg=COLORS["bg_card"],
            fg=COLORS["text_secondary"]).pack(side="left")

        # Exe path
        path_frame = tk.Frame(inner, bg=COLORS["bg_card"])
        path_frame.pack(fill="x", pady=(0, 5))

        tk.Label(path_frame, text="WhatsApp Path (optional):",
                 font=FONTS["small_bold"],
                 bg=COLORS["bg_card"]).pack(anchor="w", pady=(0, 3))

        path_row = tk.Frame(path_frame, bg=COLORS["bg_card"])
        path_row.pack(fill="x")

        self.exe_path_var = tk.StringVar()
        detected = find_whatsapp_exe()
        if detected:
            self.exe_path_var.set(detected)

        tk.Entry(path_row, textvariable=self.exe_path_var,
                 font=FONTS["small"], width=50).pack(
            side="left", ipady=4)

        browse_btn = tk.Label(
            path_row, text="📂 Browse", font=FONTS["small_bold"],
            bg=COLORS["secondary"], fg="white",
            padx=10, pady=4, cursor="hand2")
        browse_btn.pack(side="left", padx=(5, 5))
        browse_btn.bind("<Button-1>", lambda e: self.browse_exe())

        test_btn = tk.Label(
            path_row, text="🧪 Test", font=FONTS["small_bold"],
            bg=COLORS["success"], fg="white",
            padx=10, pady=4, cursor="hand2")
        test_btn.pack(side="left")
        test_btn.bind("<Button-1>", lambda e: self.test_method())

    # =============================================
    # QUICK SEND
    # =============================================

    def build_quick_send(self):
        card = tk.Frame(self.scroll_frame, bg=COLORS["bg_card"],
                        highlightbackground=COLORS["border"],
                        highlightthickness=1)
        card.pack(fill="x", pady=(0, 15), padx=5)

        inner = tk.Frame(card, bg=COLORS["bg_card"])
        inner.pack(fill="x", padx=20, pady=15)

        tk.Label(inner, text="📱 Quick Send Message",
                 font=FONTS["subheading"], bg=COLORS["bg_card"],
                 fg=COLORS["text"]).pack(anchor="w", pady=(0, 15))

        row = tk.Frame(inner, bg=COLORS["bg_card"])
        row.pack(fill="x")

        tk.Label(row, text="Phone:", font=FONTS["small_bold"],
                 bg=COLORS["bg_card"]).pack(side="left")
        self.quick_phone = tk.Entry(row, font=FONTS["input"], width=15)
        self.quick_phone.pack(side="left", padx=(5, 15), ipady=4)

        tk.Label(row, text="Vehicle No:", font=FONTS["small_bold"],
                 bg=COLORS["bg_card"]).pack(side="left")
        self.quick_vehicle = tk.Entry(row, font=FONTS["input"], width=15)
        self.quick_vehicle.pack(side="left", padx=(5, 15), ipady=4)

        send_text = "🚀 Auto Send" if HAS_AUTOGUI else "💬 Send"
        send_btn = tk.Label(row, text=send_text, font=FONTS["button"],
                            bg=COLORS["whatsapp"], fg="white",
                            padx=20, pady=6, cursor="hand2")
        send_btn.pack(side="left")
        send_btn.bind("<Button-1>", lambda e: self.quick_send())

    # =============================================
    # TEMPLATE
    # =============================================

    def build_template(self):
        card = tk.Frame(self.scroll_frame, bg=COLORS["bg_card"],
                        highlightbackground=COLORS["border"],
                        highlightthickness=1)
        card.pack(fill="x", pady=(0, 15), padx=5)

        inner = tk.Frame(card, bg=COLORS["bg_card"])
        inner.pack(fill="x", padx=20, pady=15)

        tk.Label(inner, text="📝 Message Template",
                 font=FONTS["subheading"], bg=COLORS["bg_card"],
                 fg=COLORS["text"]).pack(anchor="w", pady=(0, 5))

        tk.Label(inner,
                 text="Use {vehicle_number}, {owner_name}, "
                      "{expiry_date}. Leave empty for default.",
                 font=FONTS["small"], bg=COLORS["bg_card"],
                 fg=COLORS["text_secondary"]).pack(anchor="w", pady=(0, 10))

        self.template_text = scrolledtext.ScrolledText(
            inner, font=FONTS["input"], height=6,
            width=80, wrap="word")
        self.template_text.pack(fill="x")

        btn_frame = tk.Frame(inner, bg=COLORS["bg_card"])
        btn_frame.pack(fill="x", pady=(10, 0))

        preview_btn = tk.Label(btn_frame, text="👁️ Preview",
                               font=FONTS["small_bold"],
                               bg=COLORS["info"], fg="white",
                               padx=15, pady=5, cursor="hand2")
        preview_btn.pack(side="left")
        preview_btn.bind("<Button-1>", lambda e: self.preview_message())

        default_btn = tk.Label(btn_frame, text="🔄 Load Default",
                               font=FONTS["small_bold"],
                               bg=COLORS["secondary"], fg="white",
                               padx=15, pady=5, cursor="hand2")
        default_btn.pack(side="left", padx=(10, 0))
        default_btn.bind("<Button-1>",
                         lambda e: self.load_default_template())

    # =============================================
    # BULK SEND WITH DATE FILTER
    # =============================================

    def build_bulk_send(self):
        card = tk.Frame(self.scroll_frame, bg=COLORS["bg_card"],
                        highlightbackground=COLORS["border"],
                        highlightthickness=1)
        card.pack(fill="x", pady=(0, 15), padx=5)

        inner = tk.Frame(card, bg=COLORS["bg_card"])
        inner.pack(fill="x", padx=20, pady=15)

        tk.Label(inner, text="📨 Bulk Auto-Send Reminders",
                 font=FONTS["subheading"], bg=COLORS["bg_card"],
                 fg=COLORS["text"]).pack(anchor="w", pady=(0, 15))

        # ===== TARGET SELECTION =====
        target_frame = tk.Frame(inner, bg=COLORS["bg_card"])
        target_frame.pack(fill="x", pady=(0, 10))

        self.target_var = tk.StringVar(value="expired")
        
        # ===== DATE FILTER SECTION =====
        self.date_filter_frame = tk.Frame(inner, bg=COLORS["bg_card"])
        self.date_filter_frame.pack(fill="x", pady=(5, 10))

        date_row = tk.Frame(self.date_filter_frame, bg=COLORS["bg_card"])
        date_row.pack(fill="x") 

        # Expiry From
        tk.Label(date_row, text="📅 Expiry From:",
                 font=FONTS["small_bold"],
                 bg=COLORS["bg_card"],
                 fg=COLORS["text"]).pack(side="left")

        self.date_from_frame = tk.Frame(
            date_row, bg="white",
            highlightbackground=COLORS["border"],
            highlightthickness=1, cursor="hand2")
        self.date_from_frame.pack(side="left", padx=(5, 10))

        date_from_inner = tk.Frame(self.date_from_frame, bg="white")
        date_from_inner.pack(padx=6, pady=4)

        self.date_from_icon = tk.Label(
            date_from_inner, text="📅", font=("Segoe UI", 9),
            bg="white", cursor="hand2")
        self.date_from_icon.pack(side="left")

        self.date_from_text = tk.Label(
            date_from_inner, text="Select date",
            font=FONTS["small"], bg="white",
            fg=COLORS["text_secondary"],
            cursor="hand2", width=12, anchor="w")
        self.date_from_text.pack(side="left", padx=(3, 0))

        self.date_from_clear = tk.Label(
            date_from_inner, text="✕", font=("Segoe UI", 8),
            bg="white", fg=COLORS["text_light"], cursor="hand2")
        self.date_from_clear.pack(side="left", padx=(3, 0))
        self.date_from_clear.bind(
            "<Button-1>", lambda e: self.clear_bulk_date("from"))
        self.date_from_clear.pack_forget()

        for w in [self.date_from_frame, date_from_inner,
                  self.date_from_icon, self.date_from_text]:
            w.bind("<Button-1>",
                   lambda e: self.open_bulk_calendar("from"))
            w.bind("<Enter>",
                   lambda e: self.date_from_frame.configure(
                       highlightbackground=COLORS["primary"]))
            w.bind("<Leave>",
                   lambda e: self.date_from_frame.configure(
                       highlightbackground=COLORS["border"]))

        # Expiry To
        tk.Label(date_row, text="To:",
                 font=FONTS["small_bold"],
                 bg=COLORS["bg_card"],
                 fg=COLORS["text"]).pack(side="left")

        self.date_to_frame = tk.Frame(
            date_row, bg="white",
            highlightbackground=COLORS["border"],
            highlightthickness=1, cursor="hand2")
        self.date_to_frame.pack(side="left", padx=(5, 15))

        date_to_inner = tk.Frame(self.date_to_frame, bg="white")
        date_to_inner.pack(padx=6, pady=4)

        self.date_to_icon = tk.Label(
            date_to_inner, text="📅", font=("Segoe UI", 9),
            bg="white", cursor="hand2")
        self.date_to_icon.pack(side="left")

        self.date_to_text = tk.Label(
            date_to_inner, text="Select date",
            font=FONTS["small"], bg="white",
            fg=COLORS["text_secondary"],
            cursor="hand2", width=12, anchor="w")
        self.date_to_text.pack(side="left", padx=(3, 0))

        self.date_to_clear = tk.Label(
            date_to_inner, text="✕", font=("Segoe UI", 8),
            bg="white", fg=COLORS["text_light"], cursor="hand2")
        self.date_to_clear.pack(side="left", padx=(3, 0))
        self.date_to_clear.bind(
            "<Button-1>", lambda e: self.clear_bulk_date("to"))
        self.date_to_clear.pack_forget()

        for w in [self.date_to_frame, date_to_inner,
                  self.date_to_icon, self.date_to_text]:
            w.bind("<Button-1>",
                   lambda e: self.open_bulk_calendar("to"))
            w.bind("<Enter>",
                   lambda e: self.date_to_frame.configure(
                       highlightbackground=COLORS["primary"]))
            w.bind("<Leave>",
                   lambda e: self.date_to_frame.configure(
                       highlightbackground=COLORS["border"]))

        # Quick date buttons
        quick_frame = tk.Frame(self.date_filter_frame, bg=COLORS["bg_card"])
        quick_frame.pack(fill="x", pady=(8, 0))

        quick_dates = [
            ("Expired", self.set_expired_range),
            ("Next 7d", self.set_7day_range),
            ("Next 30d", self.set_30day_range),
            ("Next 90d", self.set_90day_range),
            ("Clear", self.clear_all_dates),
        ]

        for text, cmd in quick_dates:
            qbtn = tk.Label(
                quick_frame, text=text, font=FONTS["small"],
                bg=COLORS["bg"], fg=COLORS["primary"],
                padx=6, pady=2, cursor="hand2",
                relief="solid", borderwidth=1)
            qbtn.pack(side="left", padx=2)
            qbtn.bind("<Button-1>", lambda e, c=cmd: c())
            qbtn.bind("<Enter>",
                      lambda e, b=qbtn: b.configure(
                          bg=COLORS["primary"], fg="white"))
            qbtn.bind("<Leave>",
                      lambda e, b=qbtn: b.configure(
                          bg=COLORS["bg"], fg=COLORS["primary"]))

        # Target count and vehicle preview
        self.target_info = tk.Label(
            inner, text="", font=FONTS["body_bold"],
            bg=COLORS["bg_card"], fg=COLORS["text_secondary"])
        self.target_info.pack(anchor="w", pady=(5, 5))

        # Filtered vehicle preview list
        self.preview_frame = tk.Frame(inner, bg=COLORS["bg_card"])
        self.preview_frame.pack(fill="x", pady=(0, 10))

        # Delay
        delay_frame = tk.Frame(inner, bg=COLORS["bg_card"])
        delay_frame.pack(fill="x", pady=(0, 15))

        tk.Label(delay_frame, text="Delay between messages (sec):",
                 font=FONTS["small_bold"],
                 bg=COLORS["bg_card"]).pack(side="left")

        self.delay_var = tk.IntVar(value=15)
        ttk.Spinbox(delay_frame, from_=15, to=60,
                     textvariable=self.delay_var,
                     width=5, font=FONTS["input"]).pack(
            side="left", padx=(10, 5))

        tk.Label(delay_frame,
                 text="(includes WhatsApp load time)",
                 font=FONTS["small"], bg=COLORS["bg_card"],
                 fg=COLORS["text_light"]).pack(side="left")

        # Send / Stop buttons
        btn_frame = tk.Frame(inner, bg=COLORS["bg_card"])
        btn_frame.pack(fill="x")

        btn_text = ("🚀 Start Auto Bulk Send"
                    if HAS_AUTOGUI else "💬 Start Bulk Send")

        self.bulk_send_btn = tk.Label(
            btn_frame, text=btn_text, font=FONTS["button"],
            bg=COLORS["whatsapp"], fg="white",
            padx=25, pady=10, cursor="hand2")
        self.bulk_send_btn.pack(side="left")
        self.bulk_send_btn.bind("<Button-1>",
                                lambda e: self.start_bulk_send())

        self.stop_btn = tk.Label(
            btn_frame, text="⏹️ Stop", font=FONTS["button"],
            bg=COLORS["danger"], fg="white",
            padx=25, pady=10, cursor="hand2")
        self.stop_btn.pack(side="left", padx=(10, 0))
        self.stop_btn.bind("<Button-1>",
                           lambda e: self.stop_bulk_send())
        self.stop_btn.pack_forget()

        # Info text
        if HAS_AUTOGUI:
            info_text = (
                "🚀 AUTO-SEND: Messages sent automatically\n"
                "• Don't use mouse/keyboard during sending\n"
                "• Move mouse to top-left corner to STOP")
            info_color = COLORS["success"]
        else:
            info_text = (
                "⚠️ MANUAL: You need to click Send in WhatsApp\n"
                "• Install pyautogui for auto-send")
            info_color = COLORS["warning"]

        tk.Label(inner, text=info_text, font=FONTS["small"],
                 bg=COLORS["bg_card"], fg=info_color,
                 wraplength=700, justify="left").pack(
            anchor="w", pady=(15, 0))

        # Initial state
        self.on_target_changed()

    # =============================================
    # DATE FILTER CALENDAR METHODS
    # =============================================

    def open_bulk_calendar(self, which):
        """Open calendar popup for bulk send date filter"""
        self.close_bulk_calendar()

        self.active_calendar_popup = tk.Toplevel(self.parent)
        self.active_calendar_popup.overrideredirect(True)
        self.active_calendar_popup.configure(
            bg=COLORS["border"],
            highlightbackground=COLORS["primary"],
            highlightthickness=2)

        if which == "from":
            ref = self.date_from_frame
            current = self.filter_date_from_value
        else:
            ref = self.date_to_frame
            current = self.filter_date_to_value

        x = ref.winfo_rootx()
        y = ref.winfo_rooty() + ref.winfo_height() + 2
        self.active_calendar_popup.geometry(f"+{x}+{y}")
        self.active_calendar_popup.attributes("-topmost", True)

        main = tk.Frame(self.active_calendar_popup, bg=COLORS["bg_card"])
        main.pack(fill="both", expand=True, padx=1, pady=1)

        # Header
        title = "📅 Expiry From" if which == "from" else "📅 Expiry To"
        header = tk.Frame(main, bg=COLORS["primary"])
        header.pack(fill="x")
        tk.Label(header, text=title, font=FONTS["small_bold"],
                 bg=COLORS["primary"], fg="white", pady=6).pack()

        if HAS_CALENDAR:
            init_date = current if current else date.today()
            cal = Calendar(
                main, selectmode="day",
                year=init_date.year,
                month=init_date.month,
                day=init_date.day,
                font=("Segoe UI", 10),
                background=COLORS["primary"],
                foreground="white",
                headersbackground=COLORS["primary_dark"],
                headersforeground="white",
                selectbackground=COLORS["primary"],
                selectforeground="white",
                normalbackground="white",
                normalforeground=COLORS["text"],
                weekendbackground="#F8FAFC",
                weekendforeground=COLORS["text"],
                othermonthforeground=COLORS["text_light"],
                borderwidth=0, cursor="hand2")
            cal.pack(padx=8, pady=5)

            # Quick shortcuts
            qframe = tk.Frame(main, bg=COLORS["bg_card"])
            qframe.pack(fill="x", padx=8, pady=(0, 5))

            shortcuts = [
                ("Today", date.today()),
                ("-7d", date.today() - timedelta(days=7)),
                ("-30d", date.today() - timedelta(days=30)),
                ("+7d", date.today() + timedelta(days=7)),
                ("+30d", date.today() + timedelta(days=30)),
                ("+90d", date.today() + timedelta(days=90)),
            ]

            for text, target in shortcuts:
                qb = tk.Label(qframe, text=text,
                              font=("Segoe UI", 8),
                              bg=COLORS["bg"], fg=COLORS["primary"],
                              padx=4, pady=2, cursor="hand2",
                              relief="solid", borderwidth=1)
                qb.pack(side="left", padx=1)
                qb.bind("<Button-1>",
                        lambda e, d=target, c=cal: c.selection_set(d))
                qb.bind("<Enter>",
                        lambda e, b=qb: b.configure(
                            bg=COLORS["primary"], fg="white"))
                qb.bind("<Leave>",
                        lambda e, b=qb: b.configure(
                            bg=COLORS["bg"], fg=COLORS["primary"]))

            # Buttons
            bframe = tk.Frame(main, bg=COLORS["bg_card"])
            bframe.pack(fill="x", padx=8, pady=(0, 8))

            select_btn = tk.Label(
                bframe, text="✅ Select", font=FONTS["small_bold"],
                bg=COLORS["primary"], fg="white",
                padx=12, pady=4, cursor="hand2")
            select_btn.pack(side="left", padx=(0, 5))
            select_btn.bind("<Button-1>",
                            lambda e, w=which, c=cal:
                            self.set_bulk_date(w, c.selection_get()))

            cancel_btn = tk.Label(
                bframe, text="✖ Cancel", font=FONTS["small_bold"],
                bg=COLORS["secondary"], fg="white",
                padx=12, pady=4, cursor="hand2")
            cancel_btn.pack(side="left")
            cancel_btn.bind("<Button-1>",
                            lambda e: self.close_bulk_calendar())

            cal.bind("<<CalendarSelected>>",
                     lambda e, w=which, c=cal:
                     self.set_bulk_date(w, c.selection_get()))

        else:
            self.build_custom_bulk_calendar(main, which, current)

        self.active_calendar_popup.lift()
        self.active_calendar_popup.focus_set()

    def build_custom_bulk_calendar(self, parent, which, current):
        """Fallback calendar without tkcalendar"""
        init = current if current else date.today()
        self._bcal_year = init.year
        self._bcal_month = init.month
        self._bcal_which = which

        nav = tk.Frame(parent, bg=COLORS["bg_card"])
        nav.pack(fill="x", padx=8, pady=5)

        prev_btn = tk.Label(nav, text="◀",
                            font=("Segoe UI", 12, "bold"),
                            bg=COLORS["bg_card"],
                            fg=COLORS["primary"], cursor="hand2")
        prev_btn.pack(side="left")
        prev_btn.bind("<Button-1>",
                      lambda e: self._bcal_nav(-1))

        self._bcal_title = tk.Label(nav, text="",
                                    font=FONTS["body_bold"],
                                    bg=COLORS["bg_card"],
                                    fg=COLORS["text"])
        self._bcal_title.pack(side="left", expand=True)

        next_btn = tk.Label(nav, text="▶",
                            font=("Segoe UI", 12, "bold"),
                            bg=COLORS["bg_card"],
                            fg=COLORS["primary"], cursor="hand2")
        next_btn.pack(side="right")
        next_btn.bind("<Button-1>",
                      lambda e: self._bcal_nav(1))

        self._bcal_days = tk.Frame(parent, bg=COLORS["bg_card"])
        self._bcal_days.pack(fill="x", padx=8)

        cancel_btn = tk.Label(parent, text="✖ Cancel",
                              font=FONTS["small_bold"],
                              bg=COLORS["secondary"], fg="white",
                              padx=12, pady=4, cursor="hand2")
        cancel_btn.pack(pady=(5, 8))
        cancel_btn.bind("<Button-1>",
                        lambda e: self.close_bulk_calendar())

        self._draw_bcal()

    def _bcal_nav(self, direction):
        self._bcal_month += direction
        if self._bcal_month > 12:
            self._bcal_month = 1
            self._bcal_year += 1
        elif self._bcal_month < 1:
            self._bcal_month = 12
            self._bcal_year -= 1
        self._draw_bcal()

    def _draw_bcal(self):
        for w in self._bcal_days.winfo_children():
            w.destroy()

        self._bcal_title.configure(
            text=f"{cal_module.month_name[self._bcal_month]} "
                 f"{self._bcal_year}")

        for i, h in enumerate(["Mo", "Tu", "We", "Th",
                                "Fr", "Sa", "Su"]):
            tk.Label(self._bcal_days, text=h,
                     font=("Segoe UI", 8, "bold"),
                     bg=COLORS["bg_card"],
                     fg=COLORS["text_secondary"],
                     width=4).grid(row=0, column=i)

        cal_data = cal_module.monthcalendar(
            self._bcal_year, self._bcal_month)
        today = date.today()

        for ri, week in enumerate(cal_data):
            for ci, day in enumerate(week):
                if day == 0:
                    tk.Label(self._bcal_days, text="",
                             bg=COLORS["bg_card"],
                             width=4, height=1).grid(
                        row=ri + 1, column=ci)
                else:
                    d = date(self._bcal_year, self._bcal_month, day)
                    is_today = d == today
                    bg = COLORS["primary_light"] if is_today else "white"
                    fg = COLORS["primary"] if is_today else COLORS["text"]

                    lbl = tk.Label(self._bcal_days, text=str(day),
                                   font=("Segoe UI", 9),
                                   bg=bg, fg=fg, width=4,
                                   height=1, cursor="hand2")
                    lbl.grid(row=ri + 1, column=ci, padx=1, pady=1)
                    lbl.bind("<Button-1>",
                             lambda e, dt=d:
                             self.set_bulk_date(self._bcal_which, dt))

    def set_bulk_date(self, which, selected_date):
        """Set a date for bulk send filter"""
        if which == "from":
            self.filter_date_from_value = selected_date
            self.date_from_text.configure(
                text=selected_date.strftime("%Y-%m-%d"),
                fg=COLORS["text"])
            self.date_from_clear.pack(side="left", padx=(3, 0))
        else:
            self.filter_date_to_value = selected_date
            self.date_to_text.configure(
                text=selected_date.strftime("%Y-%m-%d"),
                fg=COLORS["text"])
            self.date_to_clear.pack(side="left", padx=(3, 0))

        self.close_bulk_calendar()

        # Auto-switch to custom if dates set manually
        if self.target_var.get() != "custom":
            self.target_var.set("custom")

        self.update_target_count()

    def clear_bulk_date(self, which):
        """Clear a bulk send date filter"""
        if which == "from":
            self.filter_date_from_value = None
            self.date_from_text.configure(
                text="Select date", fg=COLORS["text_secondary"])
            self.date_from_clear.pack_forget()
        else:
            self.filter_date_to_value = None
            self.date_to_text.configure(
                text="Select date", fg=COLORS["text_secondary"])
            self.date_to_clear.pack_forget()

        self.update_target_count()

    def clear_all_dates(self):
        """Clear both date filters"""
        self.clear_bulk_date("from")
        self.clear_bulk_date("to")
        self.update_target_count()

    def close_bulk_calendar(self):
        """Close calendar popup"""
        if self.active_calendar_popup and \
                self.active_calendar_popup.winfo_exists():
            self.active_calendar_popup.destroy()
        self.active_calendar_popup = None

    # =============================================
    # QUICK DATE RANGE SETTERS
    # =============================================

    def set_expired_range(self):
        """Set range for expired vehicles"""
        past = date.today() - timedelta(days=3650)
        yesterday = date.today() - timedelta(days=1)
        self.filter_date_from_value = past
        self.filter_date_to_value = yesterday
        self.date_from_text.configure(text="Past", fg=COLORS["danger"])
        self.date_to_text.configure(
            text=yesterday.strftime("%Y-%m-%d"), fg=COLORS["danger"])
        self.date_from_clear.pack(side="left", padx=(3, 0))
        self.date_to_clear.pack(side="left", padx=(3, 0))
        self.target_var.set("custom")
        self.update_target_count()

    def set_7day_range(self):
        """Set range for next 7 days"""
        today = date.today()
        end = today + timedelta(days=7)
        self.filter_date_from_value = today
        self.filter_date_to_value = end
        self.date_from_text.configure(
            text=today.strftime("%Y-%m-%d"), fg=COLORS["text"])
        self.date_to_text.configure(
            text=end.strftime("%Y-%m-%d"), fg=COLORS["text"])
        self.date_from_clear.pack(side="left", padx=(3, 0))
        self.date_to_clear.pack(side="left", padx=(3, 0))
        self.target_var.set("custom")
        self.update_target_count()

    def set_30day_range(self):
        """Set range for next 30 days"""
        today = date.today()
        end = today + timedelta(days=30)
        self.filter_date_from_value = today
        self.filter_date_to_value = end
        self.date_from_text.configure(
            text=today.strftime("%Y-%m-%d"), fg=COLORS["text"])
        self.date_to_text.configure(
            text=end.strftime("%Y-%m-%d"), fg=COLORS["text"])
        self.date_from_clear.pack(side="left", padx=(3, 0))
        self.date_to_clear.pack(side="left", padx=(3, 0))
        self.target_var.set("custom")
        self.update_target_count()

    def set_90day_range(self):
        """Set range for next 90 days"""
        today = date.today()
        end = today + timedelta(days=90)
        self.filter_date_from_value = today
        self.filter_date_to_value = end
        self.date_from_text.configure(
            text=today.strftime("%Y-%m-%d"), fg=COLORS["text"])
        self.date_to_text.configure(
            text=end.strftime("%Y-%m-%d"), fg=COLORS["text"])
        self.date_from_clear.pack(side="left", padx=(3, 0))
        self.date_to_clear.pack(side="left", padx=(3, 0))
        self.target_var.set("custom")
        self.update_target_count()

    def on_target_changed(self):
        """Handle target radio button change"""
        target = self.target_var.get()

        if target == "custom":
            # Show date filter
            self.date_filter_frame.pack(fill="x", pady=(5, 10))
        elif target == "expired":
            self.set_expired_range()
            return
        elif target == "expiring_7":
            self.set_7day_range()
            return
        elif target == "expiring_30":
            self.set_30day_range()
            return
        else:
            # All vehicles - clear dates
            self.clear_all_dates()

        self.update_target_count()

    # =============================================
    # GET FILTERED VEHICLES
    # =============================================

    def get_target_vehicles(self):
        """Get vehicles based on target + date filters"""
        target = self.target_var.get()

        if target == "custom":
            # Use date range filter
            filters = {}
            if self.filter_date_from_value:
                filters["expiry_from"] = \
                    self.filter_date_from_value.strftime("%Y-%m-%d")
            if self.filter_date_to_value:
                filters["expiry_to"] = \
                    self.filter_date_to_value.strftime("%Y-%m-%d")

            if filters:
                return get_all_vehicles(filters)
            else:
                return get_all_vehicles()

        elif target == "expired":
            if self.filter_date_from_value and self.filter_date_to_value:
                filters = {
                    "expiry_from": self.filter_date_from_value.strftime(
                        "%Y-%m-%d"),
                    "expiry_to": self.filter_date_to_value.strftime(
                        "%Y-%m-%d")
                }
                return get_all_vehicles(filters)
            return get_expired_vehicles()

        elif target == "expiring_7":
            if self.filter_date_from_value and self.filter_date_to_value:
                filters = {
                    "expiry_from": self.filter_date_from_value.strftime(
                        "%Y-%m-%d"),
                    "expiry_to": self.filter_date_to_value.strftime(
                        "%Y-%m-%d")
                }
                return get_all_vehicles(filters)
            return get_expiring_soon_vehicles(7)

        elif target == "expiring_30":
            if self.filter_date_from_value and self.filter_date_to_value:
                filters = {
                    "expiry_from": self.filter_date_from_value.strftime(
                        "%Y-%m-%d"),
                    "expiry_to": self.filter_date_to_value.strftime(
                        "%Y-%m-%d")
                }
                return get_all_vehicles(filters)
            return get_expiring_soon_vehicles(30)

        elif target == "all":
            return get_all_vehicles()

        return []

    def update_target_count(self):
        """Update vehicle count and preview"""
        vehicles = self.get_target_vehicles()
        count = len(vehicles)

        # Date range text
        date_info = ""
        if self.filter_date_from_value:
            date_info += f" from {self.filter_date_from_value.strftime('%Y-%m-%d')}"
        if self.filter_date_to_value:
            date_info += f" to {self.filter_date_to_value.strftime('%Y-%m-%d')}"

        self.target_info.configure(
            text=f"📋 {count} vehicle(s) found{date_info}",
            fg=COLORS["success"] if count > 0 else COLORS["danger"])

        # Update preview
        for w in self.preview_frame.winfo_children():
            w.destroy()

        if count > 0 and count <= 50:
            # Show small preview table
            preview_label = tk.Label(
                self.preview_frame,
                text=f"Preview ({min(count, 10)} of {count}):",
                font=FONTS["small_bold"],
                bg=COLORS["bg_card"],
                fg=COLORS["text_secondary"])
            preview_label.pack(anchor="w", pady=(0, 3))

            cols = ("Vehicle No", "Phone", "Expiry", "Owner")
            tree = ttk.Treeview(
                self.preview_frame, columns=cols,
                show="headings",
                height=min(5, count))

            for col in cols:
                tree.heading(col, text=col)
                tree.column(col, width=130)

            today_str = date.today().strftime("%Y-%m-%d")
            for v in vehicles[:10]:
                tag = "expired" if v["expiry_date"] < today_str else ""
                tree.insert("", "end", values=(
                    v["vehicle_number"],
                    v["phone"],
                    v["expiry_date"],
                    v.get("owner_name", "")
                ), tags=(tag,))

            tree.tag_configure("expired", background="#FEE2E2")
            tree.pack(fill="x")

            if count > 10:
                tk.Label(
                    self.preview_frame,
                    text=f"... and {count - 10} more",
                    font=FONTS["small"],
                    bg=COLORS["bg_card"],
                    fg=COLORS["text_light"]).pack(anchor="w")

        elif count == 0:
            tk.Label(
                self.preview_frame,
                text="⚠️ No vehicles match this filter. "
                     "Try different date range.",
                font=FONTS["small"],
                bg=COLORS["bg_card"],
                fg=COLORS["warning"]).pack(anchor="w")

    # =============================================
    # PROGRESS SECTION
    # =============================================

    def build_progress(self):
        card = tk.Frame(self.scroll_frame, bg=COLORS["bg_card"],
                        highlightbackground=COLORS["border"],
                        highlightthickness=1)
        card.pack(fill="x", pady=(0, 15), padx=5)

        inner = tk.Frame(card, bg=COLORS["bg_card"])
        inner.pack(fill="x", padx=20, pady=15)

        tk.Label(inner, text="📊 Progress",
                 font=FONTS["subheading"], bg=COLORS["bg_card"],
                 fg=COLORS["text"]).pack(anchor="w", pady=(0, 10))

        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            inner, variable=self.progress_var,
            maximum=100, length=400)
        self.progress_bar.pack(fill="x", pady=(0, 10))

        self.progress_label = tk.Label(
            inner, text="Ready to send", font=FONTS["body"],
            bg=COLORS["bg_card"], fg=COLORS["text_secondary"])
        self.progress_label.pack(anchor="w")

        self.log_text = scrolledtext.ScrolledText(
            inner, font=FONTS["small"], height=10,
            width=80, state="disabled", wrap="word")
        self.log_text.pack(fill="x", pady=(10, 0))

    # =============================================
    # ACTION METHODS
    # =============================================

    def refresh_status(self):
        self.show_status_info()
        self.add_log("🔍 Status refreshed")

    def browse_exe(self):
        from tkinter import filedialog
        filepath = filedialog.askopenfilename(
            title="Select WhatsApp",
            filetypes=[("WhatsApp", "WhatsApp.exe"),
                       ("Executable", "*.exe"),
                       ("All", "*.*")])
        if filepath:
            self.exe_path_var.set(filepath)
            self.add_log(f"📂 Set path: {filepath}")

    def install_pyautogui(self):
        import subprocess
        import sys
        self.add_log("📦 Installing pyautogui...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "pyautogui"])
            self.add_log("✅ Installed! Restart app.")
            messagebox.showinfo("Installed",
                                "✅ pyautogui installed!\n"
                                "Restart the application.")
        except Exception as e:
            self.add_log(f"❌ Failed: {e}")
            messagebox.showerror("Failed", str(e))

    def test_method(self):
        test_dialog = tk.Toplevel(self.parent)
        test_dialog.title("🧪 Test Send")
        test_dialog.geometry("420x250")
        test_dialog.transient(self.parent)
        test_dialog.grab_set()
        test_dialog.configure(bg=COLORS["bg_card"])

        x = (test_dialog.winfo_screenwidth() // 2) - 210
        y = (test_dialog.winfo_screenheight() // 2) - 125
        test_dialog.geometry(f"+{x}+{y}")

        tk.Label(test_dialog, text="Enter phone number:",
                 font=FONTS["body_bold"],
                 bg=COLORS["bg_card"]).pack(pady=(20, 10))

        test_phone = tk.Entry(test_dialog, font=FONTS["input"],
                              width=20)
        test_phone.pack(ipady=6)
        test_phone.focus()

        auto = self.auto_send_var.get()
        mode = "AUTO" if auto else "Manual"
        tk.Label(test_dialog, text=f"Mode: {mode}",
                 font=FONTS["small"], bg=COLORS["bg_card"],
                 fg=COLORS["text_secondary"]).pack(pady=5)

        def do_test():
            ph = test_phone.get().strip()
            if not ph:
                return
            test_dialog.destroy()
            msg = "🧪 Test from Vehicle Manager"
            self.add_log(f"\n🧪 Testing: {ph}")
            send_whatsapp_message(
                ph, msg, method=self.method_var.get(),
                exe_path=self.exe_path_var.get().strip() or None,
                auto_send=auto,
                wait_time=self.wait_time_var.get(),
                send_profile=self.send_profile_var.get())
            self.add_log("✅ Test done")

        tk.Label(test_dialog, text="🚀 Send Test",
                 font=FONTS["button"], bg=COLORS["whatsapp"],
                 fg="white", padx=20, pady=8,
                 cursor="hand2").pack(pady=15)
        test_dialog.winfo_children()[-1].bind(
            "<Button-1>", lambda e: do_test())
        test_phone.bind("<Return>", lambda e: do_test())

    def quick_send(self):
        phone = self.quick_phone.get().strip()
        if not phone:
            messagebox.showwarning("Warning", "Enter phone!")
            return

        vehicle = self.quick_vehicle.get().strip()
        custom = self.template_text.get("1.0", "end").strip() or None
        msg = format_message(vehicle or "N/A", "",
                             date.today().strftime("%Y-%m-%d"), custom)

        self.add_log(f"\n📱 Sending to {phone}...")
        success = send_whatsapp_message(
            phone, msg, method=self.method_var.get(),
            exe_path=self.exe_path_var.get().strip() or None,
            auto_send=self.auto_send_var.get(),
            wait_time=self.wait_time_var.get(),
            send_profile=self.send_profile_var.get())

        self.add_log(f"{'✅' if success else '❌'} {phone}")

    def preview_message(self):
        custom = self.template_text.get("1.0", "end").strip() or None
        msg = format_message("KA01AB1234", "John", "2025-01-15", custom)
        messagebox.showinfo("Preview", msg)

    def load_default_template(self):
        self.template_text.delete("1.0", "end")
        self.template_text.insert("1.0",
            "🚗 *Vehicle Reminder*\n"
            "Dear *{owner_name}*,\n\n"
            "Vehicle: *{vehicle_number}*\n"
            "Expiry: *{expiry_date}*\n\n"
            "Please renew. Thank you! 🙏")

    def start_bulk_send(self):
        if self.sending:
            messagebox.showwarning("Warning", "Already sending!")
            return

        vehicles = self.get_target_vehicles()
        if not vehicles:
            messagebox.showinfo("Info", "No vehicles to send!")
            return

        method = self.method_var.get()
        auto = self.auto_send_var.get()
        wait = self.wait_time_var.get()
        delay = self.delay_var.get()
        mode = "AUTO" if auto else "Manual"
        profile = self.send_profile_var.get()

        # Date range info
        date_info = ""
        if self.filter_date_from_value:
            date_info += f"\nFrom: {self.filter_date_from_value}"
        if self.filter_date_to_value:
            date_info += f"\nTo: {self.filter_date_to_value}"

        warning = ""
        if auto:
            warning = ("\n\n⚠️ Don't use mouse/keyboard during sending!")

        confirm = messagebox.askyesno(
            "Confirm",
            f"Send to {len(vehicles)} vehicle(s)?\n\n"
            f"Mode: {mode}\n"
            f"Profile: {profile}\n"
            f"Target: {self.target_var.get()}"
            f"{date_info}\n"
            f"Delay: {delay}s"
            f"{warning}")

        if not confirm:
            return

        self.sending = True
        self.bulk_send_btn.configure(
            bg=COLORS["secondary"], text="⏳ Sending...")
        self.stop_btn.pack(side="left", padx=(10, 0))
        self.progress_var.set(0)

        custom = self.template_text.get(
            "1.0", "end").strip() or None

        self.add_log(f"\n{'='*50}")
        self.add_log(f"🚀 BULK SEND STARTED")
        self.add_log(
            f"Mode: {mode} | Profile: {profile} | Targets: {len(vehicles)}")
        if date_info:
            self.add_log(f"Date Range:{date_info}")
        self.add_log(f"{'='*50}\n")

        def progress_callback(current, total, success, failed, vn):
            def update():
                if not self.sending and vn != "DONE":
                    return

                pct = (current / total) * 100
                self.progress_var.set(pct)

                if vn == "DONE":
                    self.progress_label.configure(
                        text=f"✅ Done! Sent: {success}, "
                             f"Failed: {failed}")
                    self.add_log(
                        f"\n{'='*50}\n"
                        f"✅ COMPLETE: {success}/{total}\n"
                        f"{'='*50}")
                    self.sending = False
                    btn_text = ("🚀 Start Auto Bulk Send"
                                if HAS_AUTOGUI
                                else "💬 Start Bulk Send")
                    self.bulk_send_btn.configure(
                        bg=COLORS["whatsapp"], text=btn_text)
                    self.stop_btn.pack_forget()
                else:
                    self.progress_label.configure(
                        text=f"Sending {current}/{total} — {vn}")
                    s = "✅" if success >= current - failed else "❌"
                    self.add_log(f"{s} [{current}/{total}] {vn}")

            self.parent.after(0, update)

        bulk_send_messages(
            vehicles, custom, delay,
            method=method, auto_send=auto,
            wait_time=wait,
            progress_callback=progress_callback,
            send_profile=profile)

    def stop_bulk_send(self):
        self.sending = False
        self.add_log("\n⏹️ STOPPED")
        btn_text = ("🚀 Start Auto Bulk Send"
                    if HAS_AUTOGUI else "💬 Start Bulk Send")
        self.bulk_send_btn.configure(
            bg=COLORS["whatsapp"], text=btn_text)
        self.stop_btn.pack_forget()
        self.progress_label.configure(text="Stopped")

    def add_log(self, text):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", text + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
