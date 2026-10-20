# J.A.R.V.I.S. Security Suite (Antivirus & Lightweight EDR)

A futuristic, high-performance antivirus and threat detection system powered by Python, CustomTkinter holographic UI, YARA signatures, Shannon entropy heuristic analysis, and Google Gemini AI cognitive evaluation.

---

## 🌟 Key Features

- **Holographic Arc Reactor HUD ([Dashboard.py](Dashboard.py)):** Futuristic cyber dashboard featuring live animated gauges, threat counters, system sector selection (Quick, Downloads, Desktop, USB, Custom, Full System, and RAM Active Memory), and real-time logs.
- **Deep Threat Scanning Engine ([Scan.py](Scan.py)):** 
  - Full-stream MD5 & SHA-256 signature hashing
  - PE analysis for remote process injection, API clustering, and threat packer detection
  - Shannon Entropy calculation for encrypted cryptors/ransomware
  - YARA signature matching (scripts & binaries)
  - Ultra-fast SQLite-backed Whitelist Manager (`.jarvis_whitelist.db`) with 0.00ms lookup
- **Cognitive AI Threat Core ([AI_Analyzer.py](AI_Analyzer.py)):** Integrated with Google Gemini 2.5 Flash for deep semantic assessment of ambiguous and zero-day threat behaviors.
- **Real-Time Active Surveillance:**
  - **[RealTimeMonitor.py](RealTimeMonitor.py):** Watches Downloads, Desktop, and Temp folders for newly created files.
  - **[USBWatcher.py](USBWatcher.py):** Detects USB removable drives and runs silent background sanitization.
  - **[BehavioralMonitor.py](BehavioralMonitor.py):** Monitors anomalous file modifications, process I/O, and suspicious network connections.
  - **[RegistrySurveillance.py](RegistrySurveillance.py):** Monitors Windows Run keys, Startup folders, and Windows Services subkeys for unauthorized persistence.
- **Watchdog Supervisor ([Watchdog.py](Watchdog.py)):** Self-defense process ensuring background daemons stay alive.

---

## 🚀 Getting Started

### 1. Requirements
- Python 3.10+
- Windows OS (for Winreg, Winsound, and PE features)

### 2. Install Dependencies
```bash
pip install customtkinter pillow psutil watchdog requests python-dotenv pefile yara-python
```

### 3. Configure AI Cognitive Core (Optional)
Copy `.env.example` to `.env` and configure your Gemini API Key:
```env
GEMINI_API_KEY=your_actual_api_key_here
```

### 4. Run the Security Suite
Execute the launcher batch script:
```cmd
run_scanner.bat
```
or run directly via Python:
```cmd
python Dashboard.py
```

---

## 🛡️ Architecture Overview
```
├── Dashboard.py               # HUD Control Center (CustomTkinter)
├── Scan.py                    # Core Scanning Engine & Heuristics
├── AI_Analyzer.py             # Google Gemini Cognitive Threat Core
├── RealTimeMonitor.py         # File System Watchdog Daemon
├── USBWatcher.py              # Hot-Plug Drive Monitor
├── BehavioralMonitor.py       # Process & Network Behavior Analysis
├── RegistrySurveillance.py    # Autorun & Windows Services Surveillance
├── Watchdog.py                # Process Supervisor & Self-Defense
├── run_scanner.bat            # Main System Launcher
├── assets/                    # UI Assets & Logo
└── signatures/                # YARA rules and bad hash signatures
```
