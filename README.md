<div align="center">

# 🛡️ Scan Viruses ⚡

*ระบบสแกนและกำจัดไวรัสแบบเรียลไทม์ พร้อมหน้าจอ Cyber Tactical HUD และวิเคราะห์ภัยคุกคามด้วย Gemini AI*

[![GitHub Stars](https://img.shields.io/github/stars/sanior09/Scan-viruses?style=for-the-badge&color=00e5ff&logo=github)](https://github.com/sanior09/Scan-viruses/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/sanior09/Scan-viruses?style=for-the-badge&color=0088cc&logo=github)](https://github.com/sanior09/Scan-viruses/network/members)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter%205.2-00E5FF?style=for-the-badge&logo=gui&logoColor=black)](https://github.com/TomSchimansky/CustomTkinter)
[![Google Gemini](https://img.shields.io/badge/AI%20Core-Gemini%202.5%20Flash-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)
[![SQLite Matrix](https://img.shields.io/badge/Cache-SQLite%20B--Tree-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-emerald.svg?style=for-the-badge)](LICENSE)

<br/>

[✨ ฟีเจอร์](#-ฟีเจอร์เด่น) • 
[🎯 โหมดการสแกน](#-โหมดการสแกน-7-รูปแบบ) • 
[🚀 เริ่มต้นใช้งาน](#-วิธีติดตั้งและใช้งาน) • 
[📌 โครงสร้างไฟล์](#-โครงสร้างไฟล์) • 
[📄 License](#-license)

<br/><br/>

<p align="center">
  <img src="assets/dashboard_preview.png" alt="Tactical HUD Interface" width="850">
</p>

</div>

---

## 📖 เกี่ยวกับโปรเจกต์

**Scan Viruses** เป็นโปรแกรมแอนติไวรัส & EDR ขนาดเบาบน Windows พัฒนาด้วย Python เน้นความเร็ว ไม่กินทรัพยากรเครื่อง ผสานการตรวจจับแบบดั้งเดิม (YARA & Hashes) เข้ากับ Heuristics (Shannon Entropy), ระบบเฝ้าระวังอัตโนมัติ 24 ชม. และสามารถส่งพฤติกรรมต้องสงสัยให้ **Google Gemini AI** ร่วมตัดสินใจได้ทันที

---

## ✨ ฟีเจอร์เด่น

- 🎨 **Cyber Tactical HUD** — หน้าจอ CustomTkinter ไร้ขอบ ลื่นไหล ไม่กระตุก เรนเดอร์ภาษาไทยคมชัด
- 🔍 **Multi-Tier Detection** — ตรวจจับแม่นยำด้วย SHA-256, YARA Rules และคำนวณ Shannon Entropy ดักมัลแวร์เข้ารหัส
- ⚡ **SQLite Whitelist Matrix** — แคชไฟล์ปลอดภัยผ่าน SQLite B-Tree ค้นหาเร็วระดับ 0.00 ms
- 🧠 **Gemini AI Core** — วิเคราะห์คำสั่งและไฟล์ต้องสงสัยที่คลุมเครือ (Zero-Day) ผ่าน AI
- 👁️ **24/7 Surveillance** — เฝ้าระวังโฟลเดอร์เสี่ยง (Downloads/Temp) และตรวจสแกน USB อัตโนมัติเมื่อเสียบ
- 🔐 **Persistence Watcher** — ดักจับการแอบฝังตัวใน Windows Registry, Startup และ Services
- 🛡️ **Safe Quarantine** — กักกันไฟล์ลงโฟลเดอร์นิรภัย `Quarantine/` ปลอดภัย ไม่ลบไฟล์มั่วซั่ว

---

## 🎯 โหมดการสแกน 7 รูปแบบ

| โหมดสแกน | ขอบเขตการทำงาน | ความเร็ว |
| :--- | :--- | :---: |
| ⚡ **Quick Scan** | สแกน Desktop & Downloads (จุดเสี่ยงหลัก) | เร็วมาก |
| 🔌 **USB Flash Drive** | ตรวจจับและกวาดล้างไวรัส/Autorun ในแฟลชไดรฟ์ | เร็ว |
| 📁 **Downloads** | สแกนเฉพาะไฟล์ที่เพิ่งดาวน์โหลดจากอินเทอร์เน็ต | ปานกลาง |
| 🖥️ **Desktop** | ตรวจสอบไฟล์ โปรแกรม และชอร์ตคัตบนหน้าจอ | เร็ว |
| 🧠 **RAM Active Memory** | ตรวจสอบ Process และคำสั่งแปลกปลอมในหน่วยความจำ | ทันที |
| 📂 **Custom Sector** | เลือกโฟลเดอร์หรือไดรฟ์ที่ต้องการสแกนเอง | ตามขนาด |
| 💾 **Full System** | สแกนลึกทั้งไดรฟ์ C:\ (พร้อมระบบข้ามไฟล์ระบบอัตโนมัติ) | ละเอียด |

---

## 🚀 วิธีติดตั้งและใช้งาน

### 1. ติดตั้ง
```bash
# โคลนคลังโค้ด
git clone https://github.com/sanior09/Scan-viruses.git
cd Scan-viruses

# ติดตั้งไลบรารี
pip install -r requirements.txt
```

### 2. ตั้งค่า AI (ทางเลือกเสริม)
คัดลอก `.env.example` เป็น `.env` แล้วระบุ Gemini API Key:
```env
GEMINI_API_KEY=your_actual_api_key_here
```
*(ถ้าไม่ใส่ API Key ระบบยังคงสแกนและเฝ้าระวังด้วยฐานข้อมูลในเครื่องได้ 100%)*

### 3. รันโปรแกรม
- **ดับเบิลคลิก:** `run_scanner.bat` *(แนะนำ)*
- **หรือผ่าน Terminal:** `python Dashboard.py`
- **สแกนไฟล์เดี่ยวผ่าน CLI:** `python Scan.py --no-pause "C:\path\to\file.exe"`

---

## 📌 โครงสร้างไฟล์

```
Scan-viruses/
├── Dashboard.py              # หน้าจอควบคุมหลัก (HUD)
├── Scan.py                   # แกนสแกนหลัก (Hash, Entropy, YARA, Whitelist)
├── AI_Analyzer.py            # วิเคราะห์พฤติกรรมผ่าน Google Gemini
├── RealTimeMonitor.py        # ดักจับไฟล์ใหม่ใน Downloads / Desktop / Temp
├── USBWatcher.py             # ตรวจจับและสแกนแฟลชไดรฟ์อัตโนมัติ
├── BehavioralMonitor.py      # ตรวจพฤติกรรม Process & Network
├── RegistrySurveillance.py   # ตรวจจับการฝังตัวใน Registry & Services
├── Watchdog.py               # ระบบกู้ชีพโปรเซสสายตรวจ
├── signatures/               # ฐานข้อมูล Hash & กฎ YARA
└── run_scanner.bat           # สคริปต์เริ่มระบบในคลิกเดียว
```

---

## 📄 License

แจกจ่ายภายใต้สัญญาอนุญาต [MIT License](LICENSE) ใช้งานและพัฒนาต่อยอดได้อิสระ

<div align="center">

สร้างสรรค์ด้วยความใส่ใจในความปลอดภัยของระบบ 🩵 โดย [sanior09](https://github.com/sanior09)

</div>
