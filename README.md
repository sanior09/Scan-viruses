# 🛡️ J.A.R.V.I.S. SECURITY SUITE — Tactical Endpoint Defense & EDR
**Nachapol Industries Advanced Cyber Defense System**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter%205.2-00E5FF?style=for-the-badge&logo=gui&logoColor=black)](https://github.com/TomSchimansky/CustomTkinter)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011-0078D6?style=for-the-badge&logo=windows&logoColor=white)](https://microsoft.com)
[![AI Engine](https://img.shields.io/badge/AI%20Core-Gemini%202.5%20Flash-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)
[![Database](https://img.shields.io/badge/Cache-SQLite%20B--Tree-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org/)
[![Detection](https://img.shields.io/badge/Detection-YARA%20%2B%20Entropy-FF6F00?style=for-the-badge)](signatures/)
[![License: MIT](https://img.shields.io/badge/License-MIT-F5A623?style=for-the-badge)](LICENSE)
[![Defense Status](https://img.shields.io/badge/Defense%20Matrix-ACTIVE-00E676?style=for-the-badge)](#)

ระบบรักษาความปลอดภัยและตรวจจับภัยคุกคามบนเครื่องลูกข่าย (Antivirus & Lightweight EDR) พัฒนาขึ้นด้วยภาษา Python โดยจำลองบุคลิกภาพและส่วนติดต่อผู้ใช้สไตล์ **J.A.R.V.I.S. (Just A Rather Very Intelligent System)** ผสานพลังการตรวจจับทั้งแบบ Static Signatures (YARA & Hashes), Heuristics (Shannon Entropy & PE Import Analysis), Multi-Vector Real-Time Surveillance Daemons, และเชื่อมต่อสมองปัญญาประดิษฐ์ **Google Gemini 2.5 Flash** สำหรับวิเคราะห์ภัยคุกคาม Zero-Day ขั้นสูง

<p align="center">
  <img src="assets/logo_cyan.png" alt="J.A.R.V.I.S. Security Suite Logo" width="160">
</p>

<p align="center">
  <a href="#-system-architecture--tactical-pipeline">⚡ Architecture</a> •
  <a href="#-key-features--capabilities">🌟 Features</a> •
  <a href="#-sector-scan-matrix">🎯 Scan Sectors</a> •
  <a href="#-quick-start-nachapol-protocol">🚀 Quick Start</a> •
  <a href="#-deep-dive-module-specifications">🔬 Modules Deep Dive</a> •
  <a href="#-performance-optimizations">⚡ Optimizations</a> •
  <a href="#-บันทึกจากผู้พัฒนา-developers-note">📝 Dev Note</a>
</p>

---

## ⚡ System Architecture & Tactical Pipeline

ระบบสถาปัตยกรรมการตรวจจับ 6 มิติ (Multi-Vector Defense Pipeline) ทำงานประสานกันแบบเรียลไทม์ระหว่างหน้าจอควบคุม HUD และ Background Daemons:

```
[ J.A.R.V.I.S. HUD Interface (Dashboard.py) ]
  ├── ⚡ Animated Arc Reactor Holographic Gauge (CustomTkinter Canvas)
  ├── 🎯 Sector Scanner (Quick, USB, Downloads, Desktop, RAM, Custom, Full C:)
  └── 📡 Live Tactical Event Console (Non-blocking I/O Stream)
             │
             ├──► [ Core Scan Engine (Scan.py) ]
             │      ├── 1. SHA-256 / MD5 Full-Stream Hash Matching
             │      ├── 2. PE Structure & Import Vector Analysis (pefile)
             │      ├── 3. Shannon Entropy Cryptor / Ransomware Inspection
             │      ├── 4. YARA Signatures Pattern Matching (yara-python)
             │      └── 5. SQLite B-Tree Whitelist Matrix (.jarvis_whitelist.db)
             │
             ├──► [ AI Cognitive Core (AI_Analyzer.py) ]
             │      └── Google Gemini 2.5 Flash REST API (Zero-Day Assessment)
             │
             └──► [ 24/7 Multi-Vector Surveillance Daemons ]
                    ├── 👁️ RealTimeMonitor.py      (Downloads, Desktop, Temp Watchdog)
                    ├── 🔌 USBWatcher.py          (Hot-Plug Storage Auto-Sanitizer)
                    ├── 🧠 BehavioralMonitor.py   (Process I/O Anomaly & Port Guard)
                    ├── 🔐 RegistrySurveillance.py(Autorun, Startup & Service Watcher)
                    └── 🛡️ Watchdog.py            (Self-Defense & Daemon Resurrection)
```

---

## 🌟 Key Features & Capabilities

### 1. 🖥️ Holographic Arc Reactor HUD ([Dashboard.py](Dashboard.py))
- **Dark Cyberpunk Aesthetic:** ธีมสีดำอวกาศตัดกับ Cyan Blue และ Iron Man Amber ออกแบบด้วย CustomTkinter
- **Dynamic Arc Reactor Gauge:** วงแหวนพลังงานหมุนแอนิเมชันแบบเรียลไทม์ แสดงเปอร์เซ็นต์ความคืบหน้าการสแกนที่แม่นยำ
- **Non-Blocking Async Audio:** เอฟเฟกต์เสียงคำรามแบบ Sci-Fi ทำงานแยกบน Background Thread หน้าต่างไม่ค้างแม้มิลลิวินาทีเดียว
- **One-Click Shield Activation:** ปุ่มควบคุมและเปิดระบบเฝ้าระวังเบื้องหลังครบทุกมิติได้ในคลิกเดียว

### 2. 🔍 Multi-Tier Scan Engine ([Scan.py](Scan.py))
- **Full-Stream Hashing:** คำนวณแฮช MD5 และ SHA-256 จากไบต์ข้อมูลจริงทั้งหมด เทียบฐานข้อมูล [bad_hashes.txt](signatures/bad_hashes.txt)
- **Shannon Entropy Analysis:** คำนวณความหนาแน่นของข้อมูล (0.00 – 8.00) เพื่อดักจับมัลแวร์ที่เข้ารหัส (Encrypted Cryptor / Ransomware)
- **PE Import Vector Check:** ตรวจสอบ Portable Executable Imports เพื่อตรวจจับเทคนิค Process Injection, Process Hollowing, Dropper, และ Keylogger
- **YARA Rule Compilation:** รองรับชุดกฎ YARA แบบไดนามิกแยกประเภทสคริปต์อันตรายและไบนารีระบบ
- **Safe Vault Isolation:** กักกันไฟล์น่าสงสัยเข้าสู่โฟลเดอร์ `Quarantine/` ด้วยรหัสนามสกุล `.jarvis_locked` โดยไม่ลบไฟล์ทิ้ง

### 3. 🧠 Cognitive AI Threat Core ([AI_Analyzer.py](AI_Analyzer.py))
- เชื่อมต่อ API ของ **Google Gemini 2.5 Flash** ผ่าน Structured JSON Protocol
- ทำหน้าที่เป็น "สมองส่วนวิเคราะห์พฤติกรรม" สำหรับเหตุการณ์ที่กฎตายตัว (Static Signatures) ไม่สามารถตัดสินได้
- ประเมิน Threat Level (`SAFE`, `SUSPICIOUS`, `CRITICAL`) พร้อมให้เหตุผลประกอบการระงับโปรเซส

### 4. 👁️ 24/7 Multi-Vector Real-Time Surveillance
| โมดูลสายตรวจ | หน้าที่และเวกเตอร์ที่เฝ้าระวัง | กลไกการตรวจจับ |
|---|---|---|
| **[RealTimeMonitor.py](RealTimeMonitor.py)** | เฝ้าระวังไฟล์เข้าใหม่ใน Downloads, Desktop, Temp | Watchdog FileSystemEventHandler |
| **[USBWatcher.py](USBWatcher.py)** | ตรวจจับ Flash Drive / ฮาร์ดดิสก์พกพาที่เสียบเข้าเครื่อง | Silent Background Threat Elimination |
| **[BehavioralMonitor.py](BehavioralMonitor.py)** | ดักจับโปรเซสเขียนไฟล์รัวผิดปกติ & พอร์ต C2 ต้องสงสัย | Psutil Disk I/O & Network Analysis |
| **[RegistrySurveillance.py](RegistrySurveillance.py)** | ตรวจจับการฝังตัวผ่าน Run, RunOnce, Startup, Services | Windows Registry & Subkeys Snapshot |
| **[Watchdog.py](Watchdog.py)** | พิทักษ์ระบบตนเอง คอยกู้ชีพโปรเซสสายตรวจที่ถูกปิดกั้น | Parent-Child Process Supervision |

---

## 🎯 Sector Scan Matrix (พิกัดการสแกน)

| โหมดสแกน | สัญลักษณ์ | ขอบเขตการทำงาน | ความเร็ว |
|---|:---:|---|:---:|
| **Quick Scan** | ⚡ | สแกนโฟลเดอร์ Downloads และ Desktop ซึ่งเป็นจุดตกกระทบหลักของมัลแวร์ | เร็วมาก (5-15 วิ) |
| **USB Flash Drive** | 🔌 | สแกนแฟลชไดรฟ์และ Removable Drives ทุกตัวที่เสียบอยู่เพื่อกำจัด Autorun | เร็ว |
| **Downloads** | 📁 | ตรวจสอบไฟล์ทั้งหมดในโฟลเดอร์ดาวน์โหลดของผู้ใช้งาน | ปานกลาง |
| **Desktop** | 🖥️ | ตรวจสอบไฟล์ ไอคอนโปรแกรม และทางลัดทั้งหมดบนหน้าจอเดสก์ท็อป | เร็ว |
| **RAM Active Memory** | 🧠 | สแกน Process Memory, Command-line Tokens, Fileless Execution Chains | ทันที |
| **Custom Sector** | 📂 | เลือกโฟลเดอร์หรือไดรฟ์ที่กำหนดเองผ่านไดอะล็อก Explorer | กำหนดเอง |
| **Full System** | 💾 | สแกนเจาะลึกทั้งไดรฟ์ C:\ พร้อมระบบ Smart Filter ข้ามไฟล์ขยะระบบ | ละเอียด |

---

## 🚀 Quick Start (Nachapol Protocol)

### 1. ความต้องการขั้นต่ำของระบบ (Prerequisites)
- **ระบบปฏิบัติการ:** Windows 10 หรือ Windows 11 (64-bit)
- **ภาษา:** Python 3.10 ขึ้นไป

### 2. ติดตั้ง Dependencies
เปิด Terminal ในโฟลเดอร์โปรเจกต์แล้วรัน:
```bash
pip install -r requirements.txt
```

### 3. ตั้งค่า AI Cognitive Core (ทางเลือกเสริม)
คัดลอกไฟล์ `.env.example` เป็น `.env` และระบุ Gemini API Key ของท่าน:
```env
# Google Gemini API Key for J.A.R.V.I.S. Cognitive Assessment
GEMINI_API_KEY=AIzaSyYourActualGeminiAPIKeyHere
```
*(หากไม่ใส่ API Key ระบบสแกนและโมดูลเฝ้าระวังทั้งหมดจะยังคงทำงานได้ตามปกติ 100% โดยใช้ฐานข้อมูล Heuristic และ YARA ภายในเครื่อง)*

### 4. สตาร์ทระบบ J.A.R.V.I.S.

#### 🟢 ตัวเลือกที่ 1: One-Click Boot (แนะนำ)
ดับเบิลคลิกไฟล์ **`run_scanner.bat`** เพื่อเปิดแดชบอร์ดและปลุกระบบ Watchdog อัตโนมัติ:
```cmd
run_scanner.bat
```

#### 🟡 ตัวเลือกที่ 2: รันผ่าน Command Line
```cmd
python Dashboard.py
```

#### 🔵 ตัวเลือกที่ 3: สแกนไฟล์เดี่ยวแบบ Standalone CLI
```cmd
python Scan.py --no-pause "C:\path\to\suspicious_file.exe"
```

---

## 🔬 Deep Dive: Module Specifications

### 🛡️ 1. SQLite Whitelist Matrix
เพื่อขจัดปัญหาอาการแล็กจากการอ่านไฟล์ JSON ขนาดมหึมา ระบบได้อัปเกรดเป็น SQLite พร้อมระบบ **Write-Ahead Logging (WAL)**:
- **เวลาในการค้นหา (Lookup Latency):** `0.00 มิลลิวินาที` ต่อไฟล์ ด้วย B-Tree Primary Key
- **Batch Insertion:** รองรับการบันทึกข้อมูลปลอดภัยสะสมครั้งละ 500 รายการ ช่วยลด Disk I/O Overhead
- **Data Integrity:** ข้อมูลไม่เสียหายแม้เครื่องคอมพิวเตอร์จะดับกะทันหัน

### 🧪 2. Shannon Entropy Math
ดัชนีวัดความยุ่งเหยิงของข้อมูลระดับไบนารี คำนวณตามสูตรทางคณิตศาสตร์:
$$H(X) = -\sum_{i=1}^{n} P(x_i) \log_2 P(x_i)$$
- ค่า Entropy ปกติของไฟล์ข้อความและโค้ด: `3.0 - 5.5`
- ค่า Entropy ของซอฟต์แวร์ไบนารีทั่วไป: `6.0 - 7.2`
- ค่า Entropy ของไฟล์ที่ถูกเข้ารหัสด้วย Ransomware / Obfuscated Crypter: `7.85 - 8.00` (ระบบจะแจ้งเตือนระดับสูงสุดทันที)

---

## ⚡ Performance Optimizations

1. **CPU Core Balancing:** จำกัดจำนวน Worker Threads ให้เหลือคอร์ว่างสำหรับ Windows และ GUI เสมอ 1-2 คอร์ ป้องกันปัญหาเมาส์กระตุก
2. **Fast Log Tailing:** ปรับฟังก์ชันอ่านบันทึกประวัติให้อ่านเฉพาะ 8 KB ท้ายไฟล์ ไม่โหลดซ้ำทั้งไฟล์ขนาดใหญ่
3. **Adaptive Canvas FPS:** วงแหวนโฮโลแกรมปรับเฟรมเรตอัตโนมัติ (12.5 FPS ขณะสแตนด์บาย, 20 FPS ขณะสแกน)
4. **Asynchronous Winsound:** แยกเธรดสำหรับส่งเสียงแจ้งเตือน ไม่ขัดจังหวะการตอบสนองของหน้าจอ CustomTkinter

---

```
========================================================================
                   _    _     _______      _______  _____ 
                  | |  / \   |  __ \ \    / /_   _|/ ____|
                  | | /  \  | |__) \ \  / /  | | | (___  
              _   | |/ /\ \ |  _  / \ \/ /   | |  \___ \ 
              | |__| / ____ \| | \ \  \  /   _| |_ ____) |
               \____/_/    \_\|_|  \_\  \/   |_____|_____/ 
========================================================================
              TACTICAL ENDPOINT DETECTION & RESPONSE (EDR)
========================================================================
```
*Status: DEFENSE MATRIX ACTIVE*  
*Threat Signatures Loaded: YARA Rules Online • Cognitive Core Ready*  

---

## 📝 บันทึกจากผู้พัฒนา (Developer's Note)

> *"โปรเจกต์ J.A.R.V.I.S. Security Suite เกิดขึ้นจากความตั้งใจที่จะสร้างระบบป้องกันไวรัสและภัยคุกคามที่มีหน้าตาและฟีลลิ่งแบบภาพยนตร์ไซไฟ แต่สามารถตรวจจับและวิเคราะห์ภัยคุกคามในโลกความเป็นจริงได้แม่นยำ
>
> โค้ดได้รับการปรับปรุงให้มีประสิทธิภาพสูง ไม่กินแรม ไม่สูบซีพียูจนเครื่องค้าง และแก้ปัญหา False-Positive กับไฟล์ระบบและโปรแกรมทั่วไปเรียบร้อยแล้ว
>
> เพื่อนๆ นักพัฒนาและผู้ที่สนใจด้าน Cybersecurity ทุกท่านสามารถนำโค้ดไปศึกษา Fork ดัดแปลง เพิ่มเติมกฎ YARA หรือเปิด Pull Request เพื่อต่อยอดระบบความปลอดภัยร่วมกันได้เต็มที่เลยครับ!"*
>
> — **พัฒนาด้วยใจโดย Nachapol Industries**

---

## 🤝 Attribution & Credits (ข้อตกลงการให้เครดิต)

หากท่านนำโปรเจกต์ **J.A.R.V.I.S. Security Suite** หรือส่วนหนึ่งส่วนใดของโค้ดไปใช้งาน, พัฒนาต่อยอด (Fork), ทำคลิปรีวิว/สื่อวิดีโอ, หรือนำไปจัดแสดง:
- 🌟 **กรุณาให้เครดิตผู้สร้าง:** **Nachapol Industries**
- 🔗 **แนบลิงก์กลับมายัง Repository ต้นฉบับ:** [https://github.com/sanior09/Scan-viruses](https://github.com/sanior09/Scan-viruses)
- ⚖️ **ข้อกำหนดทางกฎหมาย:** ภายใต้สัญญาอนุญาต **[MIT License](LICENSE)** ผู้ใช้งานจำเป็นต้องเก็บข้อความลิขสิทธิ์ `Copyright (c) 2026 Nachapol Industries` ไว้ในทุกสำเนาของซอฟต์แวร์

---

## 📜 License
This project is open-source under the [MIT License](LICENSE).

*Developed & Architected with ❤️ by Nachapol Industries*
