import pytest
import sys
import os

# Add root directory to Python path so `pytest` can find `app.py`
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app as flask_app  #  Correct import for Flask app in root

from application.models import User

@pytest.fixture
def app():
    """Fixture to provide the Flask app for testing."""
    yield flask_app

@pytest.fixture
def client(app):
    """Fixture to provide a test client."""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    return app.test_client()


