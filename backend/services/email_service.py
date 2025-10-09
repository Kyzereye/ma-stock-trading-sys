"""
Email Service

Handles sending emails for verification, password reset, etc.
"""

import os
import secrets
from datetime import datetime, timedelta
from flask import Flask
from flask_mail import Mail, Message
from typing import Tuple
import logging

logger = logging.getLogger(__name__)

# Email configuration will be loaded from environment variables
mail = None

def init_mail(app: Flask):
    """Initialize Flask-Mail with the app"""
    global mail
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Use your SMTP variable names from .env
    mail_server = os.getenv('SMTP_HOST', 'smtp.hostinger.com')
    mail_port = int(os.getenv('SMTP_PORT', '587'))
    mail_username = os.getenv('SMTP_USER')
    mail_password = os.getenv('SMTP_PASS')
    mail_default_sender = os.getenv('SMTP_FROM') or mail_username
    mail_use_tls = os.getenv('SMTP_SECURE', 'false').lower() != 'false'  # TLS if not explicitly false
    
    app.config['MAIL_SERVER'] = mail_server
    app.config['MAIL_PORT'] = mail_port
    app.config['MAIL_USE_TLS'] = mail_use_tls
    app.config['MAIL_USE_SSL'] = False  # Using TLS, not SSL
    app.config['MAIL_USERNAME'] = mail_username
    app.config['MAIL_PASSWORD'] = mail_password
    app.config['MAIL_DEFAULT_SENDER'] = mail_default_sender
    
    mail = Mail(app)
    
    logger.info(f"Mail service initialized:")
    logger.info(f"  Server: {mail_server}")
    logger.info(f"  Port: {mail_port}")
    logger.info(f"  Username: {mail_username}")
    logger.info(f"  Default Sender: {mail_default_sender}")
    
    return mail

class EmailService:
    """Service for sending emails"""
    
    @staticmethod
    def generate_verification_token() -> str:
        """Generate a secure random token for email verification"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def get_verification_token_expiry() -> datetime:
        """Get expiration time for verification token (15 minutes from now)"""
        return datetime.utcnow() + timedelta(minutes=15)
    
    @staticmethod
    def send_verification_email(email: str, name: str, token: str) -> Tuple[bool, str]:
        """
        Send email verification email
        
        Args:
            email: User's email address
            name: User's name
            token: Verification token
            
        Returns:
            (success, message)
        """
        if mail is None:
            logger.error("Mail service not initialized")
            return (False, "Email service not configured")
        
        try:
            # Create verification URL
            # In production, this should use your actual domain
            frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:1111')
            verification_url = f"{frontend_url}?token={token}"
            
            # Get sender email from config
            sender_email = os.getenv('SMTP_FROM') or os.getenv('SMTP_USER')
            
            # Create email message
            msg = Message(
                subject='Verify Your Email - MA Stock Trading',
                recipients=[email],
                sender=sender_email
            )
            
            # HTML email body
            msg.html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                    }}
                    .header {{
                        background-color: #1976d2;
                        color: white;
                        padding: 20px;
                        text-align: center;
                        border-radius: 5px 5px 0 0;
                    }}
                    .content {{
                        background-color: #f5f5f5;
                        padding: 30px;
                        border-radius: 0 0 5px 5px;
                    }}
                    .footer {{
                        text-align: center;
                        margin-top: 20px;
                        font-size: 12px;
                        color: #666;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Welcome to MA Stock Trading!</h1>
                    </div>
                    <div class="content">
                        <h2>Hello {name},</h2>
                        <p>Thank you for registering with MA Stock Trading System. To complete your registration and start analyzing stock trades, please verify your email address.</p>
                        
                        <p>Click the button below to verify your email:</p>
                        
                        <div style="text-align: center;">
                            <a href="{verification_url}" style="display: inline-block; padding: 12px 30px; background-color: #1976d2; color: #ffffff; text-decoration: none; border-radius: 5px; margin: 20px 0; font-weight: 500;">Verify Email Address</a>
                        </div>
                        
                        <p>Or copy and paste this link into your browser:</p>
                        <p style="word-break: break-all; background-color: white; padding: 10px; border-radius: 3px;">
                            {verification_url}
                        </p>
                        
                        <p><strong>This link will expire in 15 minutes.</strong></p>
                        
                        <p>If you didn't create an account with us, please ignore this email.</p>
                    </div>
                    <div class="footer">
                        <p>&copy; 2025 MA Stock Trading System. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Plain text fallback
            msg.body = f"""
            Hello {name},
            
            Thank you for registering with MA Stock Trading System. To complete your registration, please verify your email address.
            
            Click this link to verify your email:
            {verification_url}
            
            This link will expire in 15 minutes.
            
            If you didn't create an account with us, please ignore this email.
            
            ---
            MA Stock Trading System
            """
            
            mail.send(msg)
            logger.info(f"Verification email sent successfully to {email}")
            return (True, "Verification email sent")
            
        except Exception as e:
            logger.error(f"Error sending verification email to {email}: {e}")
            return (False, f"Failed to send verification email: {str(e)}")
    
    @staticmethod
    def send_welcome_email(email: str, name: str) -> Tuple[bool, str]:
        """
        Send welcome email after successful verification
        
        Args:
            email: User's email address
            name: User's name
            
        Returns:
            (success, message)
        """
        if mail is None:
            logger.error("Mail service not initialized")
            return (False, "Email service not configured")
        
        try:
            frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:1111')
            
            # Get sender email from config
            sender_email = os.getenv('SMTP_FROM') or os.getenv('SMTP_USER')
            
            msg = Message(
                subject='Welcome to MA Stock Trading!',
                recipients=[email],
                sender=sender_email
            )
            
            msg.html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                    }}
                    .header {{
                        background-color: #4caf50;
                        color: white;
                        padding: 20px;
                        text-align: center;
                        border-radius: 5px 5px 0 0;
                    }}
                    .content {{
                        background-color: #f5f5f5;
                        padding: 30px;
                        border-radius: 0 0 5px 5px;
                    }}
                    .feature {{
                        margin: 15px 0;
                        padding-left: 20px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎉 Email Verified Successfully!</h1>
                    </div>
                    <div class="content">
                        <h2>Welcome aboard, {name}!</h2>
                        <p>Your email has been verified and your account is now fully active.</p>
                        
                        <p>You now have access to:</p>
                        <div class="feature">✓ EMA/SMA Trading Analysis</div>
                        <div class="feature">✓ Moving Average Optimization</div>
                        <div class="feature">✓ Performance Backtesting</div>
                        <div class="feature">✓ Custom Trading Parameters</div>
                        <div class="feature">✓ Personalized Preferences</div>
                        
                        <div style="text-align: center;">
                            <a href="{frontend_url}" style="display: inline-block; padding: 12px 30px; background-color: #1976d2; color: #ffffff; text-decoration: none; border-radius: 5px; margin: 20px 0; font-weight: 500;">Start Trading Analysis</a>
                        </div>
                        
                        <p>Happy trading!</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            msg.body = f"""
            Welcome aboard, {name}!
            
            Your email has been verified and your account is now fully active.
            
            You now have access to all features of the MA Stock Trading System.
            
            Visit {frontend_url} to start analyzing your trades!
            
            Happy trading!
            ---
            MA Stock Trading System
            """
            
            mail.send(msg)
            logger.info(f"Welcome email sent successfully to {email}")
            return (True, "Welcome email sent")
            
        except Exception as e:
            logger.error(f"Error sending welcome email to {email}: {e}")
            return (False, f"Failed to send welcome email: {str(e)}")

