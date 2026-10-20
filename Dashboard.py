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

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

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

class AnimatedHoloGauge(ctk.CTkCanvas):
    def __init__(self, master, width=200, height=200, **kwargs):
        super().__init__(master, width=width, height=height, bg="#050b14", highlightthickness=0, **kwargs)
        self.width = width
        self.height = height
        self.center_x = width // 2
        self.center_y = height // 2
        self.angle_offset = 0
        self.radius = min(width, height) // 2 - 15
        self.running = True
        self.progress = 0.0
        self.scan_mode = False
        
        self.animation_thread = threading.Thread(target=self._animate_loop, daemon=True)
        self.animation_thread.start()

    def set_progress(self, progress):
        self.progress = max(0.0, min(1.0, progress))

    def set_scan_mode(self, active):
        self.scan_mode = active

    def _animate_loop(self):
        while self.running:
            try:
                self.angle_offset += 0.05
                if self.angle_offset > math.pi * 2:
                    self.angle_offset = 0
                self.after(0, self._draw_frame)
            except Exception:
                pass
            # Optimized pacing: 20 FPS during active scanning, 12.5 FPS ambient during standby to minimize CPU
            time.sleep(0.05 if self.scan_mode else 0.08)

    def _draw_frame(self):
        self.delete("all")
        
        # J.A.R.V.I.S. Classic Blue for standby, Iron Man Amber/Gold for scanning
        base_color = "#00e5ff" if not self.scan_mode else "#ffb300"
        inner_color = "#0088cc" if not self.scan_mode else "#ff4500"
        
        # Outer Ring (Dashed Arc Reactor feel)
        for i in range(12):
            start = math.degrees(self.angle_offset) + (i * 30)
            self.create_arc(
                self.center_x - self.radius, self.center_y - self.radius,
                self.center_x + self.radius, self.center_y + self.radius,
                start=start, extent=20, outline=base_color, width=2, style=tk.ARC
            )

        # Middle Ring (Counter-rotating)
        mid_radius = self.radius - 12
        for i in range(8):
            start = math.degrees(-self.angle_offset * 1.5) + (i * 45)
            self.create_arc(
                self.center_x - mid_radius, self.center_y - mid_radius,
                self.center_x + mid_radius, self.center_y + mid_radius,
                start=start, extent=30, outline=inner_color, width=3, style=tk.ARC
            )

        # Inner Pulsing Core
        pulse = abs(math.sin(self.angle_offset * 2))
        core_radius = 15 + (5 * pulse)
        self.create_oval(
            self.center_x - core_radius, self.center_y - core_radius,
            self.center_x + core_radius, self.center_y + core_radius,
            outline=base_color, fill=inner_color, width=1
        )

        if self.scan_mode:
            r_prog = self.radius - 24
            extent_prog = 360 * self.progress
            self.create_arc(
                self.center_x - r_prog, self.center_y - r_prog,
                self.center_x + r_prog, self.center_y + r_prog,
                start=90, extent=-extent_prog,
                outline="#00ff66", width=5, style=tk.ARC
            )
            pct = int(self.progress * 100)
            self.create_text(self.center_x, self.center_y + 35, text=f"{pct}%", fill="#00ff66", font=("Consolas", 14, "bold"))
        else:
            self.create_text(self.center_x, self.center_y + 35, text="STANDBY", fill=base_color, font=("Consolas", 11, "bold"))

