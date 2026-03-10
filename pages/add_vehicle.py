"""
Add/Edit Vehicle Page
With quick duration dropdown (6 months, 1 year, etc.)
"""
import tkinter as tk
from tkinter import ttk, messagebox
from styles import COLORS, FONTS
from database import add_vehicle, update_vehicle, get_vehicle_by_number
from datetime import date, datetime, timedelta
import calendar as cal_module

# Try importing tkcalendar
try:
    from tkcalendar import Calendar
    HAS_CALENDAR = True
except ImportError:
    HAS_CALENDAR = False


def add_months(source_date, months):
    """Add months to a date and subtract 1 day (expiry = day before)"""
    month = source_date.month - 1 + months
    year = source_date.year + month // 12
    month = month % 12 + 1
    import calendar
    day = min(source_date.day, calendar.monthrange(year, month)[1])
    result = date(year, month, day)

    # ✅ Subtract 1 day (expiry = 1 day before completion)
    result = result - timedelta(days=1)

    return result


class AddVehiclePage:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.editing_vehicle = None
        # NEW: Default = 1 year from today (minus 1 day)
        self.selected_date_value = add_months(date.today(), 12)
        self.calendar_popup = None
        self.calendar_check_id = None
        self.build()

    def build(self):
        card = tk.Frame(
            self.parent, bg=COLORS["bg_card"],
            highlightbackground=COLORS["border"], highlightthickness=1)
        card.pack(fill="both", expand=True)

        inner = tk.Frame(card, bg=COLORS["bg_card"])
        inner.pack(fill="both", expand=True, padx=40, pady=30)

        self.form_title = tk.Label(
            inner, text="➕ Add New Vehicle",
            font=FONTS["heading"],
            bg=COLORS["bg_card"], fg=COLORS["text"])
        self.form_title.pack(anchor="w", pady=(0, 5))

        self.form_subtitle = tk.Label(
            inner,
            text="If vehicle number already exists, "
                 "it will be renewed automatically.",
            font=FONTS["small"],
            bg=COLORS["bg_card"], fg=COLORS["text_secondary"])
        self.form_subtitle.pack(anchor="w", pady=(0, 20))

        form_frame = tk.Frame(inner, bg=COLORS["bg_card"])
        form_frame.pack(fill="x")

        # =============================================
        # Row 1: Vehicle Number & Phone
        # =============================================
        row1 = tk.Frame(form_frame, bg=COLORS["bg_card"])
        row1.pack(fill="x", pady=(0, 15))

        vn_frame = tk.Frame(row1, bg=COLORS["bg_card"])
        vn_frame.pack(side="left", fill="x", expand=True, padx=(0, 15))

        tk.Label(
            vn_frame, text="Vehicle Number *",
            font=FONTS["small_bold"],
            bg=COLORS["bg_card"], fg=COLORS["text"]
        ).pack(anchor="w", pady=(0, 3))

        self.vehicle_number_var = tk.StringVar()
        self.entry_vehicle = tk.Entry(
            vn_frame, textvariable=self.vehicle_number_var,
            font=FONTS["input"], width=25)
        self.entry_vehicle.pack(fill="x", ipady=6)
        self.vehicle_number_var.trace_add(
            "write", self.on_vehicle_number_change)

        self.vehicle_status = tk.Label(
            vn_frame, text="", font=FONTS["small"],
            bg=COLORS["bg_card"], fg=COLORS["text_secondary"])
        self.vehicle_status.pack(anchor="w", pady=(2, 0))

        ph_frame = tk.Frame(row1, bg=COLORS["bg_card"])
        ph_frame.pack(side="left", fill="x", expand=True)

        tk.Label(
            ph_frame, text="Phone Number *",
            font=FONTS["small_bold"],
            bg=COLORS["bg_card"], fg=COLORS["text"]
        ).pack(anchor="w", pady=(0, 3))

        self.entry_phone = tk.Entry(
            ph_frame, font=FONTS["input"], width=25)
        self.entry_phone.pack(fill="x", ipady=6)

        # =============================================
        # Row 2: Quick Duration + Expiry Date
        # =============================================
        row_date = tk.Frame(form_frame, bg=COLORS["bg_card"])
        row_date.pack(fill="x", pady=(0, 15))

                # ----- LEFT: Quick Duration Selector (Chips Only) -----
        duration_frame = tk.Frame(row_date, bg=COLORS["bg_card"])
        duration_frame.pack(side="left", fill="x",
                            expand=True, padx=(0, 15))

        tk.Label(
            duration_frame, text="⚡ Quick Set Validity",
            font=FONTS["small_bold"],
            bg=COLORS["bg_card"], fg=COLORS["text"]
        ).pack(anchor="w", pady=(0, 8))

        # Quick duration buttons (chips)
        chips_frame = tk.Frame(duration_frame, bg=COLORS["bg_card"])
        chips_frame.pack(fill="x")

        quick_durations = [
            ("1 M", 1),
            ("3 M", 3),
            ("6 M", 6),
            ("1 Y", 12),
        ]

        self.duration_chips = {}

        for text, months in quick_durations:
            chip = tk.Label(
                chips_frame, text=text,
                font=("Segoe UI", 10, "bold"),
                bg=COLORS["bg"],
                fg=COLORS["primary"],
                padx=14, pady=6,
                cursor="hand2",
                relief="solid",
                borderwidth=1
            )
            chip.pack(side="left", padx=(0, 6))
            chip.bind("<Button-1>",
                      lambda e, m=months, c=chip:
                      self.set_duration_months(m, c))
            chip.bind("<Enter>",
                      lambda e, c=chip: c.configure(
                          bg=COLORS["primary"], fg="white"))
            chip.bind("<Leave>",
                      lambda e, c=chip, m=months:
                      self.reset_chip_style(c, m))

            self.duration_chips[months] = chip

        # Duration info label
        self.duration_info = tk.Label(
            duration_frame, text="👆 Click to auto-set expiry date",
            font=FONTS["small"],
            bg=COLORS["bg_card"],
            fg=COLORS["text_light"])
        self.duration_info.pack(anchor="w", pady=(8, 0))

        # ----- RIGHT: Expiry Date Picker -----
        ed_frame = tk.Frame(row_date, bg=COLORS["bg_card"])
        ed_frame.pack(side="left", fill="x", expand=True)

        tk.Label(
            ed_frame, text="Expiry Date *",
            font=FONTS["small_bold"],
            bg=COLORS["bg_card"], fg=COLORS["text"]
        ).pack(anchor="w", pady=(0, 3))

        # Clickable date input field
        self.date_input_frame = tk.Frame(
            ed_frame, bg="white",
            highlightbackground=COLORS["border"],
            highlightthickness=2,
            highlightcolor=COLORS["primary"],
            cursor="hand2")
        self.date_input_frame.pack(fill="x")

        date_inner = tk.Frame(self.date_input_frame, bg="white")
        date_inner.pack(fill="both", padx=10, pady=8)

        self.cal_icon = tk.Label(
            date_inner, text="📅",
            font=("Segoe UI", 14),
            bg="white", cursor="hand2")
        self.cal_icon.pack(side="left", padx=(0, 8))

        self.date_text = tk.Label(
            date_inner,
            text=date.today().strftime("%Y-%m-%d"),
            font=("Segoe UI", 13, "bold"),
            bg="white", fg=COLORS["text"],
            cursor="hand2", width=12, anchor="w")
        self.date_text.pack(side="left", padx=(0, 10))

        self.day_name = tk.Label(
            date_inner,
            text=date.today().strftime("(%A)"),
            font=("Segoe UI", 10),
            bg="white", fg=COLORS["text_secondary"],
            cursor="hand2")
        self.day_name.pack(side="left", padx=(0, 10))

        self.arrow_label = tk.Label(
            date_inner, text="▼",
            font=("Segoe UI", 10),
            bg="white", fg=COLORS["text_secondary"],
            cursor="hand2")
        self.arrow_label.pack(side="right")

        # Bind click to ALL parts
        for widget in [self.date_input_frame, date_inner,
                       self.cal_icon, self.date_text,
                       self.day_name, self.arrow_label]:
            widget.bind("<Button-1>", self.toggle_calendar)
            widget.bind("<Enter>", self.on_date_hover)
            widget.bind("<Leave>", self.on_date_leave)

        # Date status
        self.date_status = tk.Label(
            ed_frame, text="📅 Click to pick or use quick set ⬅️",
            font=FONTS["small"],
            bg=COLORS["bg_card"], fg=COLORS["text_light"])
        self.date_status.pack(anchor="w", pady=(5, 0))

        # Calendar container
        self.calendar_container = tk.Frame(
            ed_frame, bg=COLORS["bg_card"])

        # =============================================
        # Row 3: Owner Name & Vehicle Type
        # =============================================
        row2 = tk.Frame(form_frame, bg=COLORS["bg_card"])
        row2.pack(fill="x", pady=(0, 15))

        on_frame = tk.Frame(row2, bg=COLORS["bg_card"])
        on_frame.pack(side="left", fill="x",
                      expand=True, padx=(0, 15))

        tk.Label(
            on_frame, text="Owner Name",
            font=FONTS["small_bold"],
            bg=COLORS["bg_card"], fg=COLORS["text"]
        ).pack(anchor="w", pady=(0, 3))

        self.entry_owner = tk.Entry(
            on_frame, font=FONTS["input"], width=25)
        self.entry_owner.pack(fill="x", ipady=6)

        vt_frame = tk.Frame(row2, bg=COLORS["bg_card"])
        vt_frame.pack(side="left", fill="x", expand=True)

        tk.Label(
            vt_frame, text="Vehicle Type",
            font=FONTS["small_bold"],
            bg=COLORS["bg_card"], fg=COLORS["text"]
        ).pack(anchor="w", pady=(0, 3))

        self.entry_type = ttk.Combobox(
            vt_frame, font=FONTS["input"], width=23,
            values=["Car", "Bike", "Truck", "Bus", "Auto",
                    "Van", "SUV", "Other"])
        self.entry_type.pack(fill="x", ipady=4)

        # =============================================
        # Row 4: Notes
        # =============================================
        row4 = tk.Frame(form_frame, bg=COLORS["bg_card"])
        row4.pack(fill="x", pady=(0, 20))

        tk.Label(
            row4, text="Notes",
            font=FONTS["small_bold"],
            bg=COLORS["bg_card"], fg=COLORS["text"]
        ).pack(anchor="w", pady=(0, 3))

        self.entry_notes = tk.Text(
            row4, font=FONTS["input"], height=3, width=50)
        self.entry_notes.pack(fill="x")

        # =============================================
        # Buttons
        # =============================================
        btn_frame = tk.Frame(form_frame, bg=COLORS["bg_card"])
        btn_frame.pack(fill="x", pady=(10, 0))

        self.save_btn = tk.Label(
            btn_frame, text="💾 Save Vehicle",
            font=FONTS["button"],
            bg=COLORS["primary"], fg="white",
            padx=25, pady=10, cursor="hand2")
        self.save_btn.pack(side="left", padx=(0, 10))
        self.save_btn.bind("<Button-1>",
                           lambda e: self.save_vehicle())

        clear_btn = tk.Label(
            btn_frame, text="🔄 Clear Form",
            font=FONTS["button"],
            bg=COLORS["secondary"], fg="white",
            padx=25, pady=10, cursor="hand2")
        clear_btn.pack(side="left", padx=(0, 10))
        clear_btn.bind("<Button-1>",
                        lambda e: self.clear_form())

        cancel_btn = tk.Label(
            btn_frame, text="← Back to List",
            font=FONTS["button"],
            bg=COLORS["text_light"], fg="white",
            padx=25, pady=10, cursor="hand2")
        cancel_btn.pack(side="left")
        cancel_btn.bind("<Button-1>",
                        lambda e: self.app.show_page("vehicles"))

        # Initialize date display
        self.update_date_display()

        # ✅ Auto-highlight 1 Year chip on load
        if 12 in self.duration_chips:
            self.duration_chips[12].configure(
                bg=COLORS["primary"],
                fg="white",
                borderwidth=2)

        target = self.selected_date_value
        self.duration_info.configure(
            text=f"✅ 1 year from today → "
                 f"{target.strftime('%d-%b-%Y (%A)')}",
            fg=COLORS["success"])

        # =============================================
    # QUICK DURATION METHODS
    # =============================================

    def set_duration_months(self, months, clicked_chip=None):
        """Set expiry date based on months from today"""
        today = date.today()
        new_date = add_months(today, months)

        self.selected_date_value = new_date
        self.update_date_display()

        # Highlight active chip, reset others
        for m, chip in self.duration_chips.items():
            if m == months:
                chip.configure(
                    bg=COLORS["primary"],
                    fg="white",
                    relief="solid",
                    borderwidth=2)
            else:
                chip.configure(
                    bg=COLORS["bg"],
                    fg=COLORS["primary"],
                    relief="solid",
                    borderwidth=1)

        # Show info
        if months < 12:
            duration_text = (f"{months} month"
                             f"{'s' if months > 1 else ''}")
        else:
            years = months // 12
            remaining = months % 12
            if remaining:
                duration_text = (
                    f"{years} year{'s' if years > 1 else ''} "
                    f"{remaining} month"
                    f"{'s' if remaining > 1 else ''}")
            else:
                duration_text = (
                    f"{years} year{'s' if years > 1 else ''}")

        self.duration_info.configure(
            text=f"✅ {duration_text} from today → "
                 f"{new_date.strftime('%d-%b-%Y (%A)')}",
            fg=COLORS["success"])

        # Flash effect
        self.flash_date_field()

    def reset_chip_style(self, chip, months):
        """Reset chip style on mouse leave (keep active highlighted)"""
        # Check if this chip is currently active
        selected = self.selected_date_value
        today = date.today()
        expected = add_months(today, months)

        if selected == expected:
            # Keep active style
            chip.configure(
                bg=COLORS["primary"],
                fg="white")
        else:
            # Reset to default
            chip.configure(
                bg=COLORS["bg"],
                fg=COLORS["primary"])

    def flash_date_field(self):
        """Visual flash effect when date changes"""
        self.date_input_frame.configure(
            highlightbackground=COLORS["success"],
            highlightthickness=3)

        self.parent.after(
            500,
            lambda: self.update_date_display())

    def update_duration_from_date(self):
        """Update chip highlight based on selected date"""
        d = self.selected_date_value
        today = date.today()

        if d <= today:
            # Reset all chips
            for m, chip in self.duration_chips.items():
                chip.configure(
                    bg=COLORS["bg"],
                    fg=COLORS["primary"],
                    borderwidth=1)
            self.duration_info.configure(text="")
            return

        # Check which duration matches
        matched = False
        for months, chip in self.duration_chips.items():
            expected = add_months(today, months)
            if d == expected:
                chip.configure(
                    bg=COLORS["primary"],
                    fg="white",
                    borderwidth=2)
                matched = True
            else:
                chip.configure(
                    bg=COLORS["bg"],
                    fg=COLORS["primary"],
                    borderwidth=1)

        # Show info
        diff_days = (d - today).days
        months_approx = round(diff_days / 30.44)

        if months_approx >= 12:
            years = months_approx // 12
            rem = months_approx % 12
            if rem:
                text = f"≈ {years}y {rem}m"
            else:
                text = f"≈ {years} year{'s' if years > 1 else ''}"
        else:
            text = (f"≈ {months_approx} month"
                    f"{'s' if months_approx > 1 else ''}")

        self.duration_info.configure(
            text=f"📅 {text} ({diff_days} days) → "
                 f"{d.strftime('%d-%b-%Y')}",
            fg=COLORS["info"])
    # =============================================
    # CALENDAR METHODS
    # =============================================

    def on_date_hover(self, event=None):
        self.date_input_frame.configure(
            highlightbackground=COLORS["primary"],
            highlightthickness=2)
        for widget in [self.date_input_frame, self.cal_icon,
                       self.date_text, self.day_name,
                       self.arrow_label]:
            try:
                widget.configure(bg=COLORS["primary_light"])
            except tk.TclError:
                pass
        for child in self.date_input_frame.winfo_children():
            try:
                child.configure(bg=COLORS["primary_light"])
                for gc in child.winfo_children():
                    try:
                        gc.configure(bg=COLORS["primary_light"])
                    except tk.TclError:
                        pass
            except tk.TclError:
                pass

    def on_date_leave(self, event=None):
        self.date_input_frame.configure(
            highlightbackground=COLORS["border"],
            highlightthickness=2)
        for widget in [self.date_input_frame, self.cal_icon,
                       self.date_text, self.day_name,
                       self.arrow_label]:
            try:
                widget.configure(bg="white")
            except tk.TclError:
                pass
        for child in self.date_input_frame.winfo_children():
            try:
                child.configure(bg="white")
                for gc in child.winfo_children():
                    try:
                        gc.configure(bg="white")
                    except tk.TclError:
                        pass
            except tk.TclError:
                pass

    def toggle_calendar(self, event=None):
        if self.calendar_popup and self.calendar_popup.winfo_exists():
            self.close_calendar()
        else:
            self.open_calendar()

    def open_calendar(self):
        if self.calendar_popup and self.calendar_popup.winfo_exists():
            return
        
        self.calendar_popup = tk.Toplevel(self.parent)
        self.calendar_popup.configure(bg=COLORS["bg_card"])
        self.calendar_popup.resizable(False, False)
        
        # Make it modal - blocks interaction with parent until closed
        self.calendar_popup.grab_set()
        self.calendar_popup.attributes("-topmost", True)

        main_frame = tk.Frame(
            self.calendar_popup, bg=COLORS["bg_card"])
        main_frame.pack(fill="both", expand=True, padx=0, pady=0)

        if HAS_CALENDAR:
            self.build_tkcalendar(main_frame)
        else:
            self.build_custom_calendar(main_frame)

        # Smart positioning
        self.calendar_popup.update_idletasks()
        popup_w = self.calendar_popup.winfo_reqwidth()
        popup_h = self.calendar_popup.winfo_reqheight()
        screen_w = self.calendar_popup.winfo_screenwidth()
        screen_h = self.calendar_popup.winfo_screenheight()
        input_x = self.date_input_frame.winfo_rootx()
        input_y = self.date_input_frame.winfo_rooty()
        input_h = self.date_input_frame.winfo_height()

        x = input_x
        y = input_y + input_h + 2

        if y + popup_h > screen_h:
            y = input_y - popup_h - 2
        if x + popup_w > screen_w:
            x = screen_w - popup_w - 10
        if y < 10:
            y = 10

        self.calendar_popup.geometry(f"+{x}+{y}")

        # Bind Escape key to close
        self.calendar_popup.bind("<Escape>", lambda e: self.close_calendar())
        
        try:
            self.calendar_popup.focus_set()
        except Exception:
            pass

    def build_tkcalendar(self, parent):
        header = tk.Frame(parent, bg=COLORS["primary"])
        header.pack(fill="x")
        tk.Label(header, text="📅 Select Expiry Date",
                 font=FONTS["body_bold"],
                 bg=COLORS["primary"], fg="white",
                 pady=8).pack()

        cal = Calendar(
            parent, selectmode="day",
            year=self.selected_date_value.year,
            month=self.selected_date_value.month,
            day=self.selected_date_value.day,
            font=("Segoe UI", 11),
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
            othermonthweforeground=COLORS["text_light"],
            borderwidth=0, bordercolor=COLORS["border"],
            showothermonthdays=True, cursor="hand2")
        cal.pack(padx=10, pady=5)

        # Buttons frame (single row)
        btn_frame = tk.Frame(parent, bg=COLORS["bg_card"])
        btn_frame.pack(fill="x", padx=10, pady=(5, 10))

        # Today button
        today_btn = tk.Label(
            btn_frame,
            text="📅 Today",
            font=FONTS["button"],
            bg=COLORS["primary"],
            fg="white",
            padx=20,
            pady=6,
            cursor="hand2"
        )
        today_btn.pack(side="left", padx=(0, 5))

        today_btn.bind(
            "<Button-1>",
            lambda e: cal.selection_set(date.today())
        )

        # Select button
        confirm_btn = tk.Label(
            btn_frame,
            text="✅ Select",
            font=FONTS["button"],
            bg=COLORS["primary"],
            fg="white",
            padx=20,
            pady=6,
            cursor="hand2"
        )
        confirm_btn.pack(side="left", padx=(0, 5))

        confirm_btn.bind(
            "<Button-1>",
            lambda e: self.confirm_tkcalendar(cal)
        )

        # Cancel button
        cancel_btn = tk.Label(
            btn_frame,
            text="✖ Cancel",
            font=FONTS["button"],
            bg=COLORS["secondary"],
            fg="white",
            padx=20,
            pady=6,
            cursor="hand2"
        )
        cancel_btn.pack(side="left")

        cancel_btn.bind(
            "<Button-1>",
            lambda e: self.close_calendar()
        )


    def confirm_tkcalendar(self, cal):
        selected = cal.selection_get()
        self.selected_date_value = selected
        self.update_date_display()
        self.update_duration_from_date()
        self.close_calendar()

    def build_custom_calendar(self, parent):
        header = tk.Frame(parent, bg=COLORS["primary"])
        header.pack(fill="x")
        tk.Label(header, text="📅 Select Expiry Date",
                 font=FONTS["body_bold"],
                 bg=COLORS["primary"], fg="white",
                 pady=8).pack()

        nav_frame = tk.Frame(parent, bg=COLORS["bg_card"])
        nav_frame.pack(fill="x", padx=10, pady=5)

        self.cal_year = self.selected_date_value.year
        self.cal_month = self.selected_date_value.month

        prev_btn = tk.Label(
            nav_frame, text="◀",
            font=("Segoe UI", 14, "bold"),
            bg=COLORS["bg_card"], fg=COLORS["primary"],
            cursor="hand2", padx=10)
        prev_btn.pack(side="left")
        prev_btn.bind("<Button-1>",
                      lambda e: self.cal_prev_month(parent))

        self.cal_title = tk.Label(
            nav_frame, text="",
            font=FONTS["subheading"],
            bg=COLORS["bg_card"], fg=COLORS["text"])
        self.cal_title.pack(side="left", expand=True)

        next_btn = tk.Label(
            nav_frame, text="▶",
            font=("Segoe UI", 14, "bold"),
            bg=COLORS["bg_card"], fg=COLORS["primary"],
            cursor="hand2", padx=10)
        next_btn.pack(side="right")
        next_btn.bind("<Button-1>",
                      lambda e: self.cal_next_month(parent))

        self.days_container = tk.Frame(parent, bg=COLORS["bg_card"])
        self.days_container.pack(fill="x", padx=10)

        # Quick chips
        quick_frame = tk.Frame(parent, bg=COLORS["bg_card"])
        quick_frame.pack(fill="x", padx=10, pady=5)

        for text, months in [("Today", 0), ("+3M", 3),
                              ("+6M", 6), ("+1Y", 12), ("+2Y", 24)]:
            if months == 0:
                target = date.today()
            else:
                target = add_months(date.today(), months)

            qbtn = tk.Label(
                quick_frame, text=text,
                font=FONTS["small"],
                bg=COLORS["bg"], fg=COLORS["primary"],
                padx=8, pady=3, cursor="hand2",
                relief="solid", borderwidth=1)
            qbtn.pack(side="left", padx=2)
            qbtn.bind("<Button-1>",
                      lambda e, d=target: self.select_custom_date(d))
            qbtn.bind("<Enter>",
                      lambda e, b=qbtn: b.configure(
                          bg=COLORS["primary"], fg="white"))
            qbtn.bind("<Leave>",
                      lambda e, b=qbtn: b.configure(
                          bg=COLORS["bg"], fg=COLORS["primary"]))

        cancel_btn = tk.Label(
            parent, text="✖ Cancel",
            font=FONTS["small_bold"],
            bg=COLORS["secondary"], fg="white",
            padx=15, pady=5, cursor="hand2")
        cancel_btn.pack(pady=(5, 10))
        cancel_btn.bind("<Button-1>",
                        lambda e: self.close_calendar())

        self.draw_custom_calendar()

    def draw_custom_calendar(self):
        for widget in self.days_container.winfo_children():
            widget.destroy()

        month_name = cal_module.month_name[self.cal_month]
        self.cal_title.configure(
            text=f"{month_name} {self.cal_year}")

        headers = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        for i, h in enumerate(headers):
            tk.Label(
                self.days_container, text=h,
                font=FONTS["small_bold"],
                bg=COLORS["bg_card"],
                fg=COLORS["text_secondary"],
                width=4, pady=3).grid(row=0, column=i)

        cal_data = cal_module.monthcalendar(
            self.cal_year, self.cal_month)
        today = date.today()

        for ri, week in enumerate(cal_data):
            for ci, day in enumerate(week):
                if day == 0:
                    tk.Label(
                        self.days_container, text="",
                        bg=COLORS["bg_card"],
                        width=4, height=2).grid(
                        row=ri + 1, column=ci)
                else:
                    cd = date(self.cal_year, self.cal_month, day)
                    is_today = cd == today
                    is_sel = cd == self.selected_date_value
                    is_we = ci >= 5

                    if is_sel:
                        bg, fg = COLORS["primary"], "white"
                    elif is_today:
                        bg = COLORS["primary_light"]
                        fg = COLORS["primary"]
                    elif is_we:
                        bg, fg = "#F8FAFC", COLORS["text"]
                    else:
                        bg, fg = "white", COLORS["text"]

                    lbl = tk.Label(
                        self.days_container, text=str(day),
                        font=FONTS["body"] if not is_today
                        else FONTS["body_bold"],
                        bg=bg, fg=fg, width=4, height=2,
                        cursor="hand2", relief="flat")
                    lbl.grid(row=ri + 1, column=ci,
                             padx=1, pady=1)

                    d = cd
                    lbl.bind("<Button-1>",
                             lambda e, dt=d:
                             self.select_custom_date(dt))
                    lbl.bind("<Enter>",
                             lambda e, l=lbl:
                             l.configure(bg=COLORS["primary_light"]))
                    lbl.bind("<Leave>",
                             lambda e, l=lbl, b=bg:
                             l.configure(bg=b))

    def cal_prev_month(self, parent):
        self.cal_month -= 1
        if self.cal_month < 1:
            self.cal_month = 12
            self.cal_year -= 1
        self.draw_custom_calendar()

    def cal_next_month(self, parent):
        self.cal_month += 1
        if self.cal_month > 12:
            self.cal_month = 1
            self.cal_year += 1
        self.draw_custom_calendar()

    def select_custom_date(self, selected):
        self.selected_date_value = selected
        self.update_date_display()
        self.update_duration_from_date()
        self.close_calendar()

    def close_calendar(self):
        """Close and destroy the calendar popup"""
        if self.calendar_popup:
            try:
                if self.calendar_popup.winfo_exists():
                    self.calendar_popup.grab_release()
                    self.calendar_popup.destroy()
            except Exception:
                pass
        
        self.calendar_popup = None

    def update_date_display(self):
        d = self.selected_date_value
        self.date_text.configure(text=d.strftime("%Y-%m-%d"))
        self.day_name.configure(text=d.strftime("(%A)"))

        today = date.today()
        if d < today:
            color = COLORS["danger"]
            status = (f"⚠️ Past date "
                      f"({(today - d).days} days ago)")
            self.date_input_frame.configure(
                highlightbackground=COLORS["danger"])
        elif (d - today).days <= 7:
            color = COLORS["warning"]
            status = f"⚠️ Expires in {(d - today).days} day(s)"
            self.date_input_frame.configure(
                highlightbackground=COLORS["warning"])
        elif (d - today).days <= 30:
            color = COLORS["warning"]
            status = f"📅 Expires in {(d - today).days} days"
            self.date_input_frame.configure(
                highlightbackground=COLORS["warning"])
        else:
            color = COLORS["success"]
            status = f"✅ {(d - today).days} days from today"
            self.date_input_frame.configure(
                highlightbackground=COLORS["success"])

        self.date_text.configure(fg=color)
        self.date_status.configure(text=status, fg=color)


    # =============================================
    # HELPER METHODS
    # =============================================

    def get_expiry_date(self):
        return self.selected_date_value.strftime("%Y-%m-%d")

    def set_expiry_date(self, date_str):
        try:
            d = datetime.strptime(date_str, "%Y-%m-%d").date()
            self.selected_date_value = d
            self.update_date_display()
            self.update_duration_from_date()
        except ValueError:
            pass

    def on_vehicle_number_change(self, *args):
        vn = self.vehicle_number_var.get().strip()
        if len(vn) >= 4:
            existing = get_vehicle_by_number(vn)
            if existing:
                if (self.editing_vehicle and
                        existing["id"] == self.editing_vehicle["id"]):
                    self.vehicle_status.configure(
                        text="📝 Editing this vehicle",
                        fg=COLORS["primary"])
                else:
                    self.vehicle_status.configure(
                        text=f"🔄 Vehicle exists! Will RENEW. "
                             f"Current expiry: {existing['expiry_date']}",
                        fg=COLORS["warning"])

                    # ✅ Auto-fill phone number from existing record
                    if existing.get("phone"):
                        self.entry_phone.delete(0, "end")
                        self.entry_phone.insert(0, existing["phone"])

                    # ✅ Auto-fill owner name if available
                    if existing.get("owner_name"):
                        self.entry_owner.delete(0, "end")
                        self.entry_owner.insert(0, existing["owner_name"])

                    # ✅ Auto-fill vehicle type if available
                    if existing.get("vehicle_type"):
                        self.entry_type.set(existing["vehicle_type"])

                    # ✅ Show current expiry in date picker
                    if existing.get("expiry_date"):
                        try:
                            old_date = datetime.strptime(
                                existing["expiry_date"],
                                "%Y-%m-%d").date()
                            old_formatted = old_date.strftime("%d-%b-%Y")
                            self.vehicle_status.configure(
                                text=f"🔄 Vehicle exists! Will RENEW. "
                                     f"Old expiry: {old_formatted}",
                                fg=COLORS["warning"])
                        except ValueError:
                            pass
            else:
                self.vehicle_status.configure(
                    text="✅ New vehicle number",
                    fg=COLORS["success"])
        else:
            self.vehicle_status.configure(text="")

    def load_data(self, vehicle):
        self.editing_vehicle = vehicle
        self.form_title.configure(text="✏️ Edit Vehicle")
        self.save_btn.configure(text="💾 Update Vehicle")

        self.entry_vehicle.delete(0, "end")
        self.entry_vehicle.insert(0,
                                   vehicle.get("vehicle_number", ""))
        self.entry_phone.delete(0, "end")
        self.entry_phone.insert(0, vehicle.get("phone", ""))
        self.entry_owner.delete(0, "end")
        self.entry_owner.insert(0, vehicle.get("owner_name", ""))
        self.entry_type.set(vehicle.get("vehicle_type", ""))

        if vehicle.get("expiry_date"):
            self.set_expiry_date(vehicle["expiry_date"])

        self.entry_notes.delete("1.0", "end")
        self.entry_notes.insert("1.0", vehicle.get("notes", ""))

    def save_vehicle(self):
        vehicle_number = self.entry_vehicle.get().strip().upper()
        phone = self.entry_phone.get().strip()
        expiry_date = self.get_expiry_date()
        owner_name = self.entry_owner.get().strip()
        vehicle_type = self.entry_type.get().strip()
        notes = self.entry_notes.get("1.0", "end").strip()

        # NOTE: duration is NOT saved - only expiry_date

        if not vehicle_number:
            messagebox.showerror("Error",
                                 "Vehicle number is required!")
            self.entry_vehicle.focus()
            return

        if not phone:
            messagebox.showerror("Error",
                                 "Phone number is required!")
            self.entry_phone.focus()
            return

        if not expiry_date:
            messagebox.showerror("Error",
                                 "Please pick an expiry date!")
            return

        clean_phone = phone.replace(
            "+", "").replace("-", "").replace(" ", "")
        if not clean_phone.isdigit() or len(clean_phone) < 10:
            messagebox.showerror("Error",
                                 "Invalid phone! Min 10 digits.")
            return

        try:
            if self.editing_vehicle:
                result = update_vehicle(
                    self.editing_vehicle["id"],
                    vehicle_number, phone, expiry_date,
                    owner_name, vehicle_type, notes)
                if result == "conflict":
                    messagebox.showerror(
                        "Error",
                        "Another vehicle with this number exists!")
                    return
                messagebox.showinfo("Success",
                                    "Vehicle updated! ✅")
            else:
                result = add_vehicle(
                    vehicle_number, phone, expiry_date,
                    owner_name, vehicle_type, notes)
                if result == "renewed":
                    messagebox.showinfo(
                        "Renewed! 🔄",
                        f"Vehicle {vehicle_number} renewed!")
                else:
                    messagebox.showinfo(
                        "Success ✅",
                        f"Vehicle {vehicle_number} added!")

            self.clear_form()
            self.app.show_page("vehicles")

        except Exception as e:
            messagebox.showerror("Error", f"Failed: {str(e)}")

    def clear_form(self):
        self.editing_vehicle = None
        self.form_title.configure(text="➕ Add New Vehicle")
        self.save_btn.configure(text="💾 Save Vehicle")

        self.entry_vehicle.delete(0, "end")
        self.entry_phone.delete(0, "end")
        self.entry_owner.delete(0, "end")
        self.entry_type.set("")
        self.entry_notes.delete("1.0", "end")
        self.vehicle_status.configure(text="")

        # ✅ Reset to 1 year default and highlight chip
        self.selected_date_value = add_months(date.today(), 12)
        self.update_date_display()

        # Highlight 1 Year chip, reset others
        for m, chip in self.duration_chips.items():
            if m == 12:
                chip.configure(
                    bg=COLORS["primary"],
                    fg="white",
                    borderwidth=2)
            else:
                chip.configure(
                    bg=COLORS["bg"],
                    fg=COLORS["primary"],
                    borderwidth=1)

        # Show duration info
        target = self.selected_date_value
        self.duration_info.configure(
            text=f"✅ 1 year from today → "
                 f"{target.strftime('%d-%b-%Y (%A)')}",
            fg=COLORS["success"])

        self.close_calendar()
        self.entry_vehicle.focus()