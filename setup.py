"""
Setup script - Run this first to install dependencies and initialize
"""
import subprocess
import sys
import os


def install_requirements():
    print("=" * 50)
    print("Vehicle Management System - Setup")
    print("=" * 50)

    packages = ["tkcalendar"]

    for package in packages:
        print(f"\nInstalling {package}...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", package],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print(f"  ✅ {package} installed successfully")
        except subprocess.CalledProcessError:
            print(f"  ⚠️ Failed to install {package} (optional)")

    print("\n" + "=" * 50)
    print("Setup complete! Run 'python main.py' to start.")
    print("=" * 50)


def create_directories():
    pages_dir = os.path.join(os.path.dirname(__file__), "pages")
    if not os.path.exists(pages_dir):
        os.makedirs(pages_dir)
        print(f"Created directory: {pages_dir}")

    init_file = os.path.join(pages_dir, "__init__.py")
    if not os.path.exists(init_file):
        with open(init_file, "w") as f:
            f.write('"""Pages package"""\n')
        print(f"Created: {init_file}")


def add_sample_data():
    from database import initialize_database, add_vehicle

    initialize_database()

    # ✅ REMOVED insurance_company from all sample data
    samples = [
        ("KA01AB1234", "9876543210", "2025-01-10",
         "Rajesh Kumar", "Car", "Sample car"),
        ("MH02CD5678", "9123456789", "2025-07-20",
         "Priya Sharma", "Bike", ""),
        ("TN03EF9012", "8765432109", "2025-02-28",
         "Suresh Rajan", "SUV", "Family vehicle"),
        ("DL04GH3456", "7654321098", "2024-12-15",
         "Amit Singh", "Car", "Expired insurance"),
        ("KA05IJ7890", "6543210987", "2025-08-30",
         "Lakshmi Devi", "Auto", ""),
        ("AP06KL2345", "9988776655", "2024-11-20",
         "Venkat Rao", "Truck", "Commercial"),
        ("GJ07MN6789", "8877665544", "2025-03-15",
         "Meena Patel", "Car", ""),
        ("RJ08OP1234", "7766554433", "2025-01-25",
         "Dinesh Joshi", "Bike", ""),
        ("UP09QR5678", "6655443322", "2025-06-10",
         "Anita Verma", "Van", "Delivery van"),
        ("MP10ST9012", "5544332211", "2024-10-05",
         "Ramesh Gupta", "Bus", "School bus"),
    ]

    count = 0
    for data in samples:
        result = add_vehicle(*data)
        if result == "added":
            count += 1

    print(f"\n✅ Added {count} sample vehicles")


if __name__ == "__main__":
    create_directories()
    install_requirements()

    response = input("\nAdd sample data for testing? (y/n): ").lower()
    if response == "y":
        add_sample_data()

    print("\n🚀 Run 'python main.py' to start the application!")