import winreg
import os
import logging
import time

LOG_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scan_history.log")

logging.basicConfig(
    filename=LOG_FILE_PATH,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

class RegistryMonitor:
    def __init__(self):
        self.scan_interval = 60
        self.suspicious_paths = ["temp", "appdata", "powershell", "cmd.exe", "wscript", "cscript", "vbs", "bitsadmin"]
        
        self.reg_keys = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\RunOnce")
        ]
        
        self.startup_folders = [
            os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs\Startup"),
            os.path.join(os.environ.get("PROGRAMDATA", ""), r"Microsoft\Windows\Start Menu\Programs\Startup")
        ]

    def get_autorun_entries(self):
        entries = {}
        # 1. Scan standard Run & RunOnce Registry values
        for hkey, path in self.reg_keys:
            try:
                with winreg.OpenKey(hkey, path, 0, winreg.KEY_READ) as key:
                    info = winreg.QueryInfoKey(key)
                    for i in range(info[1]):
                        name, value, _ = winreg.EnumValue(key, i)
                        entries[f"REG:{path}\\{name}"] = str(value)
            except Exception:
                continue

        # 2. Enumerate Windows Services subkeys
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services", 0, winreg.KEY_READ) as s_key:
                info = winreg.QueryInfoKey(s_key)
                for i in range(info[0]):
                    try:
                        sub_name = winreg.EnumKey(s_key, i)
                        try:
                            with winreg.OpenKey(s_key, sub_name, 0, winreg.KEY_READ) as sub:
                                try:
                                    img_path, _ = winreg.QueryValueEx(sub, "ImagePath")
                                    entries[f"SVC:{sub_name}"] = str(img_path)
                                except FileNotFoundError:
                                    entries[f"SVC:{sub_name}"] = "(No ImagePath)"
                        except Exception:
                            entries[f"SVC:{sub_name}"] = "(Restricted Access)"
                    except Exception:
                        continue
        except Exception:
            pass
                
        # 3. Scan Startup Folders
        for folder in self.startup_folders:
            if os.path.exists(folder):
                try:
                    for item in os.listdir(folder):
                        filepath = os.path.join(folder, item)
                        if os.path.isfile(filepath):
                            entries[f"STARTUP:{filepath}"] = filepath
                except Exception:
                    continue
                    
        return entries

    def run(self):
        os.system('color 0e')
        print("[*] JARVIS: Registry & Persistence Monitor Active...")
        print("[*] Baseline autorun snapshot generated (Registry, Services, Startup Folders)...")
        
        known_entries = self.get_autorun_entries()
        print(f"[*] Monitoring {len(known_entries)} persistence nodes for unauthorized modifications.")
        
        try:
            while True:
                time.sleep(self.scan_interval) 
                current_entries = self.get_autorun_entries()
                
                for key_path in current_entries:
                    if key_path not in known_entries:
                        value = current_entries[key_path]
                        is_suspicious = any(p in str(value).lower() for p in self.suspicious_paths)
                        
                        level = "[WARNING]" if not is_suspicious else "[CRITICAL]"
                        alert_msg = f"{level} NEW PERSISTENCE DETECTED: {key_path} -> {value}"
                        
                        print(f"\n[!] ALERT: {alert_msg}")
                        logging.warning(alert_msg)
                
                known_entries = current_entries
                
        except KeyboardInterrupt:
            print("\n[*] Persistence Monitor Deactivated.")
            logging.info("[SYSTEM] Persistence Monitor stopped.")

if __name__ == "__main__":
    monitor = RegistryMonitor()
    monitor.run()
