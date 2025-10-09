"""
Authentication Routes

Provides endpoints for user registration, login, and session management
"""

from flask import Blueprint, request, jsonify
from functools import wraps
import logging
import re

from services.auth_service import AuthService

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

def require_auth(f):
    """Decorator to require authentication for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'No authorization token provided'}), 401
        
        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token[7:]
        
        payload = AuthService.verify_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Add user info to request context
        request.user_id = payload.get('user_id')
        request.user_email = payload.get('email')
        
        return f(*args, **kwargs)
    
    return decorated_function

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        email = data.get('email', '').strip()
        password = data.get('password', '')
        name = data.get('name', '').strip()
        
        if not email or not password or not name:
            return jsonify({'error': 'Email, password, and name are required'}), 400
        
        success, message, user_id = AuthService.register_user(email, password, name)
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'user_id': user_id
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 400
            
    except Exception as e:
        logger.error(f"Error in register endpoint: {e}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login a user and return JWT token"""
    try:
        data = request.get_json()
        
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        success, message, token, user_data = AuthService.login_user(email, password)
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'token': token,
                'user': user_data
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 401
            
    except Exception as e:
        logger.error(f"Error in login endpoint: {e}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/validate-password', methods=['POST'])
def validate_password():
    """Validate password strength (for registration form)"""
    try:
        data = request.get_json()
        password = data.get('password', '')
        
        is_valid, failures = AuthService.validate_password_strength(password)
        
        return jsonify({
            'is_valid': is_valid,
            'failures': failures,
            'requirements': {
                'min_length': len(password) >= 11,
                'has_uppercase': bool(re.search(r'[A-Z]', password)),
                'has_lowercase': bool(re.search(r'[a-z]', password)),
                'has_number': bool(re.search(r'\d', password)),
                'has_special': bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error in validate_password endpoint: {e}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/me', methods=['GET'])
@require_auth
def get_current_user():
    """Get current user info and preferences"""
    try:
        preferences = AuthService.get_user_preferences(request.user_id)
        
        return jsonify({
            'id': request.user_id,
            'email': request.user_email,
            'preferences': preferences
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_current_user endpoint: {e}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/preferences', methods=['PUT'])
@require_auth
def update_preferences():
    """Update user preferences"""
    try:
        data = request.get_json()
        
        success, message = AuthService.update_user_preferences(request.user_id, data)
        
        if success:
            return jsonify({
                'success': True,
                'message': message
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 400
            
    except Exception as e:
        logger.error(f"Error in update_preferences endpoint: {e}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/verify', methods=['GET'])
@require_auth
def verify_token():
    """Verify if token is valid"""
    return jsonify({
        'valid': True,
        'user_id': request.user_id,
        'email': request.user_email
    }), 200

@auth_bp.route('/verify-email/<token>', methods=['GET'])
def verify_email(token: str):
    """Verify email using verification token"""
    try:
        logger.info(f"Verifying email with token: {token[:20]}...")
        success, message = AuthService.verify_email_token(token)
        
        if success:
            logger.info(f"Email verification successful")
            return jsonify({
                'success': True,
                'message': message
            }), 200
        else:
            logger.warning(f"Email verification failed: {message}")
            return jsonify({
                'success': False,
                'error': message
            }), 400
            
    except Exception as e:
        logger.error(f"Error in verify_email endpoint: {e}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/resend-verification', methods=['POST'])
def resend_verification():
    """Resend verification email"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        success, message = AuthService.resend_verification_email(email)
        
        if success:
            return jsonify({
                'success': True,
                'message': message
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 400
            
    except Exception as e:
        logger.error(f"Error in resend_verification endpoint: {e}")
        return jsonify({'error': str(e)}), 500
