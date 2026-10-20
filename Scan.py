import os
import sys
import hashlib
import json
import logging
import zipfile
import concurrent.futures
import time
import shutil
import importlib
import threading
import math
from collections import Counter
from datetime import datetime
import psutil

import sqlite3

def calculate_entropy(data):
    """Calculates Shannon Entropy of a byte buffer (0.0 to 8.0)."""
    if not data:
        return 0.0
    length = len(data)
    counts = Counter(data)
    entropy = 0.0
    for count in counts.values():
        p_x = count / length
        entropy -= p_x * math.log2(p_x)
    return entropy

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE_PATH = os.path.join(BASE_DIR, "scan_history.log")
WHITELIST_DB_PATH = os.path.join(BASE_DIR, ".jarvis_whitelist.db")
LEGACY_WHITELIST_PATH = os.path.join(BASE_DIR, ".jarvis_whitelist.json")
QUARANTINE_DIR = os.path.join(BASE_DIR, "Quarantine")
SIGNATURES_DIR = os.path.join(BASE_DIR, "signatures")
os.makedirs(QUARANTINE_DIR, exist_ok=True)

try:
    pefile = importlib.import_module("pefile")
except ImportError:
    pefile = None

try:
    yara = importlib.import_module("yara")
except ImportError:
    yara = None

