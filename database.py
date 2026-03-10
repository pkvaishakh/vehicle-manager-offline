"""
Database module - Works with both Python and EXE
"""
import sqlite3
import os
import sys
from datetime import datetime, date


def get_db_path():
    """Get database file path - next to exe or script"""
    if getattr(sys, 'frozen', False):
        # Running as EXE - put DB next to the EXE
        base = os.path.dirname(sys.executable)
    else:
        # Running as script
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "vehicles.db")


DB_FILE = get_db_path()


def get_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    """Create tables if they don't exist"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_number TEXT UNIQUE NOT NULL,
            owner_name TEXT DEFAULT '',
            phone TEXT NOT NULL,
            vehicle_type TEXT DEFAULT '',
            expiry_date TEXT NOT NULL,
            notes TEXT DEFAULT '',
            call_status TEXT DEFAULT 'Call Now',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            renewal_count INTEGER DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS message_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER,
            vehicle_number TEXT,
            phone TEXT,
            message TEXT,
            sent_at TEXT,
            status TEXT DEFAULT 'sent',
            FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
        )
    """)

    # Ensure `call_status` column exists in vehicles table (migration for older DBs)
    cursor.execute("PRAGMA table_info(vehicles)")
    columns = [row[1] for row in cursor.fetchall()]
    if "call_status" not in columns:
        cursor.execute("ALTER TABLE vehicles ADD COLUMN call_status TEXT DEFAULT 'Call Now'")

    conn.commit()
    conn.close()


def add_vehicle(vehicle_number, phone, expiry_date, owner_name="",
                vehicle_type="", notes=""):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("SELECT * FROM vehicles WHERE vehicle_number = ?",
                   (vehicle_number.upper(),))
    existing = cursor.fetchone()

    if existing:
        cursor.execute("""
            UPDATE vehicles SET
                phone = ?, expiry_date = ?, owner_name = ?,
                vehicle_type = ?, notes = ?, call_status = ?,
                updated_at = ?, renewal_count = renewal_count + 1
            WHERE vehicle_number = ?
        """, (phone, expiry_date, owner_name, vehicle_type,
              notes, "Call Now", now, vehicle_number.upper()))
        conn.commit()
        conn.close()
        return "renewed"
    else:
        cursor.execute("""
            INSERT INTO vehicles
            (vehicle_number, phone, expiry_date, owner_name,
             vehicle_type, notes, call_status, created_at, updated_at, renewal_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        """, (vehicle_number.upper(), phone, expiry_date, owner_name,
              vehicle_type, notes, "Call Now", now, now))
        conn.commit()
        conn.close()
        return "added"


def update_vehicle(vehicle_id, vehicle_number, phone, expiry_date,
                   owner_name="", vehicle_type="", notes=""):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        "SELECT id FROM vehicles WHERE vehicle_number = ? AND id != ?",
        (vehicle_number.upper(), vehicle_id))
    conflict = cursor.fetchone()
    if conflict:
        conn.close()
        return "conflict"

    cursor.execute("""
        UPDATE vehicles SET
            vehicle_number = ?, phone = ?, expiry_date = ?,
            owner_name = ?, vehicle_type = ?, notes = ?, updated_at = ?
        WHERE id = ?
    """, (vehicle_number.upper(), phone, expiry_date, owner_name,
          vehicle_type, notes, now, vehicle_id))
    conn.commit()
    conn.close()
    return "updated"


