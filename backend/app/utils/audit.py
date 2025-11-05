import csv, os
from datetime import datetime

AUDIT_FILE = "audit_log.csv"

def log_action(user_email: str, action: str, details: str = ""):
    exists = os.path.exists(AUDIT_FILE)
    try:
        with open(AUDIT_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not exists:
                writer.writerow(["timestamp", "user_email", "action", "details"])
            writer.writerow([datetime.utcnow().isoformat(), user_email, action, details])
    except PermissionError:
        print(f"AUDIT LOG FAILED: Could not write to {AUDIT_FILE}. Check file permissions.")
    except Exception as e:
        print(f"AUDIT LOG FAILED: {e}")