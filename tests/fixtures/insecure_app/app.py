"""Sample application with security issues for testing the Auditor agent.

This file intentionally contains hardcoded secrets that the auditor agent
should detect and suggest moving to environment variables.
"""

import requests

# SECURITY ISSUE: Hardcoded API key
API_KEY = "sk-ant-api03-XXXXXXXXXXXXXXXXXXXXXXXXXXXXX"

# SECURITY ISSUE: Hardcoded database password
DB_PASSWORD = "super_secret_password_123"

# SECURITY ISSUE: Hardcoded AWS credentials
AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"


def connect_to_api():
    """Connect to external API using hardcoded key."""
    return requests.get(f"https://api.example.com?key={API_KEY}")


def connect_to_db():
    """Get database connection string with hardcoded password."""
    return f"postgresql://user:{DB_PASSWORD}@localhost/db"


def get_aws_client():
    """Create AWS client using hardcoded credentials."""
    # This is insecure - credentials should come from environment
    return {
        "access_key": AWS_ACCESS_KEY,
        "secret_key": AWS_SECRET_KEY,
    }


if __name__ == "__main__":
    print("This app has security vulnerabilities!")
    print(f"API Key (exposed!): {API_KEY[:10]}...")
