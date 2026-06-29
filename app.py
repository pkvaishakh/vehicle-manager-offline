"""
Main Application class for Vehicle Management System
"""
import tkinter as tk
from tkinter import ttk, messagebox
from styles import COLORS, FONTS, DIMENSIONS
from database import initialize_database
from pages.dashboard import DashboardPage
from pages.vehicles import VehiclesPage
from pages.add_vehicle import AddVehiclePage
from pages.whatsapp import WhatsAppPage
from pages.sms import SMSPage


class VehicleManagementApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🚗 Vehicle Management System")
        self.root.geometry("1280x750")
        self.root.minsize(
            DIMENSIONS["window_min_width"],
            DIMENSIONS["window_min_height"]
        )
        self.root.configure(bg=COLORS["bg"])

        # Center window
        self.center_window()

        # Initialize database
        initialize_database()

        # Current page
        self.current_page = None
        self.current_page_name = ""
        self.pages = {}

        # Build UI
        self.build_ui()

        # Show dashboard by default
        self.show_page("dashboard")

    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        w = 1280
        h = 750
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def build_ui(self):
        """Build the main UI structure"""
        # Main container
        self.main_container = tk.Frame(self.root, bg=COLORS["bg"])
        self.main_container.pack(fill="both", expand=True)

        # Sidebar
        self.build_sidebar()

        # Content area
        self.content_frame = tk.Frame(
            self.main_container, bg=COLORS["bg"])
        self.content_frame.pack(side="left", fill="both", expand=True)

        # Header
        self.build_header()

        # Page container
        self.page_container = tk.Frame(self.content_frame, bg=COLORS["bg"])
        self.page_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    def build_sidebar(self):
        """Build the sidebar navigation"""
        sidebar = tk.Frame(
            self.main_container,
            bg=COLORS["sidebar_bg"],
            width=DIMENSIONS["sidebar_width"]
        )
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # Logo area
        logo_frame = tk.Frame(sidebar, bg=COLORS["sidebar_bg"])
        logo_frame.pack(fill="x", pady=(20, 30))

        tk.Label(
            logo_frame,
            text="🚗",
            font=("Segoe UI", 30),
            bg=COLORS["sidebar_bg"],
            fg=COLORS["sidebar_text"]
        ).pack()

        tk.Label(
            logo_frame,
            text="Vehicle Manager",
            font=("Segoe UI", 13, "bold"),
            bg=COLORS["sidebar_bg"],
            fg=COLORS["sidebar_text"]
        ).pack()

        # Navigation items
        self.nav_buttons = {}
        nav_items = [
            ("dashboard", "📊  Dashboard"),
            ("vehicles", "🚗  Vehicles"),
            ("add_vehicle", "➕  Add Vehicle"),
            ("whatsapp", "💬  WhatsApp"),
            ("sms", "📩  SMS"),
        ]

        for page_name, label in nav_items:
            btn_frame = tk.Frame(sidebar, bg=COLORS["sidebar_bg"])
            btn_frame.pack(fill="x", padx=10, pady=2)

            btn = tk.Label(
                btn_frame,
                text=label,
                font=FONTS["menu"],
                bg=COLORS["sidebar_bg"],
                fg=COLORS["sidebar_text"],
                anchor="w",
                padx=15,
                pady=10,
                cursor="hand2"
            )
            btn.pack(fill="x")

            btn.bind("<Button-1>",
                     lambda e, pn=page_name: self.show_page(pn))
            btn.bind("<Enter>",
                     lambda e, b=btn, pn=page_name: self.on_nav_hover(b, pn))
            btn.bind("<Leave>",
                     lambda e, b=btn, pn=page_name: self.on_nav_leave(b, pn))

            self.nav_buttons[page_name] = btn

        # Bottom info
        bottom_frame = tk.Frame(sidebar, bg=COLORS["sidebar_bg"])
        bottom_frame.pack(side="bottom", fill="x", pady=20, padx=15)

        tk.Label(
            bottom_frame,
            text="v1.0.0",
            font=FONTS["small"],
            bg=COLORS["sidebar_bg"],
            fg=COLORS["text_light"]
        ).pack()

    def build_header(self):
        """Build the header bar"""
        self.header = tk.Frame(
            self.content_frame, bg=COLORS["bg_white"], height=60)
        self.header.pack(fill="x", padx=20, pady=(20, 15))
        self.header.pack_propagate(False)

        self.header_title = tk.Label(
            self.header,
            text="Dashboard",
            font=FONTS["title_bar"],
            bg=COLORS["bg_white"],
            fg=COLORS["text"],
            anchor="w",
            padx=20
        )
        self.header_title.pack(side="left", fill="y")

        # Header right side - refresh button
        refresh_btn = tk.Label(
            self.header,
            text="🔄 Refresh",
            font=FONTS["small_bold"],
            bg=COLORS["primary"],
            fg="white",
            padx=15,
            pady=5,
            cursor="hand2"
        )
        refresh_btn.pack(side="right", padx=20, pady=15)
        refresh_btn.bind("<Button-1>",
                         lambda e: self.refresh_current_page())

    def on_nav_hover(self, btn, page_name):
        """Handle navigation button hover"""
        if page_name != self.current_page_name:
            btn.configure(bg=COLORS["sidebar_hover"])

    def on_nav_leave(self, btn, page_name):
        """Handle navigation button leave"""
        if page_name != self.current_page_name:
            btn.configure(bg=COLORS["sidebar_bg"])

    def show_page(self, page_name):
        """Show a specific page"""
        # Update nav highlighting
        for name, btn in self.nav_buttons.items():
            if name == page_name:
                btn.configure(
                    bg=COLORS["sidebar_active"],
                    font=FONTS["menu_active"])
            else:
                btn.configure(
                    bg=COLORS["sidebar_bg"],
                    font=FONTS["menu"])

        # Clear current page
        for widget in self.page_container.winfo_children():
            widget.destroy()

        self.current_page_name = page_name

        # Update header
        titles = {
            "dashboard": "📊 Dashboard",
            "vehicles": "🚗 Vehicle List",
            "add_vehicle": "➕ Add / Renew Vehicle",
            "whatsapp": "💬 WhatsApp Messaging",
            "sms": "📩 SMS Reminders",
        }
        self.header_title.configure(text=titles.get(page_name, ""))

        # Create page
        if page_name == "dashboard":
            self.current_page = DashboardPage(self.page_container, self)
        elif page_name == "vehicles":
            self.current_page = VehiclesPage(self.page_container, self)
        elif page_name == "add_vehicle":
            self.current_page = AddVehiclePage(self.page_container, self)
        elif page_name == "whatsapp":
            self.current_page = WhatsAppPage(self.page_container, self)
        elif page_name == "sms":
            self.current_page = SMSPage(self.page_container, self)

    def show_page_with_data(self, page_name, data=None):
        """Show a page and pass data to it"""
        self.show_page(page_name)
        if data and hasattr(self.current_page, 'load_data'):
            self.current_page.load_data(data)

    def refresh_current_page(self):
        """Refresh the current page"""
        self.show_page(self.current_page_name)

    def run(self):
        """Run the application"""
        self.root.mainloop()