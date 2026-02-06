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

def send_trip_created_email(email: str, user_name: str, trip_title: str, destination: Optional[str] = None, 
                             start_date: Optional[str] = None, end_date: Optional[str] = None, 
                             budget: float = 0.0, currency: str = "USD", description: Optional[str] = None,
                             use_ai: bool = False, start_location: Optional[str] = None):
    
    # Format dates if provided
    date_info_text = "TBD"
    if start_date:
        try:
            from datetime import datetime
            
            # Handle potential string or already datetime if accidentally passed
            if isinstance(start_date, str):
                s_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            else:
                s_dt = start_date
                
            date_info_text = s_dt.strftime("%b %d, %Y")
            
            if end_date:
                if isinstance(end_date, str):
                    e_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                else:
                    e_dt = end_date
                date_info_text += f" - {e_dt.strftime('%b %d, %Y')}"
        except Exception as e:
            print(f"Date formatting error in email: {e}")
            date_info_text = str(start_date)

    ai_badge = ""
    if use_ai:
        ai_badge = """
        <div style="display: inline-block; background-color: #E0E7FF; color: #4338CA; padding: 4px 12px; border-radius: 16px; font-size: 12px; font-weight: bold; margin-bottom: 10px;">
            ✨ AI ASSISTED
        </div>
        """

    content = f"""
    <div style="text-align: center; margin-bottom: 30px;">
        {ai_badge}
        <div class="greeting">Your Adventure Begins! ✈️</div>
        <p style="font-size: 16px; color: #666;">Hi <strong>{user_name}</strong>, your trip <strong>{trip_title}</strong> is officially on the books.</p>
    </div>

    <div style="background-color: #ffffff; border: 1px solid #E5E7EB; border-radius: 12px; padding: 25px; margin-bottom: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
        <h3 style="margin-top: 0; color: #111827; font-size: 18px; border-bottom: 1px solid #F3F4F6; padding-bottom: 10px;">Trip Summary</h3>
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="padding: 10px 0; color: #6B7280; width: 120px;">📍 Destination</td>
                <td style="padding: 10px 0; color: #111827; font-weight: 500;">{destination or 'To be decided'}</td>
            </tr>
            {f'<tr><td style="padding: 10px 0; color: #6B7280;">🏠 Origin</td><td style="padding: 10px 0; color: #111827; font-weight: 500;">{start_location}</td></tr>' if start_location else ''}
            <tr>
                <td style="padding: 10px 0; color: #6B7280;">📅 Dates</td>
                <td style="padding: 10px 0; color: #111827; font-weight: 500;">{date_info_text}</td>
            </tr>
            <tr>
                <td style="padding: 10px 0; color: #6B7280;">💰 Budget</td>
                <td style="padding: 10px 0; color: #111827; font-weight: 500;">{currency} {budget:,.2f}</td>
            </tr>
        </table>
        
        {f'<div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #F3F4F6; color: #4B5563; font-style: italic; font-size: 14px;">"{description}"</div>' if description else ''}
    </div>

    <div style="margin-bottom: 30px;">
        <h3 style="color: #111827; font-size: 16px; margin-bottom: 15px;">Next Steps:</h3>
        <ul style="padding-left: 20px; color: #4B5563; line-height: 1.8;">
            <li><strong>Invite your squad:</strong> Trips are better together! Share the trip link with friends in the app.</li>
            <li><strong>Build your itinerary:</strong> Start adding spots you want to visit and booking accommodations.</li>
            <li><strong>Track expenses:</strong> Keep everyone's wallet happy by logging costs as you go.</li>
        </ul>
    </div>
    """
    html = _get_base_template("Adventure Awaits - FairTrip", content, "Open in FairTrip", "https://fairtrip.app/trips")
    return send_email_html(email, f"Trip Confirmed: {trip_title} 🌍", html)

def send_trip_invitation_email(email: str, inviter_name: str, trip_title: str, join_url: str = "https://fairtrip.app/trips"):
    content = f"""
    <div class="greeting">You're Invited! ✈️</div>
    <p>Hi there,</p>
    <p><strong>{inviter_name}</strong> has invited you to join the trip <strong>{trip_title}</strong> on FairTrip.</p>
    <p>Join the squad to collaborate on the itinerary and track shared expenses easily.</p>
    """
    html = _get_base_template("Trip Invitation - FairTrip", content, "Join Trip", join_url)
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
