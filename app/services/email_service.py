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
            "name": settings.sender_name,
            "email": settings.sender_email,
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


async def send_early_access_confirmation_email(to_email: str) -> bool:
    """
    Send an early access confirmation email via Brevo.
    If Brevo is not configured or in development, logs to console.
    """
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>Welcome to Corpus Early Access</title>
      <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #09090b; color: #fafafa; padding: 20px; }}
        .container {{ max-width: 520px; margin: 0 auto; background: #18181b; border: 1px solid #27272a; border-radius: 12px; padding: 32px; }}
        h2 {{ margin-top: 0; color: #ffffff; font-size: 22px; }}
        p {{ color: #a1a1aa; font-size: 15px; line-height: 1.6; }}
        .footer {{ font-size: 12px; color: #71717a; margin-top: 32px; border-top: 1px solid #27272a; padding-top: 16px; }}
      </style>
    </head>
    <body>
      <div class="container">
        <h2>You're on the list.</h2>
        <p>Thank you for your interest in Corpus.</p>
        <p>Corpus is being built in the open — the intelligent decision layer for tattoo art, language verification, and artist curation.</p>
        <p>We'll notify you as soon as early access slots open up or there's something new to try.</p>
        <div class="footer">
          Corpus &bull; <a href="{settings.frontend_url}" style="color: #d4af37; text-decoration: none;">{settings.frontend_url}</a>
        </div>
      </div>
    </body>
    </html>
    """

    if not settings.brevo_api_key:
        logger.info(f"[EMAIL MOCK] Brevo not configured. Early access subscriber: {to_email}")
        print(f"\n==================== [DEV EMAIL / BREVO MOCK] ====================")
        print(f"To: {to_email}")
        print(f"Subject: You're on the Corpus early access list")
        print(f"==================================================================\n")
        return True

    payload = {
        "sender": {
            "name": settings.sender_name,
            "email": settings.sender_email,
        },
        "to": [{"email": to_email}],
        "subject": "You're on the Corpus early access list",
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
            return response.status_code in (200, 201, 202)
    except Exception as e:
        logger.error(f"Error connecting to Brevo API: {e}")
        return False


async def send_demo_request_notification_to_admin(
    requester_email: str,
    requester_name: str | None = None,
    requester_notes: str | None = None,
    ip_address: str | None = None,
) -> bool:
    """
    Send an email notification to the site administrator/owner when someone requests a demo.
    Configured recipient email defaults to settings.demo_recipient_email.
    """
    admin_email = settings.demo_recipient_email or "bankoleayobami01@gmail.com"
    name_display = requester_name.strip() if requester_name else "Not provided"
    notes_display = requester_notes.strip() if requester_notes else "None"
    ip_display = ip_address or "Unknown"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>New Corpus Demo Request</title>
      <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #09090b; color: #fafafa; padding: 20px; }}
        .container {{ max-width: 540px; margin: 0 auto; background: #18181b; border: 1px solid #27272a; border-radius: 12px; padding: 32px; }}
        h2 {{ margin-top: 0; color: #d4af37; font-size: 22px; font-weight: 600; }}
        .item {{ margin: 16px 0; padding: 12px 16px; background: #09090b; border: 1px solid #27272a; border-radius: 8px; }}
        .label {{ font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; color: #a1a1aa; margin-bottom: 4px; }}
        .value {{ font-size: 15px; color: #ffffff; word-break: break-all; }}
        .btn-wrapper {{ margin: 28px 0 16px 0; text-align: center; }}
        .btn {{ display: inline-block; padding: 12px 28px; background-color: #d4af37; color: #09090b !important; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 15px; }}
        .footer {{ font-size: 12px; color: #71717a; margin-top: 24px; border-top: 1px solid #27272a; padding-top: 16px; text-align: center; }}
      </style>
    </head>
    <body>
      <div class="container">
        <h2>New Demo Request</h2>
        <p style="color: #a1a1aa; font-size: 15px;">Someone just submitted a demo request from the Corpus landing page.</p>
        
        <div class="item">
          <div class="label">Requester Email</div>
          <div class="value"><a href="mailto:{requester_email}" style="color: #d4af37; text-decoration: none;">{requester_email}</a></div>
        </div>

        <div class="item">
          <div class="label">Requester Name</div>
          <div class="value">{name_display}</div>
        </div>

        <div class="item">
          <div class="label">Notes / Message</div>
          <div class="value">{notes_display}</div>
        </div>

        <div class="item">
          <div class="label">IP Address</div>
          <div class="value">{ip_display}</div>
        </div>

        <div class="btn-wrapper">
          <a href="mailto:{requester_email}?subject=Corpus%20Demo%20Walkthrough" class="btn">Reply to Requester</a>
        </div>

        <div class="footer">
          Corpus Automated Notification &bull; <a href="{settings.frontend_url}" style="color: #d4af37; text-decoration: none;">{settings.frontend_url}</a>
        </div>
      </div>
    </body>
    </html>
    """

    if not settings.brevo_api_key:
        logger.info(
            f"[EMAIL MOCK] Demo request notification for {admin_email}. Requester: {requester_email}"
        )
        print(f"\n==================== [DEV EMAIL / BREVO MOCK - DEMO REQUEST] ====================")
        print(f"To: {admin_email}")
        print(f"Reply-To: {requester_email}")
        print(f"Subject: [Corpus Demo Request] from {requester_email}")
        print(f"Name: {name_display}")
        print(f"=================================================================================\n")
        return True

    payload = {
        "sender": {
            "name": settings.sender_name,
            "email": settings.sender_email,
        },
        "to": [{"email": admin_email}],
        "replyTo": {
            "email": requester_email,
            "name": requester_name or requester_email,
        },
        "subject": f"[Corpus Demo Request] from {requester_email}",
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
                logger.info(f"Demo notification email sent to admin ({admin_email}) for requester {requester_email}")
                return True
            else:
                logger.error(f"Failed to send demo notification via Brevo: {response.status_code} - {response.text}")
                return False
    except Exception as e:
        logger.error(f"Error connecting to Brevo API: {e}")
        return False


async def send_demo_request_confirmation_email(
    to_email: str,
    requester_name: str | None = None,
) -> bool:
    """
    Send an acknowledgement email to the user confirming their demo request was received.
    """
    salutation = f"Hello {requester_name.strip()}," if requester_name else "Hello,"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>Corpus Demo Request Received</title>
      <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #09090b; color: #fafafa; padding: 20px; }}
        .container {{ max-width: 520px; margin: 0 auto; background: #18181b; border: 1px solid #27272a; border-radius: 12px; padding: 32px; }}
        h2 {{ margin-top: 0; color: #ffffff; font-size: 22px; }}
        p {{ color: #a1a1aa; font-size: 15px; line-height: 1.6; }}
        .footer {{ font-size: 12px; color: #71717a; margin-top: 32px; border-top: 1px solid #27272a; padding-top: 16px; }}
      </style>
    </head>
    <body>
      <div class="container">
        <h2>We've received your demo request.</h2>
        <p>{salutation}</p>
        <p>Thank you for your interest in Corpus — the intelligent decision layer for tattoo art, language verification, and artist curation.</p>
        <p>We've received your request and our team will be in touch shortly to schedule a walkthrough.</p>
        <div class="footer">
          Corpus &bull; <a href="{settings.frontend_url}" style="color: #d4af37; text-decoration: none;">{settings.frontend_url}</a>
        </div>
      </div>
    </body>
    </html>
    """

    if not settings.brevo_api_key:
        logger.info(f"[EMAIL MOCK] Demo request confirmation for requester: {to_email}")
        return True

    payload = {
        "sender": {
            "name": settings.sender_name,
            "email": settings.sender_email,
        },
        "to": [{"email": to_email, "name": requester_name or to_email}],
        "subject": "We've received your Corpus demo request",
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
            return response.status_code in (200, 201, 202)
    except Exception as e:
        logger.error(f"Error connecting to Brevo API: {e}")
        return False

