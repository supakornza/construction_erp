"""
Compile locale/th/LC_MESSAGES/django.po -> django.mo
Pure Python, no GNU gettext required.
"""
import struct
from pathlib import Path

translations = {
    "": (
        "Content-Type: text/plain; charset=UTF-8\n"
        "Content-Transfer-Encoding: 8bit\n"
        "Language: th\n"
        "Plural-Forms: nplurals=1; plural=0;\n"
    ),
    # Navigation
    "Dashboard": "แดชบอร์ด",
    "Tide Monitor": "ระดับน้ำ",
    "Turbidity Monitor": "ความขุ่นน้ำ",
    "Rock Progress": "ความคืบหน้าหิน",
    "Sand Progress": "ความคืบหน้าทราย",
    "Projects": "โครงการ",
    "Daily Reports": "รายงานประจำวัน",
    "Contractor Imports": "นำเข้าข้อมูลผู้รับเหมา",
    "Resources": "ทรัพยากร",
    "Manpower": "กำลังแรงงาน",
    "Equipment": "เครื่องจักร",
    "Materials": "วัสดุ",
    "Procurement": "จัดซื้อจัดจ้าง",
    "BOQ & Progress": "BOQ และความคืบหน้า",
    "Project Controls": "ควบคุมโครงการ",
    "Rock & Sand Control": "ควบคุมหินและทราย",
    "Revetment Progress": "ความคืบหน้าเขื่อน",
    "Recovery Plans": "แผนฟื้นตัว",
    "Project Action Plans": "แผนปฏิบัติการโครงการ",
    "Recovery Action Plans": "แผนปฏิบัติการฟื้นตัว",
    "Logistics": "โลจิสติกส์",
    "Transport Units": "หน่วยขนส่ง",
    "Cost Control": "ควบคุมต้นทุน",
    "Safety": "ความปลอดภัย",
    "Quality": "คุณภาพ",
    "Quality Control": "ควบคุมคุณภาพ",
    "Documents": "เอกสาร",
    "Admin": "ผู้ดูแลระบบ",
    "Users": "ผู้ใช้งาน",
    "Roles": "บทบาท",
    # Navbar
    "Back": "ย้อนกลับ",
    "Go back": "ย้อนกลับ",
    "Profile": "โปรไฟล์",
    "Change Password": "เปลี่ยนรหัสผ่าน",
    "Logout": "ออกจากระบบ",
}

def write_mo(path, messages):
    keys = sorted(messages.keys())
    N = len(keys)

    orig_bytes  = [k.encode("utf-8") for k in keys]
    trans_bytes = [messages[k].encode("utf-8") for k in keys]

    # String data starts after header (28 B) + two tables (N*8 B each)
    strings_base = 28 + 2 * N * 8

    # Build offset tables
    orig_offsets, trans_offsets = [], []
    pos = strings_base
    for b in orig_bytes:
        orig_offsets.append((len(b), pos))
        pos += len(b) + 1  # null-terminated

    for b in trans_bytes:
        trans_offsets.append((len(b), pos))
        pos += len(b) + 1

    # Header: magic, revision, N, orig-table offset, trans-table offset, hash size, hash offset
    data = struct.pack("<7I", 0x950412DE, 0, N, 28, 28 + N * 8, 0, 0)

    for length, offset in orig_offsets:
        data += struct.pack("<2I", length, offset)
    for length, offset in trans_offsets:
        data += struct.pack("<2I", length, offset)

    for b in orig_bytes:
        data += b + b"\x00"
    for b in trans_bytes:
        data += b + b"\x00"

    path.write_bytes(data)
    print(f"Written {N} translations to {path}")

if __name__ == "__main__":
    out = Path("locale/th/LC_MESSAGES/django.mo")
    out.parent.mkdir(parents=True, exist_ok=True)
    write_mo(out, translations)
