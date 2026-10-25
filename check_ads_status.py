import os
import sys
import urllib.request
import json

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
CLIENT_ID = "ca-pub-9735167683544437"
TARGET_URL = "https://wofga.github.io/"

def send_telegram_alert(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[Alert] Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID.")
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = json.dumps({
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            print("[Alert] Telegram message sent successfully! Status:", resp.status)
            return True
    except Exception as e:
        print("[Alert] Failed to send Telegram message:", e)
        return False

def check_ads_status():
    print(f"[Check] Checking {TARGET_URL} AdSense status...")
    req = urllib.request.Request(TARGET_URL, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode("utf-8", errors="ignore")
    
    has_script = CLIENT_ID in html
    has_units = html.count(f'data-ad-client="{CLIENT_ID}"')
    
    print(f"[Check] Script present: {has_script}, Units count: {has_units}")
    return has_script and has_units >= 3

if __name__ == "__main__":
    ok = check_ads_status()
    print("[Check] Result:", "OK" if ok else "FAIL")