class AntivirusDashboard:
    def __init__(self, root):
        self.root = root
        self.root.geometry("1000x820")
        try:
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            self.root.geometry(f"1000x820+{max(0, (sw - 1000) // 2)}+{max(0, (sh - 820) // 2)}")
        except Exception:
            pass
        self.root.configure(fg_color="#010a14")
        self.root.resizable(False, False)
        
        # สไตล์ Frameless ล้ำสมัยสไตล์ Cyberpunk HUD
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.96)
        
        # ระบบลากหน้าต่างโปรแกรม
        self.root.bind("<Button-1>", self._start_move)
        self.root.bind("<B1-Motion>", self._do_move)
        self.root.bind("<Map>", self.on_map)

        self.shutdown_flag_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".dashboard_shutdown_flag")
        self.surveillance_flag_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".surveillance_active_flag")

        self.scanning_in_progress = False
        self.current_scan_mode = "quick"
        self.custom_selected_folder = None
        self.setup_ui()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # เคลียร์สถานะตกค้าง
        if os.path.exists(self.shutdown_flag_path):
            try: os.remove(self.shutdown_flag_path)
            except: pass
            
        scripts = ["USBWatcher.py", "RealTimeMonitor.py", "BehavioralMonitor.py", "RegistrySurveillance.py"]
        monitors_running = any(self.is_script_running(s) for s in scripts)
        
        if monitors_running:
            try:
                with open(self.surveillance_flag_path, "w") as f: f.write("active")
            except: pass
            self.init_surv_btn.configure(state="disabled", text="[ ระบบเฝ้าระวังทำงานแล้ว ]", fg_color="#006b2b")

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
        # Header Control Panel (Stark Tech)
        header_frame = ctk.CTkFrame(self.root, fg_color="#050b14", corner_radius=0, height=50)
        header_frame.pack(fill="x", side="top")
        
        # Bottom glowing separator
        ctk.CTkFrame(self.root, fg_color="#00e5ff", height=2).pack(fill="x")
        
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "logo_cyan.png")
        if os.path.exists(logo_path):
            orig_img = Image.open(logo_path)
            aspect_ratio = orig_img.width / orig_img.height
            target_height = 35
            target_width = int(target_height * aspect_ratio)
            
            logo_img = ctk.CTkImage(light_image=orig_img,
                                    dark_image=orig_img,
                                    size=(target_width, target_height))
            title_lbl = ctk.CTkLabel(header_frame, text=" // J.A.R.V.I.S. DEFENSE SYSTEM", image=logo_img, compound="left",
                                     text_color="#00e5ff", font=("Consolas", 14, "bold"))
        else:
            title_lbl = ctk.CTkLabel(header_frame, text="NACHAPOL INDUSTRIES // J.A.R.V.I.S. DEFENSE SYSTEM", 
                                     text_color="#00e5ff", font=("Consolas", 14, "bold"))
            
        title_lbl.pack(side="left", padx=20, pady=10)
        
        # Titlebar Window Control Buttons (Top-Right)
        win_ctrls = ctk.CTkFrame(header_frame, fg_color="transparent")
        win_ctrls.pack(side="right", padx=(10, 15), pady=8)

        self.top_close_btn = ctk.CTkButton(
            win_ctrls,
            text="✕",
            width=36,
            height=30,
            corner_radius=6,
            font=("Consolas", 14, "bold"),
            fg_color="#1a0b12",
            text_color="#ff3366",
            hover_color="#ff003c",
            border_width=1,
            border_color="#ff003c",
            command=self.on_closing
        )
        self.top_close_btn.pack(side="right", padx=(5, 0))

        self.top_min_btn = ctk.CTkButton(
            win_ctrls,
            text="🗕",
            width=36,
            height=30,
            corner_radius=6,
            font=("Consolas", 13, "bold"),
            fg_color="#0a192f",
            text_color="#00e5ff",
            hover_color="#0088cc",
            border_width=1,
            border_color="#00e5ff",
            command=self.minimize_window
        )
        self.top_min_btn.pack(side="right", padx=(0, 5))

        self.shield_status_lbl = ctk.CTkLabel(header_frame, text="SYSTEM STATUS: ONLINE", text_color="#00e5ff", font=("Consolas", 13, "bold"))
        self.shield_status_lbl.pack(side="right", padx=15, pady=10)

        # Bottom Docked Controls Footer (PACKED FIRST TO GUARANTEE 100% VISIBILITY)
        ctk.CTkFrame(self.root, fg_color="#00e5ff", height=2).pack(fill="x", side="bottom")

        btn_frame = ctk.CTkFrame(self.root, fg_color="#050b14", corner_radius=0, height=65)
        btn_frame.pack(fill="x", side="bottom")

        self.scan_btn = ctk.CTkButton(
            btn_frame,
            text="[ ⚡ สั่งสแกนไวรัส (START SCAN) ]",
            command=self.toggle_scan,
            fg_color="#004d73",
            hover_color="#00e5ff",
            text_color="#00e5ff",
            border_width=2,
            border_color="#00e5ff",
            font=("Segoe UI", 13, "bold"),
            width=260,
            height=40
        )
        self.scan_btn.pack(side="left", padx=20, pady=12)
        
        self.init_surv_btn = ctk.CTkButton(
            btn_frame,
            text="[ 🛡️ เปิดเกราะเฝ้าระวังเบื้องหลัง ]",
            command=self.initialize_surveillance_cores,
            fg_color="#0a192f",
            hover_color="#00ff66",
            text_color="#00ff66",
            border_width=1,
            border_color="#00ff66",
            font=("Segoe UI", 11, "bold"),
            width=220,
            height=38
        )
        self.init_surv_btn.pack(side="left", padx=10)

        ctk.CTkLabel(
            btn_frame,
            text="J.A.R.V.I.S. SECURITY OS MARK IV",
            text_color="#005577",
            font=("Consolas", 10, "bold")
        ).pack(side="right", padx=20)

        # Main Content Area (Fills the available middle space)
        main_content = ctk.CTkFrame(self.root, fg_color="transparent")
        main_content.pack(fill="both", expand=True, padx=20, pady=(6, 4))

        top_split = ctk.CTkFrame(main_content, fg_color="transparent")
        top_split.pack(fill="x", pady=4)

        # จัด Layout ส่วนแคนวาส (Arc Reactor)
        gauge_bg_box = ctk.CTkFrame(top_split, fg_color="#050b14", corner_radius=12, border_width=2, border_color="#00e5ff", width=145, height=145)
        gauge_bg_box.pack(side="left", padx=(0, 12))
        gauge_bg_box.pack_propagate(False)

        self.gauge = AnimatedHoloGauge(gauge_bg_box, width=135, height=135)
        self.gauge.pack(pady=5)

        status_frame = ctk.CTkFrame(top_split, fg_color="#050b14", corner_radius=12, border_width=2, border_color="#00e5ff")
        status_frame.pack(side="right", fill="both", expand=True)
        
        lbl_title = ctk.CTkLabel(status_frame, text="[ COGNITIVE CORES & MODULE DIAGNOSTICS ]", text_color="#00e5ff", font=("Consolas", 12, "bold"))
        lbl_title.pack(pady=6)

        self.module_labels = {}
        modules = [
            ("Dashboard.py", "MARK IV HUD INTERFACE"),
            ("Watchdog.py", "WATCHDOG SELF-DEFENSE"),
            ("RealTimeMonitor.py", "MULTI-VECTOR SCANNER"),
            ("USBWatcher.py", "HARDWARE FIREWALL"),
            ("BehavioralMonitor.py", "COGNITIVE BEHAVIORAL AI"),
            ("RegistrySurveillance.py", "DEEP REGISTRY SENTINEL")
        ]
        
        grid_frame = ctk.CTkFrame(status_frame, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True, padx=12, pady=4)
        
        for i, (script, label_text) in enumerate(modules):
            row = i // 2
            col = i % 2
            lbl = ctk.CTkLabel(grid_frame, text=f"> {label_text}: CALIBRATING...", text_color="#ffb300", font=("Consolas", 10, "bold"))
            lbl.grid(row=row, column=col, sticky="w", padx=8, pady=4)
            self.module_labels[script] = lbl

        # Terminal Log View (J.A.R.V.I.S. Data Feed)
        log_frame = ctk.CTkFrame(main_content, fg_color="#050b14", corner_radius=12, border_width=2, border_color="#00e5ff")
        log_frame.pack(fill="both", expand=True, pady=6)
        
        log_title = ctk.CTkLabel(log_frame, text="[ J.A.R.V.I.S. LIVE DATA STREAM ]", text_color="#00e5ff", font=("Consolas", 11, "bold"))
        log_title.pack(anchor="w", padx=12, pady=4)
        
        self.log_area = ctk.CTkTextbox(log_frame, fg_color="#020810", text_color="#00e5ff", font=("Consolas", 11), height=110)
        self.log_area.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        # Sector Targeting Control Frame (Cyberpunk HUD Card)
        sector_panel = ctk.CTkFrame(main_content, fg_color="#030812", corner_radius=12, border_width=2, border_color="#00e5ff")
        sector_panel.pack(fill="x", padx=2, pady=(0, 4))

        # Title Row
        title_row = ctk.CTkFrame(sector_panel, fg_color="transparent")
        title_row.pack(fill="x", padx=12, pady=(5, 2))
        
        sector_title = ctk.CTkLabel(title_row, text="🎯 พิกัดเป้าหมายการสแกน (TARGET SECTOR):", text_color="#00e5ff", font=("Consolas", 12, "bold"))
        sector_title.pack(side="left")

        # Preset Mode Buttons - Row 1 (Core Sectors)
        row1_frame = ctk.CTkFrame(sector_panel, fg_color="transparent")
        row1_frame.pack(fill="x", padx=8, pady=(2, 2))

        self.sector_buttons = {}
        row1_definitions = [
            ("quick", "⚡ สแกนด่วน (Quick)"),
            ("usb", "🔌 แฟลชไดรฟ์ (USB)"),
            ("downloads", "📁 ดาวน์โหลด (Downloads)"),
            ("desktop", "🖥️ หน้าจอ Desktop")
        ]
        
        for key, title in row1_definitions:
            btn = ctk.CTkButton(
                row1_frame,
                text=title,
                command=lambda k=key: self.select_scan_mode(k),
                font=("Segoe UI", 11, "bold"),
                height=32,
                corner_radius=8,
                fg_color="#0a192f",
                text_color="#88a0b8",
                border_width=1,
                border_color="#1a365d",
                hover_color="#003859"
            )
            btn.pack(side="left", padx=3, expand=True, fill="x")
            self.sector_buttons[key] = btn

        # Preset Mode Buttons - Row 2 (Deep & Custom Sectors)
        row2_frame = ctk.CTkFrame(sector_panel, fg_color="transparent")
        row2_frame.pack(fill="x", padx=8, pady=(2, 4))

        row2_definitions = [
            ("memory", "🧠 หน่วยความจำ RAM (Active Memory)"),
            ("custom", "📂 เลือกโฟลเดอร์เอง (Browse...)"),
            ("system", "💾 ทั้งระบบ ไดรฟ์ C:\\ (Smart System)")
        ]

        for key, title in row2_definitions:
            btn = ctk.CTkButton(
                row2_frame,
                text=title,
                command=lambda k=key: self.select_scan_mode(k),
                font=("Segoe UI", 11, "bold"),
                height=32,
                corner_radius=8,
                fg_color="#0a192f",
                text_color="#88a0b8",
                border_width=1,
                border_color="#1a365d",
                hover_color="#003859"
            )
            btn.pack(side="left", padx=3, expand=True, fill="x")
            self.sector_buttons[key] = btn

        # Info & Details Display Bar
        info_bar = ctk.CTkFrame(sector_panel, fg_color="#02050a", corner_radius=8, border_width=1, border_color="#0c2340")
        info_bar.pack(fill="x", padx=8, pady=(4, 8))

        self.browse_btn = ctk.CTkButton(
            info_bar,
            text="[ 📂 เลือกโฟลเดอร์... ]",
            command=self.browse_custom_sector,
            fg_color="#003859",
            hover_color="#00b4d8",
            text_color="#00e5ff",
            border_width=1,
            border_color="#00e5ff",
            font=("Segoe UI", 11, "bold"),
            width=160,
            height=32
        )

        info_left = ctk.CTkFrame(info_bar, fg_color="transparent")
        info_left.pack(side="left", fill="both", expand=True, padx=10, pady=4)

        self.sector_desc_lbl = ctk.CTkLabel(info_left, text="", text_color="#ffb300", font=("Segoe UI", 11, "bold"), anchor="w", height=20)
        self.sector_desc_lbl.pack(anchor="w")

        self.sector_path_lbl = ctk.CTkLabel(info_left, text="", text_color="#00ff66", font=("Consolas", 10), anchor="w", height=18)
        self.sector_path_lbl.pack(anchor="w")

        # Bottom Panel Status
        self.scan_status_lbl = ctk.CTkLabel(main_content, text="AWAITING DIRECTIVES, SIR.", text_color="#00e5ff", font=("Segoe UI", 11, "bold"))
        self.scan_status_lbl.pack(anchor="w", padx=5, pady=(2, 0))

        # Set default scan mode visual state
        self.select_scan_mode("quick")

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
                    fg_color="#002b4d",
                    text_color="#00e5ff",
                    border_color="#00e5ff",
                    border_width=2
                )
            else:
                btn.configure(
                    fg_color="#071321",
                    text_color="#7d99b3",
                    border_color="#152e4d",
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
                self.sector_desc_lbl.configure(text=f"🔌 ตรวจพบแฟลชไดรฟ์ (USB): {drives_str} — พร้อมสแกนกำจัดไวรัส Autorun, Shortcut และโทรจันแฝง")
                self.sector_path_lbl.configure(text=f"📍 พิกัดไดรฟ์: {drives_str} (เสียบพร้อมทำงาน)")
                self.browse_btn.configure(text="[ 📂 เลือกไดรฟ์อื่น... ]")
                self.browse_btn.pack(side="right", padx=12, pady=6)
            else:
                self.sector_desc_lbl.configure(text="🔌 โหมดแฟลชไดรฟ์ (USB): ยังไม่พบแฟลชไดรฟ์เสียบอยู่ — กรุณาเสียบแฟลชไดรฟ์ หรือกดเลือกไดรฟ์เอง")
                self.sector_path_lbl.configure(text="📍 พิกัด: (ยังไม่พบไดรฟ์ Removable — เสียบ USB แล้วคลิกปุ่มนี้อีกครั้งเพื่อตรวจจับ)")
                self.browse_btn.configure(text="[ 📂 เลือกไดรฟ์เอง... ]")
                self.browse_btn.pack(side="right", padx=12, pady=6)

        elif mode_key == "downloads":
            self.sector_desc_lbl.configure(text="📁 โฟลเดอร์ดาวน์โหลด (Downloads): สแกนไฟล์ทั้งหมดที่เพิ่งดาวน์โหลดมาจากอินเทอร์เน็ต")
            self.sector_path_lbl.configure(text=f"📍 พิกัด: {downloads}")
            self.browse_btn.pack_forget()

        elif mode_key == "desktop":
            self.sector_desc_lbl.configure(text="🖥️ หน้าจอเดสก์ท็อป (Desktop): สแกนโปรแกรมและไฟล์ทั้งหมดที่วางอยู่บนหน้าจอเดสก์ท็อป")
            self.sector_path_lbl.configure(text=f"📍 พิกัด: {desktop}")
            self.browse_btn.pack_forget()

        elif mode_key == "memory":
            self.sector_desc_lbl.configure(text="🧠 โหมดสแกนหน่วยความจำ RAM (Active Memory): ตรวจสอบโปรเซสที่กำลังทำงาน ค้นหา Fileless Malware และคำสั่งแฝง")
            self.sector_path_lbl.configure(text="📍 พิกัด: RAM Active Running Processes & Memory Execution Chains (200+ โปรเซส)")
            self.browse_btn.pack_forget()

        elif mode_key == "custom":
            self.sector_desc_lbl.configure(text="📂 เลือกโฟลเดอร์เอง (Custom Folder): สแกนเฉพาะโฟลเดอร์ แฟลชไดรฟ์ หรือไดรฟ์ที่ท่านกำหนด")
            target_text = self.custom_selected_folder if self.custom_selected_folder else "(ยังไม่ได้เลือกโฟลเดอร์ — กดปุ่ม 'เลือกโฟลเดอร์...' ด้านขวา)"
            self.sector_path_lbl.configure(text=f"📍 พิกัด: {target_text}")
            self.browse_btn.configure(text="[ 📂 เลือกโฟลเดอร์... ]")
            self.browse_btn.pack(side="right", padx=12, pady=6)

        elif mode_key == "system":
            self.sector_desc_lbl.configure(text="💾 ทั้งระบบ C:\\ (Full System): สแกนเจาะลึกทั้งไดรฟ์ C: พร้อมระบบ Smart Filter กรองไฟล์ขยะและระบบให้อัตโนมัติ")
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
            self.log_area.insert("end", f"[*] TARGET SECTOR LOCKED: {self.custom_selected_folder}\n")
            self.log_area.see("end")

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
        for script, lbl in self.module_labels.items():
            base_name = lbl.cget("text").split(":")[0].replace("• ", "")
            if script == "Dashboard.py" or self.is_script_running(script):
                lbl.configure(text=f"• {base_name}: ONLINE", text_color="#00ff66")
            else:
                if script in ["Dashboard.py", "Watchdog.py"]:
                    lbl.configure(text=f"• {base_name}: OFFLINE", text_color="#ff3d00")
                else:
                    if not surveillance_active:
                        lbl.configure(text=f"• {base_name}: STANDBY", text_color="#ff9100")
                    else:
                        lbl.configure(text=f"• {base_name}: OFFLINE (CRITICAL)", text_color="#ff3d00")

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
                    self.log_area.insert("end", "[!] ยังไม่พบแฟลชไดรฟ์: กรุณาเสียบแฟลชไดรฟ์เข้าพอร์ต USB หรือกดเลือกไดรฟ์ก่อนสั่งสแกนครับท่าน\n")
                    self.log_area.see("end")
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
            text="[ ⏹️ หยุดสแกน (ABORT) ]",
            fg_color="#3b0d14",
            hover_color="#ff003c",
            text_color="#ff3366",
            border_color="#ff003c"
        )
        self.gauge.set_scan_mode(True)
        
        display_targets = ", ".join(targets)
        self.log_area.insert("end", f"\n\n==================================================\n")
        self.log_area.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] SECTOR ANALYSIS INITIALIZED: {display_targets}\n")
        self.log_area.insert("end", f"==================================================\n")
        self.log_area.see("end")
        play_sound_async((1200, 100), (1600, 150))

        scan_thread = threading.Thread(target=self.run_background_scan, args=(targets,), daemon=True)
        scan_thread.start()

    def abort_scan(self):
        if hasattr(self, 'scan_abort_event'):
            self.scan_abort_event.set()
        self.scan_btn.configure(
            state="disabled",
            text="[ ⏳ กำลังหยุดสแกน... ]",
            fg_color="#200808",
            text_color="#ff8888",
            border_color="#882222"
        )
        self.log_area.insert("end", f"\n[!] ABORT SIGNAL RECEIVED. HALTING SECTOR ANALYSIS...\n")
        self.log_area.see("end")
        play_sound_async((800, 200))

    def run_background_scan(self, targets):
        try:
            import Scan
            if isinstance(targets, str):
                targets = [targets]

            last_ui_update = [0.0]
            def gui_progress_callback(current, total, file_path, threat_msg):
                now = time.time()
                # Fast responsiveness: immediately dispatch threats/completion, throttle routine progress to 10 FPS
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
        self.scan_status_lbl.configure(text=f"ANALYZING SECTOR: {os.path.basename(file_path)[:55]}", text_color="#00e5ff")
        if threat_msg:
            self.log_area.insert("end", f"[!] SECURITY ALERT: THREAT SECURED -> {file_path} [{threat_msg}]\n")
            self.log_area.see("end")
            play_sound_async((2500, 50), (2500, 50))

    def on_scan_completed(self, threats):
        self.scanning_in_progress = False
        self.gauge.set_progress(1.0)
        self.gauge.set_scan_mode(False)
        self.scan_status_lbl.configure(text=f"ANALYSIS PROTOCOL COMPLETION. PURGED THREATS: {threats}", text_color="#00ff66")
        self.scan_btn.configure(
            state="normal",
            text="[ ⚡ สั่งสแกนไวรัส (START SCAN) ]",
            fg_color="#004d73",
            hover_color="#00e5ff",
            text_color="#00e5ff",
            border_color="#00e5ff"
        )
        self.log_area.insert("end", f"\n[*] SECTOR STATUS CLEANED. TOTAL THREATS ELIMINATED: {threats} SIGS.\n")
        self.log_area.see("end")
        self.load_logs()
        play_sound_async((1000, 150), (1500, 250))

    def on_scan_aborted(self, threats):
        self.scanning_in_progress = False
        self.gauge.set_scan_mode(False)
        self.scan_status_lbl.configure(text=f"ANALYSIS ABORTED. PURGED THREATS: {threats}", text_color="#ff9100")
        self.scan_btn.configure(
            state="normal",
            text="[ ⚡ สั่งสแกนไวรัส (START SCAN) ]",
            fg_color="#004d73",
            hover_color="#00e5ff",
            text_color="#00e5ff",
            border_color="#00e5ff"
        )
        self.log_area.insert("end", f"\n[*] SECTOR ANALYSIS TERMINATED EARLY. TOTAL THREATS ELIMINATED: {threats} SIGS.\n")
        self.log_area.see("end")
        play_sound_async((1000, 150))

    def on_scan_failed(self, error_msg):
        self.scanning_in_progress = False
        self.gauge.set_scan_mode(False)
        self.scan_status_lbl.configure(text=f"CORE ANALYSIS FAILURE: {error_msg}", text_color="#ff3d00")
        self.scan_btn.configure(
            state="normal",
            text="[ ⚡ สั่งสแกนไวรัส (START SCAN) ]",
            fg_color="#004d73",
            hover_color="#00e5ff",
            text_color="#00e5ff",
            border_color="#00e5ff"
        )
        self.log_area.insert("end", f"\n[-] CORE MODULE EXCEPTION: {error_msg}\n")
        self.log_area.see("end")
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
            self.init_surv_btn.configure(state="disabled", text="[ ระบบเฝ้าระวังทำงานแล้ว ]", fg_color="#006b2b")
            return

        try:
            with open(self.surveillance_flag_path, "w") as f: f.write("active")
        except Exception as e:
            self.log_area.insert("end", f"[-] Shield registration failed: {e}\n")
            return

        base_dir = os.path.dirname(os.path.abspath(__file__))
        launched_cores = []
        for script in scripts:
            script_path = os.path.join(base_dir, script)
            if os.path.exists(script_path):
                subprocess.Popen([sys.executable, script], creationflags=subprocess.CREATE_NEW_CONSOLE, cwd=base_dir)
                launched_cores.append(script)

        self.log_area.insert("end", f"\n[+] [{datetime.now().strftime('%H:%M:%S')}] DEPLOYED BACKEND SURVEILLANCE: {', '.join(launched_cores)} successfully.\n")
        self.log_area.see("end")
        
        self.init_surv_btn.configure(state="disabled", text="[ ระบบเฝ้าระวังทำงานแล้ว ]", fg_color="#006b2b")
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
                
                # Fast tail read of the last 8KB rather than parsing multi-megabyte log files
                with open(log_path, "rb") as f:
                    f.seek(0, os.SEEK_END)
                    size = f.tell()
                    seek_pos = max(0, size - 8192)
                    f.seek(seek_pos)
                    data = f.read().decode('utf-8', errors='ignore')
                    lines = [ln for ln in data.splitlines() if ln.strip()][-30:]
                    
                self.log_area.delete("1.0", "end")
                self.log_area.insert("end", "\n".join(lines) + "\n")
                self.log_area.see("end")
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