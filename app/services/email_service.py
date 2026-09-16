import logging
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


async def send_password_reset_email(
    to_email: str,
    reset_url: str,
    full_name: str | None = None,
) -> bool:
    """
    Send a password reset email via Brevo transactional email API.
    If BREVO_API_KEY is not configured or in development, logs the email and link.
    """
    recipient_name = full_name or to_email.split("@")[0]

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>Reset Your Password</title>
      <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #09090b; color: #fafafa; padding: 20px; }}
        .container {{ max-width: 520px; margin: 0 auto; background: #18181b; border: 1px solid #27272a; border-radius: 12px; padding: 32px; }}
        h2 {{ margin-top: 0; color: #ffffff; font-size: 22px; }}
        p {{ color: #a1a1aa; font-size: 15px; line-height: 1.6; }}
        .btn-wrapper {{ margin: 28px 0; text-align: center; }}
        .btn {{ display: inline-block; padding: 12px 28px; background-color: #ffffff; color: #09090b !important; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 15px; }}
        .fallback {{ word-break: break-all; font-size: 13px; color: #71717a; }}
        .footer {{ font-size: 12px; color: #71717a; margin-top: 32px; border-top: 1px solid #27272a; padding-top: 16px; }}
      </style>
    </head>
    <body>
      <div class="container">
        <h2>Reset your Corpus password</h2>
        <p>Hello {recipient_name},</p>
        <p>We received a request to reset the password for your Corpus account. Click the button below to choose a new password:</p>
        <div class="btn-wrapper">
          <a href="{reset_url}" class="btn" target="_blank">Reset Password</a>
        </div>
        <p class="fallback">Or copy and paste this link into your browser:<br>{reset_url}</p>
        <p>This link is valid for <strong>{settings.password_reset_token_expire_minutes} minutes</strong> and can only be used once.</p>
        <div class="footer">
          If you didn't request this change, you can safely ignore this email. Your password will not be changed.
        </div>
      </div>
    </body>
    </html>
    """

    # If Brevo API key is not configured, log to console for development testing
    if not settings.brevo_api_key:
        logger.info(
            f"[EMAIL MOCK] Brevo API Key not configured. Password reset link for {to_email}: {reset_url}"
        )
        print(f"\n==================== [DEV EMAIL / BREVO MOCK] ====================")
        print(f"To: {to_email}")
        print(f"Subject: Reset your Corpus password")
        print(f"Reset Link: {reset_url}")
        print(f"==================================================================\n")
        return True

    payload = {
        "sender": {
            "name": settings.emails_from_name,
            "email": settings.emails_from_email,
        },
        "to": [{"email": to_email, "name": recipient_name}],
        "subject": "Reset your Corpus password",
        "htmlContent": html_content,
    }

    headers = {
        "accept": "application/json",
        "api-key": settings.brevo_api_key,
        "content-type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(BREVO_API_URL, json=payload, headers=headers)
            if response.status_code in (200, 201, 202):
                logger.info(f"Password reset email successfully sent to {to_email} via Brevo")
                return True
            else:
                logger.error(
                    f"Failed to send email via Brevo: {response.status_code} - {response.text}"
                )
                return False
    except Exception as e:
        logger.error(f"Error connecting to Brevo API: {e}")
        return False
