import random
import string
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- MOCK OTP FOR TESTING ---
# We will use this so we don't have to send a real email in tests
MOCK_OTP = "123456"

def generate_otp(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))

def send_otp(email: str) -> str:
    otp = generate_otp()
    
    # --- MOCK CONSOLE SENDER ---
    # In a real app, you would remove this and enable the SMTP sender
    print("="*50)
    print(f"--- MOCK OTP SENDER ---")
    print(f"TO: {email}")
    print(f"OTP: {otp}")
    print("="*50)
    # For CI/CD and automated tests, we use a predictable OTP
    if os.environ.get("PYTHONPATH") == ".": # Simple check if we're in test mode
        return MOCK_OTP
    # --- END MOCK ---
    
    # --- REAL SMTP SENDER (Example) ---
    # Uncomment and configure .env to use
    """
    try:
        host = os.environ["EMAIL_HOST"]
        port = int(os.environ["EMAIL_PORT"])
        user = os.environ["EMAIL_USER"]
        password = os.environ["EMAIL_PASS"]
        sender = os.environ["EMAIL_FROM"]

        message = MIMEMultipart("alternative")
        message["Subject"] = f"Your OTP is {otp}"
        message["From"] = sender
        message["To"] = email
        
        text = f"Hi,\n\nYour OTP for Cab Aggregator is: {otp}\n\nThis is valid for 5 minutes."
        part1 = MIMEText(text, "plain")
        message.attach(part1)

        with smtplib.SMTP(host, port) as server:
            server.starttls()
            server.login(user, password)
            server.sendmail(sender, email, message.as_string())
        print(f"Successfully sent OTP to {email}")
    except Exception as e:
        print(f"Error: Could not send email. {e}")
        # Fallback to console print if email fails
        print(f"Fallback OTP for {email}: {otp}")
    """
    return otp