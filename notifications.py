import os
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List
import time

from prediction_lstm import predict_price_lstm
from prediction_xgb import predict_price_xgb
from config import supabase


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Company list (same as routes.py)
COMPANIES = [
    'TCS.ns', 'RELIANCE.ns', 'INFY.ns', 'HDFCBANK.ns', 'ICICIBANK.ns',
    'SBIN.ns', 'ITC.ns', 'LT.ns', 'AXISBANK.ns', 'BHARTIARTL.ns'
]


def _send_html_email(recipients: List[str], subject: str, html_body: str) -> bool:
    """Send a single HTML email to a list of recipients using SMTP credentials from env."""
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    sender = os.getenv('SENDER_EMAIL')
    password = os.getenv('EMAIL_PASSWORD')

    if not (smtp_server and smtp_port and sender and password and recipients):
        logging.error('SMTP configuration or recipients missing; cannot send email')
        return False

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender
    # Do not expose full recipient list in header; put first recipient or sender
    msg['To'] = recipients[0] if recipients else sender
    msg.attach(MIMEText(html_body, 'html'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=20)
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, recipients, msg.as_string())
        server.quit()
        logging.info('Email sent to %d recipients', len(recipients))
        return True
    except Exception as e:
        logging.exception('Failed to send email: %s', e)
        return False


def _build_email_html(company: str, predicted_price: float, pct_change: float, base_url: str) -> str:
    link = f"{base_url.rstrip('/')}/info?company={company}"
    html = f"""
    <html>
      <body style="font-family:Arial,Helvetica,sans-serif;background:#0b1220;color:#e6fff3;padding:20px;">
        <div style="max-width:700px;margin:0 auto;background:#071018;padding:24px;border-radius:12px;border:1px solid #153f2e;">
          <h2 style="color:#7ef0a3;margin:0 0 12px;">Stock Alert: {company}</h2>
          <p style="margin:0 0 12px;color:#d7ffe6;">Our models predict a price of <strong style="color:#b7ffd0">{predicted_price:.2f}</strong> for <strong>{company}</strong> — estimated change <strong style="color:#b7ffd0">{pct_change:.2f}%</strong> vs latest close.</p>
          <p style="margin:0 0 16px;color:#bfeed4;">Click below to view detailed company information and predictions on StockSense.</p>
          <a href="{link}" style="display:inline-block;padding:12px 18px;background:#1aa97a;color:#021012;border-radius:8px;text-decoration:none;font-weight:600;">View {company} details</a>
          <hr style="margin:18px 0;border:none;border-top:1px solid #0f3828;">
          <p style="font-size:12px;color:#98d9b6;margin:0;">You are receiving this email because you're registered with StockSense. Manage notifications in your account.</p>
        </div>
      </body>
    </html>
    """
    return html


def predict_and_select(companies: List[str], days: int = 7, model_choice: int = 1):
    """Predict prices for `companies`. Return a list of dicts with symbol, last_close, pred_last, pct_change."""
    results = []
    for c in companies:
        try:
            if model_choice == 1:
                r = predict_price_lstm(c, days=days, period='1y')
            else:
                r = predict_price_xgb(c, days=days, period='1y')

            preds = r.get('predictions') or []
            if not preds:
                logging.info('No predictions for %s', c)
                continue

            pred_last = float(preds[-1]['y'])
            last_close = float(r.get('last_close', preds[0]['y']))
            pct = (pred_last - last_close) / last_close * 100 if last_close else 0.0

            results.append({'symbol': c, 'last_close': last_close, 'pred_last': pred_last, 'pct_change': pct})
            logging.info('Predicted %s -> last_close=%.2f pred_last=%.2f pct=%.2f%%', c, last_close, pred_last, pct)
        except FileNotFoundError as e:
            logging.warning('Model files missing for %s: %s', c, e)
        except Exception as e:
            logging.exception('Prediction failed for %s: %s', c, e)

    # Select those with positive pct_change and sort descending
    increasing = [r for r in results if r['pct_change'] > 0]
    increasing.sort(key=lambda x: x['pct_change'], reverse=True)
    return increasing


def fetch_user_emails() -> List[str]:
    try:
        result = supabase.table('users').select('email').execute()
        users = result.data or []
        emails = [u.get('email') for u in users if u.get('email')]
        logging.info('Fetched %d user emails from Supabase', len(emails))
        return emails
    except Exception as e:
        logging.exception('Failed to fetch user emails: %s', e)
        return []


def run_notifications(days: int = 7, model_choice: int = 1, max_companies: int = 3, base_url: str = None):
    """Main entrypoint: predict all companies, pick top increasing ones and email users (max `max_companies`)."""
    if base_url is None:
        base_url = os.getenv('APP_BASE_URL', 'http://localhost:5000')

    logging.info('Starting notifications run: days=%d model=%d', days, model_choice)

    increasing = predict_and_select(COMPANIES, days=days, model_choice=model_choice)
    if not increasing:
        logging.info('No increasing stocks detected; nothing to send')
        return

    to_send = increasing[:max_companies]
    recipients = fetch_user_emails()
    if not recipients:
        logging.info('No recipients; aborting email send')
        return

    for item in to_send:
        company = item['symbol']
        pred = item['pred_last']
        pct = item['pct_change']
        subject = f"StockSense Alert: {company} predicted to rise {pct:.2f}%"
        html = _build_email_html(company, pred, pct, base_url)

        try:
            ok = _send_html_email(recipients, subject, html)
            if ok:
                logging.info('Notification sent for %s', company)
            else:
                logging.error('Failed to send notification for %s', company)
        except Exception as e:
            logging.exception('Error sending notification for %s: %s', company, e)


if __name__ == '__main__':
    # Allow manual testing of the notifications runner
    run_notifications()
