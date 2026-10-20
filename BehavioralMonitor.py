import psutil
import time
import os
import sys
import logging
from datetime import datetime
import json 
from AI_Analyzer import send_to_gemini_for_analysis

LOG_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scan_history.log")

logging.basicConfig(
    filename=LOG_FILE_PATH,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

class BehavioralEngine:
    def __init__(self):
        self.file_write_threshold = 300  
        self.process_lifespan_threshold = 10 
        self.network_check_interval = 30 
        # Excluded standard web ports (80, 443) to avoid flagging standard HTTPS/HTTP applications
        self.suspicious_ports = [21, 23, 445, 1337, 3389, 4444, 5555, 6667, 7777, 8888, 27017] 
        self.previous_io_data = {}
        self.last_network_check_time = time.time()
        self.whitelist_names = ["RealTimeMonitor.py", "USBWatcher.py", "Scan.py", "Dashboard.py", "BehavioralMonitor.py", "Watchdog.py", "RegistrySurveillance.py"]
        self.safe_binaries = ["explorer.exe", "svchost.exe", "code.exe", "antigravity.exe", "git.exe", "python.exe", "taskhostw.exe"]

    def is_whitelisted(self, cmdline, name, pid):
        if pid == os.getpid() or ("python" not in cmdline.lower() and "system" in name.lower()):
            return True
        cmdline_lower = cmdline.lower()
        name_lower = name.lower()
        if any(s.lower() in cmdline_lower for s in self.whitelist_names) or any(s.lower() in name_lower for s in self.whitelist_names):
            return True
        if any(safe in name_lower for safe in self.safe_binaries):
            return True
        return False

    def suspend_process(self, pid, reason="Unknown"):
        try:
            p = psutil.Process(pid)
            if p.status() == psutil.STATUS_RUNNING:
                p.suspend()
                alert_msg = f"[ACTION] Process (PID: {pid}, Name: {p.name()}) SUSPENDED due to: {reason}"
                print(f"\n[!!!] {alert_msg}")
                logging.critical(alert_msg)
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            logging.error(f"Failed to suspend process {pid}: {e}")
        return False

    def consult_ai_core(self, event_type, source, details):
        event_data = {
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "source": source,
            "details": details
        }
        print(f"\n[*] J.A.R.V.I.S: Routing anomaly to AI Cognitive Core for analysis...")
        result = send_to_gemini_for_analysis(event_data)
        
        # Only take disruptive action if AI explicitly validates CRITICAL threat
        if result and result.get("threat_level") == "CRITICAL" and result.get("action") == "SUSPEND":
            print(f"[!] J.A.R.V.I.S: AI confirms CRITICAL threat. Initiating auto-suspend sequence.")
            return True
        elif result and result.get("threat_level") == "SUSPICIOUS":
            print(f"[*] J.A.R.V.I.S: AI flagged behavior as SUSPICIOUS. Alert logged for observation.")
            return False
        else:
            print(f"[*] J.A.R.V.I.S: AI deems behavior SAFE or cognitive core offline. Neutral baseline maintained.")
            return False

    def analyze_process_cmdline(self, pid, name, cmdline, create_time):
        cmd_lower = cmdline.lower()
        if "powershell -exec bypass" in cmd_lower or ("cmd.exe /c" in cmd_lower and any(b in cmd_lower for b in ["bitsadmin", "certutil", "vssadmin"])):
            if (time.time() - create_time) < self.process_lifespan_threshold:
                alert_msg = f"[WARNING] Suspicious command line detected (PID: {pid}, Name: {name}): {cmdline}"
                print(f"\n[!] ALERT: {alert_msg}")
                logging.warning(alert_msg)
                
                details = {"pid": pid, "name": name, "cmdline": cmdline}
                should_suspend = self.consult_ai_core("SUSPICIOUS_CMDLINE", "BehavioralEngine", details)
                
                if should_suspend:
                    self.suspend_process(pid, "AI Confirmed: Malicious Command Line")

    def analyze_process_io(self, proc, pid, name):
        try:
            current_io = proc.io_counters()
            if current_io: 
                if pid in self.previous_io_data:
                    bytes_written_diff = current_io.write_bytes - self.previous_io_data[pid].write_bytes
                    files_written_diff = current_io.write_count - self.previous_io_data[pid].write_count

                    if files_written_diff > self.file_write_threshold:
                        alert_msg = f"[CRITICAL] Process (PID: {pid}, Name: {name}) performing anomalous rapid file writes ({files_written_diff})"
                        print(f"\n[!] ALERT: {alert_msg}")
                        logging.critical(alert_msg)
                        
                        details = {"pid": pid, "name": name, "files_written": files_written_diff, "bytes_written": bytes_written_diff}
                        should_suspend = self.consult_ai_core("RAPID_FILE_WRITE", "BehavioralEngine", details)
                        
                        if should_suspend:
                            self.suspend_process(pid, "AI Confirmed: Rapid file modification (Ransomware)")
                            
                self.previous_io_data[pid] = current_io
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            if pid in self.previous_io_data:
                del self.previous_io_data[pid]

    def analyze_network_connections(self):
        if (time.time() - self.last_network_check_time) > self.network_check_interval:
            for proc in psutil.process_iter(['pid', 'name', 'connections']):
                try:
                    pinfo = proc.info
                    pid = pinfo['pid']
                    name = pinfo['name']
                    
                    if self.is_whitelisted("", name, pid):
                        continue

                    for conn in (pinfo.get('connections') or []):
                        if conn.raddr and conn.status == psutil.CONN_ESTABLISHED:
                            if conn.raddr.port in self.suspicious_ports and not any(ok in name.lower() for ok in ["browser", "mail", "chrome", "edge", "firefox", "teams"]):
                                alert_msg = f"[WARNING] Process (PID: {pid}, Name: {name}) connected to suspicious port {conn.raddr.port} at {conn.raddr.ip}"
                                print(f"\n[!] ALERT: {alert_msg}")
                                logging.warning(alert_msg)
                                
                                details = {"pid": pid, "name": name, "remote_ip": conn.raddr.ip, "remote_port": conn.raddr.port}
                                should_suspend = self.consult_ai_core("SUSPICIOUS_NETWORK_CONN", "BehavioralEngine", details)
                                
                                if should_suspend:
                                    self.suspend_process(pid, f"AI Confirmed: Suspicious Network Connection to port {conn.raddr.port}")
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            self.last_network_check_time = time.time()

    def run(self):
        os.system('color 0e')
        print("[*] JARVIS: Behavioral Analysis Engine (Cognitive Core Integrated) Active...")
        logging.info("[SYSTEM] Behavioral Analysis Engine started.")

        try:
            while True:
                current_pids = set()
                for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
                    try:
                        pinfo = proc.info
                        pid = pinfo['pid']
                        name = pinfo['name'] or ''
                        cmdline_list = pinfo.get('cmdline')
                        cmdline = ' '.join(cmdline_list) if cmdline_list else ''
                        create_time = pinfo.get('create_time') or time.time()
                        current_pids.add(pid)
                        
                        if self.is_whitelisted(cmdline, name, pid):
                            continue

                        self.analyze_process_cmdline(pid, name, cmdline, create_time)
                        self.analyze_process_io(proc, pid, name)

                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        if pid in self.previous_io_data:
                            del self.previous_io_data[pid]
                        continue

                # Cleanup stale PIDs
                for pid in list(self.previous_io_data.keys()):
                    if pid not in current_pids:
                        del self.previous_io_data[pid]

                self.analyze_network_connections()
                time.sleep(5) 

        except KeyboardInterrupt:
            print("\n[*] Behavioral Analysis Engine Deactivated.")
            logging.info("[SYSTEM] Behavioral Analysis Engine stopped.")
        except Exception as e:
            print(f"\n[CRITICAL ERROR] Behavioral Monitor crashed: {e}")
            logging.critical(f"Behavioral Monitor crashed: {e}", exc_info=True)

if __name__ == "__main__":
    engine = BehavioralEngine()
    engine.run()
