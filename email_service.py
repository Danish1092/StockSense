import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER')
        self.smtp_port = int(os.getenv('SMTP_PORT'))
        self.sender_email = os.getenv('SENDER_EMAIL')
        self.sender_password = os.getenv('EMAIL_PASSWORD')

    def send_verification_email(self, to_email, verification_code):
        subject = "Verify Your StockSense Account"
        body = f"""
        Welcome to StockSense!
        
        Your verification code is: {verification_code}
        
        This code will expire in 10 minutes.
        """
        self._send_email(to_email, subject, body)

    def send_password_reset_email(self, to_email, reset_code):
        subject = "Reset Your StockSense Password"
        body = f"""
        You requested to reset your password.
        
        Your password reset code is: {reset_code}
        
        This code will expire in 10 minutes.
        If you didn't request this, please ignore this email.
        """
        self._send_email(to_email, subject, body)

    def _send_email(self, to_email, subject, body):
        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)
            server.quit()
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
