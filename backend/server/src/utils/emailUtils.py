import smtplib
import os
import logging

from html import escape
from urllib.parse import urlencode
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()


def create_email_transporter():
    try:
        port = int(os.getenv("EMAIL_PORT", 587))
    except ValueError:
        raise ValueError(f"EMAIL_PORT must be a valid integer, got: {os.getenv('EMAIL_PORT')}")

    host = os.getenv("EMAIL_HOST")
    if not host:
        raise ValueError("EMAIL_HOST environment variable is not set")

    config = {
        "host": host,
        "port": port,
        "secure": os.getenv("EMAIL_SECURE", "false").lower() == "true",
        "user": os.getenv("EMAIL_USER"),
        "password": os.getenv("EMAIL_PASSWORD"),
        "from": os.getenv("EMAIL_FROM", f"no-reply@{os.getenv('APP_DOMAIN', 'localhost')}"),
    }

    required_vars = ["EMAIL_HOST", "EMAIL_USER", "EMAIL_PASSWORD"]
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    return config


def send_email(config, to, subject, html):
    msg = MIMEMultipart("alternative")
    msg["From"] = config["from"]
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(html, "html"))

    try:
        smtp_class = smtplib.SMTP_SSL if config["secure"] else smtplib.SMTP
        with smtp_class(config["host"], config["port"]) as server:
            server.ehlo()
            if not config["secure"]:
                try:
                    server.starttls()
                    server.ehlo()
                except Exception as exc:
                    logging.warning("STARTTLS failed; credentials may be sent in plaintext: %s", exc)
                    raise RuntimeError("STARTTLS is required for non-SSL SMTP connections")

            server.login(config["user"], config["password"])
            server.sendmail(config["from"], to, msg.as_string())
    except Exception as e:
        raise RuntimeError(f"Error occurred while sending email: {e}")

def send_email_verification(email, token):
    config = create_email_transporter()
    cors_origin = os.getenv("CORS_ORIGIN")
    if not cors_origin:
        raise ValueError("CORS_ORIGIN environment variable is not set")
    
    query_params = urlencode({"token": token})
    verification_url = f"{cors_origin}/verifyEmail?{query_params}"

    html = build_email_verification_html(verification_url)
    send_email(config, email, "Bbot email verification", html)

def send_password_reset_email(email, token):
    config = create_email_transporter()
    cors_origin = os.getenv("CORS_ORIGIN")
    if not cors_origin:
        raise ValueError("CORS_ORIGIN environment variable is not set")
    
    query_params = urlencode({"token": token})
    reset_url = f"{cors_origin}/resetPassword?{query_params}"

    html = build_reset_password_html(reset_url)
    send_email(config, email, "Bbot password reset", html)

def build_email_verification_html(verification_url):
    safe_url = escape(verification_url, quote=True)
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Email Verification</title>
    </head>
    <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 0;">
      <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #f4f4f4;">
        <tr>
          <td align="center">
            <table width="600" border="0" cellspacing="0" cellpadding="0" style="background-color: #ffffff; margin: 20px 0; border-radius: 8px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);">
              <tr>
                <td align="center" style="padding: 40px 20px;">
                  <h1 style="color: #333333;">Verify Your Email Address</h1>
                  <p style="color: #666666; font-size: 16px;">
                    Thank you for registering with Bbot. To complete your registration, please click the button below to verify your email address.
                  </p>
                  <a href="{safe_url}" style="display: inline-block; padding: 15px 25px; margin: 20px 0; background-color: #007bff; color: #ffffff; text-decoration: none; border-radius: 5px; font-size: 16px;">Verify Email</a>
                  <p style="color: #666666; font-size: 14px;">
                    If you did not create an account, no further action is required.
                  </p>
                  <p style="color: #aaaaaa; font-size: 12px;">
                    &copy; 2026 Bbot. All rights reserved.
                  </p>
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>
    </body>
    </html>
    """

def build_reset_password_html(reset_url):
    safe_url = escape(reset_url, quote=True)
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Password Reset</title>
    </head>
    <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 0;">
      <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #f4f4f4;">
        <tr>
          <td align="center">
            <table width="600" border="0" cellspacing="0" cellpadding="0" style="background-color: #ffffff; margin: 20px 0; border-radius: 8px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);">
              <tr>
                <td align="center" style="padding: 40px 20px;">
                  <h1 style="color: #333333;">Reset Your Password</h1>
                  <p style="color: #666666; font-size: 16px;">
                    You are receiving this email because you requested a password reset for your Bbot account. Please click the button below to reset your password.
                  </p>
                 <a href="{safe_url}" style="display: inline-block; padding: 15px 25px; margin: 20px 0; background-color: #007bff; color: #ffffff; text-decoration: none; border-radius: 5px; font-size: 16px;">Reset Password</a>
                  <p style="color: #666666; font-size: 14px;">
                    If you did not request a password reset, please ignore this email.
                  </p>
                  <p style="color: #aaaaaa; font-size: 12px;">
                    &copy; 2026 Bbot. All rights reserved.
                  </p>
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>
    </body>
    </html>
    """