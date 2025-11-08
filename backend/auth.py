"""
OAuth Authentication Module for Scanner Server

This module provides OAuth 2.0 authentication support with configurable providers.
Users can bring their own OAuth provider (Google, GitHub, Azure AD, custom, etc.)
"""

import logging
import secrets
from functools import wraps
from flask import redirect, url_for, session, request, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from authlib.integrations.flask_client import OAuth
from .config import load_config

logger = logging.getLogger(__name__)

# User model for Flask-Login
class User(UserMixin):
    def __init__(self, user_id, email=None, name=None):
        self.id = user_id
        self.email = email
        self.name = name

# Initialize Flask-Login
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    """Load user from session"""
    user_data = session.get('user')
    if user_data and user_data.get('id') == user_id:
        return User(
            user_id=user_data['id'],
            email=user_data.get('email'),
            name=user_data.get('name')
        )
    return None

@login_manager.unauthorized_handler
def unauthorized():
    """Handle unauthorized access"""
    from flask import render_template
    if request.headers.get('Accept') == 'application/json':
        return jsonify({
            'success': False,
            'error': 'Authentication required',
            'login_url': url_for('auth_login', _external=True)
        }), 401
    # Show login page instead of redirecting
    return render_template('login.html'), 401

# Initialize OAuth
oauth = OAuth()

def init_oauth(app):
    """Initialize OAuth with Flask app"""
    # Set secret key for session management
    if not app.config.get('SECRET_KEY'):
        app.config['SECRET_KEY'] = secrets.token_hex(32)
        logger.warning("Generated random SECRET_KEY. Set a persistent SECRET_KEY in production!")

    # Initialize login manager
    login_manager.init_app(app)
    login_manager.login_view = 'auth_login'

    # Initialize OAuth
    oauth.init_app(app)

    # Register OAuth client dynamically based on config
    config = load_config()
    oauth_config = config.get('oauth', {})

    if oauth_config.get('enabled'):
        register_oauth_client(oauth_config)

def register_oauth_client(oauth_config):
    """Register OAuth client with the configured provider"""
    try:
        provider = oauth_config.get('provider', 'custom')

        # Common OAuth client configuration
        client_kwargs = {
            'scope': oauth_config.get('scope', 'openid profile email')
        }

        # Predefined provider configurations
        if provider == 'google':
            oauth.register(
                name='oauth_provider',
                server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
                client_id=oauth_config.get('client_id'),
                client_secret=oauth_config.get('client_secret'),
                client_kwargs=client_kwargs
            )
        elif provider == 'github':
            oauth.register(
                name='oauth_provider',
                access_token_url='https://github.com/login/oauth/access_token',
                authorize_url='https://github.com/login/oauth/authorize',
                api_base_url='https://api.github.com/',
                client_id=oauth_config.get('client_id'),
                client_secret=oauth_config.get('client_secret'),
                client_kwargs={'scope': 'user:email'}
            )
        elif provider == 'azure':
            tenant_id = oauth_config.get('tenant_id', 'common')
            oauth.register(
                name='oauth_provider',
                server_metadata_url=f'https://login.microsoftonline.com/{tenant_id}/v2.0/.well-known/openid-configuration',
                client_id=oauth_config.get('client_id'),
                client_secret=oauth_config.get('client_secret'),
                client_kwargs=client_kwargs
            )
        else:
            # Custom provider
            oauth.register(
                name='oauth_provider',
                client_id=oauth_config.get('client_id'),
                client_secret=oauth_config.get('client_secret'),
                authorize_url=oauth_config.get('authorization_url'),
                access_token_url=oauth_config.get('token_url'),
                userinfo_endpoint=oauth_config.get('userinfo_url'),
                client_kwargs=client_kwargs
            )

        logger.info(f"OAuth client registered for provider: {provider}")
    except Exception as e:
        logger.exception(f"Failed to register OAuth client: {e}")

def is_user_allowed(email):
    """Check if user email is in the allowed list"""
    config = load_config()
    oauth_config = config.get('oauth', {})
    allowed_users = oauth_config.get('allowed_users', [])

    # If no allowed users specified, allow all authenticated users
    if not allowed_users:
        return True

    # Check if user email is in allowed list
    return email in allowed_users

