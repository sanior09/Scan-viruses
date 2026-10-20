import os
import time
import sys
import subprocess
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

WATCH_PATHS = [
    os.path.join(os.path.expanduser("~"), "Downloads"),
    os.path.join(os.path.expanduser("~"), "Desktop"),
    os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Temp')
]

# Files/extensions that should not trigger full scans (transient system locks)
IGNORED_PATTERNS = {'.crdownload', '.tmp', '.part', '.jarvis_locked'}

class SecurityHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self.current_dir = os.path.dirname(os.path.realpath(__file__))
        self.script_path = os.path.join(self.current_dir, "Scan.py")
        self.executable = sys.executable.replace("pythonw.exe", "python.exe")
        self.CREATE_NO_WINDOW = 0x08000000

    def on_created(self, event):
        if not event.is_directory:
            file_path = event.src_path
            _, ext = os.path.splitext(file_path.lower())
            if ext in IGNORED_PATTERNS or "Quarantine" in file_path:
                return

            print(f"\n[!] New file detected: {file_path}")
            # Dispatch to worker thread to avoid blocking Watchdog event queue
            threading.Thread(target=self._delayed_scan, args=(file_path,), daemon=True).start()

    def _delayed_scan(self, file_path):
        # Brief pause to allow writing process to complete file handle flush
        time.sleep(0.5)
        if os.path.exists(file_path):
            self.trigger_scan(file_path)

    def trigger_scan(self, file_path):
        if not os.path.exists(self.script_path):
            print(f"[-] Error: Could not locate scan engine at {self.script_path}")
            return

        # Run silent scan without popping up disruptive console windows
        subprocess.Popen(
            [self.executable, self.script_path, "--no-pause", file_path],
            creationflags=self.CREATE_NO_WINDOW,
            cwd=self.current_dir
        )

if __name__ == "__main__":
    os.system('color 0e')
    print("[*] JARVIS: Multi-vector Surveillance active...")
    event_handler = SecurityHandler()
    observer = Observer()

    active_paths = 0
    for path in WATCH_PATHS:
        if os.path.exists(path):
            observer.schedule(event_handler, path, recursive=False)
            print(f"[*] Monitoring Sector: {path}")
            active_paths += 1

    if active_paths > 0:
        observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