logging.basicConfig(
    filename=LOG_FILE_PATH,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

SKIP_EXTENSIONS = {'.mp4', '.mkv', '.mp3', '.jpg', '.jpeg', '.png', '.gif', '.iso', '.vmdk', 
                   '.avi', '.mov', '.wav', '.flac', '.ogg', '.webm', '.mpeg', '.mpg', '.bmp', 
                   '.tiff', '.webp', '.ico', '.svg', '.woff', '.woff2', '.ttf', '.jarvis_locked'}

JARVIS_CORE_FILES = ['scan.py', 'dashboard.py', 'watchdog.py', 'behavioralmonitor.py', 
                     'usbwatcher.py', 'registrysurveillance.py', 'realtimemonitor.py', 'ai_analyzer.py']

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

DEFAULT_EXCLUDED_DIRS = {
    '$recycle.bin', 'system volume information', 'winsxs',
    'package cache', 'msocache', '.git', 'node_modules', '__pycache__'
}


class WhitelistManager:
    """High-performance SQLite-backed Whitelist Manager for instant 0.00ms lookups and zero JSON overhead."""
    def __init__(self):
        self._lock = threading.Lock()
        self._pending_inserts = []
        self._conn = None
        self._init_db()

    def _init_db(self):
        try:
            self._conn = sqlite3.connect(WHITELIST_DB_PATH, check_same_thread=False)
            with self._conn:
                self._conn.execute("PRAGMA journal_mode = WAL")
                self._conn.execute("PRAGMA synchronous = NORMAL")
                self._conn.execute(
                    "CREATE TABLE IF NOT EXISTS whitelist (path TEXT PRIMARY KEY, size INTEGER, mtime REAL)"
                )
            
            # Check for legacy JSON migration if DB is newly created
            migration_marker = os.path.join(BASE_DIR, ".whitelist_migrated")
            if os.path.exists(LEGACY_WHITELIST_PATH) and not os.path.exists(migration_marker):
                self._migrate_legacy(migration_marker)
        except Exception as e:
            logging.error(f"Whitelist database initialization failure: {e}")

    def _migrate_legacy(self, marker_path):
        try:
            with open(LEGACY_WHITELIST_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
            rows = [(k, v.get('size', 0), v.get('mtime', 0.0)) for k, v in data.items()]
            with self._conn:
                self._conn.executemany("INSERT OR REPLACE INTO whitelist VALUES (?, ?, ?)", rows)
            with open(marker_path, 'w') as f:
                f.write("migrated")
            logging.info(f"Successfully migrated {len(rows)} whitelist records to SQLite database.")
        except Exception as e:
            logging.error(f"Legacy whitelist migration error: {e}")

    def is_safe(self, file_path, stat=None):
        if not self._conn:
            return False
        try:
            if stat is None:
                stat = os.stat(file_path)
            with self._lock:
                cur = self._conn.cursor()
                cur.execute("SELECT size, mtime FROM whitelist WHERE path = ?", (file_path,))
                row = cur.fetchone()
            if row:
                cached_size, cached_mtime = row
                if stat.st_size == cached_size and abs(stat.st_mtime - cached_mtime) < 0.001:
                    return True
        except Exception:
            pass
        return False

    def add(self, file_path, stat=None):
        try:
            if stat is None:
                stat = os.stat(file_path)
            with self._lock:
                self._pending_inserts.append((file_path, stat.st_size, stat.st_mtime))
                if len(self._pending_inserts) >= 500:
                    self._flush()
        except Exception:
            pass

    def _flush(self):
        if self._conn and self._pending_inserts:
            try:
                with self._conn:
                    self._conn.executemany(
                        "INSERT OR REPLACE INTO whitelist VALUES (?, ?, ?)", self._pending_inserts
                    )
                self._pending_inserts.clear()
            except Exception as e:
                logging.error(f"Whitelist flush failure: {e}")

    def save(self):
        with self._lock:
            self._flush()

class PEAnalyzer:
    def __init__(self):
        self.executable_extensions = {'.exe', '.dll', '.sys', '.scr', '.cpl', '.ocx', '.efi'}
        
        # Categorized Threat Vectors
        self.critical_categories = {
            "Process Injection & Hollowing": [
                b"VirtualAllocEx", b"WriteProcessMemory", b"CreateRemoteThread", 
                b"NtUnmapViewOfSection", b"VirtualProtectEx", b"SetThreadContext", 
                b"QueueUserAPC"
            ],
            "Anti-Analysis & Sandbox Evasion": [
                b"CheckRemoteDebuggerPresent", b"NtQueryInformationProcess"
            ],
            "Stealth Hooking & Keylogging": [
                b"SetWindowsHookExA", b"SetWindowsHookExW", b"GetAsyncKeyState"
            ],
            "Remote Dropper & Shell": [
                b"URLDownloadToFileA", b"URLDownloadToFileW", b"WinExec"
            ],
            "Ransomware Cryptography": [
                b"CryptEncrypt", b"BCryptEncrypt"
            ]
        }
        
        # Known packer signatures in section names
        self.packed_section_names = {
            'upx0', 'upx1', 'upx2', '.aspack', '.adata', 'mpress1', 'mpress2', 
            '.themida', 'pecompact2', '.nsp0', '.tsu', '.vmp0', '.vmp1'
        }

    def analyze(self, file_path, first_bytes=None):
        if not pefile:
            return None

        # Pre-filter: only analyze PE files that begin with the DOS MZ signature
        if first_bytes is not None:
            if not first_bytes.startswith(b"MZ"):
                return None
        else:
            _, ext = os.path.splitext(file_path.lower())
            if ext not in self.executable_extensions:
                return None
            try:
                with open(file_path, 'rb') as f:
                    if f.read(2) != b"MZ":
                        return None
            except Exception:
                return None

        try:
            # Fast load headers and parse section headers & Import Directory
            pe = pefile.PE(file_path, fast_load=True)
            pe.parse_data_directories(directories=[
                pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_IMPORT']
            ])
            
            detected_threats = []
            matched_apis = []
            
            # 1. Section Inspection (Packing & Entropy)
            max_section_entropy = 0.0
            found_packed_section = None
            if hasattr(pe, 'sections'):
                for section in pe.sections:
                    try:
                        sec_name = section.Name.decode('utf-8', errors='ignore').strip('\x00').lower()
                        sec_entropy = section.get_entropy()
                        if sec_entropy > max_section_entropy:
                            max_section_entropy = sec_entropy
                        if sec_name in self.packed_section_names:
                            found_packed_section = sec_name
                    except Exception:
                        pass

            # 2. Categorized API Import Analysis
            category_hits = {}
            if hasattr(pe, 'DIRECTORY_ENTRY_IMPORT'):
                for entry in pe.DIRECTORY_ENTRY_IMPORT:
                    for imp in entry.imports:
                        if imp.name:
                            for cat, apis in self.critical_categories.items():
                                if any(api in imp.name for api in apis):
                                    api_str = imp.name.decode('utf-8', errors='ignore')
                                    matched_apis.append(api_str)
                                    category_hits.setdefault(cat, []).append(api_str)

            pe.close()

            # 3. High-Confidence Threat Decision Rules
            # Rule A: Process Injection & Hollowing (High risk)
            inj_hits = category_hits.get("Process Injection & Hollowing", [])
            has_alloc = any("VirtualAllocEx" in a for a in inj_hits)
            has_write = any("WriteProcessMemory" in a for a in inj_hits)
            has_remote_thread = any("CreateRemoteThread" in a for a in inj_hits)
            has_unmap = any("NtUnmapViewOfSection" in a for a in inj_hits)
            
            if (has_alloc and has_write and (has_remote_thread or has_unmap)) or len(inj_hits) >= 3:
                apis = ", ".join(inj_hits[:3])
                detected_threats.append(f"Process Injection Vector ({apis})")

            # Rule B: Remote Dropper + Execution
            drop_hits = category_hits.get("Remote Dropper & Shell", [])
            if any("URLDownloadToFile" in a for a in drop_hits) and any("WinExec" in a for a in drop_hits):
                apis = ", ".join(drop_hits[:2])
                detected_threats.append(f"Remote Dropper & Shell Vector ({apis})")

            # Rule C: Stealth Keylogger
            key_hits = category_hits.get("Stealth Hooking & Keylogging", [])
            if any("GetAsyncKeyState" in a for a in key_hits) and any("SetWindowsHookEx" in a for a in key_hits):
                apis = ", ".join(key_hits[:3])
                detected_threats.append(f"Stealth Keylogger / Hooking Vector ({apis})")

            # Rule D: Ransomware Cryptography + Extreme Entropy
            if "Ransomware Cryptography" in category_hits and max_section_entropy >= 7.85:
                apis = ", ".join(category_hits["Ransomware Cryptography"][:2])
                detected_threats.append(f"Ransomware Encryption Vector (Entropy {max_section_entropy:.2f}, {apis})")

            # Rule E: Known Threat Packer + Suspicious APIs
            if found_packed_section and len(matched_apis) >= 2 and max_section_entropy >= 7.6:
                detected_threats.append(f"Known Threat Packer ({found_packed_section.upper()}, Entropy {max_section_entropy:.2f})")

            if detected_threats:
                return " | ".join(detected_threats)

        except Exception:
            pass
        return None

class HeuristicEngine:
    def __init__(self):
        self.buffer_chunk_size = 1048576  # 1MB
        self.overlap_size = 128
        
        self.known_bad_hashes = self._load_bad_hashes()
        self.suspicious_strings = [
            (b"powershell" + b" -ExecutionPolicy Bypass", "Suspicious PowerShell bypass flag"),
            (b"powershell" + b" -exec bypass", "Suspicious PowerShell bypass flag"),
            (b"powershell" + b" -w hidden", "Hidden PowerShell execution window"),
            (b"eval(base" + b"64_decode", "Obfuscated payload execution (eval base64)"),
            (b"frombase" + b"64string", "Base64 payload deobfuscation routine"),
            (b"vssadmin" + b" delete shadows", "Ransomware shadow copy deletion script"),
            (b"wmic" + b" shadowcopy delete", "Ransomware shadow copy deletion script"),
            (b"wbadmin" + b" delete catalog", "Ransomware backup catalog deletion"),
            (b"bcdedit" + b" /set {default} recoveryenabled no", "Ransomware recovery disabling script"),
            (b"bypass" + b" uac", "UAC bypass utility string"),
            (b"WScript" + b".Shell", "Suspicious Windows Scripting Host object creation"),
            (b"Scripting.FileSystemObject", "Suspicious Scripting File System Access"),
            (b"mshta.exe", "Suspicious Microsoft HTML Application execution"),
            (b"certutil" + b" -urlcache", "Certutil living-off-the-land downloader"),
            (bytes([88, 53, 79, 33, 80, 37, 64, 65, 80, 91, 52, 92, 92, 80, 90, 88, 53, 52, 40, 80, 94, 41, 55, 67, 67, 41, 55, 125, 36, 69, 73, 67, 65, 82, 45, 83, 84, 65, 78, 68, 65, 82, 68, 45, 65, 78, 84, 73, 86, 73, 82, 85, 83, 45, 84, 69, 83, 84, 45, 70, 73, 76, 69, 33, 36, 72, 43, 72, 42]), "EICAR Standard Test Signature")
        ]
        self.yara_rules = self._compile_yara()
        
    def _load_bad_hashes(self):
        hashes = set()
        hash_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "signatures", "bad_hashes.txt")
        if os.path.exists(hash_file):
            try:
                with open(hash_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            hashes.add(line.lower())
                logging.info(f"Loaded {len(hashes)} bad hashes from signature database.")
            except Exception as e:
                logging.error(f"Failed to load hash database: {e}")
        return hashes

    def _compile_yara(self):
        if yara is None:
            return None
            
        sig_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "signatures")
        yar_files = {}
        if os.path.exists(sig_dir):
            for f in os.listdir(sig_dir):
                if f.endswith('.yar'):
                    yar_files[f] = os.path.join(sig_dir, f)
        
        if not yar_files:
            logging.warning("No YARA rules found in signatures directory.")
            return None
            
        try:
            compiled_rules = yara.compile(filepaths=yar_files)
            logging.info(f"Successfully compiled {len(yar_files)} YARA rule files.")
            return compiled_rules
        except Exception as e:
            logging.error(f"YARA compilation failed: {e}")
            return None

    def scan_bytes(self, raw_data):
        for pat, desc in self.suspicious_strings:
            if pat in raw_data:
                return f"Found suspicious string: {desc}"
        return None

    def check_script_heuristics(self, ext, content):
        if ext not in {'.bat', '.cmd', '.ps1', '.vbs', '.js', '.hta', '.wsf', '.reg'}:
            return None
            
        content_lower = content.lower()
        
        # 1. Obfuscated PowerShell / IEX download cradle
        if b"invoke-expression" in content_lower and (b"downloadstring" in content_lower or b"frombase64" in content_lower):
            return "Malicious Script: PowerShell Download & Execute cradle"
            
        # 2. Ransomware shadow destruction
        if b"vssadmin" in content_lower and b"delete" in content_lower and b"shadows" in content_lower:
            return "Malicious Script: Ransomware Shadow Copy Destruction"

        # 3. Encoded command or hidden window
        if b"-encodedcommand" in content_lower or b"-enc " in content_lower:
            return "Malicious Script: Obfuscated Base64 Encoded PowerShell"

        # 4. Living-off-the-land Downloader
        if b"certutil" in content_lower and (b"-urlcache" in content_lower or b"-decode" in content_lower):
            return "Malicious Script: Certutil Living-off-the-land Downloader/Decoder"
            
        # 5. Scheduled Persistence / Registry Run Keys
        if b"reg add" in content_lower and (b"\\run" in content_lower or b"\\runonce" in content_lower):
            return "Suspicious Script: Registry Persistence Autostart Insertion"
            
        return None

    def yara_scan(self, file_path, data=None):
        if self.yara_rules:
            try:
                if data is not None:
                    matches = self.yara_rules.match(data=data, timeout=5)
                else:
                    matches = self.yara_rules.match(filepath=file_path, timeout=5)
                if matches:
                    detected_rules = ", ".join([match.rule for match in matches])
                    return f"YARA detection match: {detected_rules}"
            except Exception:
                pass
        return None


class ScanEngine:
    def __init__(self):
        self.whitelist = WhitelistManager()
        self.pe_analyzer = PEAnalyzer()
        self.heuristic = HeuristicEngine()
        
    def scan_file(self, file_path):
        _, ext = os.path.splitext(file_path.lower())
        if ext in SKIP_EXTENSIONS:
            return False, file_path, None, False

        try:
            # Skip signature files and core modules
            abs_path = os.path.abspath(file_path).lower()
            if abs_path.startswith(os.path.abspath(SIGNATURES_DIR).lower()):
                return False, file_path, None, True

            filename = os.path.basename(file_path).lower()
            if any(core.split('.')[0] in filename for core in JARVIS_CORE_FILES):
                return False, file_path, None, True

            stat = os.stat(file_path)
            file_size = stat.st_size

            # Fast in-memory Whitelist check
            if self.whitelist.is_safe(file_path, stat=stat):
                return False, file_path, None, True
            
            if file_size > MAX_FILE_SIZE or file_size == 0:
                return False, file_path, None, False

            # Archive inspection (.zip)
            if ext == '.zip':
                try:
                    with zipfile.ZipFile(file_path, 'r') as z:
                        for member in z.namelist():
                            if member.endswith('/'): continue
                            with z.open(member) as f:
                                content = f.read(MAX_FILE_SIZE)
                                finding = self.heuristic.scan_bytes(content)
                                if finding:
                                    return True, file_path, f"Zip infected payload ({member}): {finding}", False
                except Exception:
                    pass

            # SINGLE-PASS READ: Open file ONCE
            with open(file_path, 'rb') as f:
                first_chunk = f.read(self.heuristic.buffer_chunk_size)
                if not first_chunk:
                    return False, file_path, None, False

                hasher_md5 = hashlib.md5(first_chunk)
                hasher_sha256 = hashlib.sha256(first_chunk)

                # 1. Portable Executable IAT & Section check (only if file starts with MZ)
                pe_finding = None
                if first_chunk.startswith(b"MZ"):
                    pe_finding = self.pe_analyzer.analyze(file_path, first_bytes=first_chunk)
                    if pe_finding:
                        return True, file_path, pe_finding, False

                # 2. Suspicious string scan on first chunk
                string_finding = self.heuristic.scan_bytes(first_chunk)
                if string_finding:
                    return True, file_path, string_finding, False

                # 3. Script Deobfuscation & Heuristics
                script_finding = self.heuristic.check_script_heuristics(ext, first_chunk)
                if script_finding:
                    return True, file_path, script_finding, False

                # 4. Stream remaining chunks if file exceeds 1MB for full hashing & deep string scan
                if file_size > len(first_chunk):
                    overlap = first_chunk[-self.heuristic.overlap_size:]
                    while True:
                        chunk = f.read(self.heuristic.buffer_chunk_size)
                        if not chunk:
                            break
                        hasher_md5.update(chunk)
                        hasher_sha256.update(chunk)
                        full_block = overlap + chunk
                        string_finding = self.heuristic.scan_bytes(full_block)
                        if string_finding:
                            return True, file_path, string_finding, False
                        overlap = chunk[-self.heuristic.overlap_size:] if len(chunk) >= self.heuristic.overlap_size else chunk

                # 5. Full file Hash check (MD5 & SHA256 against signature database)
                md5_res = hasher_md5.hexdigest().lower()
                sha256_res = hasher_sha256.hexdigest().lower()
                if md5_res in self.heuristic.known_bad_hashes or sha256_res in self.heuristic.known_bad_hashes:
                    return True, file_path, f"Known threat signature matching hash ({md5_res[:8]}...)", False

            # 6. YARA Rule matching (in-memory for files <= 1MB, disk for larger)
            yara_data = first_chunk if file_size <= len(first_chunk) else None
            yara_finding = self.heuristic.yara_scan(file_path, data=yara_data)
            if yara_finding:
                return True, file_path, yara_finding, False

            # 7. Shannon Entropy & AI Cognitive Inspection for Zero-Day threats
            if ext in {'.exe', '.dll', '.scr', '.ps1', '.vbs', '.bat', '.cmd'} and file_size > 512:
                entropy = calculate_entropy(first_chunk)
                
                # High entropy alone in PE files is often legitimate compression (UPX, VSTs, modern DLLs)
                # Only flag as cryptor if extreme entropy (>= 7.85) AND accompanied by suspicious indicators
                if entropy >= 7.85 and ext in {'.exe', '.dll', '.scr'} and (pe_finding or string_finding):
                    return True, file_path, f"Zero-Day Cryptor/Ransomware (Extreme Entropy: {entropy:.2f}/8.00)", False

                # If entropy is elevated or ambiguous, consult Gemini AI Cognitive Core if online
                if (entropy >= 7.30 and (pe_finding or string_finding)) or (string_finding and "Suspicious" in string_finding):
                    try:
                        from AI_Analyzer import send_to_gemini_for_analysis
                        event_data = {
                            "event_type": "DEEP_FILE_HEURISTIC",
                            "timestamp": datetime.now().isoformat(),
                            "source": "ScanEngine.DeepAnalyzer",
                            "details": {
                                "filename": filename,
                                "entropy": round(entropy, 2),
                                "size_bytes": file_size,
                                "extension": ext,
                                "preliminary_indicator": string_finding or "Elevated Shannon Entropy"
                            }
                        }
                        ai_assessment = send_to_gemini_for_analysis(event_data)
                        if ai_assessment and ai_assessment.get("threat_level") in ("CRITICAL", "SUSPICIOUS") and ai_assessment.get("action") == "SUSPEND":
                            return True, file_path, f"AI Cognitive Core [{ai_assessment.get('threat_level')}]: {ai_assessment.get('analysis')}", False
                    except Exception:
                        pass

            # Passed all inspections - add to whitelist
            self.whitelist.add(file_path, stat=stat)
            return False, file_path, None, False

        except (PermissionError, OSError):
            return False, file_path, None, False

class QuarantineManager:
    @staticmethod
    def isolate_threat(file_path):
        try:
            os.makedirs(QUARANTINE_DIR, exist_ok=True)
            filename = os.path.basename(file_path)
            safe_name = f"{filename}.jarvis_locked"
            destination = os.path.join(QUARANTINE_DIR, safe_name)
            
            # Avoid collision if destination file already exists
            if os.path.exists(destination):
                base, ext = os.path.splitext(safe_name)
                safe_name = f"{base}_{int(time.time())}{ext}"
                destination = os.path.join(QUARANTINE_DIR, safe_name)

            # Move and isolate the file safely
            shutil.move(file_path, destination)
            logging.warning(f"[QUARANTINE] Threat isolated: {file_path} -> {destination}")
            return True
        except Exception as e:
            logging.error(f"[QUARANTINE_FAILED] Could not isolate {file_path}: {e}")
            # Safety guarantee: Never delete user/system files as fallback!
            return False

def scan_single_file(file_path, progress_callback=None):
    """Scans an individual file target and isolates it if malicious."""
    if not os.path.isfile(file_path):
        return 0
    engine = ScanEngine()
    is_threat, f_path, threat_desc, _ = engine.scan_file(file_path)
    if is_threat:
        quarantined = QuarantineManager.isolate_threat(f_path)
        status_msg = f"{threat_desc} [ISOLATED IN VAULT]" if quarantined else f"{threat_desc} [QUARANTINE FAILED]"
        if progress_callback:
            progress_callback(1, 1, f_path, status_msg)
        else:
            print(f"[!] THREAT SECURED: {f_path} - {status_msg}")
        logging.warning(f"SINGLE_FILE_SCAN THREAT: {f_path} - {status_msg}")
        engine.whitelist.save()
        return 1
    else:
        if progress_callback:
            progress_callback(1, 1, f_path, None)
        else:
            print(f"[+] File Clean: {f_path}")
        engine.whitelist.save()
        return 0

def scan_directory(directory_path, progress_callback=None, abort_event=None, excluded_dirs=None):
    engine = ScanEngine()
    threats_found = 0
    scanned_count = 0
    last_update_time = time.time()
    
    exclusions = set(DEFAULT_EXCLUDED_DIRS)
    if excluded_dirs:
        exclusions.update(d.lower() for d in excluded_dirs)

    quarantine_norm = os.path.abspath(QUARANTINE_DIR).lower()
    signatures_norm = os.path.abspath(SIGNATURES_DIR).lower()

    # Pre-traverse directory structure to obtain accurate total file count
    file_list = []
    try:
        for root, dirs, files in os.walk(directory_path, topdown=True):
            if abort_event and abort_event.is_set():
                break
            
            # Exclude unwanted directories in-place to avoid descending into them
            dirs[:] = [
                d for d in dirs 
                if d.lower() not in exclusions and 
                os.path.abspath(os.path.join(root, d)).lower() not in (quarantine_norm, signatures_norm)
            ]

            for f in files:
                if abort_event and abort_event.is_set():
                    break
                file_list.append(os.path.join(root, f))
    except Exception as e:
        logging.error(f"Error walking directory {directory_path}: {e}")

    total_files = len(file_list)
    if total_files == 0:
        return 0

    total_cores = os.cpu_count() or 4
    # Reserve at least 1-2 CPU cores so the OS and GUI thread never suffer from GIL starvation
    balanced_workers = max(1, min(6, total_cores - 2 if total_cores > 3 else 2))

    with concurrent.futures.ThreadPoolExecutor(max_workers=balanced_workers) as executor:
        futures = set()
        
        def process_future(fut):
            nonlocal scanned_count, threats_found, last_update_time
            scanned_count += 1
            try:
                is_threat, file_path, threat_desc, skipped = fut.result()
            except Exception:
                return
            
            if is_threat:
                quarantined = QuarantineManager.isolate_threat(file_path)
                status_msg = f"{threat_desc} [ISOLATED IN VAULT]" if quarantined else f"{threat_desc} [QUARANTINE FAILED]"
                if quarantined: threats_found += 1
                
                if progress_callback:
                    progress_callback(scanned_count, total_files, file_path, status_msg)
                else:
                    logging.warning(f"THREAT HANDLED: {file_path} - {status_msg}")
            else:
                if progress_callback:
                    curr_time = time.time()
                    if curr_time - last_update_time > 0.05: # Max 20 updates per second
                        progress_callback(scanned_count, total_files, file_path, None)
                        last_update_time = curr_time

        try:
            for file_path in file_list:
                if abort_event and abort_event.is_set():
                    break
                fut = executor.submit(engine.scan_file, file_path)
                futures.add(fut)
                
                if len(futures) >= 1000:
                    done = {fu for fu in futures if fu.done()}
                    if not done:
                        done, _ = concurrent.futures.wait(futures, return_when=concurrent.futures.FIRST_COMPLETED)
                    futures.difference_update(done)
                    for d in done:
                        process_future(d)
        except Exception as e:
            logging.error(f"Error dispatching scan futures: {e}")
            
        for fut in concurrent.futures.as_completed(futures):
            if abort_event and abort_event.is_set():
                for f_rem in futures:
                    f_rem.cancel()
                break
            process_future(fut)

    engine.whitelist.save()
    return threats_found

def scan_active_processes(progress_callback=None, abort_event=None):
    threats_found = 0
    scanned_count = 0
    last_update_time = time.time()
    
    suspicious_cmd_tokens = [
        "powershell -exec bypass",
        "-executionpolicy bypass",
        "-encodedcommand",
        "downloadstring(",
        "vssadmin delete shadows",
        "wmic shadowcopy delete",
        "certutil -urlcache",
        "mshta http",
        "bitsadmin /transfer"
    ]
    
    suspicious_dirs = [
        os.environ.get('TEMP', '').lower(),
        os.path.join(os.environ.get('APPDATA', ''), 'Local', 'Temp').lower()
    ]
    
    try:
        procs = list(psutil.process_iter(['pid', 'name', 'exe', 'cmdline']))
    except Exception:
        procs = []
        
    total = len(procs)
    
    for p in procs:
        if abort_event and abort_event.is_set():
            break
        scanned_count += 1
        try:
            info = p.info
            pid = info.get('pid')
            name = (info.get('name') or '').lower()
            exe = (info.get('exe') or '')
            cmdline_list = info.get('cmdline') or []
            cmdline = " ".join(cmdline_list).lower()
            
            # Skip self, system idle, and core JARVIS processes
            if pid == os.getpid() or any(c in name for c in ['python', 'system', 'registry']):
                if any(core.split('.')[0] in cmdline for core in JARVIS_CORE_FILES):
                    if progress_callback:
                        progress_callback(scanned_count, total, f"PID {pid}: {name}", None)
                    continue

            threat_desc = None
            
            # 1. Suspicious command line arguments
            for token in suspicious_cmd_tokens:
                if token in cmdline:
                    threat_desc = f"Malicious Process Parameter ({token})"
                    break
                    
            # 2. Executable running from temporary / untrusted paths
            if not threat_desc and exe:
                exe_lower = exe.lower()
                for s_dir in suspicious_dirs:
                    if s_dir and exe_lower.startswith(s_dir) and not any(ok in exe_lower for ok in ['update', 'installer', 'chrome', 'teams', 'antigravity']):
                        threat_desc = f"Untrusted Binary running from Temp Directory: {os.path.basename(exe)}"
                        break
                        
            if threat_desc:
                action_note = "SUSPENDED"
                try:
                    p.suspend()
                    p.kill()
                    action_note = "TERMINATED & NEUTRALIZED"
                except Exception:
                    pass
                    
                if exe and os.path.exists(exe):
                    QuarantineManager.isolate_threat(exe)
                    
                threats_found += 1
                status_msg = f"{threat_desc} [{action_note}]"
                if progress_callback:
                    progress_callback(scanned_count, total, f"PID {pid}: {name}", status_msg)
                logging.warning(f"[MEMORY_SCAN_THREAT] PID: {pid} | Name: {name} | {status_msg}")
            else:
                if progress_callback:
                    curr_time = time.time()
                    if curr_time - last_update_time > 0.05:
                        progress_callback(scanned_count, total, f"PID {pid}: {name}", None)
                        last_update_time = curr_time
                        
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
            
    return threats_found

if __name__ == "__main__":
    no_pause = "--no-pause" in sys.argv
    is_interactive = sys.stdin.isatty() and not no_pause
    clean_args = [arg for arg in sys.argv[1:] if not arg.startswith("--")]

    if clean_args:
        target = clean_args[0]
        if target.lower() in ("--memory", "-m", "memory", "ram"):
            print("[*] JARVIS: Initiating active memory and running process scan...")
            threats = scan_active_processes()
            print(f"\n[*] Active memory scan complete. Threats eliminated: {threats}")
        elif os.path.isfile(target):
            print(f"[*] JARVIS: Initiating single-file security analysis on: {target}")
            threats = scan_single_file(target)
            print(f"\n[*] Single-file scan complete. Threats detected: {threats}")
        elif os.path.isdir(target):
            print(f"[*] JARVIS: Initiating standalone scan on sector: {target}")
            threats = scan_directory(target)
            print(f"\n[*] Scan complete. Threats eliminated: {threats}")
        else:
            print(f"[-] Target path not found: {target}")
    else:
        print("[*] J.A.R.V.I.S Scan Engine loaded. Awaiting parameters.")

    if is_interactive and "Dashboard" not in sys.executable:
        try:
            input("Press Enter to exit...")
        except (EOFError, KeyboardInterrupt):
            pass