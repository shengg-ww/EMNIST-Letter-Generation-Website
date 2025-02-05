import pytest
from application import app as flask_app # Ensure this is your Flask app import
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


