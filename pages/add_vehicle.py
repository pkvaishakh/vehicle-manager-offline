
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
    """Add months to a date and subtract 1 day"""
    month = source_date.month - 1 + months
    year = source_date.year + month // 12
    month = month % 12 + 1

    import calendar
    day = min(source_date.day, calendar.monthrange(year, month)[1])

    result = date(year, month, day)

    # Expiry date is one day before full completion
    result = result - timedelta(days=1)
    return result


class AddVehiclePage:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.editing_vehicle = None

        # Preserve last selected start date, duration and expiry date
        if not hasattr(self.app, "_vehicle_form_last_dates"):
            start = date.today()
            self.app._vehicle_form_last_dates = {
                "start": start,
                "duration": 12,
                "expiry": add_months(start, 12)
            }

        saved_dates = self.app._vehicle_form_last_dates

        self.start_date_value = saved_dates["start"]
        self.selected_duration_months = saved_dates["duration"]
        self.selected_date_value = saved_dates["expiry"]

        self.calendar_popup = None
        self.calendar_check_id = None
        self.calendar_target = "expiry"

        self.build()

    def build(self):
        card = tk.Frame(
            self.parent,
            bg=COLORS["bg_card"],
            highlightbackground=COLORS["border"],
            highlightthickness=1
        )
        card.pack(fill="both", expand=True)

        inner = tk.Frame(card, bg=COLORS["bg_card"])
        inner.pack(fill="both", expand=True, padx=40, pady=30)

        self.form_title = tk.Label(
            inner,
            text="➕ Add New Vehicle",
            font=FONTS["heading"],
            bg=COLORS["bg_card"],
            fg=COLORS["text"]
        )
        self.form_title.pack(anchor="w", pady=(0, 4))

        self.form_subtitle = tk.Label(
            inner,
            text="If vehicle number already exists, it will be renewed automatically.",
            font=FONTS["small"],
            bg=COLORS["bg_card"],
            fg=COLORS["text_secondary"]
        )
        self.form_subtitle.pack(anchor="w", pady=(0, 6))

        self.vehicle_status = tk.Label(
            inner,
            text="",
            font=FONTS["small_bold"],
            bg=COLORS["bg_card"],
            fg=COLORS["text_secondary"]
        )
        self.vehicle_status.pack(anchor="w", pady=(0, 18))

        form_frame = tk.Frame(inner, bg=COLORS["bg_card"])
        form_frame.pack(fill="both", expand=True)

        form_frame.columnconfigure(0, weight=1)
        form_frame.columnconfigure(1, minsize=24)
        form_frame.columnconfigure(2, weight=1)

        # Vehicle Number
        vn_frame = tk.Frame(form_frame, bg=COLORS["bg_card"])
        vn_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))

        tk.Label(
            vn_frame,
            text="Vehicle Number *",
            font=FONTS["small_bold"],
            bg=COLORS["bg_card"],
            fg=COLORS["text"]
        ).pack(anchor="w", pady=(0, 6))

        self.vehicle_number_var = tk.StringVar()
        self.entry_vehicle = tk.Entry(
            vn_frame,
            textvariable=self.vehicle_number_var,
            font=FONTS["input"]
        )
        self.entry_vehicle.pack(fill="x", ipady=6)

        self.vehicle_number_var.trace_add(
            "write",
            self.on_vehicle_number_change
        )

        # Phone Number
        ph_frame = tk.Frame(form_frame, bg=COLORS["bg_card"])
        ph_frame.grid(row=0, column=2, sticky="ew", pady=(0, 20))

        tk.Label(
            ph_frame,
            text="Phone Number *",
            font=FONTS["small_bold"],
            bg=COLORS["bg_card"],
            fg=COLORS["text"]
        ).pack(anchor="w", pady=(0, 6))

        self.entry_phone = tk.Entry(
            ph_frame,
            font=FONTS["input"]
        )
        self.entry_phone.pack(fill="x", ipady=6)

        # Quick Validity Bar
        quick_bar = tk.Frame(form_frame, bg=COLORS["bg_card"])
        quick_bar.grid(
            row=1,
            column=0,
            columnspan=3,
            sticky="w",
            pady=(0, 10)
        )

        quick_durations = [
            ("1 Month", 1),
            ("3 Months", 3),
            ("6 Months", 6),
            ("1 Year", 12),
        ]

        self.duration_chips = {}

        for text, months in quick_durations:
            chip = tk.Label(
                quick_bar,
                text=text,
                font=("Segoe UI", 9, "bold"),
                bg=COLORS["bg"],
                fg=COLORS["primary"],
                padx=16,
                pady=5,
                cursor="hand2",
                relief="solid",
                borderwidth=1
            )
            chip.pack(side="left", padx=(0, 8))

            chip.bind(
                "<Button-1>",
                lambda e, m=months, c=chip: self.set_duration_months(m, c)
            )
            chip.bind(
                "<Enter>",
                lambda e, c=chip: c.configure(
                    bg=COLORS["primary"],
                    fg="white"
                )
            )
            chip.bind(
                "<Leave>",
                lambda e, c=chip, m=months: self.reset_chip_style(c, m)
            )

            self.duration_chips[months] = chip

        # Start Date
        start_frame = tk.Frame(form_frame, bg=COLORS["bg_card"])
        start_frame.grid(row=2, column=0, sticky="ew", pady=(0, 24))

        tk.Label(
            start_frame,
            text="📅 Start Date",
            font=FONTS["small_bold"],
            bg=COLORS["bg_card"],
            fg=COLORS["text"]
        ).pack(anchor="w", pady=(0, 6))

        self.start_input_frame = tk.Frame(
            start_frame,
            bg="white",
            highlightbackground=COLORS["border"],
            highlightthickness=1,
            cursor="hand2"
        )
        self.start_input_frame.pack(fill="x")

        start_inner = tk.Frame(self.start_input_frame, bg="white")
        start_inner.pack(fill="both", padx=12, pady=8)

        self.start_icon = tk.Label(
            start_inner,
            text="📅",
            font=("Segoe UI", 13),
            bg="white",
            cursor="hand2"
        )
        self.start_icon.pack(side="left", padx=(0, 8))

        self.start_text = tk.Label(
            start_inner,
            text=self.start_date_value.strftime("%Y-%m-%d"),
            font=("Segoe UI", 12, "bold"),
            bg="white",
            fg=COLORS["text"],
            cursor="hand2",
            anchor="w"
        )
        self.start_text.pack(side="left")

        for widget in [
            self.start_input_frame,
            start_inner,
            self.start_icon,
            self.start_text
        ]:
            widget.bind(
                "<Button-1>",
                lambda e, t="start": self.toggle_calendar(target=t)
            )
            widget.bind("<Enter>", self.on_start_hover)
            widget.bind("<Leave>", self.on_start_leave)

        # Expiry Date
        ed_frame = tk.Frame(form_frame, bg=COLORS["bg_card"])
        ed_frame.grid(row=2, column=2, sticky="ew", pady=(0, 24))

        tk.Label(
            ed_frame,
            text="Expiry Date *",
            font=FONTS["small_bold"],
            bg=COLORS["bg_card"],
            fg=COLORS["text"]
        ).pack(anchor="w", pady=(0, 6))

        self.date_input_frame = tk.Frame(
            ed_frame,
            bg="white",
            highlightbackground=COLORS["border"],
            highlightthickness=1,
            cursor="hand2"
        )
        self.date_input_frame.pack(fill="x")

        date_inner = tk.Frame(self.date_input_frame, bg="white")
        date_inner.pack(fill="both", padx=12, pady=8)

        self.cal_icon = tk.Label(
            date_inner,
            text="📅",
            font=("Segoe UI", 13),
            bg="white",
            cursor="hand2"
        )
        self.cal_icon.pack(side="left", padx=(0, 8))

        self.date_text = tk.Label(
            date_inner,
            text=self.selected_date_value.strftime("%Y-%m-%d"),
            font=("Segoe UI", 12, "bold"),
            bg="white",
            fg=COLORS["text"],
            cursor="hand2",
            width=11,
            anchor="w"
        )
        self.date_text.pack(side="left", padx=(0, 6))

        self.day_name = tk.Label(
            date_inner,
            text=self.selected_date_value.strftime("(%A)"),
            font=("Segoe UI", 10),
            bg="white",
            fg=COLORS["text_secondary"],
            cursor="hand2"
        )
        self.day_name.pack(side="left")

        self.arrow_label = tk.Label(
            date_inner,
            text="▼",
            font=("Segoe UI", 9),
            bg="white",
            fg=COLORS["text_secondary"],
            cursor="hand2"
        )
        self.arrow_label.pack(side="right")

        for widget in [
            self.date_input_frame,
            date_inner,
            self.cal_icon,
            self.date_text,
            self.day_name,
            self.arrow_label
        ]:
            widget.bind(
                "<Button-1>",
                lambda e, t="expiry": self.toggle_calendar(target=t)
            )
            widget.bind("<Enter>", self.on_date_hover)
            widget.bind("<Leave>", self.on_date_leave)

        # Buttons
        btn_frame = tk.Frame(form_frame, bg=COLORS["bg_card"])
        btn_frame.grid(
            row=3,
            column=0,
            columnspan=3,
            sticky="w",
            pady=(10, 0)
        )

        self.save_btn = tk.Label(
            btn_frame,
            text="💾 Save Vehicle",
            font=FONTS["button"],
            bg=COLORS["primary"],
            fg="white",
            padx=28,
            pady=10,
            cursor="hand2"
        )
        self.save_btn.pack(side="left", padx=(0, 12))
        self.save_btn.bind("<Button-1>", lambda e: self.save_vehicle())

        clear_btn = tk.Label(
            btn_frame,
            text="🔄 Clear Form",
            font=FONTS["button"],
            bg=COLORS["secondary"],
            fg="white",
            padx=24,
            pady=10,
            cursor="hand2"
        )
        clear_btn.pack(side="left", padx=(0, 12))
        clear_btn.bind("<Button-1>", lambda e: self.clear_form())

        cancel_btn = tk.Label(
            btn_frame,
            text="← Back to List",
            font=FONTS["button"],
            bg=COLORS["text_light"],
            fg="white",
            padx=24,
            pady=10,
            cursor="hand2"
        )
        cancel_btn.pack(side="left")
        cancel_btn.bind(
            "<Button-1>",
            lambda e: self.app.show_page("vehicles")
        )

        self.update_start_date_display()
        self.update_date_display()
        self.refresh_duration_chips()

    # =============================================
    # PRESERVE DATE SELECTION METHODS
    # =============================================

    def remember_date_selection(self):
        """Save currently selected start date, duration and expiry date."""
        self.app._vehicle_form_last_dates = {
            "start": self.start_date_value,
            "duration": self.selected_duration_months,
            "expiry": self.selected_date_value
        }

    def restore_last_date_selection(self):
        """Restore previously selected start date, duration and expiry date."""
        saved_dates = getattr(self.app, "_vehicle_form_last_dates", None)

        if not saved_dates:
            start = date.today()
            saved_dates = {
                "start": start,
                "duration": 12,
                "expiry": add_months(start, 12)
            }
            self.app._vehicle_form_last_dates = saved_dates

        self.start_date_value = saved_dates["start"]
        self.selected_duration_months = saved_dates["duration"]
        self.selected_date_value = saved_dates["expiry"]

        self.update_start_date_display()
        self.update_date_display()
        self.refresh_duration_chips()

    def refresh_duration_chips(self):
        """Refresh quick validity chip style."""
        for months, chip in self.duration_chips.items():
            expected = add_months(self.start_date_value, months)

            is_active = (
                self.selected_duration_months == months
                and self.selected_date_value == expected
            )

            if is_active:
                chip.configure(
                    bg=COLORS["primary"],
                    fg="white",
                    relief="solid",
                    borderwidth=2
                )
            else:
                chip.configure(
                    bg=COLORS["bg"],
                    fg=COLORS["primary"],
                    relief="solid",
                    borderwidth=1
                )

    # =============================================
    # START DATE UI METHODS
    # =============================================

    def update_start_date_display(self):
        self.start_text.configure(
            text=self.start_date_value.strftime("%Y-%m-%d")
        )

    def on_start_hover(self, event=None):
        self.start_input_frame.configure(
            highlightbackground=COLORS["primary"],
            highlightthickness=1
        )

        for w in [
            self.start_input_frame,
            self.start_icon,
            self.start_text
        ]:
            try:
                w.configure(bg=COLORS["primary_light"])
            except tk.TclError:
                pass

        for child in self.start_input_frame.winfo_children():
            try:
                child.configure(bg=COLORS["primary_light"])
            except tk.TclError:
                pass

    def on_start_leave(self, event=None):
        self.start_input_frame.configure(
            highlightbackground=COLORS["border"],
            highlightthickness=1
        )

        for w in [
            self.start_input_frame,
            self.start_icon,
            self.start_text
        ]:
            try:
                w.configure(bg="white")
            except tk.TclError:
                pass

        for child in self.start_input_frame.winfo_children():
            try:
                child.configure(bg="white")
            except tk.TclError:
                pass

    # =============================================
    # QUICK DURATION METHODS
    # =============================================

    def set_duration_months(self, months, clicked_chip=None):
        """Set expiry date based on selected duration from start date."""
        self.selected_duration_months = months
        self.selected_date_value = add_months(self.start_date_value, months)

        self.update_date_display()
        self.refresh_duration_chips()
        self.remember_date_selection()
        self.flash_date_field()

    def reset_chip_style(self, chip, months):
        """Reset chip style on mouse leave."""
        expected = add_months(self.start_date_value, months)

        if (
            self.selected_duration_months == months
            and self.selected_date_value == expected
        ):
            chip.configure(
                bg=COLORS["primary"],
                fg="white",
                borderwidth=2
            )
        else:
            chip.configure(
                bg=COLORS["bg"],
                fg=COLORS["primary"],
                borderwidth=1
            )

    def flash_date_field(self):
        """Visual flash effect when expiry date changes."""
        self.date_input_frame.configure(
            highlightbackground=COLORS["success"],
            highlightthickness=2
        )

        self.parent.after(
            500,
            lambda: self.update_date_display()
        )

    def update_duration_from_date(self):
        """Update quick validity chip based on selected expiry date."""
        selected_expiry = self.selected_date_value
        start = self.start_date_value

        matched_duration = None

        if selected_expiry > start:
            for months in self.duration_chips:
                expected = add_months(start, months)
                if selected_expiry == expected:
                    matched_duration = months
                    break

        self.selected_duration_months = matched_duration
        self.refresh_duration_chips()

    # =============================================
    # CALENDAR METHODS
    # =============================================

    def toggle_calendar(self, event=None, target="expiry"):
        self.calendar_target = target

        if self.calendar_popup and self.calendar_popup.winfo_exists():
            self.close_calendar()
        else:
            self.open_calendar()

    def on_date_hover(self, event=None):
        self.date_input_frame.configure(
            highlightbackground=COLORS["primary"],
            highlightthickness=1
        )

        for widget in [
            self.date_input_frame,
            self.cal_icon,
            self.date_text,
            self.day_name,
            self.arrow_label
        ]:
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
            highlightthickness=1
        )

        for widget in [
            self.date_input_frame,
            self.cal_icon,
            self.date_text,
            self.day_name,
            self.arrow_label
        ]:
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

    def open_calendar(self):
        if self.calendar_popup and self.calendar_popup.winfo_exists():
            return

        self.calendar_popup = tk.Toplevel(self.parent)
        self.calendar_popup.configure(bg=COLORS["bg_card"])
        self.calendar_popup.resizable(False, False)

        self.calendar_popup.grab_set()
        self.calendar_popup.attributes("-topmost", True)

        main_frame = tk.Frame(
            self.calendar_popup,
            bg=COLORS["bg_card"]
        )
        main_frame.pack(fill="both", expand=True, padx=0, pady=0)

        if HAS_CALENDAR:
            self.build_tkcalendar(main_frame)
        else:
            self.build_custom_calendar(main_frame)

        self.calendar_popup.update_idletasks()

        popup_w = self.calendar_popup.winfo_reqwidth()
        popup_h = self.calendar_popup.winfo_reqheight()
        screen_w = self.calendar_popup.winfo_screenwidth()
        screen_h = self.calendar_popup.winfo_screenheight()

        target_frame = (
            self.start_input_frame
            if self.calendar_target == "start"
            else self.date_input_frame
        )

        input_x = target_frame.winfo_rootx()
        input_y = target_frame.winfo_rooty()
        input_h = target_frame.winfo_height()

        x = input_x
        y = input_y + input_h + 2

        if y + popup_h > screen_h:
            y = input_y - popup_h - 2

        if x + popup_w > screen_w:
            x = screen_w - popup_w - 10

        if y < 10:
            y = 10

        self.calendar_popup.geometry(f"+{x}+{y}")
        self.calendar_popup.bind(
            "<Escape>",
            lambda e: self.close_calendar()
        )

        try:
            self.calendar_popup.focus_set()
        except Exception:
            pass

    def build_tkcalendar(self, parent):
        header = tk.Frame(parent, bg=COLORS["primary"])
        header.pack(fill="x")

        tk.Label(
            header,
            text="📅 Select Date",
            font=FONTS["body_bold"],
            bg=COLORS["primary"],
            fg="white",
            pady=8
        ).pack()

        current = (
            self.start_date_value
            if self.calendar_target == "start"
            else self.selected_date_value
        )

        cal = Calendar(
            parent,
            selectmode="day",
            year=current.year,
            month=current.month,
            day=current.day,
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
            borderwidth=0,
            bordercolor=COLORS["border"],
            showothermonthdays=True,
            cursor="hand2"
        )
        cal.pack(padx=10, pady=5)

        btn_frame = tk.Frame(parent, bg=COLORS["bg_card"])
        btn_frame.pack(fill="x", padx=10, pady=(5, 10))

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

        if self.calendar_target == "start":
            self.start_date_value = selected
            self.update_start_date_display()

            if self.selected_duration_months:
                self.selected_date_value = add_months(
                    self.start_date_value,
                    self.selected_duration_months
                )
                self.update_date_display()
                self.flash_date_field()

            self.update_duration_from_date()

        else:
            self.selected_date_value = selected
            self.update_date_display()
            self.update_duration_from_date()

        self.remember_date_selection()
        self.close_calendar()

    def build_custom_calendar(self, parent):
        header = tk.Frame(parent, bg=COLORS["primary"])
        header.pack(fill="x")

        tk.Label(
            header,
            text="📅 Select Date",
            font=FONTS["body_bold"],
            bg=COLORS["primary"],
            fg="white",
            pady=8
        ).pack()

        nav_frame = tk.Frame(parent, bg=COLORS["bg_card"])
        nav_frame.pack(fill="x", padx=10, pady=5)

        current = (
            self.start_date_value
            if self.calendar_target == "start"
            else self.selected_date_value
        )

        self.cal_year = current.year
        self.cal_month = current.month

        prev_btn = tk.Label(
            nav_frame,
            text="◀",
            font=("Segoe UI", 14, "bold"),
            bg=COLORS["bg_card"],
            fg=COLORS["primary"],
            cursor="hand2",
            padx=10
        )
        prev_btn.pack(side="left")
        prev_btn.bind(
            "<Button-1>",
            lambda e: self.cal_prev_month(parent)
        )

        self.cal_title = tk.Label(
            nav_frame,
            text="",
            font=FONTS["subheading"],
            bg=COLORS["bg_card"],
            fg=COLORS["text"]
        )
        self.cal_title.pack(side="left", expand=True)

        next_btn = tk.Label(
            nav_frame,
            text="▶",
            font=("Segoe UI", 14, "bold"),
            bg=COLORS["bg_card"],
            fg=COLORS["primary"],
            cursor="hand2",
            padx=10
        )
        next_btn.pack(side="right")
        next_btn.bind(
            "<Button-1>",
            lambda e: self.cal_next_month(parent)
        )

        self.days_container = tk.Frame(parent, bg=COLORS["bg_card"])
        self.days_container.pack(fill="x", padx=10)

        if self.calendar_target == "expiry":
            quick_frame = tk.Frame(parent, bg=COLORS["bg_card"])
            quick_frame.pack(fill="x", padx=10, pady=5)

            quick_items = [
                ("Today", 0),
                ("+3M", 3),
                ("+6M", 6),
                ("+1Y", 12),
                ("+2Y", 24)
            ]

            for text, months in quick_items:
                if months == 0:
                    target = date.today()
                else:
                    target = add_months(date.today(), months)

                qbtn = tk.Label(
                    quick_frame,
                    text=text,
                    font=FONTS["small"],
                    bg=COLORS["bg"],
                    fg=COLORS["primary"],
                    padx=8,
                    pady=3,
                    cursor="hand2",
                    relief="solid",
                    borderwidth=1
                )
                qbtn.pack(side="left", padx=2)

                qbtn.bind(
                    "<Button-1>",
                    lambda e, d=target: self.select_custom_date(d)
                )
                qbtn.bind(
                    "<Enter>",
                    lambda e, b=qbtn: b.configure(
                        bg=COLORS["primary"],
                        fg="white"
                    )
                )
                qbtn.bind(
                    "<Leave>",
                    lambda e, b=qbtn: b.configure(
                        bg=COLORS["bg"],
                        fg=COLORS["primary"]
                    )
                )

        cancel_btn = tk.Label(
            parent,
            text="✖ Cancel",
            font=FONTS["small_bold"],
            bg=COLORS["secondary"],
            fg="white",
            padx=15,
            pady=5,
            cursor="hand2"
        )
        cancel_btn.pack(pady=(5, 10))
        cancel_btn.bind(
            "<Button-1>",
            lambda e: self.close_calendar()
        )

        self.draw_custom_calendar()

    def draw_custom_calendar(self):
        for widget in self.days_container.winfo_children():
            widget.destroy()

        month_name = cal_module.month_name[self.cal_month]

        self.cal_title.configure(
            text=f"{month_name} {self.cal_year}"
        )

        headers = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]

        for i, h in enumerate(headers):
            tk.Label(
                self.days_container,
                text=h,
                font=FONTS["small_bold"],
                bg=COLORS["bg_card"],
                fg=COLORS["text_secondary"],
                width=4,
                pady=3
            ).grid(row=0, column=i)

        cal_data = cal_module.monthcalendar(
            self.cal_year,
            self.cal_month
        )

        today = date.today()

        for ri, week in enumerate(cal_data):
            for ci, day in enumerate(week):
                if day == 0:
                    tk.Label(
                        self.days_container,
                        text="",
                        bg=COLORS["bg_card"],
                        width=4,
                        height=2
                    ).grid(row=ri + 1, column=ci)
                else:
                    cd = date(self.cal_year, self.cal_month, day)

                    selected_date = (
                        self.start_date_value
                        if self.calendar_target == "start"
                        else self.selected_date_value
                    )

                    is_today = cd == today
                    is_selected = cd == selected_date
                    is_weekend = ci >= 5

                    if is_selected:
                        bg = COLORS["primary"]
                        fg = "white"
                    elif is_today:
                        bg = COLORS["primary_light"]
                        fg = COLORS["primary"]
                    elif is_weekend:
                        bg = "#F8FAFC"
                        fg = COLORS["text"]
                    else:
                        bg = "white"
                        fg = COLORS["text"]

                    lbl = tk.Label(
                        self.days_container,
                        text=str(day),
                        font=(
                            FONTS["body_bold"]
                            if is_today
                            else FONTS["body"]
                        ),
                        bg=bg,
                        fg=fg,
                        width=4,
                        height=2,
                        cursor="hand2",
                        relief="flat"
                    )
                    lbl.grid(row=ri + 1, column=ci, padx=1, pady=1)

                    d = cd

                    lbl.bind(
                        "<Button-1>",
                        lambda e, dt=d: self.select_custom_date(dt)
                    )
                    lbl.bind(
                        "<Enter>",
                        lambda e, l=lbl: l.configure(
                            bg=COLORS["primary_light"]
                        )
                    )
                    lbl.bind(
                        "<Leave>",
                        lambda e, l=lbl, b=bg: l.configure(bg=b)
                    )

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
        if self.calendar_target == "start":
            self.start_date_value = selected
            self.update_start_date_display()

            if self.selected_duration_months:
                self.selected_date_value = add_months(
                    self.start_date_value,
                    self.selected_duration_months
                )
                self.update_date_display()
                self.flash_date_field()

            self.update_duration_from_date()

        else:
            self.selected_date_value = selected
            self.update_date_display()
            self.update_duration_from_date()

        self.remember_date_selection()
        self.close_calendar()

    def close_calendar(self):
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

        self.date_text.configure(
            text=d.strftime("%Y-%m-%d")
        )

        self.day_name.configure(
            text=d.strftime("(%A)")
        )

        today = date.today()

        if d < today:
            color = COLORS["danger"]
            self.date_input_frame.configure(
                highlightbackground=COLORS["danger"]
            )
        elif (d - today).days <= 30:
            color = COLORS["warning"]
            self.date_input_frame.configure(
                highlightbackground=COLORS["warning"]
            )
        else:
            color = COLORS["success"]
            self.date_input_frame.configure(
                highlightbackground=COLORS["border"]
            )

        self.date_text.configure(fg=color)

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
                if (
                    self.editing_vehicle
                    and existing["id"] == self.editing_vehicle["id"]
                ):
                    self.vehicle_status.configure(
                        text="📝 Editing this vehicle",
                        fg=COLORS["primary"]
                    )
                else:
                    self.vehicle_status.configure(
                        text=(
                            f"🔄 Vehicle exists! Will RENEW. "
                            f"Current expiry: {existing['expiry_date']}"
                        ),
                        fg=COLORS["warning"]
                    )

                    if existing.get("phone"):
                        self.entry_phone.delete(0, "end")
                        self.entry_phone.insert(0, existing["phone"])

                    if existing.get("expiry_date"):
                        try:
                            old_date = datetime.strptime(
                                existing["expiry_date"],
                                "%Y-%m-%d"
                            ).date()

                            old_formatted = old_date.strftime("%d-%b-%Y")

                            self.vehicle_status.configure(
                                text=(
                                    f"🔄 Vehicle exists! Will RENEW. "
                                    f"Old expiry: {old_formatted}"
                                ),
                                fg=COLORS["warning"]
                            )
                        except ValueError:
                            pass
            else:
                self.vehicle_status.configure(
                    text="✅ New vehicle number",
                    fg=COLORS["success"]
                )
        else:
            self.vehicle_status.configure(text="")

    def load_data(self, vehicle):
        self.editing_vehicle = vehicle

        self.form_title.configure(text="✏️ Edit Vehicle")
        self.save_btn.configure(text="💾 Update Vehicle")

        self.entry_vehicle.delete(0, "end")
        self.entry_vehicle.insert(
            0,
            vehicle.get("vehicle_number", "")
        )

        self.entry_phone.delete(0, "end")
        self.entry_phone.insert(
            0,
            vehicle.get("phone", "")
        )

        # Do not overwrite preserved add-form start/duration here.
        # Only show vehicle's saved expiry while editing.
        if vehicle.get("expiry_date"):
            self.set_expiry_date(vehicle["expiry_date"])

    def save_vehicle(self):
        vehicle_number = self.entry_vehicle.get().strip().upper()
        phone = self.entry_phone.get().strip()
        expiry_date = self.get_expiry_date()

        if not vehicle_number:
            messagebox.showerror(
                "Error",
                "Vehicle number is required!"
            )
            self.entry_vehicle.focus()
            return

        if not phone:
            messagebox.showerror(
                "Error",
                "Phone number is required!"
            )
            self.entry_phone.focus()
            return

        if not expiry_date:
            messagebox.showerror(
                "Error",
                "Please pick an expiry date!"
            )
            return

        clean_phone = (
            phone.replace("+", "")
            .replace("-", "")
            .replace(" ", "")
        )

        if not clean_phone.isdigit() or len(clean_phone) < 10:
            messagebox.showerror(
                "Error",
                "Invalid phone! Min 10 digits."
            )
            return

        try:
            # Save current selected start/duration/expiry before saving
            self.remember_date_selection()

            if self.editing_vehicle:
                result = update_vehicle(
                    self.editing_vehicle["id"],
                    vehicle_number,
                    phone,
                    expiry_date,
                    "",
                    "",
                    ""
                )

                if result == "conflict":
                    messagebox.showerror(
                        "Error",
                        "Another vehicle with this number exists!"
                    )
                    return

                messagebox.showinfo(
                    "Success",
                    "Vehicle updated! ✅"
                )

            else:
                result = add_vehicle(
                    vehicle_number,
                    phone,
                    expiry_date,
                    "",
                    "",
                    ""
                )

                if result == "renewed":
                    messagebox.showinfo(
                        "Renewed! 🔄",
                        f"Vehicle {vehicle_number} renewed!"
                    )
                else:
                    messagebox.showinfo(
                        "Success ✅",
                        f"Vehicle {vehicle_number} added!"
                    )

            self.clear_form()
            self.app.show_page("vehicles")

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed: {str(e)}"
            )

    def clear_form(self):
        self.editing_vehicle = None

        self.form_title.configure(text="➕ Add New Vehicle")
        self.save_btn.configure(text="💾 Save Vehicle")

        self.entry_vehicle.delete(0, "end")
        self.entry_phone.delete(0, "end")
        self.vehicle_status.configure(text="")

        # Restore previously selected start date, quick validity and expiry date
        self.restore_last_date_selection()

        self.close_calendar()
        self.entry_vehicle.focus()
