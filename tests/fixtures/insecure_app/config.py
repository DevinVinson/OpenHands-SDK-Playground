"""Configuration file with additional hardcoded secrets.

The auditor agent should also find these vulnerabilities.
"""

# More hardcoded secrets
STRIPE_SECRET_KEY = "sk_live_XXXXXXXXXXXXXXXXXXXXXXXX"
STRIPE_PUBLISHABLE_KEY = "pk_live_XXXXXXXXXXXXXXXXXXXXXXXX"

JWT_SECRET = "my-super-secret-jwt-key-dont-share"
SESSION_SECRET = "another-secret-that-should-not-be-here"

# Database config with embedded password
DATABASE_URL = "mysql://admin:password123@db.example.com:3306/production"

# Third-party service credentials
SENDGRID_API_KEY = "SG.xxxxxxxxxxxxxxxxxxxx"
TWILIO_AUTH_TOKEN = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"


class Config:
    """Application configuration."""

    DEBUG = True
    SECRET_KEY = JWT_SECRET
    DATABASE_URI = DATABASE_URL
