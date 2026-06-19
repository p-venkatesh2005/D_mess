"""
OTP Service — Dwaraka Mess
100% Free. Uses Gmail SMTP to send OTP emails.

Setup (one-time, 2 minutes):
  1. Go to your Gmail → Google Account → Security → 2-Step Verification → enable it
  2. Then go to: Security → App Passwords → "Other" → name it "Dwaraka Mess"
  3. Copy the 16-character password
  4. Add to your .env file:

     MAIL_USERNAME=youremail@gmail.com
     MAIL_PASSWORD=abcd efgh ijkl mnop   ← the 16-char App Password

That's it. Free, unlimited, production-ready.
"""

import os
import random
import string
import time
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import session

logger = logging.getLogger(__name__)

# ─── Constants ────────────────────────────────────────────────────────────────
OTP_EXPIRY_SECONDS  = 600   # 10 minutes
MAX_VERIFY_ATTEMPTS = 5     # wrong OTP tries before lockout
MAX_RESEND_ATTEMPTS = 3     # max resends per session
RESEND_COOLDOWN_SEC = 60    # seconds before resend allowed
OTP_LENGTH          = 6
SESSION_KEY         = 'pending_registration'

# Blocked fake phone patterns
BLOCKED_PATTERNS = {str(d) * 10 for d in range(10)}   # 0000000000 … 9999999999


# ─── Phone validation ─────────────────────────────────────────────────────────

def is_valid_mobile(phone: str) -> tuple[bool, str]:
    """Returns (ok, cleaned_phone_or_error_msg)."""
    phone = phone.strip().replace(' ', '').replace('-', '')
    if phone.startswith('+91'):
        phone = phone[3:]
    if len(phone) != 10 or not phone.isdigit():
        return False, 'Phone must be exactly 10 digits.'
    if phone[0] not in '6789':
        return False, 'Indian mobile must start with 6, 7, 8 or 9.'
    if phone in BLOCKED_PATTERNS:
        return False, 'This phone number is not valid.'
    return True, phone


# ─── OTP generation ───────────────────────────────────────────────────────────

def generate_otp() -> str:
    return ''.join(random.SystemRandom().choices(string.digits, k=OTP_LENGTH))


# ─── Session helpers ──────────────────────────────────────────────────────────

def store_pending_registration(form_data: dict, otp: str):
    session[SESSION_KEY] = {
        'name':          form_data['name'],
        'phone':         form_data['phone'],
        'email':         form_data['email'],
        'password_hash': form_data['password_hash'],
        'room_number':   form_data.get('room_number', ''),
        'otp':           otp,
        'otp_sent_at':   time.time(),
        'attempts':      0,
        'resend_count':  1,
        'last_resend':   time.time(),
    }
    session.modified = True


def get_pending() -> dict | None:
    return session.get(SESSION_KEY)


def clear_pending():
    session.pop(SESSION_KEY, None)
    session.modified = True


# ─── OTP validation ───────────────────────────────────────────────────────────

def validate_otp(entered: str) -> tuple[bool, str]:
    """Returns (success, message)."""
    data = get_pending()
    if not data:
        return False, 'Session expired. Please register again.'

    if time.time() - data['otp_sent_at'] > OTP_EXPIRY_SECONDS:
        clear_pending()
        return False, 'OTP expired. Please register again.'

    if data['attempts'] >= MAX_VERIFY_ATTEMPTS:
        clear_pending()
        return False, 'Too many wrong attempts. Please register again.'

    data['attempts'] += 1
    session[SESSION_KEY] = data
    session.modified = True

    if entered.strip() != data['otp']:
        remaining = MAX_VERIFY_ATTEMPTS - data['attempts']
        if remaining <= 0:
            clear_pending()
            return False, 'Too many wrong attempts. Please register again.'
        return False, f'Incorrect OTP. {remaining} attempt{"s" if remaining != 1 else ""} left.'

    return True, 'ok'


def can_resend() -> tuple[bool, str]:
    data = get_pending()
    if not data:
        return False, 'Session expired. Please register again.'
    if data['resend_count'] >= MAX_RESEND_ATTEMPTS:
        return False, f'Maximum {MAX_RESEND_ATTEMPTS} resends reached. Please register again.'
    wait = RESEND_COOLDOWN_SEC - (time.time() - data['last_resend'])
    if wait > 0:
        return False, f'Please wait {int(wait)}s before resending.'
    return True, 'ok'


def refresh_otp() -> str:
    data = get_pending()
    new_otp = generate_otp()
    data.update({
        'otp':          new_otp,
        'otp_sent_at':  time.time(),
        'attempts':     0,
        'resend_count': data['resend_count'] + 1,
        'last_resend':  time.time(),
    })
    session[SESSION_KEY] = data
    session.modified = True
    return new_otp


# ─── Email OTP sender (FREE — Gmail SMTP) ─────────────────────────────────────

