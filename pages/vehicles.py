"""
Vehicles List Page - CRUD operations and filtering
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from styles import COLORS, FONTS
from database import (
    get_all_vehicles,
    delete_vehicle,
    get_vehicle_by_id,
    log_message,
    set_call_status,
)
from whatsapp_sender import format_message, send_whatsapp_message
from import_export import (export_to_csv, export_to_pdf,
                           import_from_csv, import_from_json,
                           generate_sample_csv)
from datetime import date, datetime

# Try importing tkcalendar
try:
    from tkcalendar import Calendar
    HAS_CALENDAR = True
except ImportError:
    HAS_CALENDAR = False

import calendar as cal_module


class VehiclesPage:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.selected_items = []
        self.filter_date_from_value = None
        self.filter_date_to_value = None
        self.filter_updated_from_value = None
        self.filter_updated_to_value = None
        self.active_calendar_popup = None
        self.build()
        self.load_vehicles()

    def build(self):
        self.build_filters()
        self.build_action_bar()
        self.build_table()
        self.build_status_bar()

    def build_filters(self):
        filter_frame = tk.Frame(
            self.parent, bg=COLORS["bg_card"],
            highlightbackground=COLORS["border"], highlightthickness=1)
        filter_frame.pack(fill="x", pady=(0, 10))

        inner = tk.Frame(filter_frame, bg=COLORS["bg_card"])
        inner.pack(fill="x", padx=15, pady=12)

        tk.Label(
            inner, text="🔍 Filters",
            font=FONTS["body_bold"],
            bg=COLORS["bg_card"], fg=COLORS["text"]
        ).pack(anchor="w", pady=(0, 8))

        # Row 1: Text filters
        row1 = tk.Frame(inner, bg=COLORS["bg_card"])
        row1.pack(fill="x", pady=(0, 8))

        tk.Label(row1, text="Vehicle No:", font=FONTS["small"],
                 bg=COLORS["bg_card"], fg=COLORS["text_secondary"]
                 ).pack(side="left")
        self.filter_vehicle = tk.Entry(row1, font=FONTS["input"], width=14)
        self.filter_vehicle.pack(side="left", padx=(5, 15))

        tk.Label(row1, text="Phone:", font=FONTS["small"],
                 bg=COLORS["bg_card"], fg=COLORS["text_secondary"]
                 ).pack(side="left")
        self.filter_phone = tk.Entry(row1, font=FONTS["input"], width=14)
        self.filter_phone.pack(side="left", padx=(5, 15))

        tk.Label(row1, text="Owner:", font=FONTS["small"],
                 bg=COLORS["bg_card"], fg=COLORS["text_secondary"]
                 ).pack(side="left")
        self.filter_owner = tk.Entry(row1, font=FONTS["input"], width=14)
        self.filter_owner.pack(side="left", padx=(5, 15))

        tk.Label(row1, text="Status:", font=FONTS["small"],
                 bg=COLORS["bg_card"], fg=COLORS["text_secondary"]
                 ).pack(side="left")
        self.filter_status = ttk.Combobox(
            row1, values=["All", "Active", "Expired", "Expiring Soon"],
            state="readonly", width=12, font=FONTS["small"])
        self.filter_status.set("All")
        self.filter_status.pack(side="left", padx=(5, 0))

        tk.Label(row1, text="Call Status:", font=FONTS["small"],
                 bg=COLORS["bg_card"], fg=COLORS["text_secondary"]
                 ).pack(side="left", padx=(15, 0))
        self.filter_call_status = ttk.Combobox(
            row1,
            values=["All", "No response", "Call Now", "Call Again", "Success"],
            state="readonly", width=12, font=FONTS["small"])
        self.filter_call_status.set("All")
        self.filter_call_status.pack(side="left", padx=(5, 0))

        # Row 2: Date filters + buttons
        row2 = tk.Frame(inner, bg=COLORS["bg_card"])
        row2.pack(fill="x")

        # ===== EXPIRY DATE FROM =====
        tk.Label(row2, text="Expiry From:", font=FONTS["small"],
                 bg=COLORS["bg_card"], fg=COLORS["text_secondary"]
                 ).pack(side="left")

        self.date_from_frame = tk.Frame(
            row2, bg="white",
            highlightbackground=COLORS["border"],
            highlightthickness=1, cursor="hand2")
        self.date_from_frame.pack(side="left", padx=(5, 10))

        self.date_from_inner = tk.Frame(self.date_from_frame, bg="white")
        self.date_from_inner.pack(padx=6, pady=4)

        self.date_from_icon = tk.Label(
            self.date_from_inner, text="📅",
            font=("Segoe UI", 9), bg="white", cursor="hand2")
        self.date_from_icon.pack(side="left")

        self.date_from_text = tk.Label(
            self.date_from_inner, text="Any",
            font=FONTS["small"], bg="white",
            fg=COLORS["text_secondary"],
            cursor="hand2", width=10, anchor="w")
        self.date_from_text.pack(side="left", padx=(3, 0))

        self.date_from_clear = tk.Label(
            self.date_from_inner, text="✕",
            font=("Segoe UI", 8), bg="white",
            fg=COLORS["text_light"], cursor="hand2")
        self.date_from_clear.pack(side="left", padx=(3, 0))
        self.date_from_clear.bind(
            "<Button-1>", lambda e: self.clear_date_filter("from"))
        self.date_from_clear.pack_forget()  # Hide initially

        # Bind clicks
        for w in [self.date_from_frame, self.date_from_inner,
                  self.date_from_icon, self.date_from_text]:
            w.bind("<Button-1>",
                   lambda e: self.open_filter_calendar("from"))
            w.bind("<Enter>",
                   lambda e: self.date_from_frame.configure(
                       highlightbackground=COLORS["primary"]))
            w.bind("<Leave>",
                   lambda e: self.date_from_frame.configure(
                       highlightbackground=COLORS["border"]))

        # ===== EXPIRY DATE TO =====
        tk.Label(row2, text="To:", font=FONTS["small"],
                 bg=COLORS["bg_card"], fg=COLORS["text_secondary"]
                 ).pack(side="left")

        self.date_to_frame = tk.Frame(
            row2, bg="white",
            highlightbackground=COLORS["border"],
            highlightthickness=1, cursor="hand2")
        self.date_to_frame.pack(side="left", padx=(5, 15))

        self.date_to_inner = tk.Frame(self.date_to_frame, bg="white")
        self.date_to_inner.pack(padx=6, pady=4)

        self.date_to_icon = tk.Label(
            self.date_to_inner, text="📅",
            font=("Segoe UI", 9), bg="white", cursor="hand2")
        self.date_to_icon.pack(side="left")

        self.date_to_text = tk.Label(
            self.date_to_inner, text="Any",
            font=FONTS["small"], bg="white",
            fg=COLORS["text_secondary"],
            cursor="hand2", width=10, anchor="w")
        self.date_to_text.pack(side="left", padx=(3, 0))

        self.date_to_clear = tk.Label(
            self.date_to_inner, text="✕",
            font=("Segoe UI", 8), bg="white",
            fg=COLORS["text_light"], cursor="hand2")
        self.date_to_clear.pack(side="left", padx=(3, 0))
        self.date_to_clear.bind(
            "<Button-1>", lambda e: self.clear_date_filter("to"))
        self.date_to_clear.pack_forget()  # Hide initially

        # Bind clicks
        for w in [self.date_to_frame, self.date_to_inner,
                  self.date_to_icon, self.date_to_text]:
            w.bind("<Button-1>",
                   lambda e: self.open_filter_calendar("to"))
            w.bind("<Enter>",
                   lambda e: self.date_to_frame.configure(
                       highlightbackground=COLORS["primary"]))
            w.bind("<Leave>",
                   lambda e: self.date_to_frame.configure(
                       highlightbackground=COLORS["border"]))

        # ===== UPDATED DATE FROM =====
        tk.Label(row2, text="Updated From:", font=FONTS["small"],
                 bg=COLORS["bg_card"], fg=COLORS["text_secondary"]
                 ).pack(side="left")

        self.updated_from_frame = tk.Frame(
            row2, bg="white",
            highlightbackground=COLORS["border"],
            highlightthickness=1, cursor="hand2")
        self.updated_from_frame.pack(side="left", padx=(5, 10))

        self.updated_from_inner = tk.Frame(self.updated_from_frame, bg="white")
        self.updated_from_inner.pack(padx=6, pady=4)

        self.updated_from_icon = tk.Label(
            self.updated_from_inner, text="📅",
            font=("Segoe UI", 9), bg="white", cursor="hand2")
        self.updated_from_icon.pack(side="left")

        self.updated_from_text = tk.Label(
            self.updated_from_inner, text="Any",
            font=FONTS["small"], bg="white",
            fg=COLORS["text_secondary"],
            cursor="hand2", width=10, anchor="w")
        self.updated_from_text.pack(side="left", padx=(3, 0))

        self.updated_from_clear = tk.Label(
            self.updated_from_inner, text="✕",
            font=("Segoe UI", 8), bg="white",
            fg=COLORS["text_light"], cursor="hand2")
        self.updated_from_clear.pack(side="left", padx=(3, 0))
        self.updated_from_clear.bind(
            "<Button-1>", lambda e: self.clear_date_filter("updated_from"))
        self.updated_from_clear.pack_forget()  # Hide initially

        # ===== UPDATED DATE TO =====
        tk.Label(row2, text="To:", font=FONTS["small"],
                 bg=COLORS["bg_card"], fg=COLORS["text_secondary"]
                 ).pack(side="left")

        self.updated_to_frame = tk.Frame(
            row2, bg="white",
            highlightbackground=COLORS["border"],
            highlightthickness=1, cursor="hand2")
        self.updated_to_frame.pack(side="left", padx=(5, 15))

        self.updated_to_inner = tk.Frame(self.updated_to_frame, bg="white")
        self.updated_to_inner.pack(padx=6, pady=4)

        self.updated_to_icon = tk.Label(
            self.updated_to_inner, text="📅",
            font=("Segoe UI", 9), bg="white", cursor="hand2")
        self.updated_to_icon.pack(side="left")

        self.updated_to_text = tk.Label(
            self.updated_to_inner, text="Any",
            font=FONTS["small"], bg="white",
            fg=COLORS["text_secondary"],
            cursor="hand2", width=10, anchor="w")
        self.updated_to_text.pack(side="left", padx=(3, 0))

        self.updated_to_clear = tk.Label(
            self.updated_to_inner, text="✕",
            font=("Segoe UI", 8), bg="white",
            fg=COLORS["text_light"], cursor="hand2")
        self.updated_to_clear.pack(side="left", padx=(3, 0))
        self.updated_to_clear.bind(
            "<Button-1>", lambda e: self.clear_date_filter("updated_to"))
        self.updated_to_clear.pack_forget()  # Hide initially

        # Bind clicks
        for w in [self.updated_from_frame, self.updated_from_inner,
                  self.updated_from_icon, self.updated_from_text]:
            w.bind("<Button-1>",
                   lambda e: self.open_filter_calendar("updated_from"))
            w.bind("<Enter>",
                   lambda e: self.updated_from_frame.configure(
                       highlightbackground=COLORS["primary"]))
            w.bind("<Leave>",
                   lambda e: self.updated_from_frame.configure(
                       highlightbackground=COLORS["border"]))

        for w in [self.updated_to_frame, self.updated_to_inner,
                  self.updated_to_icon, self.updated_to_text]:
            w.bind("<Button-1>",
                   lambda e: self.open_filter_calendar("updated_to"))
            w.bind("<Enter>",
                   lambda e: self.updated_to_frame.configure(
                       highlightbackground=COLORS["primary"]))
            w.bind("<Leave>",
                   lambda e: self.updated_to_frame.configure(
                       highlightbackground=COLORS["border"]))

        # ===== Quick date filter buttons =====
        tk.Label(row2, text="│", font=FONTS["small"],
                 bg=COLORS["bg_card"], fg=COLORS["border"]
                 ).pack(side="left", padx=(0, 5))

        quick_filters = [
            ("Expired", self.filter_expired_dates),
        ]

        for text, cmd in quick_filters:
            qbtn = tk.Label(
                row2, text=text, font=FONTS["small"],
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

        # ===== Separator and Search/Clear =====
        tk.Label(row2, text="│", font=FONTS["small"],
                 bg=COLORS["bg_card"], fg=COLORS["border"]
                 ).pack(side="left", padx=(5, 5))

        search_btn = tk.Label(
            row2, text="🔍 Search", font=FONTS["small_bold"],
            bg=COLORS["primary"], fg="white", padx=12, pady=4,
            cursor="hand2")
        search_btn.pack(side="left", padx=(0, 5))
        search_btn.bind("<Button-1>", lambda e: self.load_vehicles())

        clear_btn = tk.Label(
            row2, text="✖ Clear All", font=FONTS["small_bold"],
            bg=COLORS["secondary"], fg="white", padx=12, pady=4,
            cursor="hand2")
        clear_btn.pack(side="left", padx=(0, 0))
        clear_btn.bind("<Button-1>", lambda e: self.clear_filters())

        # Bind Enter key
        self.filter_vehicle.bind("<Return>", lambda e: self.load_vehicles())
        self.filter_phone.bind("<Return>", lambda e: self.load_vehicles())
        self.filter_owner.bind("<Return>", lambda e: self.load_vehicles())

    # =============================================
    # DATE FILTER CALENDAR METHODS
    # =============================================

    def open_filter_calendar(self, which):
        """Open calendar popup for date filter"""
        self.close_filter_calendar()

        self.active_calendar_popup = tk.Toplevel(self.parent)
        self.active_calendar_popup.overrideredirect(True)
        self.active_calendar_popup.configure(
            bg=COLORS["border"],
            highlightbackground=COLORS["primary"],
            highlightthickness=2)

        # Position below the date field
        if which == "from":
            ref = self.date_from_frame
            current = self.filter_date_from_value
            title = "📅 Expiry From"
        elif which == "to":
            ref = self.date_to_frame
            current = self.filter_date_to_value
            title = "📅 Expiry To"
        elif which == "updated_from":
            ref = self.updated_from_frame
            current = self.filter_updated_from_value
            title = "📅 Updated From"
        else:
            ref = self.updated_to_frame
            current = self.filter_updated_to_value
            title = "📅 Updated To"

        x = ref.winfo_rootx()
        y = ref.winfo_rooty() + ref.winfo_height() + 2
        self.active_calendar_popup.geometry(f"+{x}+{y}")
        self.active_calendar_popup.attributes("-topmost", True)

        main = tk.Frame(self.active_calendar_popup, bg=COLORS["bg_card"])
        main.pack(fill="both", expand=True, padx=1, pady=1)

        # Header
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

            # Quick dates
            qframe = tk.Frame(main, bg=COLORS["bg_card"])
            qframe.pack(fill="x", padx=8, pady=(0, 5))

            from datetime import timedelta
            quick = [("Today", date.today()),
                     ("-7d", date.today() - timedelta(days=7)),
                     ("-30d", date.today() - timedelta(days=30)),
                     ("+30d", date.today() + timedelta(days=30)),
                     ("+90d", date.today() + timedelta(days=90))]

            for text, target in quick:
                qb = tk.Label(qframe, text=text, font=("Segoe UI", 8),
                              bg=COLORS["bg"], fg=COLORS["primary"],
                              padx=5, pady=2, cursor="hand2",
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
                            self.set_date_filter(w, c.selection_get()))

            cancel_btn = tk.Label(
                bframe, text="✖ Cancel", font=FONTS["small_bold"],
                bg=COLORS["secondary"], fg="white",
                padx=12, pady=4, cursor="hand2")
            cancel_btn.pack(side="left")
            cancel_btn.bind("<Button-1>",
                            lambda e: self.close_filter_calendar())

            # Double click selects
            cal.bind("<<CalendarSelected>>",
                     lambda e, w=which, c=cal:
                     self.set_date_filter(w, c.selection_get()))

        else:
            # Fallback without tkcalendar
            self.build_custom_filter_calendar(main, which, current)

        self.active_calendar_popup.lift()
        self.active_calendar_popup.focus_set()

    def build_custom_filter_calendar(self, parent, which, current):
        """Custom calendar for filter (fallback)"""
        init = current if current else date.today()

        self._cal_year = init.year
        self._cal_month = init.month
        self._cal_which = which

        # Navigation
        nav = tk.Frame(parent, bg=COLORS["bg_card"])
        nav.pack(fill="x", padx=8, pady=5)

        prev_btn = tk.Label(nav, text="◀", font=("Segoe UI", 12, "bold"),
                            bg=COLORS["bg_card"], fg=COLORS["primary"],
                            cursor="hand2")
        prev_btn.pack(side="left")
        prev_btn.bind("<Button-1>", lambda e: self._cal_nav(-1, parent))

        self._cal_title = tk.Label(nav, text="", font=FONTS["body_bold"],
                                   bg=COLORS["bg_card"], fg=COLORS["text"])
        self._cal_title.pack(side="left", expand=True)

        next_btn = tk.Label(nav, text="▶", font=("Segoe UI", 12, "bold"),
                            bg=COLORS["bg_card"], fg=COLORS["primary"],
                            cursor="hand2")
        next_btn.pack(side="right")
        next_btn.bind("<Button-1>", lambda e: self._cal_nav(1, parent))

        self._cal_days_frame = tk.Frame(parent, bg=COLORS["bg_card"])
        self._cal_days_frame.pack(fill="x", padx=8)

        # Cancel
        cancel_btn = tk.Label(parent, text="✖ Cancel",
                              font=FONTS["small_bold"],
                              bg=COLORS["secondary"], fg="white",
                              padx=12, pady=4, cursor="hand2")
        cancel_btn.pack(pady=(5, 8))
        cancel_btn.bind("<Button-1>",
                        lambda e: self.close_filter_calendar())

        self._draw_filter_cal()

    def _cal_nav(self, direction, parent):
        """Navigate custom calendar months"""
        self._cal_month += direction
        if self._cal_month > 12:
            self._cal_month = 1
            self._cal_year += 1
        elif self._cal_month < 1:
            self._cal_month = 12
            self._cal_year -= 1
        self._draw_filter_cal()

    def _draw_filter_cal(self):
        """Draw custom filter calendar grid"""
        for w in self._cal_days_frame.winfo_children():
            w.destroy()

        month_name = cal_module.month_name[self._cal_month]
        self._cal_title.configure(text=f"{month_name} {self._cal_year}")

        headers = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        for i, h in enumerate(headers):
            tk.Label(self._cal_days_frame, text=h,
                     font=("Segoe UI", 8, "bold"),
                     bg=COLORS["bg_card"], fg=COLORS["text_secondary"],
                     width=4).grid(row=0, column=i)

        cal_data = cal_module.monthcalendar(self._cal_year, self._cal_month)
        today = date.today()

        for ri, week in enumerate(cal_data):
            for ci, day in enumerate(week):
                if day == 0:
                    tk.Label(self._cal_days_frame, text="",
                             bg=COLORS["bg_card"],
                             width=4, height=1).grid(row=ri+1, column=ci)
                else:
                    d = date(self._cal_year, self._cal_month, day)
                    is_today = d == today
                    bg = COLORS["primary_light"] if is_today else "white"
                    fg = COLORS["primary"] if is_today else COLORS["text"]

                    lbl = tk.Label(
                        self._cal_days_frame, text=str(day),
                        font=("Segoe UI", 9),
                        bg=bg, fg=fg, width=4, height=1,
                        cursor="hand2")
                    lbl.grid(row=ri+1, column=ci, padx=1, pady=1)
                    lbl.bind("<Button-1>",
                             lambda e, dt=d:
                             self.set_date_filter(self._cal_which, dt))

    def set_date_filter(self, which, selected_date):
        """Set a date filter value"""
        if which == "from":
            self.filter_date_from_value = selected_date
            self.date_from_text.configure(
                text=selected_date.strftime("%Y-%m-%d"),
                fg=COLORS["text"])
            self.date_from_clear.pack(side="left", padx=(3, 0))
        elif which == "to":
            self.filter_date_to_value = selected_date
            self.date_to_text.configure(
                text=selected_date.strftime("%Y-%m-%d"),
                fg=COLORS["text"])
            self.date_to_clear.pack(side="left", padx=(3, 0))
        elif which == "updated_from":
            self.filter_updated_from_value = selected_date
            self.updated_from_text.configure(
                text=selected_date.strftime("%Y-%m-%d"),
                fg=COLORS["text"])
            self.updated_from_clear.pack(side="left", padx=(3, 0))
        else:
            self.filter_updated_to_value = selected_date
            self.updated_to_text.configure(
                text=selected_date.strftime("%Y-%m-%d"),
                fg=COLORS["text"])
            self.updated_to_clear.pack(side="left", padx=(3, 0))

        self.close_filter_calendar()
        self.load_vehicles()  # Auto search

    def clear_date_filter(self, which):
        """Clear a date filter"""
        if which == "from":
            self.filter_date_from_value = None
            self.date_from_text.configure(
                text="Any", fg=COLORS["text_secondary"])
            self.date_from_clear.pack_forget()
        elif which == "to":
            self.filter_date_to_value = None
            self.date_to_text.configure(
                text="Any", fg=COLORS["text_secondary"])
            self.date_to_clear.pack_forget()
        elif which == "updated_from":
            self.filter_updated_from_value = None
            self.updated_from_text.configure(
                text="Any", fg=COLORS["text_secondary"])
            self.updated_from_clear.pack_forget()
        else:
            self.filter_updated_to_value = None
            self.updated_to_text.configure(
                text="Any", fg=COLORS["text_secondary"])
            self.updated_to_clear.pack_forget()

        self.load_vehicles()  # Auto refresh

    def close_filter_calendar(self):
        """Close any open filter calendar popup"""
        if self.active_calendar_popup and \
                self.active_calendar_popup.winfo_exists():
            self.active_calendar_popup.destroy()
        self.active_calendar_popup = None

    # =============================================
    # QUICK DATE FILTERS
    # =============================================

    def filter_today(self):
        """Filter expiry date = today"""
        today = date.today()
        self.filter_date_from_value = today
        self.filter_date_to_value = today
        self.date_from_text.configure(
            text=today.strftime("%Y-%m-%d"), fg=COLORS["text"])
        self.date_to_text.configure(
            text=today.strftime("%Y-%m-%d"), fg=COLORS["text"])
        self.date_from_clear.pack(side="left", padx=(3, 0))
        self.date_to_clear.pack(side="left", padx=(3, 0))
        self.load_vehicles()

    def filter_this_week(self):
        """Filter expiry date = this week"""
        from datetime import timedelta
        today = date.today()
        start = today
        end = today + timedelta(days=7)
        self.filter_date_from_value = start
        self.filter_date_to_value = end
        self.date_from_text.configure(
            text=start.strftime("%Y-%m-%d"), fg=COLORS["text"])
        self.date_to_text.configure(
            text=end.strftime("%Y-%m-%d"), fg=COLORS["text"])
        self.date_from_clear.pack(side="left", padx=(3, 0))
        self.date_to_clear.pack(side="left", padx=(3, 0))
        self.load_vehicles()

    def filter_this_month(self):
        """Filter expiry date = this month"""
        from datetime import timedelta
        today = date.today()
        start = today
        end = today + timedelta(days=30)
        self.filter_date_from_value = start
        self.filter_date_to_value = end
        self.date_from_text.configure(
            text=start.strftime("%Y-%m-%d"), fg=COLORS["text"])
        self.date_to_text.configure(
            text=end.strftime("%Y-%m-%d"), fg=COLORS["text"])
        self.date_from_clear.pack(side="left", padx=(3, 0))
        self.date_to_clear.pack(side="left", padx=(3, 0))
        self.load_vehicles()

    def filter_expired_dates(self):
        """Filter only expired vehicles by date"""
        from datetime import timedelta
        today = date.today()
        past = today - timedelta(days=3650)  # 10 years back
        yesterday = today - timedelta(days=1)
        self.filter_date_from_value = past
        self.filter_date_to_value = yesterday
        self.date_from_text.configure(
            text="Past", fg=COLORS["danger"])
        self.date_to_text.configure(
            text=yesterday.strftime("%Y-%m-%d"), fg=COLORS["danger"])
        self.date_from_clear.pack(side="left", padx=(3, 0))
        self.date_to_clear.pack(side="left", padx=(3, 0))
        self.load_vehicles()

    # =============================================
    # EXISTING METHODS (UPDATED)
    # =============================================

    def build_action_bar(self):
        action_frame = tk.Frame(self.parent, bg=COLORS["bg"])
        action_frame.pack(fill="x", pady=(0, 5))

        left = tk.Frame(action_frame, bg=COLORS["bg"])
        left.pack(side="left")

        buttons_left = [
            ("➕ Add New", COLORS["primary"], self.add_new),
            ("✏️ Edit", COLORS["warning"], self.edit_selected),
            ("🗑️ Delete", COLORS["danger"], self.delete_selected),
            ("💬 Send WhatsApp", COLORS["whatsapp"],
             self.send_whatsapp_selected),
        ]

        for text, color, cmd in buttons_left:
            btn = tk.Label(
                left, text=text, font=FONTS["small_bold"],
                bg=color, fg="white", padx=12, pady=5, cursor="hand2")
            btn.pack(side="left", padx=(0, 5))
            btn.bind("<Button-1>", lambda e, c=cmd: c())

        right = tk.Frame(action_frame, bg=COLORS["bg"])
        right.pack(side="right")

        buttons_right = [
            ("📥 Import CSV", COLORS["info"], self.import_csv),
            ("📤 Export CSV", COLORS["secondary"], self.export_csv),
            ("� Export PDF", COLORS["secondary"], self.export_pdf),
            ("� Share List", COLORS["primary"], self.share_search_results_whatsapp),
            ("�📄 Sample CSV", COLORS["text_light"],
             self.download_sample),
        ]

        for text, color, cmd in buttons_right:
            btn = tk.Label(
                right, text=text, font=FONTS["small_bold"],
                bg=color, fg="white", padx=10, pady=5, cursor="hand2")
            btn.pack(side="left", padx=(5, 0))
            btn.bind("<Button-1>", lambda e, c=cmd: c())

    def build_table(self):
        table_frame = tk.Frame(
            self.parent, bg=COLORS["bg_card"],
            highlightbackground=COLORS["border"], highlightthickness=1)
        table_frame.pack(fill="both", expand=True)

        columns = (
            "id", "vehicle_number", "owner_name", "phone",
            "vehicle_type", "expiry_date",
            "status", "call_status", "renewals", "updated_at"
        )

        tree_scroll_y = ttk.Scrollbar(table_frame)
        tree_scroll_y.pack(side="right", fill="y")

        tree_scroll_x = ttk.Scrollbar(table_frame, orient="horizontal")
        tree_scroll_x.pack(side="bottom", fill="x")

        style = ttk.Style()
        style.configure("Treeview", font=FONTS["table_body"], rowheight=28)
        style.configure("Treeview.Heading", font=FONTS["table_header"])
        style.map("Treeview",
                  background=[("selected", COLORS["primary_light"])])

        self.tree = ttk.Treeview(
            table_frame, columns=columns, show="headings",
            yscrollcommand=tree_scroll_y.set,
            xscrollcommand=tree_scroll_x.set,
            selectmode="extended")

        tree_scroll_y.config(command=self.tree.yview)
        tree_scroll_x.config(command=self.tree.xview)

        col_config = {
            "id": ("ID", 50),
            "vehicle_number": ("Vehicle No", 130),
            "owner_name": ("Owner", 150),
            "phone": ("Phone", 130),
            "vehicle_type": ("Type", 90),
            "expiry_date": ("Expiry Date", 110),
            "status": ("Status", 110),
            "call_status": ("Call Status", 120),
            "renewals": ("Renewals", 80),
            "updated_at": ("Updated", 160),
        }

        for col, (heading, width) in col_config.items():
            self.tree.heading(col, text=heading,
                              command=lambda c=col: self.sort_column(c))
            self.tree.column(col, width=width, minwidth=50)

        self.tree.pack(fill="both", expand=True)

        self.context_menu = tk.Menu(self.tree, tearoff=0)
        self.context_menu.add_command(label="✏️ Edit",
                                      command=self.edit_selected)
        self.context_menu.add_command(label="🗑️ Delete",
                                      command=self.delete_selected)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="💬 Send WhatsApp",
                                      command=self.send_whatsapp_selected)
        self.context_menu.add_separator()

        # Call status submenu
        call_status_menu = tk.Menu(self.context_menu, tearoff=0)
        for status in ["No response", "Call Now", "Call Again", "Success"]:
            call_status_menu.add_command(
                label=status,
                command=lambda s=status: self.set_selected_call_status(s))
        self.context_menu.add_cascade(label="📞 Set Call Status",
                                      menu=call_status_menu)

        self.context_menu.add_separator()
        self.context_menu.add_command(label="📋 Copy Vehicle No",
                                      command=self.copy_vehicle_number)

        self.tree.bind("<Button-3>", self.show_context_menu)
        self.tree.bind("<Double-1>", lambda e: self.edit_selected())

    def build_status_bar(self):
        self.status_bar = tk.Frame(self.parent, bg=COLORS["bg_card"],
                                   height=30)
        self.status_bar.pack(fill="x", pady=(5, 0))

        self.status_label = tk.Label(
            self.status_bar, text="Ready", font=FONTS["small"],
            bg=COLORS["bg_card"], fg=COLORS["text_secondary"],
            padx=10, pady=3)
        self.status_label.pack(side="left")

        self.count_label = tk.Label(
            self.status_bar, text="", font=FONTS["small"],
            bg=COLORS["bg_card"], fg=COLORS["text_secondary"],
            padx=10, pady=3)
        self.count_label.pack(side="right")

    def get_filters(self):
        """Get current filter values including date filters"""
        filters = {}
        vn = self.filter_vehicle.get().strip()
        if vn:
            filters["vehicle_number"] = vn
        ph = self.filter_phone.get().strip()
        if ph:
            filters["phone"] = ph
        on = self.filter_owner.get().strip()
        if on:
            filters["owner_name"] = on

        status = self.filter_status.get()
        if status == "Active":
            filters["status"] = "active"
        elif status == "Expired":
            filters["status"] = "expired"
        elif status == "Expiring Soon":
            filters["status"] = "expiring_soon"

        call_status = self.filter_call_status.get()
        if call_status and call_status != "All":
            filters["call_status"] = call_status

        # ✅ Date filters
        if self.filter_date_from_value:
            filters["expiry_from"] = \
                self.filter_date_from_value.strftime("%Y-%m-%d")
        if self.filter_date_to_value:
            filters["expiry_to"] = \
                self.filter_date_to_value.strftime("%Y-%m-%d")

        if self.filter_updated_from_value:
            filters["updated_from"] = \
                self.filter_updated_from_value.strftime("%Y-%m-%d")
        if self.filter_updated_to_value:
            filters["updated_to"] = \
                self.filter_updated_to_value.strftime("%Y-%m-%d")

        return filters

    def load_vehicles(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        filters = self.get_filters()
        vehicles = get_all_vehicles(filters)
        today = date.today().strftime("%Y-%m-%d")

        for v in vehicles:
            if v["expiry_date"] < today:
                status = "❌ Expired"
                tag = "expired"
            else:
                from datetime import timedelta
                soon = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")
                if v["expiry_date"] <= soon:
                    status = "⚠️ Expiring"
                    tag = "expiring"
                else:
                    status = "✅ Active"
                    tag = "active"

            self.tree.insert("", "end", values=(
                v["id"],
                v["vehicle_number"],
                v.get("owner_name", ""),
                v["phone"],
                v.get("vehicle_type", ""),
                v["expiry_date"],
                status,
                v.get("call_status", "No response"),
                v.get("renewal_count", 0),
                v.get("updated_at", v.get("created_at", ""))
            ), tags=(tag,))

        self.tree.tag_configure("expired", background="#FEE2E2")
        self.tree.tag_configure("expiring", background="#FEF3C7")
        self.tree.tag_configure("active", background="#FFFFFF")

        count = len(vehicles)
        self.count_label.configure(text=f"Showing {count} vehicle(s)")

        # Show active filter info
        active_filters = []
        if self.filter_date_from_value:
            active_filters.append(
                f"Expiry From: {self.filter_date_from_value.strftime('%Y-%m-%d')}")
        if self.filter_date_to_value:
            active_filters.append(
                f"Expiry To: {self.filter_date_to_value.strftime('%Y-%m-%d')}")
        if self.filter_updated_from_value:
            active_filters.append(
                f"Updated From: {self.filter_updated_from_value.strftime('%Y-%m-%d')}")
        if self.filter_updated_to_value:
            active_filters.append(
                f"Updated To: {self.filter_updated_to_value.strftime('%Y-%m-%d')}")

        if active_filters:
            self.status_label.configure(
                text=f"📅 Date filter: {' | '.join(active_filters)}")
        else:
            self.status_label.configure(text="Vehicles loaded successfully")

    def clear_filters(self):
        """Clear ALL filters including dates"""
        self.filter_vehicle.delete(0, "end")
        self.filter_phone.delete(0, "end")
        self.filter_owner.delete(0, "end")
        self.filter_status.set("All")

        # ✅ Clear date filters
        self.filter_date_from_value = None
        self.filter_date_to_value = None
        self.filter_updated_from_value = None
        self.filter_updated_to_value = None
        self.date_from_text.configure(
            text="Any", fg=COLORS["text_secondary"])
        self.date_to_text.configure(
            text="Any", fg=COLORS["text_secondary"])
        self.updated_from_text.configure(
            text="Any", fg=COLORS["text_secondary"])
        self.updated_to_text.configure(
            text="Any", fg=COLORS["text_secondary"])
        self.date_from_clear.pack_forget()
        self.date_to_clear.pack_forget()
        self.updated_from_clear.pack_forget()
        self.updated_to_clear.pack_forget()

        self.load_vehicles()

    def sort_column(self, col):
        data = [(self.tree.set(child, col), child)
                for child in self.tree.get_children("")]
        try:
            data.sort(key=lambda t: int(t[0]) if t[0].isdigit() else t[0])
        except (ValueError, AttributeError):
            data.sort(key=lambda t: t[0])

        for index, (val, child) in enumerate(data):
            self.tree.move(child, "", index)

    def get_selected_vehicle(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning",
                                   "Please select a vehicle first!")
            return None

        item = self.tree.item(selection[0])
        values = item["values"]
        vehicle_id = values[0]
        return get_vehicle_by_id(vehicle_id)

    def add_new(self):
        self.app.show_page("add_vehicle")

    def edit_selected(self):
        vehicle = self.get_selected_vehicle()
        if vehicle:
            self.app.show_page_with_data("add_vehicle", vehicle)

    def delete_selected(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning",
                                   "Please select vehicle(s) to delete!")
            return

        count = len(selection)
        msg = (f"Are you sure you want to delete {count} vehicle(s)?\n"
               "This action cannot be undone!")
        if messagebox.askyesno("Confirm Delete", msg):
            for item in selection:
                values = self.tree.item(item)["values"]
                delete_vehicle(values[0])

            self.load_vehicles()
            messagebox.showinfo("Success",
                                f"{count} vehicle(s) deleted successfully!")

    def send_whatsapp_selected(self):
        """Send WhatsApp message to selected vehicle"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning",
                                   "Please select vehicle(s) to send message!")
            return

        count = 0
        for item in selection:
            values = self.tree.item(item)["values"]
            vehicle = get_vehicle_by_id(values[0])
            if vehicle:
                msg = format_message(
                    vehicle["vehicle_number"],
                    vehicle.get("owner_name", ""),
                    vehicle["expiry_date"])
                success = send_whatsapp_message(vehicle["phone"], msg)
                if success:
                    log_message(
                        vehicle["id"],
                        vehicle["vehicle_number"],
                        vehicle["phone"],
                        msg)
                    count += 1

        messagebox.showinfo(
            "WhatsApp",
            f"WhatsApp opened for {count} vehicle(s).\n"
            "Please click Send in WhatsApp for each message.")

    def share_search_results_whatsapp(self):
        """Share the current search results (vehicle + phone) via WhatsApp."""
        filters = self.get_filters()
        vehicles = get_all_vehicles(filters)

        if not vehicles:
            messagebox.showinfo(
                "Share List",
                "No vehicles match the current filter. Please adjust filters and try again.")
            return

        # Build message text
        lines = ["Vehicle List (Number - Phone):"]
        for v in vehicles:
            lines.append(f"{v['vehicle_number']} - {v['phone']}")

        body = "\n".join(lines)

        # Ask for recipient phone number
        recipient = simpledialog.askstring(
            "Share via WhatsApp",
            "Enter recipient phone number (with country code):")

        if not recipient:
            return

        success = send_whatsapp_message(recipient, body, auto_send=False)
        if success:
            messagebox.showinfo(
                "WhatsApp",
                "WhatsApp opened with the list. Please send the message.")
        else:
            messagebox.showerror(
                "WhatsApp",
                "Could not open WhatsApp. Please ensure WhatsApp is installed and try again.")

    def set_selected_call_status(self, status):
        """Update call status for selected vehicle(s)."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning",
                                   "Please select vehicle(s) to update!")
            return

        for item in selection:
            values = self.tree.item(item)["values"]
            vehicle_id = values[0]
            set_call_status(vehicle_id, status)

        self.load_vehicles()
        self.status_label.configure(
            text=f"Call status set to '{status}' for {len(selection)} vehicle(s)")

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def copy_vehicle_number(self):
        vehicle = self.get_selected_vehicle()
        if vehicle:
            self.parent.clipboard_clear()
            self.parent.clipboard_append(vehicle["vehicle_number"])
            self.status_label.configure(
                text=f"Copied: {vehicle['vehicle_number']}")

    def export_csv(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            initialfile="vehicles_export.csv")
        if filepath:
            filters = self.get_filters()
            count = export_to_csv(filepath, filters)
            messagebox.showinfo("Export",
                                f"Exported {count} vehicles to CSV!")

    def export_pdf(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")],
            initialfile="vehicles_export.pdf")
        if filepath:
            try:
                filters = self.get_filters()
                count = export_to_pdf(filepath, filters)
                messagebox.showinfo("Export",
                                    f"Exported {count} vehicles to PDF!")
            except ImportError:
                messagebox.showerror(
                    "Missing Library",
                    "PDF export requires reportlab library.\n\n"
                    "Install it using: pip install reportlab")
            except Exception as e:
                messagebox.showerror("Export Error", str(e))

    def import_csv(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("CSV Files", "*.csv"),
                       ("JSON Files", "*.json"),
                       ("All Files", "*.*")])
        if filepath:
            try:
                if filepath.endswith(".json"):
                    added, renewed, errors = import_from_json(filepath)
                else:
                    added, renewed, errors = import_from_csv(filepath)

                msg = (f"Import Complete!\n\n"
                       f"Added: {added}\n"
                       f"Renewed: {renewed}\n"
                       f"Errors: {len(errors)}")
                if errors:
                    msg += "\n\nErrors:\n" + "\n".join(errors[:10])
                    if len(errors) > 10:
                        msg += f"\n...and {len(errors) - 10} more"

                messagebox.showinfo("Import Result", msg)
                self.load_vehicles()

            except Exception as e:
                messagebox.showerror("Import Error", str(e))

    def download_sample(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            initialfile="sample_vehicles.csv")
        if filepath:
            generate_sample_csv(filepath)
            messagebox.showinfo("Sample CSV",
                                f"Sample CSV saved to:\n{filepath}")