# pyrefly: ignore[missing-import]
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
from PIL import Image
import os
import sys
import psutil
import subprocess
import threading
import math
import time
import winsound
import ctypes
from datetime import datetime

# Enable Per-Monitor DPI Awareness so Windows renders native fonts with razor-sharp anti-aliasing
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Modern High-Legibility Typography Matrix
FONT_THAI = "Leelawadee UI"
FONT_TECH = "Consolas"

def play_sound_async(*beeps):
    """Executes sound sequences in a dedicated daemon thread to prevent freezing Tkinter GUI."""
    def _worker():
        try:
            for item in beeps:
                if isinstance(item, tuple) and len(item) == 2:
                    winsound.Beep(item[0], item[1])
                elif isinstance(item, int):
                    winsound.Beep(item, 100)
        except Exception:
            pass
    threading.Thread(target=_worker, daemon=True).start()

class GaugeAdapter:
    """Cyber Progress Controller (Handles scan progress telemetry smoothly without circular ring)."""
    def __init__(self, progress_bar=None, pct_lbl=None):
        self.progress_bar = progress_bar
        self.pct_lbl = pct_lbl
        self.running = False

    def set_progress(self, progress):
        val = max(0.0, min(1.0, progress))
        if self.progress_bar:
            self.progress_bar.set(val)
        if self.pct_lbl:
            if val > 0:
                self.pct_lbl.configure(text=f"PROGRESS: {int(val * 100)}%")
            else:
                self.pct_lbl.configure(text="")

    def set_scan_mode(self, active):
        if not active and self.progress_bar:
            if self.progress_bar.get() < 1.0:
                self.progress_bar.set(0.0)
                if self.pct_lbl:
                    self.pct_lbl.configure(text="")

