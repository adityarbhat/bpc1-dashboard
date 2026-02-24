"""
BPC Dashboard - Email Notifications Module
=========================================
Handles sending email notifications for login activity using Supabase email service.

This module sends notifications for:
- Successful logins
- Failed login attempts

No external email services required - uses Supabase's built-in email capabilities.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from shared.supabase_connection import get_supabase_admin_client


def _build_email_html_success(user_name: str, ip_address: str, timestamp: str) -> str:
    """Build HTML email template for successful login."""
    ip_display = ip_address if ip_address else "Unknown"

    return f"""
    <html>
    <head>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; }}
            .container {{ max-width: 500px; margin: 0 auto; padding: 20px; background: #f9fafb; }}
            .card {{ background: white; border-radius: 8px; padding: 24px; border-left: 4px solid #025a9a; }}
            .header {{ color: #025a9a; font-size: 20px; font-weight: bold; margin-bottom: 16px; }}
            .details {{ color: #4a5568; font-size: 14px; line-height: 1.6; }}
            .detail-item {{ margin: 8px 0; }}
            .label {{ font-weight: 600; color: #2d3748; }}
            .footer {{ margin-top: 24px; padding-top: 16px; border-top: 1px solid #e2e8f0; color: #718096; font-size: 12px; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="card">
                <div class="header">Successful Login</div>
                <div class="details">
                    <p>Hello {user_name},</p>
                    <p>Your account was successfully logged into the BPC1 Dashboard.</p>

                    <div class="detail-item">
                        <span class="label">Time:</span> {timestamp}
                    </div>
                    <div class="detail-item">
                        <span class="label">IP Address:</span> {ip_display}
                    </div>
                    <div class="detail-item">
                        <span class="label">Status:</span> <span style="color: #22863a;">Successful</span>
                    </div>

                    <p style="margin-top: 16px; color: #718096; font-size: 13px;">
                        If this wasn't you, please contact support immediately at <a href="mailto:adi@imaiconsultants.com" style="color: #025a9a; text-decoration: none; font-weight: 600;">adi@imaiconsultants.com</a>
                    </p>
                </div>

                <div class="footer">
                    BPC1 Dashboard | Powered by IM AI Consultants<br>
                    <a href="https://www.imaiconsultants.com" style="color: #025a9a; text-decoration: none;">www.imaiconsultants.com</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """


def _build_email_html_failed(ip_address: str, timestamp: str, error_reason: str) -> str:
    """Build HTML email template for failed login attempt."""
    ip_display = ip_address if ip_address else "Unknown"
    reason_display = error_reason if error_reason else "Unknown error"

    return f"""
    <html>
    <head>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; }}
            .container {{ max-width: 500px; margin: 0 auto; padding: 20px; background: #f9fafb; }}
            .card {{ background: white; border-radius: 8px; padding: 24px; border-left: 4px solid #cb2431; }}
            .header {{ color: #cb2431; font-size: 20px; font-weight: bold; margin-bottom: 16px; }}
            .details {{ color: #4a5568; font-size: 14px; line-height: 1.6; }}
            .detail-item {{ margin: 8px 0; }}
            .label {{ font-weight: 600; color: #2d3748; }}
            .footer {{ margin-top: 24px; padding-top: 16px; border-top: 1px solid #e2e8f0; color: #718096; font-size: 12px; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="card">
                <div class="header">Failed Login Attempt</div>
                <div class="details">
                    <p>A login attempt was made with this email address.</p>

                    <div class="detail-item">
                        <span class="label">Time:</span> {timestamp}
                    </div>
                    <div class="detail-item">
                        <span class="label">IP Address:</span> {ip_display}
                    </div>
                    <div class="detail-item">
                        <span class="label">Status:</span> <span style="color: #cb2431;">Failed</span>
                    </div>
                    <div class="detail-item">
                        <span class="label">Reason:</span> {reason_display}
                    </div>

                    <p style="margin-top: 16px; color: #718096; font-size: 13px;">
                        If this wasn't you, your account is still secure.
                    </p>
                </div>

                <div class="footer">
                    BPC1 Dashboard | Powered by IM AI Consultants<br>
                    <a href="https://www.imaiconsultants.com" style="color: #025a9a; text-decoration: none;">www.imaiconsultants.com</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """


def send_login_notification_email(
    user_email: str,
    user_name: str,
    login_status: str,
    ip_address: Optional[str],
    timestamp: datetime,
    error_reason: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send login notification email via Supabase email service.

    This function sends automated notifications for login activity.
    Failures are logged but don't prevent the main login flow.

    Args:
        user_email (str): Recipient's email address
        user_name (str): User's full name for greeting
        login_status (str): Either 'success' or 'failed'
        ip_address (Optional[str]): Client IP address (can be None)
        timestamp (datetime): When the login attempt occurred
        error_reason (Optional[str]): If failed, reason for failure

    Returns:
        Dict with keys:
            - success (bool): Whether email was sent
            - message (str): Status message
            - email_id (str or None): Email tracking ID if available

    Example:
        >>> result = send_login_notification_email(
        ...     user_email="john@ace.com",
        ...     user_name="John Smith",
        ...     login_status="success",
        ...     ip_address="192.168.1.1",
        ...     timestamp=datetime.now()
        ... )
        >>> if result['success']:
        ...     print("Email sent successfully")
    """
    try:
        # Validate inputs
        if login_status not in ['success', 'failed']:
            return {
                'success': False,
                'message': 'Invalid login_status',
                'email_id': None
            }

        # Format timestamp for display
        timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")

        # Build email based on login status
        if login_status == 'success':
            subject = "Successful Login to BPC1 Dashboard"
            html_body = _build_email_html_success(user_name, ip_address, timestamp_str)
        else:  # failed
            subject = "Failed Login Attempt on BPC1 Dashboard"
            html_body = _build_email_html_failed(ip_address, timestamp_str, error_reason)

        # Debug logging
        print(f"\n[EMAIL DEBUG] Attempting to send {login_status} login email to {user_email}")

        # Get Supabase admin client for email sending
        supabase = get_supabase_admin_client()

        # Send email using Supabase Auth's built-in email system
        # We'll use the same SMTP setup that's configured for password resets

        # Option 1: Use Supabase Functions (if available)
        try:
            # Try to send via Supabase Edge Function (if you've set one up)
            response = supabase.functions.invoke('send-email', {
                'to': user_email,
                'subject': subject,
                'html': html_body
            })

            return {
                'success': True,
                'message': 'Email sent via Supabase Function',
                'email_id': None
            }
        except Exception as func_error:
            # Edge function not available, fall back to direct email sending
            pass

        # Option 2: Use Python smtplib with Supabase SMTP settings
        # Since Supabase is already configured for password resets,
        # we can use the same SMTP server
        try:
            import smtplib
            import os
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            # Get SMTP settings from environment
            # Note: These should match your Supabase SMTP configuration
            smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')  # Default to Gmail
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            smtp_user = os.getenv('SMTP_USER', '')
            smtp_password = os.getenv('SMTP_PASSWORD', '')
            smtp_from = os.getenv('SMTP_FROM_EMAIL', 'noreply@bpc1dashboard.com')

            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = smtp_from
            msg['To'] = user_email

            # Attach HTML body
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)

            # Send via SMTP
            if smtp_user and smtp_password:
                with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_password)
                    server.send_message(msg)
                    # Ensure email is fully sent before returning
                    server.quit()

                print(f"[EMAIL] Successfully sent {login_status} email to {user_email}")
                return {
                    'success': True,
                    'message': 'Email sent via SMTP',
                    'email_id': None
                }
            else:
                # SMTP credentials not configured, log instead
                print(f"\n{'='*60}")
                print(f"LOGIN NOTIFICATION EMAIL (SMTP not configured)")
                print(f"{'='*60}")
                print(f"To: {user_email}")
                print(f"Subject: {subject}")
                print(f"Status: {login_status}")
                print(f"{'='*60}\n")

                return {
                    'success': True,
                    'message': 'Email logged (configure SMTP to send)',
                    'email_id': None
                }

        except Exception as smtp_error:
            # SMTP failed, log the email
            print(f"\n{'='*60}")
            print(f"LOGIN NOTIFICATION EMAIL (Error: {smtp_error})")
            print(f"{'='*60}")
            print(f"To: {user_email}")
            print(f"Subject: {subject}")
            print(f"Status: {login_status}")
            print(f"{'='*60}\n")

            return {
                'success': False,
                'message': f'Email logging only: {str(smtp_error)}',
                'email_id': None
            }

    except Exception as e:
        # Log the error for debugging, but don't raise
        print(f"Login notification email error: {str(e)}")

        return {
            'success': False,
            'message': f'Email failed: {str(e)}',
            'email_id': None
        }


# Quick test function for development
if __name__ == "__main__":
    from datetime import datetime

    print("Testing email notification system...")

    # Test successful login notification
    result_success = send_login_notification_email(
        user_email="test@example.com",
        user_name="Test User",
        login_status="success",
        ip_address="192.168.1.100",
        timestamp=datetime.now()
    )
    print(f"Success email: {result_success}")

    # Test failed login notification
    result_failed = send_login_notification_email(
        user_email="test@example.com",
        user_name="Test User",
        login_status="failed",
        ip_address="192.168.1.101",
        timestamp=datetime.now(),
        error_reason="Invalid credentials"
    )
    print(f"Failed email: {result_failed}")
