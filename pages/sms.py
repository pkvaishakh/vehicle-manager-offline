"""
SMS Reminder Page - bulk SMS using a local Android SMS gateway server.
"""
import calendar as cal_module
import json
import os
import tkinter as tk
from datetime import date, datetime, timedelta
from threading import Event
from tkinter import ttk, messagebox, scrolledtext

from database import (
    get_all_vehicles,
    get_expired_vehicles,
    get_expiring_soon_vehicles,
)
from sms_sender import (
    bulk_send_messages,
    ping_sms_server,
    format_sms_message,
)
from styles import COLORS, FONTS

SMS_CONFIG_FILENAME = "sms_config.json"

try:
    from tkcalendar import Calendar
    HAS_CALENDAR = True
except ImportError:
    HAS_CALENDAR = False


class SMSPage:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.sending = False
        self.stop_event = None
        self.filter_date_from_value = None
        self.filter_date_to_value = None
        self.active_calendar_popup = None
        self.build()
        self.load_config()
        self.on_target_changed()

    def get_config_path(self):
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        return os.path.join(root, SMS_CONFIG_FILENAME)

    def load_config(self):
        try:
            path = self.get_config_path()
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                self.api_url_var.set(config.get("api_url", ""))
                self.api_username_var.set(config.get("username", ""))
                self.api_password_var.set(config.get("password", ""))
        except Exception:
            pass

    def save_config(self):
        try:
            path = self.get_config_path()
            config = {
                "api_url": self.api_url_var.get().strip(),
                "username": self.api_username_var.get().strip(),
                "password": self.api_password_var.get().strip(),
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
        except Exception:
            pass

    def build(self):
        canvas = tk.Canvas(self.parent, bg=COLORS["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.parent, orient="vertical",
                                  command=canvas.yview)
        self.scroll_frame = tk.Frame(canvas, bg=COLORS["bg"])

        self.scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(event):
            try:
                if canvas.winfo_exists():
                    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except (tk.TclError, AttributeError):
                pass

        try:
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
        except Exception:
            pass

        self.build_server_section()
        self.build_template()
        self.build_bulk_send()
        self.build_progress()

    def build_server_section(self):
        card = tk.Frame(self.scroll_frame, bg=COLORS["bg_card"],
                        highlightbackground=COLORS["border"],
                        highlightthickness=1)
        card.pack(fill="x", pady=(0, 15), padx=5)

        inner = tk.Frame(card, bg=COLORS["bg_card"])
        inner.pack(fill="x", padx=20, pady=15)

        tk.Label(inner, text="📡 SMS Gateway Configuration",
                 font=FONTS["subheading"], bg=COLORS["bg_card"],
                 fg=COLORS["text"]).pack(anchor="w", pady=(0, 10))

        row1 = tk.Frame(inner, bg=COLORS["bg_card"])
        row1.pack(fill="x", pady=(0, 10))

        tk.Label(row1, text="Local API URL:", font=FONTS["small_bold"],
                 bg=COLORS["bg_card"]).pack(side="left")
        self.api_url_var = tk.StringVar()
        api_url_entry = tk.Entry(row1, textvariable=self.api_url_var,
                 font=FONTS["input"], width=42)
        api_url_entry.pack(side="left", padx=(5, 10), ipady=4)
        api_url_entry.bind("<FocusOut>", lambda e: self.save_config())

        test_btn = tk.Label(row1, text="🧪 Test Server",
                             font=FONTS["small_bold"],
                             bg=COLORS["success"], fg="white",
                             padx=15, pady=6, cursor="hand2")
        test_btn.pack(side="left")
        test_btn.bind("<Button-1>", lambda e: self.test_server())

        row2 = tk.Frame(inner, bg=COLORS["bg_card"])
        row2.pack(fill="x", pady=(0, 10))

        tk.Label(row2, text="Username:", font=FONTS["small_bold"],
                 bg=COLORS["bg_card"]).pack(side="left")
        self.api_username_var = tk.StringVar()
        api_username_entry = tk.Entry(row2, textvariable=self.api_username_var,
                 font=FONTS["input"], width=18)
        api_username_entry.pack(side="left", padx=(5, 20), ipady=4)
        api_username_entry.bind("<FocusOut>", lambda e: self.save_config())

        tk.Label(row2, text="Password:", font=FONTS["small_bold"],
                 bg=COLORS["bg_card"]).pack(side="left")
        self.api_password_var = tk.StringVar()
        api_password_entry = tk.Entry(row2, textvariable=self.api_password_var,
                 font=FONTS["input"], width=18, show="*")
        api_password_entry.pack(side="left", padx=(5, 0), ipady=4)
        api_password_entry.bind("<FocusOut>", lambda e: self.save_config())

        tk.Label(inner,
                 text="Enter the local server URL shown by SMSGate app.",
                 font=FONTS["small"], bg=COLORS["bg_card"],
                 fg=COLORS["text_secondary"]).pack(anchor="w")
        tk.Label(inner,
                 text="Example: http://192.168.1.50:8080/send",
                 font=FONTS["small"], bg=COLORS["bg_card"],
                 fg=COLORS["text_secondary"]).pack(anchor="w")

    def build_template(self):
        card = tk.Frame(self.scroll_frame, bg=COLORS["bg_card"],
                        highlightbackground=COLORS["border"],
                        highlightthickness=1)
        card.pack(fill="x", pady=(0, 15), padx=5)

        inner = tk.Frame(card, bg=COLORS["bg_card"])
        inner.pack(fill="x", padx=20, pady=15)

        tk.Label(inner, text="📝 SMS Message Template",
                 font=FONTS["subheading"], bg=COLORS["bg_card"],
                 fg=COLORS["text"]).pack(anchor="w", pady=(0, 5))

        tk.Label(inner,
                 text="Use {vehicle_number}, {owner_name}, {expiry_date}.",
                 font=FONTS["small"], bg=COLORS["bg_card"],
                 fg=COLORS["text_secondary"]).pack(anchor="w", pady=(0, 10))

        self.template_text = scrolledtext.ScrolledText(
            inner, font=FONTS["input"], height=6, width=80, wrap="word")
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

    def build_bulk_send(self):
        card = tk.Frame(self.scroll_frame, bg=COLORS["bg_card"],
                        highlightbackground=COLORS["border"],
                        highlightthickness=1)
        card.pack(fill="x", pady=(0, 15), padx=5)

        inner = tk.Frame(card, bg=COLORS["bg_card"])
        inner.pack(fill="x", padx=20, pady=15)

        tk.Label(inner, text="📨 Bulk SMS Reminders",
                 font=FONTS["subheading"], bg=COLORS["bg_card"],
                 fg=COLORS["text"]).pack(anchor="w", pady=(0, 15))

        self.target_var = tk.StringVar(value="custom")
        self.date_filter_frame = tk.Frame(inner, bg=COLORS["bg_card"])
        self.date_filter_frame.pack(fill="x", pady=(5, 10))

        date_row = tk.Frame(self.date_filter_frame, bg=COLORS["bg_card"])
        date_row.pack(fill="x")

        tk.Label(date_row, text="📅 Expiry From:", font=FONTS["small_bold"],
                 bg=COLORS["bg_card"], fg=COLORS["text"]).pack(side="left")

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
            date_from_inner, text="Select date", font=FONTS["small"],
            bg="white", fg=COLORS["text_secondary"],
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
            w.bind("<Button-1>", lambda e: self.open_bulk_calendar("from"))
            w.bind("<Enter>",
                   lambda e: self.date_from_frame.configure(
                       highlightbackground=COLORS["primary"]))
            w.bind("<Leave>",
                   lambda e: self.date_from_frame.configure(
                       highlightbackground=COLORS["border"]))

        tk.Label(date_row, text="To:", font=FONTS["small_bold"],
                 bg=COLORS["bg_card"], fg=COLORS["text"]).pack(side="left")

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
            date_to_inner, text="Select date", font=FONTS["small"],
            bg="white", fg=COLORS["text_secondary"],
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
            w.bind("<Button-1>", lambda e: self.open_bulk_calendar("to"))
            w.bind("<Enter>",
                   lambda e: self.date_to_frame.configure(
                       highlightbackground=COLORS["primary"]))
            w.bind("<Leave>",
                   lambda e: self.date_to_frame.configure(
                       highlightbackground=COLORS["border"]))

        quick_frame = tk.Frame(self.date_filter_frame, bg=COLORS["bg_card"])
        quick_frame.pack(fill="x", pady=(10, 0))

        for text, cmd in [
            ("Expired", self.set_expired_range),
            ("Next 7d", self.set_7day_range),
            ("Next 30d", self.set_30day_range),
            ("Next 90d", self.set_90day_range),
            ("Clear", self.clear_all_dates),
        ]:
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

        self.target_info = tk.Label(
            inner, text="", font=FONTS["body_bold"],
            bg=COLORS["bg_card"], fg=COLORS["text_secondary"])
        self.target_info.pack(anchor="w", pady=(5, 5))

        self.preview_frame = tk.Frame(inner, bg=COLORS["bg_card"])
        self.preview_frame.pack(fill="x", pady=(0, 10))

        delay_frame = tk.Frame(inner, bg=COLORS["bg_card"])
        delay_frame.pack(fill="x", pady=(0, 15))

        tk.Label(delay_frame, text="Delay between messages (sec):",
                 font=FONTS["small_bold"], bg=COLORS["bg_card"]).pack(side="left")

        self.delay_var = tk.IntVar(value=15)
        ttk.Spinbox(delay_frame, from_=5, to=60,
                     textvariable=self.delay_var,
                     width=5, font=FONTS["input"]).pack(
            side="left", padx=(10, 5))

        self.bulk_send_btn = tk.Label(
            delay_frame, text="💬 Start Bulk SMS",
            font=FONTS["button"], bg=COLORS["success"],
            fg="white", padx=25, pady=10, cursor="hand2")
        self.bulk_send_btn.pack(side="left")
        self.bulk_send_btn.bind("<Button-1>", lambda e: self.start_bulk_send())

        self.stop_btn = tk.Label(
            delay_frame, text="⏹️ Stop", font=FONTS["button"],
            bg=COLORS["danger"], fg="white", padx=25, pady=10,
            cursor="hand2")
        self.stop_btn.bind("<Button-1>", lambda e: self.stop_bulk_send())
        self.stop_btn.pack(side="left", padx=(10, 0))
        self.stop_btn.pack_forget()

        tk.Label(inner,
                 text="Messages are sent through the local SMS gateway server.",
                 font=FONTS["small"], bg=COLORS["bg_card"],
                 fg=COLORS["text_secondary"], wraplength=700,
                 justify="left").pack(anchor="w")

        self.on_target_changed()

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
            inner, variable=self.progress_var, maximum=100, length=400)
        self.progress_bar.pack(fill="x", pady=(0, 10))

        self.progress_label = tk.Label(
            inner, text="Ready to send", font=FONTS["body"],
            bg=COLORS["bg_card"], fg=COLORS["text_secondary"]) 
        self.progress_label.pack(anchor="w")

        self.log_text = scrolledtext.ScrolledText(
            inner, font=FONTS["small"], height=10, width=80,
            state="disabled", wrap="word")
        self.log_text.pack(fill="x", pady=(10, 0))

    def open_bulk_calendar(self, which):
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
        init = current if current else date.today()
        self._bcal_year = init.year
        self._bcal_month = init.month
        self._bcal_which = which

        nav = tk.Frame(parent, bg=COLORS["bg_card"])
        nav.pack(fill="x", padx=8, pady=5)

        prev_btn = tk.Label(nav, text="◀", font=("Segoe UI", 12, "bold"),
                            bg=COLORS["bg_card"], fg=COLORS["primary"],
                            cursor="hand2")
        prev_btn.pack(side="left")
        prev_btn.bind("<Button-1>", lambda e: self._bcal_nav(-1))

        self._bcal_title = tk.Label(nav, text="", font=FONTS["body_bold"],
                                    bg=COLORS["bg_card"],
                                    fg=COLORS["text"])
        self._bcal_title.pack(side="left", expand=True)

        next_btn = tk.Label(nav, text="▶", font=("Segoe UI", 12, "bold"),
                            bg=COLORS["bg_card"], fg=COLORS["primary"],
                            cursor="hand2")
        next_btn.pack(side="right")
        next_btn.bind("<Button-1>", lambda e: self._bcal_nav(1))

        self._bcal_days = tk.Frame(parent, bg=COLORS["bg_card"])
        self._bcal_days.pack(fill="x", padx=8)

        cancel_btn = tk.Label(parent, text="✖ Cancel",
                              font=FONTS["small_bold"],
                              bg=COLORS["secondary"], fg="white",
                              padx=12, pady=4, cursor="hand2")
        cancel_btn.pack(pady=(5, 8))
        cancel_btn.bind("<Button-1>", lambda e: self.close_bulk_calendar())

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
                     bg=COLORS["bg_card"], fg=COLORS["text_secondary"],
                     width=4).grid(row=0, column=i)

        cal_data = cal_module.monthcalendar(self._bcal_year, self._bcal_month)
        today = date.today()

        for ri, week in enumerate(cal_data):
            for ci, day in enumerate(week):
                if day == 0:
                    tk.Label(self._bcal_days, text="",
                             bg=COLORS["bg_card"], width=4, height=1).grid(
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
        if self.target_var.get() != "custom":
            self.target_var.set("custom")
        self.update_target_count()

    def clear_bulk_date(self, which):
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
        self.clear_bulk_date("from")
        self.clear_bulk_date("to")
        self.update_target_count()

    def close_bulk_calendar(self):
        if self.active_calendar_popup and self.active_calendar_popup.winfo_exists():
            self.active_calendar_popup.destroy()
        self.active_calendar_popup = None

    def set_expired_range(self):
        yesterday = date.today() - timedelta(days=1)
        past = date.today() - timedelta(days=3650)
        self.filter_date_from_value = past
        self.filter_date_to_value = yesterday
        self.date_from_text.configure(text="Past", fg=COLORS["danger"])
        self.date_to_text.configure(text=yesterday.strftime("%Y-%m-%d"),
                                    fg=COLORS["danger"])
        self.date_from_clear.pack(side="left", padx=(3, 0))
        self.date_to_clear.pack(side="left", padx=(3, 0))
        self.target_var.set("custom")
        self.update_target_count()

    def set_7day_range(self):
        today = date.today()
        end = today + timedelta(days=7)
        self.filter_date_from_value = today
        self.filter_date_to_value = end
        self.date_from_text.configure(text=today.strftime("%Y-%m-%d"),
                                     fg=COLORS["text"])
        self.date_to_text.configure(text=end.strftime("%Y-%m-%d"),
                                   fg=COLORS["text"])
        self.date_from_clear.pack(side="left", padx=(3, 0))
        self.date_to_clear.pack(side="left", padx=(3, 0))
        self.target_var.set("custom")
        self.update_target_count()

    def set_30day_range(self):
        today = date.today()
        end = today + timedelta(days=30)
        self.filter_date_from_value = today
        self.filter_date_to_value = end
        self.date_from_text.configure(text=today.strftime("%Y-%m-%d"),
                                     fg=COLORS["text"])
        self.date_to_text.configure(text=end.strftime("%Y-%m-%d"),
                                   fg=COLORS["text"])
        self.date_from_clear.pack(side="left", padx=(3, 0))
        self.date_to_clear.pack(side="left", padx=(3, 0))
        self.target_var.set("custom")
        self.update_target_count()

    def set_90day_range(self):
        today = date.today()
        end = today + timedelta(days=90)
        self.filter_date_from_value = today
        self.filter_date_to_value = end
        self.date_from_text.configure(text=today.strftime("%Y-%m-%d"),
                                     fg=COLORS["text"])
        self.date_to_text.configure(text=end.strftime("%Y-%m-%d"),
                                   fg=COLORS["text"])
        self.date_from_clear.pack(side="left", padx=(3, 0))
        self.date_to_clear.pack(side="left", padx=(3, 0))
        self.target_var.set("custom")
        self.update_target_count()

    def on_target_changed(self):
        target = self.target_var.get()
        if target == "custom":
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
            self.clear_all_dates()
        self.update_target_count()

    def get_target_vehicles(self):
        target = self.target_var.get()
        if target == "custom":
            filters = {}
            if self.filter_date_from_value:
                filters["expiry_from"] = self.filter_date_from_value.strftime("%Y-%m-%d")
            if self.filter_date_to_value:
                filters["expiry_to"] = self.filter_date_to_value.strftime("%Y-%m-%d")
            return get_all_vehicles(filters) if filters else get_all_vehicles()
        elif target == "expired":
            if self.filter_date_from_value and self.filter_date_to_value:
                filters = {
                    "expiry_from": self.filter_date_from_value.strftime("%Y-%m-%d"),
                    "expiry_to": self.filter_date_to_value.strftime("%Y-%m-%d"),
                }
                return get_all_vehicles(filters)
            return get_expired_vehicles()
        elif target == "expiring_7":
            if self.filter_date_from_value and self.filter_date_to_value:
                filters = {
                    "expiry_from": self.filter_date_from_value.strftime("%Y-%m-%d"),
                    "expiry_to": self.filter_date_to_value.strftime("%Y-%m-%d"),
                }
                return get_all_vehicles(filters)
            return get_expiring_soon_vehicles(7)
        elif target == "expiring_30":
            if self.filter_date_from_value and self.filter_date_to_value:
                filters = {
                    "expiry_from": self.filter_date_from_value.strftime("%Y-%m-%d"),
                    "expiry_to": self.filter_date_to_value.strftime("%Y-%m-%d"),
                }
                return get_all_vehicles(filters)
            return get_expiring_soon_vehicles(30)
        elif target == "all":
            return get_all_vehicles()
        return []

    def update_target_count(self):
        vehicles = self.get_target_vehicles()
        count = len(vehicles)
        date_info = ""
        if self.filter_date_from_value:
            date_info += f" from {self.filter_date_from_value.strftime('%Y-%m-%d')}"
        if self.filter_date_to_value:
            date_info += f" to {self.filter_date_to_value.strftime('%Y-%m-%d')}"

        self.target_info.configure(
            text=f"📋 {count} vehicle(s) found{date_info}",
            fg=COLORS["success"] if count > 0 else COLORS["danger"])

        for w in self.preview_frame.winfo_children():
            w.destroy()

        if count > 0 and count <= 50:
            preview_label = tk.Label(
                self.preview_frame,
                text=f"Preview ({min(count, 10)} of {count}):",
                font=FONTS["small_bold"], bg=COLORS["bg_card"],
                fg=COLORS["text_secondary"])
            preview_label.pack(anchor="w", pady=(0, 3))

            cols = ("Vehicle No", "Phone", "Expiry", "Owner")
            tree = ttk.Treeview(self.preview_frame, columns=cols,
                                show="headings", height=min(5, count))
            for col in cols:
                tree.heading(col, text=col)
                tree.column(col, width=120)

            today_str = date.today().strftime("%Y-%m-%d")
            for v in vehicles[:10]:
                tag = "expired" if v["expiry_date"] < today_str else ""
                tree.insert("", "end", values=(
                    v["vehicle_number"],
                    v["phone"],
                    v["expiry_date"],
                    v.get("owner_name", ""),
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
                text="⚠️ No vehicles match this filter. Try a different date range.",
                font=FONTS["small"], bg=COLORS["bg_card"],
                fg=COLORS["warning"]).pack(anchor="w")

    def test_server(self):
        api_url = self.api_url_var.get().strip()
        username = self.api_username_var.get().strip()
        password = self.api_password_var.get().strip()
        if not api_url:
            messagebox.showwarning("Warning", "Enter the SMS gateway URL.")
            return

        self.add_log("🔍 Testing SMS server...")
        ok = ping_sms_server(api_url, username=username, password=password)
        if ok:
            messagebox.showinfo("OK", "SMS server is reachable.")
            self.add_log("✅ SMS server reachable")
            self.save_config()
        else:
            messagebox.showerror("Failed", "Cannot reach SMS server. Check URL and network.")
            self.add_log("❌ SMS server unreachable")

    def preview_message(self):
        msg = format_sms_message("KA01AB1234", "John", "2025-01-15",
                                 self.template_text.get("1.0", "end").strip() or None)
        messagebox.showinfo("Preview", msg)

    def load_default_template(self):
        self.template_text.delete("1.0", "end")
        self.template_text.insert("1.0",
            "🚗 വാഹനപുകപരിശോധനകേന്ദ്രത്തിൽ നിന്നുള്ള അറിയിപ്പ്...\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Dear {owner_name},\n\n"
            "താങ്കളുടെ {vehicle_number} വാഹനത്തിന്റെ വാഹനപുക സർട്ടിഫിക്കറ്റ് കാലാവധി {expiry_date} ന് അവസാനിക്കുന്നു.\n\n"
            "സർക്കാർ അധികാരികളിൽ നിന്നുള്ള നിയമപരമായ ശിക്ഷാനടപടികൾ/പിഴ ഒഴിവാക്കുന്നതിനായി, \n"
            "കാലാവധി തീരുന്നതിന് മുൻപായി ഞങ്ങളുടെ വാഹനപുകപരിശോധനാകേന്ദ്രത്തിൽ നിന്നും സർട്ടിഫിക്കറ്റ് പുതുക്കുക.\n\n"
            "*IDEAL VEHICLE PUC TESTING CENTER (PNR ROAD)*\n"
            "അഡ്രസ്സ്: പൂനൂർ  റോഡ് ,നരിക്കുനി, പെട്രോൾ പമ്പിന് സമീപം, 673585\n"
            "ഫോൺ: +91 95677 86078\n"
            "ലൊക്കേഷൻ: https://maps.app.goo.gl/Rpa4LGkaCriTAGUq8\n"
            "Mon - Sat: 9:00 AM to 9:00 PM, Sun: 9:00 AM to 9:00 PM")

    def start_bulk_send(self):
        if self.sending:
            messagebox.showwarning("Warning", "Bulk SMS is already running.")
            return

        api_url = self.api_url_var.get().strip()
        if not api_url:
            messagebox.showwarning("Warning", "Please enter the SMS gateway URL.")
            return

        vehicles = self.get_target_vehicles()
        if not vehicles:
            messagebox.showinfo("Info", "No vehicles to send SMS to.")
            return

        delay = self.delay_var.get()
        custom = self.template_text.get("1.0", "end").strip() or None
        username = self.api_username_var.get().strip()
        password = self.api_password_var.get().strip()
        if delay < 1:
            delay = 5

        confirm = messagebox.askyesno(
            "Confirm",
            f"Send SMS to {len(vehicles)} vehicle(s)?\n"
            f"Delay: {delay}s\n"
            f"URL: {api_url}\n"
            "Make sure the Android device is on the same network and SMSGate local server is enabled."
        )
        if not confirm:
            return

        self.save_config()
        self.sending = True
        self.stop_event = Event()
        self.bulk_send_btn.configure(bg=COLORS["secondary"], text="⏳ Sending...")
        self.stop_btn.pack(side="left", padx=(10, 0))
        self.progress_var.set(0)

        self.add_log(f"\n{'='*50}")
        self.add_log(f"🚀 BULK SMS STARTED ({len(vehicles)} vehicles)")
        self.add_log(f"URL: {api_url}")
        self.add_log(f"{'='*50}\n")

        def progress_callback(current, total, success, failed, vehicle_number, error):
            def update():
                if not self.sending and vehicle_number != "DONE":
                    return
                pct = (current / total) * 100 if total else 0
                self.progress_var.set(pct)
                if vehicle_number == "DONE":
                    self.progress_label.configure(
                        text=f"✅ Done! Sent: {success}, Failed: {failed}")
                    self.add_log(
                        f"\n{'='*50}\n"
                        f"✅ COMPLETE: {success}/{total}\n"
                        f"{'='*50}")
                    self.sending = False
                    self.bulk_send_btn.configure(bg=COLORS["success"], text="💬 Start Bulk SMS")
                    self.stop_btn.pack_forget()
                else:
                    self.progress_label.configure(
                        text=f"Sending {current}/{total} — {vehicle_number}")
                    log_text = f"🔁 [{current}/{total}] {vehicle_number}"
                    if error:
                        log_text += f" — ERROR: {error}"
                    self.add_log(log_text)
            self.parent.after(0, update)

        bulk_send_messages(
            vehicles=vehicles,
            custom_message=custom,
            delay=delay,
            api_url=api_url,
            username=username,
            password=password,
            timeout=20,
            progress_callback=progress_callback,
            stop_event=self.stop_event,
        )

    def stop_bulk_send(self):
        if self.stop_event:
            self.stop_event.set()
        self.sending = False
        self.bulk_send_btn.configure(bg=COLORS["success"], text="💬 Start Bulk SMS")
        self.stop_btn.pack_forget()
        self.progress_label.configure(text="Stopped")
        self.add_log("\n⏹️ STOPPED")

    def add_log(self, text):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", text + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
