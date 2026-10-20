import os
import time
import subprocess
import sys
import psutil
import logging

LOG_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scan_history.log")

logging.basicConfig(
    filename=LOG_FILE_PATH,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

class USBMonitor:
    def __init__(self):
        self.existing_drives = {d.device for d in psutil.disk_partitions()}
        self.script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Scan.py")
        
        # CREATE_NO_WINDOW flag to make it completely silent for the user
        self.CREATE_NO_WINDOW = 0x08000000

    def run(self):
        os.system('color 0e')
        print("[*] JARVIS: USB Surveillance Monitor Active...")
        print("[*] Waiting for external hardware connections...")
        logging.info("[SYSTEM] USB Surveillance Monitor started.")
        
        try:
            while True:
                current_drives = {d.device for d in psutil.disk_partitions()}
                new_drives = current_drives - self.existing_drives
                
                for drive in new_drives:
                    print(f"\n[!] ALERT: New physical drive detected at {drive}")
                    print(f"[*] Initiating silent threat elimination scan on {drive}...")
                    logging.info(f"[USB] New drive detected: {drive}. Starting silent scan.")
                    
                    if os.path.exists(self.script_path):
                        # Run silent scan without popping up a console window or hanging on input
                        subprocess.Popen(
                            [sys.executable, self.script_path, "--no-pause", drive], 
                            cwd=os.path.dirname(self.script_path),
                            creationflags=self.CREATE_NO_WINDOW
                        )
                    else:
                        logging.error(f"[USB] Scan.py missing at {self.script_path}")
                
                self.existing_drives = current_drives
                time.sleep(2) 
        except KeyboardInterrupt:
            print("\n[*] USB Surveillance Monitor Deactivated.")
            logging.info("[SYSTEM] USB Surveillance Monitor stopped.")

if __name__ == "__main__":
    monitor = USBMonitor()
    monitor.run()