class AntivirusDashboard:
    def __init__(self, root):
        self.root = root
        self.window_width = 1040
        self.window_height = 840
        self.root.geometry(f"{self.window_width}x{self.window_height}")
        try:
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            x = max(0, (sw - self.window_width) // 2)
            y = max(0, (sh - self.window_height) // 2)
            self.root.geometry(f"{self.window_width}x{self.window_height}+{x}+{y}")
        except Exception:
            pass
            
        # Clean solid background (Zero ghosting/bleed-through)
        self.root.configure(fg_color="#040812")
        self.root.resizable(False, False)
        
        # Cyberpunk Frameless Window with Topmost display
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)

        self.shutdown_flag_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".dashboard_shutdown_flag")
        self.surveillance_flag_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".surveillance_active_flag")

        self.scanning_in_progress = False
        self.current_scan_mode = "quick"
        self.custom_selected_folder = None
        self.module_widgets = {}
        self.module_labels = {}
        
        self.setup_ui()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Clear legacy flags
        if os.path.exists(self.shutdown_flag_path):
            try: os.remove(self.shutdown_flag_path)
            except: pass
            
        scripts = ["USBWatcher.py", "RealTimeMonitor.py", "BehavioralMonitor.py", "RegistrySurveillance.py"]
        monitors_running = any(self.is_script_running(s) for s in scripts)
        
        if monitors_running:
            try:
                with open(self.surveillance_flag_path, "w") as f: f.write("active")
            except: pass
            self.init_surv_btn.configure(state="disabled", text="[ ✓ เกราะเฝ้าระวังทำงานแล้ว ]", fg_color="#003314", text_color="#00ff88", border_color="#00ff88")

        self.periodic_check()
        # J.A.R.V.I.S. Power-up sequence (Non-blocking audio)
        play_sound_async((600, 100), (800, 100), (1200, 100), (1800, 250))

    def _start_move(self, event):
        self.x = event.x
        self.y = event.y

    def _do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def on_map(self, event):
        if event.widget == self.root and self.root.state() == 'normal':
            self.root.after(10, lambda: self.root.overrideredirect(True))

    def minimize_window(self):
        self.root.overrideredirect(False)
        self.root.iconify()

    def setup_ui(self):
        # Master HUD Container (Sleek 1.5px Cyan Cyber Border Frame)
        self.master_hud = ctk.CTkFrame(
            self.root,
            fg_color="#060c18",
            corner_radius=12,
            border_width=1.5,
            border_color="#00e5ff"
        )
        self.master_hud.pack(fill="both", expand=True, padx=2, pady=2)

        # Header Control Panel (Stark Tech Topbar)
        header_frame = ctk.CTkFrame(self.master_hud, fg_color="#081322", corner_radius=10, height=52)
        header_frame.pack(fill="x", side="top", padx=3, pady=(3, 0))
        
        # Window Drag Support via Header
        header_frame.bind("<Button-1>", self._start_move)
        header_frame.bind("<B1-Motion>", self._do_move)
        
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "logo_cyan.png")
        if os.path.exists(logo_path):
            orig_img = Image.open(logo_path)
            aspect_ratio = orig_img.width / orig_img.height
            target_height = 26
            target_width = int(target_height * aspect_ratio)
            
            logo_img = ctk.CTkImage(light_image=orig_img,
                                    dark_image=orig_img,
                                    size=(target_width, target_height))
            title_lbl = ctk.CTkLabel(header_frame, text=" // DEFENSE SYSTEM MARK IV", image=logo_img, compound="left",
                                     text_color="#00e5ff", font=(FONT_THAI, 12, "bold"))
        else:
            title_lbl = ctk.CTkLabel(header_frame, text="NACHAPOL INDUSTRIES // J.A.R.V.I.S. DEFENSE SYSTEM MARK IV", 
                                     text_color="#00e5ff", font=(FONT_THAI, 13, "bold"))
            
        title_lbl.pack(side="left", padx=16, pady=10)
        title_lbl.bind("<Button-1>", self._start_move)
        title_lbl.bind("<B1-Motion>", self._do_move)

        # Titlebar Window Control Buttons (Top-Right)
        win_ctrls = ctk.CTkFrame(header_frame, fg_color="transparent")
        win_ctrls.pack(side="right", padx=(10, 14), pady=8)

        self.top_close_btn = ctk.CTkButton(
            win_ctrls,
            text="✕",
            width=36,
            height=30,
            corner_radius=6,
            font=(FONT_THAI, 13, "bold"),
            fg_color="#1a0b12",
            text_color="#ff3366",
            hover_color="#ff003c",
            border_width=1,
            border_color="#ff003c",
            command=self.on_closing
        )
        self.top_close_btn.pack(side="right", padx=(6, 0))

        self.top_min_btn = ctk.CTkButton(
            win_ctrls,
            text="🗕",
            width=36,
            height=30,
            corner_radius=6,
            font=(FONT_THAI, 12, "bold"),
            fg_color="#0a192f",
            text_color="#00e5ff",
            hover_color="#0088cc",
            border_width=1,
            border_color="#183b5e",
            command=self.minimize_window
        )
        self.top_min_btn.pack(side="right", padx=(0, 4))

        # Status Pill in Header
        self.shield_status_lbl = ctk.CTkLabel(
            header_frame, 
            text="● SYSTEM: ARMED", 
            text_color="#00ff88", 
            fg_color="#082b19", 
            corner_radius=6, 
            padx=12, 
            pady=4,
            font=(FONT_TECH, 11, "bold")
        )
        self.shield_status_lbl.pack(side="right", padx=12, pady=10)

        # Bottom Docked Controls Footer
        ctk.CTkFrame(self.master_hud, fg_color="#10253e", height=1).pack(fill="x", side="bottom")
        btn_frame = ctk.CTkFrame(self.master_hud, fg_color="#081322", corner_radius=10, height=70)
        btn_frame.pack(fill="x", side="bottom", padx=3, pady=(0, 3))

        self.scan_btn = ctk.CTkButton(
            btn_frame,
            text="[ ⚡ สั่งสแกนไวรัส (START SCAN) ]",
            command=self.toggle_scan,
            fg_color="#004d73",
            hover_color="#00b4d8",
            text_color="#ffffff",
            border_width=2,
            border_color="#00e5ff",
            font=(FONT_THAI, 13, "bold"),
            width=290,
            height=46,
            corner_radius=8
        )
        self.scan_btn.pack(side="left", padx=16, pady=12)
        
        self.init_surv_btn = ctk.CTkButton(
            btn_frame,
            text="[ 🛡️ เปิดเกราะเฝ้าระวังเบื้องหลัง ]",
            command=self.initialize_surveillance_cores,
            fg_color="#082b19",
            hover_color="#00a846",
            text_color="#00ff88",
            border_width=1.5,
            border_color="#00e676",
            font=(FONT_THAI, 12, "bold"),
            width=250,
            height=46,
            corner_radius=8
        )
        self.init_surv_btn.pack(side="left", padx=10)

        branding_box = ctk.CTkFrame(btn_frame, fg_color="transparent")
        branding_box.pack(side="right", padx=18)
        ctk.CTkLabel(
            branding_box,
            text="J.A.R.V.I.S. DEFENSE MATRIX MARK IV",
            text_color="#4f7a9f",
            font=(FONT_TECH, 10, "bold")
        ).pack(anchor="e")
        ctk.CTkLabel(
            branding_box,
            text="ZERO-DAY COGNITIVE ENGINE • ACTIVE",
            text_color="#2b4c68",
            font=(FONT_TECH, 9)
        ).pack(anchor="e")

        # Main Content Area
        main_content = ctk.CTkFrame(self.master_hud, fg_color="transparent")
        main_content.pack(fill="both", expand=True, padx=16, pady=(8, 4))

        # Cognitive Cores Diagnostic Frame (Full Width 3x2 Matrix)
        status_frame = ctk.CTkFrame(main_content, fg_color="#070f1e", corner_radius=10, border_width=1, border_color="#142c47")
        status_frame.pack(fill="x", pady=(0, 6))
        
        status_header = ctk.CTkFrame(status_frame, fg_color="transparent")
        status_header.pack(fill="x", padx=12, pady=(6, 4))
        
        lbl_title = ctk.CTkLabel(status_header, text="[ COGNITIVE CORES & TELEMETRY MATRIX ]", text_color="#00e5ff", font=(FONT_THAI, 12, "bold"))
        lbl_title.pack(side="left")

        modules = [
            ("Dashboard.py", "🖥️ MARK IV HUD INTERFACE"),
            ("Watchdog.py", "🛡️ WATCHDOG SELF-DEFENSE"),
            ("RealTimeMonitor.py", "⚡ MULTI-VECTOR SCANNER"),
            ("USBWatcher.py", "🔌 USB SENTINEL FIREWALL"),
            ("BehavioralMonitor.py", "🧠 COGNITIVE BEHAVIORAL AI"),
            ("RegistrySurveillance.py", "📜 DEEP REGISTRY SENTINEL")
        ]
        
        grid_frame = ctk.CTkFrame(status_frame, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        
        for i, (script, label_text) in enumerate(modules):
            row = i // 3
            col = i % 3
            grid_frame.grid_columnconfigure(col, weight=1)
            
            card = ctk.CTkFrame(grid_frame, fg_color="#091424", border_width=1, border_color="#122744", corner_radius=6, height=38)
            card.grid(row=row, column=col, padx=5, pady=3, sticky="nsew")
            card.pack_propagate(False)
            
            title_lbl = ctk.CTkLabel(card, text=label_text, font=(FONT_THAI, 11, "bold"), text_color="#d0e3f7")
            title_lbl.pack(side="left", padx=10)
            
            pill = ctk.CTkLabel(
                card, 
                text="● STANDBY", 
                font=(FONT_TECH, 10, "bold"), 
                text_color="#ffb300", 
                fg_color="#332000", 
                corner_radius=4, 
                padx=8, 
                pady=2
            )
            pill.pack(side="right", padx=8)
            
            self.module_widgets[script] = {"card": card, "pill": pill, "title": label_text}
            self.module_labels[script] = pill

        # Terminal Log View (J.A.R.V.I.S. Data Feed)
        log_frame = ctk.CTkFrame(main_content, fg_color="#060e1c", corner_radius=10, border_width=1, border_color="#142c47")
        log_frame.pack(fill="both", expand=True, pady=(0, 6))
        
        log_header = ctk.CTkFrame(log_frame, fg_color="transparent")
        log_header.pack(fill="x", padx=12, pady=(6, 4))
        
        log_title = ctk.CTkLabel(log_header, text="[ 🛰️ J.A.R.V.I.S. QUANTUM TELEMETRY STREAM ]", text_color="#00e5ff", font=(FONT_THAI, 12, "bold"))
        log_title.pack(side="left")
        
        live_pill = ctk.CTkLabel(log_header, text="● LIVE FEED", font=(FONT_TECH, 9, "bold"), text_color="#00ff88", fg_color="#082b19", corner_radius=4, padx=6, pady=1)
        live_pill.pack(side="left", padx=8)
        
        clear_btn = ctk.CTkButton(
            log_header,
            text="[ 🧹 ล้างหน้าจอ ]",
            command=self.clear_log_screen,
            fg_color="#0a192f",
            hover_color="#003859",
            text_color="#7ba4cc",
            border_width=1,
            border_color="#142c47",
            font=(FONT_THAI, 11, "bold"),
            height=26,
            width=95
        )
        clear_btn.pack(side="right", padx=(4, 0))

        view_log_btn = ctk.CTkButton(
            log_header,
            text="[ 📄 ดูไฟล์ Log ]",
            command=self.open_log_file,
            fg_color="#0a192f",
            hover_color="#003859",
            text_color="#7ba4cc",
            border_width=1,
            border_color="#142c47",
            font=(FONT_THAI, 11, "bold"),
            height=26,
            width=95
        )
        view_log_btn.pack(side="right", padx=4)
        
        self.log_area = ctk.CTkTextbox(log_frame, fg_color="#030712", text_color="#00e5ff", font=(FONT_TECH, 10.5), height=115)
        self.log_area.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        
        # Configure syntax tags for log stream
        inner_txt = self.log_area._textbox
        inner_txt.tag_config("threat", foreground="#ff3366")
        inner_txt.tag_config("success", foreground="#00ff88")
        inner_txt.tag_config("warn", foreground="#ffb300")
        inner_txt.tag_config("info", foreground="#00d4f0")
        inner_txt.tag_config("dim", foreground="#537599")

        # Sector Targeting Control Frame (Cyberpunk HUD Card)
        sector_panel = ctk.CTkFrame(main_content, fg_color="#060e1c", corner_radius=10, border_width=1, border_color="#142c47")
        sector_panel.pack(fill="x", padx=0, pady=(0, 6))

        # Title Row
        title_row = ctk.CTkFrame(sector_panel, fg_color="transparent")
        title_row.pack(fill="x", padx=12, pady=(6, 3))
        
        sector_title = ctk.CTkLabel(title_row, text="🎯 กำหนดพิกัดเป้าหมาย (TARGET SECTOR MATRIX):", text_color="#00e5ff", font=(FONT_THAI, 12, "bold"))
        sector_title.pack(side="left")

        # Preset Mode Buttons - Row 1 (Core Sectors)
        row1_frame = ctk.CTkFrame(sector_panel, fg_color="transparent")
        row1_frame.pack(fill="x", padx=8, pady=(2, 2))

        self.sector_buttons = {}
        row1_definitions = [
            ("quick", "⚡ สแกนด่วน (Quick Scan)"),
            ("usb", "🔌 แฟลชไดรฟ์ (USB Storage)"),
            ("downloads", "📁 โฟลเดอร์ดาวน์โหลด (Downloads)"),
            ("desktop", "🖥️ หน้าจอเดสก์ท็อป (Desktop)")
        ]
        
        for key, title in row1_definitions:
            btn = ctk.CTkButton(
                row1_frame,
                text=title,
                command=lambda k=key: self.select_scan_mode(k),
                font=(FONT_THAI, 12, "bold"),
                height=38,
                corner_radius=8,
                fg_color="#0a1526",
                text_color="#89a9c9",
                border_width=1,
                border_color="#142c47",
                hover_color="#122744"
            )
            btn.pack(side="left", padx=3, expand=True, fill="x")
            self.sector_buttons[key] = btn

        # Preset Mode Buttons - Row 2 (Deep & Custom Sectors)
        row2_frame = ctk.CTkFrame(sector_panel, fg_color="transparent")
        row2_frame.pack(fill="x", padx=8, pady=(2, 6))

        row2_definitions = [
            ("memory", "🧠 หน่วยความจำ RAM (Active Memory)"),
            ("custom", "📂 เลือกโฟลเดอร์เอง (Custom Path...)"),
            ("system", "💾 ทั้งระบบ ไดรฟ์ C:\\ (Smart System)")
        ]

        for key, title in row2_definitions:
            btn = ctk.CTkButton(
                row2_frame,
                text=title,
                command=lambda k=key: self.select_scan_mode(k),
                font=(FONT_THAI, 12, "bold"),
                height=38,
                corner_radius=8,
                fg_color="#0a1526",
                text_color="#89a9c9",
                border_width=1,
                border_color="#142c47",
                hover_color="#122744"
            )
            btn.pack(side="left", padx=3, expand=True, fill="x")
            self.sector_buttons[key] = btn

        # Info & Details Display Bar (Holographic Readout Card)
        info_bar = ctk.CTkFrame(sector_panel, fg_color="#040b17", corner_radius=8, border_width=1, border_color="#0e233d")
        info_bar.pack(fill="x", padx=8, pady=(0, 8))

        # Neon Cyan Left Indicator Strip
        accent_strip = ctk.CTkFrame(info_bar, fg_color="#00e5ff", width=4, corner_radius=2)
        accent_strip.pack(side="left", fill="y", padx=(0, 8))

        self.browse_btn = ctk.CTkButton(
            info_bar,
            text="[ 📂 เลือกโฟลเดอร์... ]",
            command=self.browse_custom_sector,
            fg_color="#003a5c",
            hover_color="#00b4d8",
            text_color="#00e5ff",
            border_width=1,
            border_color="#00e5ff",
            font=(FONT_THAI, 12, "bold"),
            width=165,
            height=34,
            corner_radius=6
        )

        info_left = ctk.CTkFrame(info_bar, fg_color="transparent")
        info_left.pack(side="left", fill="both", expand=True, padx=6, pady=5)

        self.sector_desc_lbl = ctk.CTkLabel(info_left, text="", text_color="#ffca28", font=(FONT_THAI, 12, "bold"), anchor="w", height=22)
        self.sector_desc_lbl.pack(anchor="w")

        self.sector_path_lbl = ctk.CTkLabel(info_left, text="", text_color="#00ff9d", font=(FONT_TECH, 11), anchor="w", height=20)
        self.sector_path_lbl.pack(anchor="w")

        # Bottom Live Directive Banner with Cyber Progress Bar
        banner_frame = ctk.CTkFrame(main_content, fg_color="#040b17", corner_radius=6, border_width=1, border_color="#0f243b", height=42)
        banner_frame.pack(fill="x", pady=(0, 2))
        
        banner_top = ctk.CTkFrame(banner_frame, fg_color="transparent")
        banner_top.pack(fill="x", padx=12, pady=(4, 2))

        self.scan_status_lbl = ctk.CTkLabel(
            banner_top, 
            text="⚡ SYSTEM DIRECTIVE: AWAITING COMMAND, SIR. ALL SYSTEMS COMBAT READY.", 
            text_color="#00e5ff", 
            font=(FONT_THAI, 11, "bold")
        )
        self.scan_status_lbl.pack(side="left")

        self.progress_pct_lbl = ctk.CTkLabel(
            banner_top,
            text="",
            text_color="#00ff88",
            font=(FONT_TECH, 11, "bold")
        )
        self.progress_pct_lbl.pack(side="right")

        self.progress_bar = ctk.CTkProgressBar(
            banner_frame,
            fg_color="#081526",
            progress_color="#00e5ff",
            height=4,
            corner_radius=2
        )
        self.progress_bar.pack(fill="x", padx=12, pady=(0, 5))
        self.progress_bar.set(0.0)

        # Initialize progress controller (handles all gauge calls seamlessly)
        self.gauge = GaugeAdapter(self.progress_bar, self.progress_pct_lbl)

        # Set default scan mode visual state
        self.select_scan_mode("quick")

    def append_formatted_log(self, line):
        if not line:
            return
        tag = "info"
        lower = line.lower()
        if any(k in lower for k in ["threat", "alert", "critical", "failed", "exception", "[!]"]):
            tag = "threat"
        elif any(k in lower for k in ["cleaned", "online", "success", "completion", "[+]"]):
            tag = "success"
        elif any(k in lower for k in ["initialized", "standby", "halting", "abort", "[*]"]):
            tag = "warn"
        elif " - info - " in lower:
            tag = "dim"
            
        self.log_area._textbox.insert("end", line + "\n", tag)
        self.log_area._textbox.see("end")

    def clear_log_screen(self):
        self.log_area.delete("1.0", "end")
        self.append_formatted_log("[*] TELEMETRY BUFFER FLUSHED BY OPERATOR DIRECTIVE.")

    def open_log_file(self):
        log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scan_history.log")
        if os.path.exists(log_path):
            try:
                os.startfile(log_path)
            except Exception:
                subprocess.Popen(["notepad.exe", log_path])

    def get_connected_usb_drives(self):
        usb_drives = []
        try:
            bitmask = ctypes.windll.kernel32.GetLogicalDrives()
            for letter in 'DEFGHIJKLMNOPQRSTUVWXYZ':
                if bitmask & (1 << (ord(letter) - ord('A'))):
                    drive_path = f"{letter}:\\"
                    # 2 = DRIVE_REMOVABLE
                    if ctypes.windll.kernel32.GetDriveTypeW(drive_path) == 2:
                        usb_drives.append(drive_path)
        except Exception:
            pass
        return usb_drives

    def select_scan_mode(self, mode_key):
        self.current_scan_mode = mode_key
        user_home = os.path.expanduser("~")
        downloads = os.path.join(user_home, "Downloads")
        desktop = os.path.join(user_home, "Desktop")

        # Update button visual states
        for key, btn in self.sector_buttons.items():
            if key == mode_key:
                btn.configure(
                    fg_color="#003554",
                    text_color="#ffffff",
                    border_color="#00e5ff",
                    border_width=2
                )
            else:
                btn.configure(
                    fg_color="#0a1526",
                    text_color="#89a9c9",
                    border_color="#142c47",
                    border_width=1
                )

        if mode_key == "quick":
            self.sector_desc_lbl.configure(text="⚡ สแกนด่วน (Quick Scan): สแกนจุดเสี่ยงสูงที่มัลแวร์มักแฝงตัว (Desktop & Downloads) — รวดเร็ว ปลอดภัย")
            self.sector_path_lbl.configure(text=f"📍 พิกัด: {desktop} | {downloads}")
            self.browse_btn.pack_forget()

        elif mode_key == "usb":
            usb_drives = self.get_connected_usb_drives()
            if usb_drives:
                drives_str = ", ".join(usb_drives)
                self.sector_desc_lbl.configure(text=f"🔌 ตรวจพบแฟลชไดรฟ์ (USB Storage): {drives_str} — พร้อมสแกนกวาดล้าง Autorun, Shortcut และโทรจัน")
                self.sector_path_lbl.configure(text=f"📍 พิกัดไดรฟ์: {drives_str} (เสียบเชื่อมต่อพร้อมสแกน)")
                self.browse_btn.configure(text="[ 📂 เลือกไดรฟ์อื่น... ]")
                self.browse_btn.pack(side="right", padx=12, pady=6)
            else:
                self.sector_desc_lbl.configure(text="🔌 โหมดแฟลชไดรฟ์ (USB Storage): ยังไม่พบแฟลชไดรฟ์เสียบอยู่ — กรุณาเสียบแฟลชไดรฟ์ หรือกดเลือกไดรฟ์เอง")
                self.sector_path_lbl.configure(text="📍 พิกัด: (ยังไม่พบไดรฟ์ Removable — เสียบ USB แล้วคลิกปุ่มนี้อีกครั้งเพื่อตรวจจับ)")
                self.browse_btn.configure(text="[ 📂 เลือกไดรฟ์เอง... ]")
                self.browse_btn.pack(side="right", padx=12, pady=6)

        elif mode_key == "downloads":
            self.sector_desc_lbl.configure(text="📁 โฟลเดอร์ดาวน์โหลด (Downloads): สแกนไฟล์ทั้งหมดที่เพิ่งดาวน์โหลดมาจากอินเทอร์เน็ต")
            self.sector_path_lbl.configure(text=f"📍 พิกัด: {downloads}")
            self.browse_btn.pack_forget()

        elif mode_key == "desktop":
            self.sector_desc_lbl.configure(text="🖥️ หน้าจอเดสก์ท็อป (Desktop): สแกนโปรแกรม ไฟล์ดาวน์โหลด และทางลัดบนหน้าจอเดสก์ท็อป")
            self.sector_path_lbl.configure(text=f"📍 พิกัด: {desktop}")
            self.browse_btn.pack_forget()

        elif mode_key == "memory":
            self.sector_desc_lbl.configure(text="🧠 โหมดสแกนหน่วยความจำ RAM (Active Memory): ตรวจสอบโปรเซสที่กำลังทำงาน ค้นหา Fileless Malware และคำสั่งแฝง")
            self.sector_path_lbl.configure(text="📍 พิกัด: RAM Active Running Processes & Memory Execution Chains (200+ โปรเซส)")
            self.browse_btn.pack_forget()

        elif mode_key == "custom":
            self.sector_desc_lbl.configure(text="📂 เลือกโฟลเดอร์เอง (Custom Path): สแกนเฉพาะโฟลเดอร์ แฟลชไดรฟ์ หรือไดรฟ์ที่ท่านกำหนด")
            target_text = self.custom_selected_folder if self.custom_selected_folder else "(ยังไม่ได้เลือกโฟลเดอร์ — กดปุ่ม 'เลือกโฟลเดอร์...' ด้านขวา)"
            self.sector_path_lbl.configure(text=f"📍 พิกัด: {target_text}")
            self.browse_btn.configure(text="[ 📂 เลือกโฟลเดอร์... ]")
            self.browse_btn.pack(side="right", padx=12, pady=6)

        elif mode_key == "system":
            self.sector_desc_lbl.configure(text="💾 ทั้งระบบ C:\\ (Smart System): สแกนเจาะลึกทั้งไดรฟ์ C: พร้อมระบบ Smart Filter กรองไฟล์ขยะและระบบให้อัตโนมัติ")
            self.sector_path_lbl.configure(text="📍 พิกัด: C:\\ (เปิดใช้ Smart Exclusions ข้าม WinSxS, Cache และไฟล์ระบบ)")
            self.browse_btn.pack_forget()

        if mode_key not in ["custom", "usb"]:
            self.browse_btn.pack_forget()

        if not self.scanning_in_progress:
            mode_display_names = {
                "quick": "⚡ สแกนด่วน (QUICK SCAN)",
                "usb": "🔌 แฟลชไดรฟ์ (USB FLASH DRIVE)",
                "downloads": "📁 ดาวน์โหลด (DOWNLOADS)",
                "desktop": "🖥️ เดสก์ท็อป (DESKTOP)",
                "memory": "🧠 แรม / โปรเซส (RAM ACTIVE MEMORY)",
                "custom": "📂 โฟลเดอร์ที่กำหนดเอง (CUSTOM)",
                "system": "💾 ทั้งระบบ ไดรฟ์ C:\\ (FULL SYSTEM)"
            }
            sec_name = mode_display_names.get(mode_key, mode_key.upper())
            self.scan_status_lbl.configure(
                text=f"🎯 พิกัดพร้อม: [{sec_name}] — กดปุ่ม [ ⚡ สั่งสแกนไวรัส ] ด้านล่างเพื่อเริ่มการสแกน",
                text_color="#00e5ff"
            )

    def browse_custom_sector(self):
        title_text = "เลือกแฟลชไดรฟ์หรือโฟลเดอร์สำหรับสแกน" if self.current_scan_mode == "usb" else "เลือกโฟลเดอร์สำหรับสแกน"
        selected = filedialog.askdirectory(title=title_text)
        if selected:
            self.custom_selected_folder = os.path.normpath(selected)
            self.sector_path_lbl.configure(text=f"📍 พิกัด: {self.custom_selected_folder}")
            if not self.scanning_in_progress:
                folder_name = os.path.basename(self.custom_selected_folder) or self.custom_selected_folder
                self.scan_status_lbl.configure(
                    text=f"🎯 พิกัดพร้อม: [📂 {folder_name}] — กดปุ่ม [ ⚡ สั่งสแกนไวรัส ] ด้านล่างเพื่อเริ่มการสแกน",
                    text_color="#00e5ff"
                )
            self.append_formatted_log(f"[*] TARGET SECTOR LOCKED: {self.custom_selected_folder}")

    def is_script_running(self, script_name):
        for proc in psutil.process_iter(['cmdline']):
            try:
                cmdline = proc.info.get('cmdline')
                if cmdline and any(script_name in arg for arg in cmdline):
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False

    def update_status(self):
        surveillance_active = os.path.exists(self.surveillance_flag_path)
        all_online = True
        
        for script, widget_data in self.module_widgets.items():
            pill = widget_data["pill"]
            if script == "Dashboard.py" or self.is_script_running(script):
                pill.configure(text="● ONLINE", text_color="#00ff88", fg_color="#072b18")
            else:
                if script in ["Dashboard.py", "Watchdog.py"]:
                    pill.configure(text="● OFFLINE", text_color="#ff3366", fg_color="#330814")
                    all_online = False
                else:
                    if not surveillance_active:
                        pill.configure(text="● STANDBY", text_color="#ffb300", fg_color="#332000")
                    else:
                        pill.configure(text="● OFFLINE", text_color="#ff3366", fg_color="#330814")
                        all_online = False

        if all_online and surveillance_active:
            self.shield_status_lbl.configure(text="● SYSTEM: FULLY ARMED", text_color="#00ff88", fg_color="#082b19")
        elif surveillance_active:
            self.shield_status_lbl.configure(text="● SHIELD: ACTIVE", text_color="#00ff88", fg_color="#082b19")
        else:
            self.shield_status_lbl.configure(text="● SYSTEM: STANDBY", text_color="#ffb300", fg_color="#332000")

    def toggle_scan(self):
        if self.scanning_in_progress:
            self.abort_scan()
        else:
            self.trigger_manual_scan()

    def trigger_manual_scan(self):
        if self.scanning_in_progress:
            return

        targets = []
        user_home = os.path.expanduser("~")
        downloads = os.path.join(user_home, "Downloads")
        desktop = os.path.join(user_home, "Desktop")

        if self.current_scan_mode == "quick":
            if os.path.exists(downloads): targets.append(downloads)
            if os.path.exists(desktop): targets.append(desktop)
            if not targets: targets.append(user_home)
        elif self.current_scan_mode == "usb":
            usb_drives = self.get_connected_usb_drives()
            if usb_drives:
                targets.extend(usb_drives)
            elif self.custom_selected_folder and os.path.exists(self.custom_selected_folder):
                targets.append(self.custom_selected_folder)
            else:
                self.browse_custom_sector()
                if self.custom_selected_folder and os.path.exists(self.custom_selected_folder):
                    targets.append(self.custom_selected_folder)
                else:
                    self.append_formatted_log("[!] ยังไม่พบแฟลชไดรฟ์: กรุณาเสียบแฟลชไดรฟ์เข้าพอร์ต USB หรือกดเลือกไดรฟ์ก่อนสั่งสแกนครับท่าน")
                    play_sound_async((600, 200))
                    return
        elif self.current_scan_mode == "downloads":
            targets.append(downloads if os.path.exists(downloads) else user_home)
        elif self.current_scan_mode == "desktop":
            targets.append(desktop if os.path.exists(desktop) else user_home)
        elif self.current_scan_mode == "memory":
            targets.append("ACTIVE_MEMORY_RAM")
        elif self.current_scan_mode == "custom":
            if not self.custom_selected_folder or not os.path.exists(self.custom_selected_folder):
                self.browse_custom_sector()
            if not self.custom_selected_folder:
                return
            targets.append(self.custom_selected_folder)
        elif self.current_scan_mode == "system":
            targets.append("C:\\")
        else:
            targets.append("C:\\")

        if not targets:
            return
            
        self.scanning_in_progress = True
        self.scan_abort_event = threading.Event()
        self.scan_btn.configure(
            state="normal",
            text="[ ⏹️ หยุดสแกนทันที (ABORT) ]",
            fg_color="#5a0e1c",
            hover_color="#ff1744",
            text_color="#ffffff",
            border_color="#ff1744",
            border_width=2
        )
        self.gauge.set_scan_mode(True)
        
        display_targets = ", ".join(targets)
        self.append_formatted_log(f"\n==================================================")
        self.append_formatted_log(f"[{datetime.now().strftime('%H:%M:%S')}] SECTOR ANALYSIS INITIALIZED: {display_targets}")
        self.append_formatted_log(f"==================================================")
        play_sound_async((1200, 100), (1600, 150))

        scan_thread = threading.Thread(target=self.run_background_scan, args=(targets,), daemon=True)
        scan_thread.start()

    def abort_scan(self):
        if hasattr(self, 'scan_abort_event'):
            self.scan_abort_event.set()
        self.scan_btn.configure(
            state="disabled",
            text="[ ⏳ กำลังหยุดสแกน... ]",
            fg_color="#2b0a10",
            text_color="#ff8888",
            border_color="#882222"
        )
        self.append_formatted_log(f"\n[!] ABORT SIGNAL RECEIVED. HALTING SECTOR ANALYSIS...")
        play_sound_async((800, 200))

    def run_background_scan(self, targets):
        try:
            import Scan
            if isinstance(targets, str):
                targets = [targets]

            last_ui_update = [0.0]
            def gui_progress_callback(current, total, file_path, threat_msg):
                now = time.time()
                if threat_msg or current >= total or (now - last_ui_update[0] >= 0.1):
                    last_ui_update[0] = now
                    progress_val = min(1.0, max(0.0, current / total)) if total > 0 else (current % 1000) / 1000.0
                    self.root.after(0, self.update_gui_progress, progress_val, file_path, threat_msg)

            threats_total = 0
            if "ACTIVE_MEMORY_RAM" in targets:
                threats_total = Scan.scan_active_processes(
                    progress_callback=gui_progress_callback,
                    abort_event=self.scan_abort_event
                )
            else:
                for path_to_scan in targets:
                    if self.scan_abort_event.is_set():
                        break
                    threats_total += Scan.scan_directory(
                        path_to_scan, 
                        progress_callback=gui_progress_callback, 
                        abort_event=self.scan_abort_event
                    )

            if self.scan_abort_event.is_set():
                self.root.after(0, self.on_scan_aborted, threats_total)
            else:
                self.root.after(0, self.on_scan_completed, threats_total)
        except Exception as e:
            self.root.after(0, self.on_scan_failed, str(e))

    def update_gui_progress(self, progress, file_path, threat_msg):
        self.gauge.set_progress(progress)
        pct_str = f"{int(progress * 100)}%"
        base_name = os.path.basename(file_path)[:50]
        self.scan_status_lbl.configure(text=f"🛰️ SCANNING [{pct_str}]: {base_name}", text_color="#00e5ff")
        if threat_msg:
            self.append_formatted_log(f"[!] SECURITY ALERT: THREAT SECURED -> {file_path} [{threat_msg}]")
            play_sound_async((2500, 50), (2500, 50))

    def on_scan_completed(self, threats):
        self.scanning_in_progress = False
        self.gauge.set_progress(1.0)
        self.gauge.set_scan_mode(False)
        self.scan_status_lbl.configure(text=f"✓ ANALYSIS COMPLETED. TOTAL THREATS PURGED: {threats}", text_color="#00ff88")
        self.scan_btn.configure(
            state="normal",
            text="[ ⚡ สั่งสแกนไวรัส (START SCAN) ]",
            fg_color="#004d73",
            hover_color="#00b4d8",
            text_color="#ffffff",
            border_color="#00e5ff",
            border_width=2
        )
        self.append_formatted_log(f"\n[*] SECTOR STATUS CLEANED. TOTAL THREATS ELIMINATED: {threats} SIGS.")
        self.load_logs()
        play_sound_async((1000, 150), (1500, 250))

    def on_scan_aborted(self, threats):
        self.scanning_in_progress = False
        self.gauge.set_scan_mode(False)
        self.scan_status_lbl.configure(text=f"⏹️ ANALYSIS ABORTED BY OPERATOR DIRECTIVE. PURGED: {threats}", text_color="#ff9100")
        self.scan_btn.configure(
            state="normal",
            text="[ ⚡ สั่งสแกนไวรัส (START SCAN) ]",
            fg_color="#004d73",
            hover_color="#00b4d8",
            text_color="#ffffff",
            border_color="#00e5ff",
            border_width=2
        )
        self.append_formatted_log(f"\n[*] SECTOR ANALYSIS TERMINATED EARLY. TOTAL THREATS ELIMINATED: {threats} SIGS.")
        play_sound_async((1000, 150))

    def on_scan_failed(self, error_msg):
        self.scanning_in_progress = False
        self.gauge.set_scan_mode(False)
        self.scan_status_lbl.configure(text=f"❌ CORE MODULE EXCEPTION: {error_msg}", text_color="#ff3366")
        self.scan_btn.configure(
            state="normal",
            text="[ ⚡ สั่งสแกนไวรัส (START SCAN) ]",
            fg_color="#004d73",
            hover_color="#00b4d8",
            text_color="#ffffff",
            border_color="#00e5ff",
            border_width=2
        )
        self.append_formatted_log(f"\n[-] CORE MODULE EXCEPTION: {error_msg}")
        self.load_logs()
        play_sound_async((300, 300), (250, 400))

    def initialize_surveillance_cores(self):
        if os.path.exists(self.surveillance_flag_path):
            return

        scripts = ["USBWatcher.py", "RealTimeMonitor.py", "BehavioralMonitor.py", "RegistrySurveillance.py"]
        already_running = [s for s in scripts if self.is_script_running(s)]
        if already_running:
            try:
                with open(self.surveillance_flag_path, "w") as f: f.write("active")
            except: pass
            self.init_surv_btn.configure(state="disabled", text="[ ✓ เกราะเฝ้าระวังทำงานแล้ว ]", fg_color="#003314", text_color="#00ff88", border_color="#00ff88")
            return

        try:
            with open(self.surveillance_flag_path, "w") as f: f.write("active")
        except Exception as e:
            self.append_formatted_log(f"[-] Shield registration failed: {e}")
            return

        base_dir = os.path.dirname(os.path.abspath(__file__))
        launched_cores = []
        for script in scripts:
            script_path = os.path.join(base_dir, script)
            if os.path.exists(script_path):
                subprocess.Popen([sys.executable, script], creationflags=subprocess.CREATE_NEW_CONSOLE, cwd=base_dir)
                launched_cores.append(script)

        self.append_formatted_log(f"\n[+] [{datetime.now().strftime('%H:%M:%S')}] DEPLOYED BACKEND SURVEILLANCE: {', '.join(launched_cores)} successfully.")
        
        self.init_surv_btn.configure(state="disabled", text="[ ✓ เกราะเฝ้าระวังทำงานแล้ว ]", fg_color="#003314", text_color="#00ff88", border_color="#00ff88")
        play_sound_async((900, 100), (1200, 100), (1600, 150))

    def load_logs(self):
        if self.scanning_in_progress:
            return
        log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scan_history.log")
        if os.path.exists(log_path):
            try:
                mtime = os.path.getmtime(log_path)
                if hasattr(self, '_last_log_mtime') and self._last_log_mtime == mtime:
                    return
                self._last_log_mtime = mtime
                
                with open(log_path, "rb") as f:
                    f.seek(0, os.SEEK_END)
                    size = f.tell()
                    seek_pos = max(0, size - 8192)
                    f.seek(seek_pos)
                    data = f.read().decode('utf-8', errors='ignore')
                    lines = [ln for ln in data.splitlines() if ln.strip()][-25:]
                    
                self.log_area.delete("1.0", "end")
                for ln in lines:
                    self.append_formatted_log(ln)
            except Exception:
                pass

    def on_closing(self):
        scripts_to_terminate = ["Watchdog.py", "RealTimeMonitor.py", "USBWatcher.py", "Scan.py", "BehavioralMonitor.py", "RegistrySurveillance.py"]
        if os.path.exists(self.surveillance_flag_path):
            try: os.remove(self.surveillance_flag_path)
            except: pass

        with open(self.shutdown_flag_path, "w") as f:
            f.write("shutdown")
            
        for proc in psutil.process_iter(['cmdline']):
            try:
                cmdline = proc.info.get('cmdline')
                if cmdline:
                    cmd_str = " ".join(cmdline)
                    if any(script in cmd_str for script in scripts_to_terminate):
                        proc.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        self.gauge.running = False
        self.root.destroy()
        sys.exit(0)

    def periodic_check(self):
        self.update_status()
        self.load_logs()
        self.root.after(1500, self.periodic_check)

if __name__ == "__main__":
    app_root = ctk.CTk()
    app = AntivirusDashboard(app_root)
    app_root.mainloop()
