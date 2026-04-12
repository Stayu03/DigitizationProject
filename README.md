# ระบบจัดการกระบวนการแปลงเอกสารเป็นดิจิทัล (Digitization Process Management System)

# ต้นแบบระบบสำหรับงานภายในสำนักงานวิทยทรัพยากร จุฬาลงกรณ์มหาวิทยาลัย

# ภาพรวมโครงการ ระบบเว็บแอปพลิเคชันนี้พัฒนาขึ้นเพื่อบริหารจัดการและติดตามสถานะกระบวนการแปลงเอกสารเป็นดิจิทัล (Digitization) ตั้งแต่การนำเข้าเอกสารไปจนถึงการสรุปรายงาน 

# โครงสร้างระบบ (Information Architecture)

# 1. ส่วนหน้าหลัก
# P_01 Log In: หน้าสำหรับเข้าสู่ระบบ 
# P_02 Dashboard: แสดงรายการอัปเดตของเอกสารทั้งหมดในรูปแบบภาพรวม 
# P_03 Document List: รายการเอกสารทั้งหมดในระบบ 

# 2. ส่วนการจัดการกระบวนการ (Core Transactions)
# P_04 (P_04_1)Process Tracking: ติดตามและอัปเดตสถานะการแปลงเอกสารเป็นดิจิทัลของแต่ละรายการ 
    # P_05 (P_04_2) Add Document *Admin Only* : เพิ่มรายการเอกสารใหม่เข้าสู่กระบวนการ Digitization 
    # P_06 (P_04_3) Report: สรุปรายงานภาพรวมของกระบวนการทั้งหมด และสามารถดาวน์โหลดได้ 

# 3. ส่วนการตั้งค่าและจัดการระบบ *Admin Only*
# P_07 Setting: การตั้งค่าพื้นฐานของระบบ 
# P_08 System Management: จัดการข้อมูลตัวเลือกต่างๆในระบบ 
# P_09 (P_09_1) User Management: จัดการและสร้างบัญชีผู้ใช้งาน 
    # P_10 (P_09_2) Create Account : จัดการบัญชีผู้ใช้งาน เช่น การเพิ่ม ลบ หรือระงับการใช้งาน

# สิทธิ์ผู้ใช้งาน (User Roles)
# All (General User): สามารถเข้าถึงหน้า Log In, Dashboard, Document List, Process Tracking และ Report ได้ 
# Admin: สามารถเข้าถึงทุกส่วน


# โครงสร้างไฟล์ที่ควรใช้
# /digitization_project
# webapp.py      # ไฟล์หลักสำหรับรัน Streamlit Web App
# database.py    # จัดการการเชื่อมต่อ SQLite, init database, query function
# models.py      # นิยามโครงสร้างข้อมูล เช่น User, Document, ProcessLog
# requirements.txt   # รายการ package ที่ต้องติดตั้ง
# README.md      # อธิบายระบบ วิธีรัน และโครงสร้างโปรเจกต์

# pages/         # แยกไฟล์แต่ละหน้าตาม Page ID
# login.py               # P_01 Log In
# dashboard.py           # P_02 Dashboard
# document_list.py       # P_03 Document List
# process_tracking.py    # P_04 Process Tracking และ P_05 Add Document (Admin Only)
# report.py              # P_06 Report
# setting.py             # P_07 Setting/Profile
# system_management.py   # P_08 System Management (Admin Only)
# user_management.py     # P_09 User Management (Admin Only)
# create_account.py      # P_10 Create Account (Admin Only)

# utils/         # แนะนำให้เพิ่มเพื่อแยก logic ออกจากหน้า UI
# auth.py                # login, logout, role check, session state
# constants.py           # status, role, dropdown options ต่างๆ
# theme.py               # โทนสีชมพู, style helper, reusable UI config

# data/          # แนะนำให้เพิ่มถ้าต้องมีไฟล์ฐานข้อมูลหรือ mock data
# digitization.db        # SQLite database file

# .streamlit/
# config.toml            # theme และ config ของ Streamlit

## การรันระบบ (แนะนำ)

### 1) โหมดพัฒนา (Development)

```bash
cd "/Users/stang/Digitization Project/Digi_WebApp/DIgitizationProject"
.venv/bin/python run.py
```

ตัวเลือกผ่าน environment variables:
- `APP_HOST` ค่าเริ่มต้น `127.0.0.1`
- `APP_PORT` ค่าเริ่มต้น `5001`
- `APP_DEBUG` ค่าเริ่มต้น `0`

### 2) โหมดใช้งานจริง (Production ด้วย Gunicorn)

```bash
cd "/Users/stang/Digitization Project/Digi_WebApp/DIgitizationProject"
chmod +x scripts/start_gunicorn.sh
APP_HOST=0.0.0.0 APP_PORT=5001 APP_WORKERS=2 ./scripts/start_gunicorn.sh
```

หมายเหตุ:
- ถ้าต้องการให้เครื่องอื่นในวง LAN เข้าได้ ให้ใช้ `APP_HOST=0.0.0.0`
- ถ้าต้องการให้เปิดได้เฉพาะเครื่องตัวเอง ให้ใช้ `APP_HOST=127.0.0.1`

### 3) ตั้งให้รันอัตโนมัติเมื่อเปิดเครื่อง macOS (launchd)

คัดลอกไฟล์ตัวอย่าง:

```bash
cp deploy/launchd/com.digitization.webapp.plist ~/Library/LaunchAgents/
launchctl unload ~/Library/LaunchAgents/com.digitization.webapp.plist 2>/dev/null || true
launchctl load ~/Library/LaunchAgents/com.digitization.webapp.plist
launchctl start com.digitization.webapp
```

คำสั่งตรวจสอบ:

```bash
launchctl list | grep com.digitization.webapp
tail -n 50 /tmp/digitization-webapp.err.log
tail -n 50 /tmp/digitization-webapp.out.log
```

คำสั่งหยุด:

```bash
launchctl stop com.digitization.webapp
launchctl unload ~/Library/LaunchAgents/com.digitization.webapp.plist
```

