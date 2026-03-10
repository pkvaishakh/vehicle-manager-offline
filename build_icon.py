"""
Create a simple app icon for the EXE
Run: python build_icon.py
"""
import struct
import os


def create_simple_ico():
    """Create a minimal valid .ico file"""
    # 16x16 icon with car emoji colors
    width, height = 16, 16
    
    # Simple blue square icon with white car shape
    # BMP pixel data (bottom-up, BGRA format)
    pixels = []
    for y in range(height):
        for x in range(width):
            # Blue background
            b, g, r, a = 235, 99, 37, 255  # #2563EB

            # White car shape in center
            ry = height - 1 - y  # flip y
            if 4 <= ry <= 11 and 2 <= x <= 13:
                if 6 <= ry <= 9:
                    b, g, r, a = 255, 255, 255, 255
                elif ry == 5 and 4 <= x <= 11:
                    b, g, r, a = 255, 255, 255, 255
                elif ry == 10 and (3 <= x <= 5 or 10 <= x <= 12):
                    b, g, r, a = 40, 40, 40, 255  # wheels

            pixels.extend([b, g, r, a])

    pixel_data = bytes(pixels)

    # BMP header for 16x16 32-bit
    bmp_size = 40 + len(pixel_data)
    
    # BITMAPINFOHEADER
    bmp_header = struct.pack('<IiiHHIIiiII',
        40,           # header size
        width,        # width
        height * 2,   # height (doubled for ICO)
        1,            # planes
        32,           # bits per pixel
        0,            # compression
        len(pixel_data),  # image size
        0, 0,         # resolution
        0, 0          # colors
    )

    # AND mask (transparency - all opaque)
    and_mask = bytes([0] * (((width + 31) // 32) * 4 * height))

    # ICO file structure
    ico_data = b''
    
    # ICONDIR header
    ico_data += struct.pack('<HHH', 0, 1, 1)  # reserved, type=1, count=1
    
    # ICONDIRENTRY
    entry_offset = 6 + 16  # header + 1 entry
    data = bmp_header + pixel_data + and_mask
    ico_data += struct.pack('<BBBBHHII',
        width if width < 256 else 0,
        height if height < 256 else 0,
        0,        # colors
        0,        # reserved
        1,        # planes
        32,       # bits
        len(data),
        entry_offset
    )
    
    ico_data += data

    filepath = "app_icon.ico"
    with open(filepath, 'wb') as f:
        f.write(ico_data)
    
    print(f"✅ Icon created: {filepath}")
    return filepath


if __name__ == "__main__":
    create_simple_ico()