"""
Import/Export module for Vehicle Management System
Supports CSV and JSON formats
"""
import csv
import json
import os
from datetime import datetime
from database import get_all_vehicles, add_vehicle

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.units import inch
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


def export_to_csv(filepath, filters=None):
    """Export vehicles to CSV file"""
    vehicles = get_all_vehicles(filters)

    if not vehicles:
        return 0

    fieldnames = [
        "vehicle_number", "owner_name", "phone", "vehicle_type",
        "expiry_date", "notes",
        "created_at", "updated_at", "renewal_count"
    ]

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for vehicle in vehicles:
            writer.writerow(vehicle)

    return len(vehicles)


def export_to_json(filepath, filters=None):
    """Export vehicles to JSON file"""
    vehicles = get_all_vehicles(filters)

    if not vehicles:
        return 0

    export_data = []
    for v in vehicles:
        item = {k: v[k] for k in v if k != "id"}
        export_data.append(item)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)

    return len(vehicles)


def export_to_pdf(filepath, filters=None):
    """Export vehicles to PDF file"""
    if not HAS_REPORTLAB:
        raise ImportError("reportlab library is required for PDF export")
    
    vehicles = get_all_vehicles(filters)
    
    if not vehicles:
        return 0
    
    # Create PDF document
    doc = SimpleDocTemplate(
        filepath, pagesize=A4,
        rightMargin=0.5*inch, leftMargin=0.5*inch,
        topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    # Container for PDF elements
    elements = []
    
    # Add title
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1e3a8a'),
        spaceAfter=12,
        alignment=1  # Center alignment
    )
    
    title = Paragraph("Vehicle Management Report", title_style)
    elements.append(title)
    
    # Add date
    date_style = ParagraphStyle(
        'DateStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#666666'),
        spaceAfter=12,
        alignment=1
    )
    date_para = Paragraph(f"Generated on: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}", date_style)
    elements.append(date_para)
    
    elements.append(Spacer(1, 0.2*inch))
    
    # Prepare table data
    table_data = [[
        'Vehicle No', 'Owner', 'Phone', 'Type',
        'Expiry Date', 'Status', 'Renewals'
    ]]
    
    # Status colors
    def get_status_color(expiry_date_str):
        try:
            expiry = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
            today = datetime.now().date()
            days_left = (expiry - today).days
            
            if days_left < 0:
                return colors.HexColor('#dc2626')  # Red - Expired
            elif days_left <= 7:
                return colors.HexColor('#f97316')  # Orange - Expiring soon
            elif days_left <= 30:
                return colors.HexColor('#eab308')  # Yellow - Expiring in a month
            else:
                return colors.HexColor('#16a34a')  # Green - Valid
        except:
            return colors.black
    
    # Add vehicle rows
    for vehicle in vehicles:
        table_data.append([
            vehicle.get('vehicle_number', ''),
            vehicle.get('owner_name', '')[:20],
            vehicle.get('phone', ''),
            vehicle.get('vehicle_type', ''),
            vehicle.get('expiry_date', ''),
            vehicle.get('status', ''),
            str(vehicle.get('renewal_count', 0))
        ])
    
    # Create table with styling
    table = Table(table_data, colWidths=[1.2*inch, 1.3*inch, 1.2*inch, 0.8*inch,
                                         1.1*inch, 1*inch, 0.8*inch])
    
    # Apply table styling
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e0e0e0')),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')])
    ])
    
    table.setStyle(table_style)
    elements.append(table)
    
    # Build PDF
    doc.build(elements)
    
    return len(vehicles)


def import_from_csv(filepath):
    """Import vehicles from CSV file"""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    added = 0
    renewed = 0
    errors = []

    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for i, row in enumerate(reader, 1):
            try:
                vehicle_number = row.get("vehicle_number", "").strip()
                phone = row.get("phone", "").strip()
                expiry_date = row.get("expiry_date", "").strip()

                if not vehicle_number or not phone or not expiry_date:
                    errors.append(
                        f"Row {i}: Missing required fields "
                        f"(vehicle_number, phone, expiry_date)")
                    continue

                try:
                    datetime.strptime(expiry_date, "%Y-%m-%d")
                except ValueError:
                    try:
                        dt = datetime.strptime(expiry_date, "%d-%m-%Y")
                        expiry_date = dt.strftime("%Y-%m-%d")
                    except ValueError:
                        try:
                            dt = datetime.strptime(expiry_date, "%d/%m/%Y")
                            expiry_date = dt.strftime("%Y-%m-%d")
                        except ValueError:
                            errors.append(
                                f"Row {i}: Invalid date format '{expiry_date}'")
                            continue

                result = add_vehicle(
                    vehicle_number=vehicle_number,
                    phone=phone,
                    expiry_date=expiry_date,
                    owner_name=row.get("owner_name", ""),
                    vehicle_type=row.get("vehicle_type", ""),
                    notes=row.get("notes", "")
                )

                if result == "added":
                    added += 1
                elif result == "renewed":
                    renewed += 1

            except Exception as e:
                errors.append(f"Row {i}: {str(e)}")

    return added, renewed, errors


def import_from_json(filepath):
    """Import vehicles from JSON file"""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        data = [data]

    added = 0
    renewed = 0
    errors = []

    for i, row in enumerate(data, 1):
        try:
            vehicle_number = row.get("vehicle_number", "").strip()
            phone = row.get("phone", "").strip()
            expiry_date = row.get("expiry_date", "").strip()

            if not vehicle_number or not phone or not expiry_date:
                errors.append(
                    f"Record {i}: Missing required fields")
                continue

            try:
                datetime.strptime(expiry_date, "%Y-%m-%d")
            except ValueError:
                errors.append(
                    f"Record {i}: Invalid date format '{expiry_date}'")
                continue

            result = add_vehicle(
                vehicle_number=vehicle_number,
                phone=phone,
                expiry_date=expiry_date,
                owner_name=row.get("owner_name", ""),
                vehicle_type=row.get("vehicle_type", ""),
                notes=row.get("notes", "")
            )

            if result == "added":
                added += 1
            elif result == "renewed":
                renewed += 1

        except Exception as e:
            errors.append(f"Record {i}: {str(e)}")

    return added, renewed, errors


def generate_sample_csv(filepath):
    """Generate a sample CSV template"""
    fieldnames = [
        "vehicle_number", "owner_name", "phone", "vehicle_type",
        "expiry_date", "notes"
    ]
    sample_data = [
        {
            "vehicle_number": "KA01AB1234",
            "owner_name": "John Doe",
            "phone": "9876543210",
            "vehicle_type": "Car",
            "expiry_date": "2025-12-31",
            "notes": "Sample entry"
        },
        {
            "vehicle_number": "MH02CD5678",
            "owner_name": "Jane Smith",
            "phone": "9123456789",
            "vehicle_type": "Bike",
            "expiry_date": "2025-06-15",
            "notes": ""
        }
    ]

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sample_data)

    return filepath