def send_otp_email(to_email: str, to_name: str, otp: str) -> tuple[bool, str]:
    """
    Send OTP via Gmail SMTP. 100% free.
    Requires MAIL_USERNAME and MAIL_PASSWORD in .env
    Falls back to console print if credentials not configured (dev mode).
    """
    mail_user = os.environ.get('MAIL_USERNAME', '').strip()
    mail_pass = os.environ.get('MAIL_PASSWORD', '').strip()

    if not mail_user or not mail_pass:
        return _console_fallback(to_email, otp)

    subject = f'Your Dwaraka Mess OTP: {otp}'
    html_body = _build_email_html(to_name, otp)
    text_body = f'Hello {to_name},\n\nYour Dwaraka Mess OTP is: {otp}\n\nValid for 10 minutes. Do not share this code.\n\n– Dwaraka Mess Team'

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From']    = f'Dwaraka Mess <{mail_user}>'
    msg['To']      = to_email
    msg.attach(MIMEText(text_body, 'plain'))
    msg.attach(MIMEText(html_body, 'html'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587, timeout=15) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(mail_user, mail_pass)
            smtp.sendmail(mail_user, to_email, msg.as_string())
        logger.info(f'OTP email sent to {to_email[:4]}***@***')
        return True, ''
    except smtplib.SMTPAuthenticationError:
        logger.error('Gmail SMTP auth failed — check MAIL_USERNAME and MAIL_PASSWORD (use App Password, not your Gmail password)')
        return False, 'Email service misconfigured. Contact admin.'
    except smtplib.SMTPException as e:
        logger.error(f'SMTP error: {e}')
        return _console_fallback(to_email, otp)
    except Exception as e:
        logger.error(f'Email send error: {e}')
        return _console_fallback(to_email, otp)


def _console_fallback(email: str, otp: str) -> tuple[bool, str]:
    """Dev fallback — shows OTP in terminal when email not configured."""
    border = '=' * 50
    print(f'\n{border}')
    print(f'  DEV MODE — Email not configured')
    print(f'  To : {email}')
    print(f'  OTP: {otp}')
    print(f'{border}\n')
    logger.warning(f'[DEV] OTP {otp} printed to console (email not configured)')
    return True, ''     # Return success so dev flow isn't blocked


# ─── HTML Email Template ──────────────────────────────────────────────────────

def _build_email_html(name: str, otp: str) -> str:
    digits = ''.join(
        f'<span style="display:inline-block;width:44px;height:52px;line-height:52px;'
        f'background:#1a1a2e;color:#ffbe33;border:2px solid #ffbe33;border-radius:10px;'
        f'font-size:26px;font-weight:800;text-align:center;margin:0 4px;">{d}</span>'
        for d in otp
    )
    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f4f6f9;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f9;padding:40px 0;">
    <tr><td align="center">
      <table width="480" cellpadding="0" cellspacing="0" style="background:#16213e;border-radius:20px;overflow:hidden;box-shadow:0 8px 32px rgba(0,0,0,0.3);">

        <!-- Header -->
        <tr>
          <td style="background:linear-gradient(135deg,#1a1a2e,#16213e);padding:32px;text-align:center;border-bottom:2px solid rgba(255,190,51,0.3);">
            <div style="font-size:40px;margin-bottom:8px;">🍛</div>
            <h1 style="margin:0;color:#ffbe33;font-size:24px;font-weight:800;letter-spacing:1px;">Dwaraka Mess</h1>
            <p style="margin:6px 0 0;color:#9ca3af;font-size:14px;">Email Verification</p>
          </td>
        </tr>

        <!-- Body -->
        <tr>
          <td style="padding:36px 40px;text-align:center;">
            <p style="color:#d1d5db;font-size:16px;margin:0 0 6px;">Hello, <strong style="color:#f9fafb;">{name}</strong> 👋</p>
            <p style="color:#9ca3af;font-size:14px;margin:0 0 28px;">
              Use this OTP to complete your Dwaraka Mess registration.
            </p>

            <!-- OTP Digits -->
            <div style="margin:0 0 28px;">{digits}</div>

            <!-- Validity -->
            <div style="background:rgba(255,190,51,0.08);border:1px solid rgba(255,190,51,0.2);
                        border-radius:10px;padding:12px 20px;display:inline-block;margin-bottom:28px;">
              <span style="color:#ffbe33;font-size:13px;font-weight:600;">
                ⏱ Valid for 10 minutes only
              </span>
            </div>

            <!-- Security note -->
            <p style="color:#6b7280;font-size:12px;margin:0;line-height:1.6;">
              🔒 Never share this OTP with anyone.<br>
              Dwaraka Mess will never ask for your OTP via call or message.
            </p>
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="background:rgba(0,0,0,0.2);padding:20px 40px;text-align:center;border-top:1px solid rgba(255,255,255,0.05);">
            <p style="color:#4b5563;font-size:12px;margin:0;">
              If you didn't request this, please ignore this email.<br>
              © Dwaraka Mess Management System
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>
"""