def auth_required(f):
    """Decorator to protect routes with OAuth authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        config = load_config()
        oauth_config = config.get('oauth', {})

        # If OAuth is not enabled, allow access
        if not oauth_config.get('enabled'):
            return f(*args, **kwargs)

        # If OAuth is enabled, require authentication
        if not current_user.is_authenticated:
            return login_manager.unauthorized()

        return f(*args, **kwargs)

    return decorated_function

def login():
    """Initiate OAuth login flow"""
    config = load_config()
    oauth_config = config.get('oauth', {})

    if not oauth_config.get('enabled'):
        return jsonify({
            'success': False,
            'error': 'OAuth is not enabled'
        }), 400

    redirect_uri = oauth_config.get('redirect_uri', url_for('auth_callback', _external=True))
    return oauth.oauth_provider.authorize_redirect(redirect_uri)

def callback():
    """Handle OAuth callback"""
    try:
        config = load_config()
        oauth_config = config.get('oauth', {})

        # Get access token
        token = oauth.oauth_provider.authorize_access_token()

        # Get user info
        provider = oauth_config.get('provider', 'custom')

        if provider == 'github':
            # GitHub uses a different API for user info
            resp = oauth.oauth_provider.get('user')
            user_info = resp.json()
            email = user_info.get('email')
            if not email:
                # Try to get primary email from emails endpoint
                emails_resp = oauth.oauth_provider.get('user/emails')
                emails = emails_resp.json()
                for email_obj in emails:
                    if email_obj.get('primary'):
                        email = email_obj.get('email')
                        break
            name = user_info.get('name') or user_info.get('login')
            user_id = str(user_info.get('id'))
        else:
            # Standard OpenID Connect userinfo endpoint
            user_info = oauth.oauth_provider.userinfo()
            email = user_info.get('email')
            name = user_info.get('name') or user_info.get('preferred_username')
            user_id = user_info.get('sub') or user_info.get('id')

        # Check if user is allowed
        if not is_user_allowed(email):
            logger.warning(f"Unauthorized login attempt from: {email}")
            return jsonify({
                'success': False,
                'error': 'Your account is not authorized to access this application'
            }), 403

        # Create user session
        user = User(user_id=user_id, email=email, name=name)
        login_user(user)

        # Store user info in session
        session['user'] = {
            'id': user_id,
            'email': email,
            'name': name
        }

        logger.info(f"User logged in: {email}")

        # Redirect to home page
        return redirect(url_for('index'))

    except Exception as e:
        logger.exception(f"OAuth callback error: {e}")
        return jsonify({
            'success': False,
            'error': 'Authentication failed'
        }), 400

def logout_user_route():
    """Handle user logout"""
    if current_user.is_authenticated:
        logger.info(f"User logged out: {session.get('user', {}).get('email')}")

    logout_user()
    session.clear()

    return redirect(url_for('index'))

def test_oauth_config(oauth_settings):
    """Test OAuth configuration"""
    try:
        required_fields = {
            'custom': ['client_id', 'client_secret', 'authorization_url', 'token_url', 'userinfo_url'],
            'google': ['client_id', 'client_secret'],
            'github': ['client_id', 'client_secret'],
            'azure': ['client_id', 'client_secret', 'tenant_id']
        }

        provider = oauth_settings.get('provider', 'custom')
        required = required_fields.get(provider, required_fields['custom'])

        missing_fields = [field for field in required if not oauth_settings.get(field)]

        if missing_fields:
            return {
                'success': False,
                'error': f"Missing required fields: {', '.join(missing_fields)}"
            }

        # Validate URLs for custom provider
        if provider == 'custom':
            urls = ['authorization_url', 'token_url', 'userinfo_url']
            for url_field in urls:
                url = oauth_settings.get(url_field, '')
                if not url.startswith('https://') and not url.startswith('http://'):
                    return {
                        'success': False,
                        'error': f"Invalid URL format for {url_field}"
                    }

        return {
            'success': True,
            'message': 'OAuth configuration is valid'
        }

    except Exception as e:
        logger.exception(f"Error testing OAuth config: {e}")
        return {
            'success': False,
            'error': str(e)
        }
