"""
Dashboard Page - Shows statistics and overview
"""
import tkinter as tk
from tkinter import ttk
from styles import COLORS, FONTS
from database import (get_dashboard_stats, get_expired_vehicles,
                      get_expiring_soon_vehicles, get_updated_today_vehicles)


class DashboardPage:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.canvas = None
        self.mousewheel_bind = None
        self.build()

    def build(self):
        """Build dashboard layout"""
        # Main scrollable frame
        self.canvas = tk.Canvas(self.parent, bg=COLORS["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.parent, orient="vertical",
                                  command=self.canvas.yview)
        self.scroll_frame = tk.Frame(self.canvas, bg=COLORS["bg"])

        self.scroll_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind mousewheel (with safety check)
        def _on_mousewheel(event):
            try:
                if self.canvas and self.canvas.winfo_exists():
                    self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except tk.TclError:
                pass

        self.mousewheel_bind = self.canvas.bind("<MouseWheel>", _on_mousewheel)
        self.parent.bind("<Destroy>", self._cleanup)

        # Get stats
        stats = get_dashboard_stats()

        # Stats Cards Row 1
        self.build_stats_row1(stats)

        # Stats Cards Row 2
        self.build_stats_row2(stats)

        # Quick Actions
        self.build_quick_actions()

        # Recent expired list
        self.build_expired_list()

        # Expiring soon list
        self.build_expiring_soon_list()

        # Updated today list
        self.build_updated_today_list()

    def _cleanup(self, event=None):
        """Clean up bindings when page is destroyed"""
        if self.mousewheel_bind:
            try:
                if self.canvas and self.canvas.winfo_exists():
                    self.canvas.unbind("<MouseWheel>", self.mousewheel_bind)
            except Exception:
                pass
        self.canvas = None

    def build_stats_row1(self, stats):
        """Build first row of stat cards"""
        row = tk.Frame(self.scroll_frame, bg=COLORS["bg"])
        row.pack(fill="x", pady=(0, 15))

        cards = [
            ("Total Vehicles", stats["total"], "🚗",
             COLORS["primary"], COLORS["primary_light"]),
            ("Active", stats["active"], "✅",
             COLORS["success"], COLORS["success_light"]),
            ("Expired", stats["expired"], "❌",
             COLORS["danger"], COLORS["danger_light"]),
            ("Expiring in 7 Days", stats["expiring_7_days"], "⚠️",
             COLORS["warning"], COLORS["warning_light"]),
        ]

        for i, (label, value, icon, color, bg_color) in enumerate(cards):
            self.create_stat_card(row, label, value, icon, color, bg_color, i)

    def build_stats_row2(self, stats):
        """Build second row of stat cards"""
        row = tk.Frame(self.scroll_frame, bg=COLORS["bg"])
        row.pack(fill="x", pady=(0, 15))

        cards = [
            ("Expiring in 30 Days", stats["expiring_30_days"], "📅",
             COLORS["info"], COLORS["info_light"]),
            ("Created Today", stats["created_today"], "🆕",
             COLORS["success"], COLORS["success_light"]),
            ("Renewed Today", stats["renewed_today"], "🔄",
             COLORS["primary"], COLORS["primary_light"]),
            ("Messages Sent Today", stats["messages_today"], "💬",
             COLORS["whatsapp"], "#E8F5E9"),
        ]

        for i, (label, value, icon, color, bg_color) in enumerate(cards):
            self.create_stat_card(row, label, value, icon, color, bg_color, i)

    def create_stat_card(self, parent, label, value, icon, color,
                         bg_color, col):
        """Create a statistics card"""
        parent.grid_columnconfigure(col, weight=1)

        card = tk.Frame(parent, bg=COLORS["bg_card"], highlightbackground=COLORS["border"],
                        highlightthickness=1)
        card.grid(row=0, column=col, sticky="nsew", padx=5, pady=5)

        inner = tk.Frame(card, bg=COLORS["bg_card"])
        inner.pack(fill="both", expand=True, padx=20, pady=15)

        # Top row: icon and label
        top = tk.Frame(inner, bg=COLORS["bg_card"])
        top.pack(fill="x")

        icon_label = tk.Label(
            top, text=icon, font=("Segoe UI", 20),
            bg=bg_color, fg=color, padx=8, pady=2)
        icon_label.pack(side="left")

        # Value
        tk.Label(
            inner, text=str(value), font=FONTS["stat_number"],
            bg=COLORS["bg_card"], fg=color, anchor="w"
        ).pack(fill="x", pady=(10, 0))

        # Label
        tk.Label(
            inner, text=label, font=FONTS["stat_label"],
            bg=COLORS["bg_card"], fg=COLORS["text_secondary"], anchor="w"
        ).pack(fill="x")

    def build_quick_actions(self):
        """Build quick action buttons"""
        section = tk.Frame(self.scroll_frame, bg=COLORS["bg_card"],
                           highlightbackground=COLORS["border"],
                           highlightthickness=1)
        section.pack(fill="x", pady=(0, 15), padx=5)

        inner = tk.Frame(section, bg=COLORS["bg_card"])
        inner.pack(fill="x", padx=20, pady=15)

        tk.Label(
            inner, text="⚡ Quick Actions",
            font=FONTS["subheading"],
            bg=COLORS["bg_card"], fg=COLORS["text"]
        ).pack(anchor="w", pady=(0, 10))

        btn_frame = tk.Frame(inner, bg=COLORS["bg_card"])
        btn_frame.pack(fill="x")

        buttons = [
            ("➕ Add Vehicle", COLORS["primary"],
             lambda: self.app.show_page("add_vehicle")),
            ("🚗 View All Vehicles", COLORS["secondary"],
             lambda: self.app.show_page("vehicles")),
            ("💬 Send Reminders", COLORS["whatsapp"],
             lambda: self.app.show_page("whatsapp")),
            ("⚠️ View Expired", COLORS["danger"],
             lambda: self.show_expired()),
        ]

        for text, color, command in buttons:
            btn = tk.Label(
                btn_frame, text=text, font=FONTS["button"],
                bg=color, fg="white", padx=20, pady=8, cursor="hand2"
            )
            btn.pack(side="left", padx=(0, 10))
            btn.bind("<Button-1>", lambda e, cmd=command: cmd())

    def build_expired_list(self):
        """Build expired vehicles list"""
        expired = get_expired_vehicles()

        section = tk.Frame(self.scroll_frame, bg=COLORS["bg_card"],
                           highlightbackground=COLORS["border"],
                           highlightthickness=1)
        section.pack(fill="x", pady=(0, 15), padx=5)

        inner = tk.Frame(section, bg=COLORS["bg_card"])
        inner.pack(fill="x", padx=20, pady=15)

        header = tk.Frame(inner, bg=COLORS["bg_card"])
        header.pack(fill="x", pady=(0, 10))

        tk.Label(
            header, text=f"❌ Expired Vehicles ({len(expired)})",
            font=FONTS["subheading"],
            bg=COLORS["bg_card"], fg=COLORS["danger"]
        ).pack(side="left")

        if expired:
            # Table
            cols = ("Vehicle No", "Owner", "Phone", "Expiry Date")
            tree = ttk.Treeview(inner, columns=cols, show="headings",
                                height=min(5, len(expired)))

            for col in cols:
                tree.heading(col, text=col)
                tree.column(col, width=150)

            for v in expired[:10]:  # Show max 10
                tree.insert("", "end", values=(
                    v["vehicle_number"],
                    v.get("owner_name", ""),
                    v["phone"],
                    v["expiry_date"]
                ))

            tree.pack(fill="x")

            if len(expired) > 10:
                tk.Label(
                    inner,
                    text=f"... and {len(expired) - 10} more",
                    font=FONTS["small"],
                    bg=COLORS["bg_card"],
                    fg=COLORS["text_secondary"]
                ).pack(anchor="w", pady=(5, 0))
        else:
            tk.Label(
                inner,
                text="✅ No expired vehicles! All up to date.",
                font=FONTS["body"],
                bg=COLORS["bg_card"],
                fg=COLORS["success"]
            ).pack(anchor="w")

    def build_expiring_soon_list(self):
        """Build expiring soon vehicles list"""
        expiring = get_expiring_soon_vehicles(7)

        section = tk.Frame(self.scroll_frame, bg=COLORS["bg_card"],
                           highlightbackground=COLORS["border"],
                           highlightthickness=1)
        section.pack(fill="x", pady=(0, 15), padx=5)

        inner = tk.Frame(section, bg=COLORS["bg_card"])
        inner.pack(fill="x", padx=20, pady=15)

        header = tk.Frame(inner, bg=COLORS["bg_card"])
        header.pack(fill="x", pady=(0, 10))

        tk.Label(
            header,
            text=f"⚠️ Expiring Within 7 Days ({len(expiring)})",
            font=FONTS["subheading"],
            bg=COLORS["bg_card"], fg=COLORS["warning"]
        ).pack(side="left")

        if expiring:
            cols = ("Vehicle No", "Owner", "Phone", "Expiry Date")
            tree = ttk.Treeview(inner, columns=cols, show="headings",
                                height=min(5, len(expiring)))

            for col in cols:
                tree.heading(col, text=col)
                tree.column(col, width=150)

            for v in expiring[:10]:
                tree.insert("", "end", values=(
                    v["vehicle_number"],
                    v.get("owner_name", ""),
                    v["phone"],
                    v["expiry_date"]
                ))

            tree.pack(fill="x")
        else:
            tk.Label(
                inner,
                text="✅ No vehicles expiring within 7 days.",
                font=FONTS["body"],
                bg=COLORS["bg_card"],
                fg=COLORS["success"]
            ).pack(anchor="w")

    def build_updated_today_list(self):
        """Build a list of vehicles updated today."""
        updated = get_updated_today_vehicles(10)

        section = tk.Frame(self.scroll_frame, bg=COLORS["bg_card"],
                           highlightbackground=COLORS["border"],
                           highlightthickness=1)
        section.pack(fill="x", pady=(0, 15), padx=5)

        inner = tk.Frame(section, bg=COLORS["bg_card"])
        inner.pack(fill="x", padx=20, pady=15)

        header = tk.Frame(inner, bg=COLORS["bg_card"])
        header.pack(fill="x", pady=(0, 10))

        tk.Label(
            header,
            text=f"🕒 Updated Today ({len(updated)})",
            font=FONTS["subheading"],
            bg=COLORS["bg_card"], fg=COLORS["primary"]
        ).pack(side="left")

        if updated:
            cols = ("Vehicle No", "Owner", "Phone", "Updated At")
            tree = ttk.Treeview(inner, columns=cols, show="headings",
                                height=min(5, len(updated)))

            for col in cols:
                tree.heading(col, text=col)
                tree.column(col, width=150)

            for v in updated[:10]:
                tree.insert("", "end", values=(
                    v["vehicle_number"],
                    v.get("owner_name", ""),
                    v["phone"],
                    v.get("updated_at", "")
                ))

            tree.pack(fill="x")
        else:
            tk.Label(
                inner,
                text="✅ No vehicles updated today.",
                font=FONTS["body"],
                bg=COLORS["bg_card"],
                fg=COLORS["success"]
            ).pack(anchor="w")

    def show_expired(self):
        """Navigate to vehicles page with expired filter"""
        self.app.show_page("vehicles")