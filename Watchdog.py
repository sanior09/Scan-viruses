import psutil
import time
import os
import sys
import subprocess
import logging

LOG_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scan_history.log")
logging.basicConfig(
    filename=LOG_FILE_PATH, level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s', encoding='utf-8'
)

SCRIPTS_TO_MONITOR = ["RealTimeMonitor.py", "USBWatcher.py", "BehavioralMonitor.py", "RegistrySurveillance.py", "Dashboard.py"]
DASHBOARD_SHUTDOWN_FLAG = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".dashboard_shutdown_flag")
SURVEILLANCE_ACTIVE_FLAG = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".surveillance_active_flag")

def is_script_running(script_name):
    current_pid = os.getpid()
    for proc in psutil.process_iter(['pid', 'cmdline']):
        try:
            if proc.info['pid'] == current_pid:
                continue
            cmdline = proc.info.get('cmdline')
            if cmdline and any(script_name.lower() in arg.lower() for arg in cmdline):
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return False

def start_script(script_name):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(current_dir, script_name)
    if not os.path.exists(script_path):
        return
        
    print(f"[*] Watchdog: Initiating recovery protocol for {script_name}...")
    logging.warning(f"[WATCHDOG] Recovering terminated module: {script_name}.")
    
    flags = subprocess.CREATE_NEW_CONSOLE
    if script_name != "Dashboard.py":
        flags = 0x08000000  # CREATE_NO_WINDOW for silent background cores
        
    subprocess.Popen([sys.executable, script_path], creationflags=flags, cwd=current_dir)

def watchdog_monitor():
    os.system('color 0e')
    print("[*] JARVIS: Self-Defense Protocol (Watchdog) Active...")
    logging.info("[SYSTEM] Watchdog supervisor protocol initiated.")

    try:
        while True:
            # If shutdown signal is flagged by user closing the HUD, terminate supervisor gracefully
            if os.path.exists(DASHBOARD_SHUTDOWN_FLAG):
                print("[*] Watchdog: Dashboard shutdown signal confirmed. Terminating supervisor.")
                logging.info("[SYSTEM] Watchdog terminated via dashboard shutdown signal.")
                sys.exit(0)
                
            surveillance_active = os.path.exists(SURVEILLANCE_ACTIVE_FLAG)
            for script in SCRIPTS_TO_MONITOR:
                # Only keep surveillance daemons alive if the master surveillance shield is active
                if script != "Dashboard.py" and not surveillance_active:
                    continue
                if not is_script_running(script):
                    start_script(script)
            time.sleep(15)
    except KeyboardInterrupt:
        print("\n[*] Watchdog Protocol Deactivated.")
        logging.info("[SYSTEM] Watchdog supervisor protocol halted.")
    except Exception as e:
        logging.critical(f"Watchdog crashed: {e}", exc_info=True)

if __name__ == "__main__":
    watchdog_monitor()