def set_call_status(vehicle_id, status):
    """Update the call status for a vehicle without touching updated_at."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE vehicles SET call_status = ? WHERE id = ?",
        (status, vehicle_id))
    conn.commit()
    conn.close()


def delete_vehicle(vehicle_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM vehicles WHERE id = ?", (vehicle_id,))
    conn.commit()
    conn.close()


def get_vehicle_by_id(vehicle_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vehicles WHERE id = ?", (vehicle_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_vehicle_by_number(vehicle_number):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vehicles WHERE vehicle_number = ?",
                   (vehicle_number.upper(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_vehicles(filters=None):
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM vehicles WHERE 1=1"
    params = []

    if filters:
        if filters.get("vehicle_number"):
            query += " AND vehicle_number LIKE ?"
            params.append(f"%{filters['vehicle_number'].upper()}%")
        if filters.get("phone"):
            query += " AND phone LIKE ?"
            params.append(f"%{filters['phone']}%")
        if filters.get("owner_name"):
            query += " AND owner_name LIKE ?"
            params.append(f"%{filters['owner_name']}%")
        if filters.get("expiry_from"):
            query += " AND expiry_date >= ?"
            params.append(filters["expiry_from"])
        if filters.get("expiry_to"):
            query += " AND expiry_date <= ?"
            params.append(filters["expiry_to"])
        if filters.get("updated_from"):
            query += " AND updated_at >= ?"
            params.append(filters["updated_from"])
        if filters.get("updated_to"):
            query += " AND updated_at <= ?"
            params.append(filters["updated_to"])
        if filters.get("status") == "expired":
            query += " AND expiry_date < ?"
            params.append(date.today().strftime("%Y-%m-%d"))
        elif filters.get("status") == "active":
            query += " AND expiry_date >= ?"
            params.append(date.today().strftime("%Y-%m-%d"))
        elif filters.get("status") == "expiring_soon":
            from datetime import timedelta
            soon = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")
            query += " AND expiry_date >= ? AND expiry_date <= ?"
            params.append(date.today().strftime("%Y-%m-%d"))
            params.append(soon)

        if filters.get("call_status") and filters.get("call_status") != "All":
            query += " AND call_status = ?"
            params.append(filters.get("call_status"))

    # Sort vehicles by most recently updated first (new records and renewals update `updated_at`)
    query += " ORDER BY updated_at DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_dashboard_stats():
    conn = get_connection()
    cursor = conn.cursor()
    today = date.today().strftime("%Y-%m-%d")
    from datetime import timedelta
    week_ago = (date.today() - timedelta(days=7)).strftime("%Y-%m-%d")
    month_later = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")
    week_later = (date.today() + timedelta(days=7)).strftime("%Y-%m-%d")

    stats = {}

    cursor.execute("SELECT COUNT(*) as cnt FROM vehicles")
    stats["total"] = cursor.fetchone()["cnt"]

    cursor.execute(
        "SELECT COUNT(*) as cnt FROM vehicles WHERE expiry_date < ?",
        (today,))
    stats["expired"] = cursor.fetchone()["cnt"]

    cursor.execute(
        "SELECT COUNT(*) as cnt FROM vehicles WHERE expiry_date >= ?",
        (today,))
    stats["active"] = cursor.fetchone()["cnt"]

    cursor.execute(
        "SELECT COUNT(*) as cnt FROM vehicles "
        "WHERE expiry_date >= ? AND expiry_date <= ?",
        (today, week_later))
    stats["expiring_7_days"] = cursor.fetchone()["cnt"]

    cursor.execute(
        "SELECT COUNT(*) as cnt FROM vehicles "
        "WHERE expiry_date >= ? AND expiry_date <= ?",
        (today, month_later))
    stats["expiring_30_days"] = cursor.fetchone()["cnt"]

    cursor.execute(
        "SELECT COUNT(*) as cnt FROM vehicles "
        "WHERE DATE(created_at) = ?", (today,))
    stats["created_today"] = cursor.fetchone()["cnt"]

    cursor.execute(
        "SELECT COUNT(*) as cnt FROM vehicles "
        "WHERE DATE(updated_at) = ?", (today,))
    stats["updated_today"] = cursor.fetchone()["cnt"]

    cursor.execute(
        "SELECT COUNT(*) as cnt FROM vehicles "
        "WHERE DATE(updated_at) = ? AND created_at != updated_at",
        (today,))
    stats["renewed_today"] = cursor.fetchone()["cnt"]

    cursor.execute(
        "SELECT COUNT(*) as cnt FROM vehicles "
        "WHERE DATE(created_at) >= ?", (week_ago,))
    stats["created_this_week"] = cursor.fetchone()["cnt"]

    cursor.execute("SELECT SUM(renewal_count) as cnt FROM vehicles")
    result = cursor.fetchone()["cnt"]
    stats["total_renewals"] = result if result else 0

    cursor.execute(
        "SELECT COUNT(*) as cnt FROM message_log "
        "WHERE DATE(sent_at) = ?", (today,))
    stats["messages_today"] = cursor.fetchone()["cnt"]

    cursor.execute("SELECT COUNT(*) as cnt FROM message_log")
    stats["total_messages"] = cursor.fetchone()["cnt"]

    conn.close()
    return stats


def log_message(vehicle_id, vehicle_number, phone, message):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO message_log
        (vehicle_id, vehicle_number, phone, message, sent_at)
        VALUES (?, ?, ?, ?, ?)
    """, (vehicle_id, vehicle_number, phone, message, now))
    conn.commit()
    conn.close()


def get_expired_vehicles():
    today = date.today().strftime("%Y-%m-%d")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM vehicles WHERE expiry_date < ? "
        "ORDER BY expiry_date ASC", (today,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_expiring_soon_vehicles(days=30):
    from datetime import timedelta
    today = date.today().strftime("%Y-%m-%d")
    future = (date.today() + timedelta(days=days)).strftime("%Y-%m-%d")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM vehicles WHERE expiry_date >= ? "
        "AND expiry_date <= ? ORDER BY expiry_date ASC",
        (today, future))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_updated_today_vehicles(limit=10):
    """Return vehicles updated today, sorted by most recent update."""
    today = date.today().strftime("%Y-%m-%d")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM vehicles WHERE DATE(updated_at) = ? "
        "ORDER BY updated_at DESC LIMIT ?",
        (today, limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]