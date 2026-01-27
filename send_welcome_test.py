import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# Configuration (matching auth.py)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "help.agam.online@gmail.com"
SENDER_PASSWORD = "tabm iwxi szlf rdap"

def send_welcome_email(email: str, name: str):
    """Send Welcome Email via Gmail SMTP"""
    try:
        print(f"Connecting to {SMTP_SERVER}:{SMTP_PORT}...")
        print(f"Sender: {SENDER_EMAIL}")
        
        msg = MIMEMultipart()
        msg['From'] = f"FairTrip <{SENDER_EMAIL}>"
        msg['To'] = email
        msg['Subject'] = "Welcome to FairShare!"

        body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Welcome to FairTrip</title>
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
                    height: 200px;
                    object-fit: cover;
                    background-image: url('https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?w=600&q=80');
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
                .feature-list {{
                    list-style: none;
                    padding: 0;
                    margin: 30px 0;
                }}
                .feature-item {{
                    display: flex;
                    align-items: flex-start;
                    margin-bottom: 20px;
                }}
                .feature-icon {{
                    font-size: 24px;
                    margin-right: 15px;
                    min-width: 30px;
                    text-align: center;
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
                <div class="hero-image"></div>
                <!-- fallback header if image fails loading or for styling -->
                <div class="header">
                    <h1>FairTrip</h1>
                </div>
                
                <div class="content">
                    <div class="greeting">Welcome to the Family, {name}! 🌍</div>
                    
                    <p>We are absolutely thrilled to have you on board. FairTrip isn't just an app; it's your new travel companion that ensures every journey is memorable and every expense is fair.</p>
                    
                    <ul class="feature-list">
                        <li class="feature-item">
                            <span class="feature-icon">✈️</span>
                            <div>
                                <strong>Plan Seamlessly</strong><br>
                                Create detailed itineraries and collaborate with your travel squad in real-time.
                            </div>
                        </li>
                        <li class="feature-item">
                            <span class="feature-icon">💸</span>
                            <div>
                                <strong>Split Expenses, Stress-Free</strong><br>
                                Log costs as you go. Our AI handles the math so you can focus on the fun.
                            </div>
                        </li>
                        <li class="feature-item">
                            <span class="feature-icon">🔒</span>
                            <div>
                                <strong>Secure Your Documents</strong><br>
                                Keep passports and tickets safe in your biometric-secured vault.
                            </div>
                        </li>
                    </ul>

                    <a href="https://agamjain.online" class="cta-button">Start Planning Now</a>
                    
                    <p style="text-align: center; margin-top: 30px;">
                        Need help? Just reply to this email.<br>
                        We're here for you 24/7.
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
        msg.attach(MIMEText(body, 'html'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        print("Logging in...")
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        
        print("Sending email...")
        text = msg.as_string()
        server.sendmail(SENDER_EMAIL, email, text)
        server.quit()
        print(f"Welcome email successfully sent to {email}")
        return True
    except Exception as e:
        print(f"Error sending welcome email: {e}")
        return False

if __name__ == "__main__":
    target_email = "aagamjain152003@gmail.com"
    print(f"Attempting to send welcome email to {target_email} with new password")
    send_welcome_email(target_email, "Aagam Jain")
