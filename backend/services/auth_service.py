"""
Authentication Service

Handles user authentication, password hashing, and JWT token generation
"""

import bcrypt
import jwt
import re
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
from email_validator import validate_email, EmailNotValidError
import logging

from utils.database import get_db_connection
from services.email_service import EmailService

logger = logging.getLogger(__name__)

# JWT Configuration
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-this-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

class AuthService:
    """Service for handling authentication operations"""
    
    @staticmethod
    def validate_password_strength(password: str) -> Tuple[bool, list]:
        """
        Validate password meets requirements:
        - Minimum 11 characters
        - At least 1 uppercase letter
        - At least 1 lowercase letter
        - At least 1 number
        - At least 1 special character
        
        Returns: (is_valid, list_of_failed_requirements)
        """
        failures = []
        
        if len(password) < 11:
            failures.append("Password must be at least 11 characters long")
        
        if not re.search(r'[A-Z]', password):
            failures.append("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', password):
            failures.append("Password must contain at least one lowercase letter")
        
        if not re.search(r'\d', password):
            failures.append("Password must contain at least one number")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            failures.append("Password must contain at least one special character")
        
        return (len(failures) == 0, failures)
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """
        Validate email format
        
        Returns: (is_valid, error_message)
        """
        try:
            # Validate and normalize the email
            valid = validate_email(email, check_deliverability=False)
            return (True, "")
        except EmailNotValidError as e:
            return (False, str(e))
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    @staticmethod
    def create_access_token(user_id: int, email: str) -> str:
        """Create a JWT access token"""
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {
            'user_id': user_id,
            'email': email,
            'exp': expire,
            'iat': datetime.utcnow()
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        return token
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict]:
        """
        Verify a JWT token and return the payload
        
        Returns: payload dict if valid, None if invalid
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    @staticmethod
    def register_user(email: str, password: str, name: str) -> Tuple[bool, str, Optional[int]]:
        """
        Register a new user
        
        Returns: (success, message, user_id)
        """
        try:
            # Validate email
            is_valid_email, email_error = AuthService.validate_email(email)
            if not is_valid_email:
                return (False, f"Invalid email: {email_error}", None)
            
            # Validate password
            is_valid_password, password_errors = AuthService.validate_password_strength(password)
            if not is_valid_password:
                return (False, "; ".join(password_errors), None)
            
            # Check if user already exists
            conn = get_db_connection()
            conn.connect()
            cursor = conn.connection.cursor()
            
            cursor.execute("SELECT id FROM users WHERE email = %s", (email.lower(),))
            if cursor.fetchone():
                cursor.close()
                conn.connection.close()
                return (False, "Email already registered", None)
            
            # Hash password
            password_hash = AuthService.hash_password(password)
            
            # Generate verification token
            verification_token = EmailService.generate_verification_token()
            token_expires = EmailService.get_verification_token_expiry()
            
            # Create user with verification token
            cursor.execute(
                """INSERT INTO users (email, password_hash, email_verified, verification_token, verification_token_expires) 
                VALUES (%s, %s, %s, %s, %s)""",
                (email.lower(), password_hash, False, verification_token, token_expires)
            )
            conn.connection.commit()
            user_id = cursor.lastrowid
            
            # Create default preferences
            cursor.execute(
                """INSERT INTO user_preferences 
                (user_id, name, default_days, default_atr_period, default_atr_multiplier, 
                default_ma_type, default_initial_capital)
                VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (user_id, name, 365, 14, 2.0, 'ema', 100000.00)
            )
            conn.connection.commit()
            
            cursor.close()
            conn.connection.close()
            
            # Send verification email
            email_success, email_message = EmailService.send_verification_email(email.lower(), name, verification_token)
            if not email_success:
                logger.warning(f"Failed to send verification email to {email}: {email_message}")
            
            logger.info(f"User registered successfully: {email}")
            return (True, "Registration successful. Please check your email to verify your account.", user_id)
            
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            return (False, f"Registration failed: {str(e)}", None)
    
    @staticmethod
    def login_user(email: str, password: str) -> Tuple[bool, str, Optional[str], Optional[Dict]]:
        """
        Authenticate a user and return a JWT token
        
        Returns: (success, message, token, user_data)
        """
        try:
            conn = get_db_connection()
            conn.connect()
            cursor = conn.connection.cursor()
            
            # Get user
            cursor.execute(
                """SELECT u.id, u.email, u.password_hash, u.is_active, u.email_verified,
                p.name, p.default_days, p.default_atr_period, p.default_atr_multiplier,
                p.default_ma_type, p.default_initial_capital
                FROM users u
                LEFT JOIN user_preferences p ON u.id = p.user_id
                WHERE u.email = %s""",
                (email.lower(),)
            )
            user = cursor.fetchone()
            
            if not user:
                cursor.close()
                conn.connection.close()
                return (False, "Invalid email or password", None, None)
            
            # Handle dict or tuple result
            if isinstance(user, dict):
                user_id = user['id']
                user_email = user['email']
                password_hash = user['password_hash']
                is_active = user['is_active']
                email_verified = user['email_verified']
                name = user['name']
                default_days = user['default_days']
                default_atr_period = user['default_atr_period']
                default_atr_multiplier = user['default_atr_multiplier']
                default_ma_type = user['default_ma_type']
                default_initial_capital = user['default_initial_capital']
            else:
                user_id, user_email, password_hash, is_active, email_verified, name, default_days, default_atr_period, \
                    default_atr_multiplier, default_ma_type, default_initial_capital = user
            
            if not is_active:
                cursor.close()
                conn.connection.close()
                return (False, "Account is inactive", None, None)
            
            if not email_verified:
                cursor.close()
                conn.connection.close()
                return (False, "Please verify your email address before logging in", None, None)
            
            # Verify password
            if not AuthService.verify_password(password, password_hash):
                cursor.close()
                conn.connection.close()
                return (False, "Invalid email or password", None, None)
            
            # Update last login
            cursor.execute(
                "UPDATE users SET last_login = NOW() WHERE id = %s",
                (user_id,)
            )
            conn.connection.commit()
            cursor.close()
            conn.connection.close()
            
            # Create token
            token = AuthService.create_access_token(user_id, user_email)
            
            # Prepare user data
            user_data = {
                'id': user_id,
                'email': user_email,
                'name': name,
                'preferences': {
                    'default_days': default_days,
                    'default_atr_period': default_atr_period,
                    'default_atr_multiplier': float(default_atr_multiplier) if default_atr_multiplier else 2.0,
                    'default_ma_type': default_ma_type,
                    'default_initial_capital': float(default_initial_capital) if default_initial_capital else 100000.0
                }
            }
            
            logger.info(f"User logged in successfully: {email}")
            return (True, "Login successful", token, user_data)
            
        except Exception as e:
            logger.error(f"Error logging in user: {e}")
            return (False, f"Login failed: {str(e)}", None, None)
    
    @staticmethod
    def get_user_preferences(user_id: int) -> Optional[Dict]:
        """Get user preferences"""
        try:
            conn = get_db_connection()
            conn.connect()
            cursor = conn.connection.cursor()
            
            cursor.execute(
                """SELECT name, default_days, default_atr_period, default_atr_multiplier,
                default_ma_type, default_initial_capital
                FROM user_preferences WHERE user_id = %s""",
                (user_id,)
            )
            prefs = cursor.fetchone()
            cursor.close()
            conn.connection.close()
            
            if not prefs:
                return None
            
            return {
                'name': prefs[0],
                'default_days': prefs[1],
                'default_atr_period': prefs[2],
                'default_atr_multiplier': float(prefs[3]) if prefs[3] else 2.0,
                'default_ma_type': prefs[4],
                'default_initial_capital': float(prefs[5]) if prefs[5] else 100000.0
            }
            
        except Exception as e:
            logger.error(f"Error getting user preferences: {e}")
            return None
    
    @staticmethod
    def update_user_preferences(user_id: int, preferences: Dict) -> Tuple[bool, str]:
        """Update user preferences"""
        try:
            conn = get_db_connection()
            conn.connect()
            cursor = conn.connection.cursor()
            
            update_fields = []
            values = []
            
            if 'name' in preferences:
                update_fields.append("name = %s")
                values.append(preferences['name'])
            if 'default_days' in preferences:
                update_fields.append("default_days = %s")
                values.append(preferences['default_days'])
            if 'default_atr_period' in preferences:
                update_fields.append("default_atr_period = %s")
                values.append(preferences['default_atr_period'])
            if 'default_atr_multiplier' in preferences:
                update_fields.append("default_atr_multiplier = %s")
                values.append(preferences['default_atr_multiplier'])
            if 'default_ma_type' in preferences:
                update_fields.append("default_ma_type = %s")
                values.append(preferences['default_ma_type'])
            if 'default_initial_capital' in preferences:
                update_fields.append("default_initial_capital = %s")
                values.append(preferences['default_initial_capital'])
            
            if not update_fields:
                return (False, "No preferences to update")
            
            values.append(user_id)
            query = f"UPDATE user_preferences SET {', '.join(update_fields)} WHERE user_id = %s"
            
            cursor.execute(query, values)
            conn.connection.commit()
            cursor.close()
            conn.connection.close()
            
            logger.info(f"User preferences updated for user_id: {user_id}")
            return (True, "Preferences updated successfully")
            
        except Exception as e:
            logger.error(f"Error updating user preferences: {e}")
            return (False, f"Failed to update preferences: {str(e)}")
    
    @staticmethod
    def verify_email_token(token: str) -> Tuple[bool, str]:
        """
        Verify email using verification token
        
        Returns: (success, message)
        """
        try:
            conn = get_db_connection()
            conn.connect()
            cursor = conn.connection.cursor()
            
            # Get user with this token
            cursor.execute(
                """SELECT id, email, email_verified, verification_token_expires 
                FROM users 
                WHERE verification_token = %s""",
                (token,)
            )
            user = cursor.fetchone()
            
            if not user:
                cursor.close()
                conn.connection.close()
                return (False, "Invalid verification token")
            
            if isinstance(user, dict):
                user_id = user['id']
                email = user['email']
                email_verified = user['email_verified']
                token_expires = user['verification_token_expires']
            else:
                user_id, email, email_verified, token_expires = user
            
            if email_verified:
                cursor.close()
                conn.connection.close()
                return (True, "Email already verified")
            
            # Check if token has expired
            if token_expires and datetime.utcnow() > token_expires:
                cursor.close()
                conn.connection.close()
                return (False, "Verification token has expired. Please request a new one.")
            
            # Mark email as verified
            cursor.execute(
                """UPDATE users 
                SET email_verified = TRUE, verification_token = NULL, verification_token_expires = NULL 
                WHERE id = %s""",
                (user_id,)
            )
            conn.connection.commit()
            
            # Get user's name for welcome email
            cursor.execute("SELECT name FROM user_preferences WHERE user_id = %s", (user_id,))
            pref = cursor.fetchone()
            name = pref['name'] if isinstance(pref, dict) else pref[0] if pref else "User"
            
            cursor.close()
            conn.connection.close()
            
            # Send welcome email
            EmailService.send_welcome_email(email, name)
            
            logger.info(f"Email verified successfully for: {email}")
            return (True, "Email verified successfully! You can now log in.")
            
        except Exception as e:
            logger.error(f"Error verifying email: {e}")
            return (False, f"Email verification failed: {str(e)}")
    
    @staticmethod
    def resend_verification_email(email: str) -> Tuple[bool, str]:
        """
        Resend verification email
        
        Returns: (success, message)
        """
        try:
            conn = get_db_connection()
            conn.connect()
            cursor = conn.connection.cursor()
            
            # Get user
            cursor.execute(
                """SELECT u.id, u.email, u.email_verified
                FROM users u
                WHERE u.email = %s""",
                (email.lower(),)
            )
            user = cursor.fetchone()
            
            if not user:
                cursor.close()
                conn.connection.close()
                return (False, "Email not found")
            
            if isinstance(user, dict):
                user_id = user['id']
                user_email = user['email']
                email_verified = user['email_verified']
            else:
                user_id, user_email, email_verified = user
            
            if email_verified:
                cursor.close()
                conn.connection.close()
                return (False, "Email already verified")
            
            # Generate new verification token
            verification_token = EmailService.generate_verification_token()
            token_expires = EmailService.get_verification_token_expiry()
            
            # Update token
            cursor.execute(
                """UPDATE users 
                SET verification_token = %s, verification_token_expires = %s 
                WHERE id = %s""",
                (verification_token, token_expires, user_id)
            )
            conn.connection.commit()
            
            # Get user's name
            cursor.execute("SELECT name FROM user_preferences WHERE user_id = %s", (user_id,))
            pref = cursor.fetchone()
            name = pref['name'] if isinstance(pref, dict) else pref[0] if pref else "User"
            
            cursor.close()
            conn.connection.close()
            
            # Send verification email
            email_success, email_message = EmailService.send_verification_email(user_email, name, verification_token)
            if not email_success:
                return (False, email_message)
            
            logger.info(f"Verification email resent to: {email}")
            return (True, "Verification email sent. Please check your inbox.")
            
        except Exception as e:
            logger.error(f"Error resending verification email: {e}")
            return (False, f"Failed to resend verification email: {str(e)}")

