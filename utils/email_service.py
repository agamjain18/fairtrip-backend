import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from typing import Optional

# Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "help.agam.online@gmail.com"
SENDER_PASSWORD = os.getenv("EMAIL_APP_PASSWORD", "tabm iwxi szlf rdap") 

def _get_base_template(title: str, content: str, action_text: Optional[str] = None, action_url: Optional[str] = None) -> str:
    action_button = ""
    if action_text and action_url:
        action_button = f"""
        <a href="{action_url}" class="cta-button">{action_text}</a>
        """
        
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <style>
            body {{
                font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
                background-color: #f4f7f6;
                margin: 0;
                padding: 0;
                -webkit-font-smoothing: antialiased;
            }}
            .container {{
                max-width: 600px;
                margin: 20px auto;
                background-color: #ffffff;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #4A9EFF 0%, #00C896 100%);
                padding: 40px 20px;
                text-align: center;
                color: white;
            }}
            .header h1 {{
                margin: 0;
                font-size: 28px;
                font-weight: 700;
                letter-spacing: 1px;
            }}
            .hero-image {{
                width: 100%;
                height: 150px;
                object-fit: cover;
                background-image: url('https://images.unsplash.com/photo-1517486808906-6ca8b3f04846?w=600&q=80');
                background-size: cover;
                background-position: center;
            }}
            .content {{
                padding: 30px;
                color: #333333;
                line-height: 1.6;
            }}
            .greeting {{
                font-size: 24px;
                font-weight: 600;
                color: #1E3A5F;
                margin-bottom: 20px;
            }}
            .cta-button {{
                display: block;
                width: 200px;
                margin: 30px auto;
                padding: 15px 0;
                background-color: #4A9EFF;
                color: white !important;
                text-decoration: none;
                text-align: center;
                border-radius: 30px;
                font-weight: bold;
                font-size: 16px;
                box-shadow: 0 4px 15px rgba(74, 158, 255, 0.3);
            }}
            .footer {{
                background-color: #f8f9fa;
                padding: 20px;
                text-align: center;
                font-size: 12px;
                color: #888888;
                border-top: 1px solid #eeeeee;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>FairTrip</h1>
            </div>
            
            <div class="content">
                {content}
                {action_button}
                
                <p style="text-align: center; margin-top: 30px; font-size: 0.9em; color: #888;">
                    This is an automated notification.
                </p>
            </div>
            
            <div class="footer">
                &copy; 2026 FairTrip Inc. • Travel Together, Split Easily<br>
                <a href="#" style="color: #4A9EFF; text-decoration: none;">Privacy Policy</a> • <a href="#" style="color: #4A9EFF; text-decoration: none;">Unsubscribe</a>
            </div>
        </div>
    </body>
    </html>
    """

def send_email_html(to_email: str, subject: str, html_content: str):
    try:
        msg = MIMEMultipart()
        msg['From'] = f"FairTrip <{SENDER_EMAIL}>"
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(html_content, 'html'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        server.quit()
        print(f"Email sent to {to_email}: {subject}")
        return True
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")
        return False

# --- Specific Notifications ---

def send_trip_created_email(email: str, user_name: str, trip_title: str):
    content = f"""
    <div class="greeting">Trip Created! 🌍</div>
    <p>Hi {user_name},</p>
    <p>You have successfully created a new trip: <strong>{trip_title}</strong>.</p>
    <p>It's time to start planning! Invite friends, add itinerary items, and get ready for an adventure.</p>
    """
    html = _get_base_template("Trip Created - FairTrip", content, "View Trip", "https://fairtrip.app/trips")
    return send_email_html(email, f"Trip Created: {trip_title}", html)

def send_trip_invitation_email(email: str, inviter_name: str, trip_title: str):
    content = f"""
    <div class="greeting">You're Invited! ✈️</div>
    <p>Hi there,</p>
    <p><strong>{inviter_name}</strong> has invited you to join the trip <strong>{trip_title}</strong> on FairTrip.</p>
    <p>Join the squad to collaborate on the itinerary and track shared expenses easily.</p>
    """
    html = _get_base_template("Trip Invitation - FairTrip", content, "Join Trip", "https://fairtrip.app/trips")
    return send_email_html(email, f"Invitation to {trip_title}", html)

def send_trip_deleted_email(email: str, user_name: str, trip_title: str):
    content = f"""
    <div class="greeting">Trip Deleted 🗑️</div>
    <p>Hi {user_name},</p>
    <p>The trip <strong>{trip_title}</strong> has been deleted by the creator.</p>
    <p>All associated data (expenses, itinerary) has been removed. We hope you can plan a new adventure soon!</p>
    """
    html = _get_base_template("Trip Deleted - FairTrip", content, "Plan New Trip", "https://fairtrip.app/trips")
    return send_email_html(email, f"Trip Deleted: {trip_title}", html)

def send_friend_added_email(email: str, friend_name: str):
    content = f"""
    <div class="greeting">New Friend! 👥</div>
    <p>You and <strong>{friend_name}</strong> are now friends on FairTrip.</p>
    <p>You can now invite each other to trips and split expenses seamlessly.</p>
    """
    html = _get_base_template("New Friend - FairTrip", content, "View Friends", "https://fairtrip.app/friends")
    return send_email_html(email, f"New Friend: {friend_name}", html)

def send_settlement_email(email: str, payer_name: str, amount: float, currency: str, trip_title: str):
    content = f"""
    <div class="greeting">Payment Recorded 💸</div>
    <p>Hi,</p>
    <p><strong>{payer_name}</strong> has recorded a payment of <strong>{currency} {amount}</strong> to you for the trip <strong>{trip_title}</strong>.</p>
    <p>If this is correct, no further action is needed. If not, you can dispute it in the app.</p>
    """
    html = _get_base_template("Payment Received - FairTrip", content, "View Wallet", "https://fairtrip.app/wallet")
    return send_email_html(email, f"Payment Recorded: {currency} {amount}", html)
