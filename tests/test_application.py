import pytest
import requests
import base64
from application.models import User, Entry
from application import db, app
import json
import numpy as np
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import random
import string
import time
import base64
from flask import url_for
from werkzeug.security import check_password_hash, generate_password_hash

from unittest.mock import patch



# Test to ensure @login_required works; Prevents unauthroised users access
def test_protected_route_requires_login(client):
    """Ensure protected routes are inaccessible without login."""
    response = client.get('/history')  # Should redirect to login
    assert response.status_code == 302  # Redirect
    assert "/index" in response.location  # Redirects to login






#---------------------------------------------------------------------------------------------#
# Consistency Testing of logging in with same user
# This test is used to evaluate whether the login can return the same response for different kinds of user inputs across mutliple occurences
@pytest.mark.parametrize("credentials, expected_status, expected_message", [
    ({"username": "admin", "password": "1"}, 200, "Login successful"),  # Valid login
    ({"username": "admin", "password": "1"}, 200, "Login successful"),  # Same valid login
    ({"username": "admin", "password": "122123"}, 401, "Invalid username or password"),  # Invalid password
    ({"username": "big_admin", "password": "1"}, 401, "Invalid username or password"),  # Non-existent user
])
def test_api_login_consistency(client, credentials, expected_status, expected_message):


    # Perform first login
    response1 = client.post('/api/login', json=credentials)
    assert response1.status_code == expected_status
    if expected_status == 200:
        assert response1.json.get('message') == expected_message
    else:
        assert response1.json.get('error') == expected_message

    # Perform second login with the same credentials
    response2 = client.post('/api/login', json=credentials)
    assert response2.status_code == expected_status
    if expected_status == 200:
        assert response2.json.get('message') == expected_message
    else:
        assert response2.json.get('error') == expected_message

    # Ensure the responses are consistent
    assert response1.json == response2.json, f"Inconsistent login responses: {response1.json} != {response2.json}"




# --------------------------------------------------------------------------------------------------------------------------#
#  Validity Testing of duplicate users registering 
# This test is to check whether the regsiter form rejects duplicate usernames or emails and return appropriate error messages.
@pytest.mark.parametrize("payload, expected_error", [
    ({
        "username": "admin",  # Pre-existing username
        "email": "admin123@gmail.com",
        "password": "password",
        "confirm_password": "password"
    }, "Username already exists"),
    ({
        "username": "admin123",
        "email": "admin@gmail.com",  # Pre-existing email
        "password": "password123",
        "confirm_password": "password123"
    }, "Email already exists"),
])
def test_api_register(client,payload, expected_error):

    # Test the API
    response = client.post('/api/register', json=payload)
    assert response.status_code == 400
    response_data = response.get_json()
    assert expected_error in response_data.get("error", "")


# -------------------------------------------------------------------------------------------------------------------------------------------------------#
# Validity Testing for retrieval of history from database where user does not exist
# Ensure that when provided with a non-existent user_id, return an appropriate error message and status code.
@pytest.mark.parametrize("user_id, expected_error, expected_status", [
    (999, "User not found", 404),  # Non-existent user ID
])

def test_get_user_history_expected_failures(client, user_id, expected_error, expected_status):
    # Mock login for testing
    with client.session_transaction() as session:
        session['_user_id'] = 1  # Mock user ID

    # Send a GET request to the history API
    response = client.get(f'/api/history/{user_id}')
    
    # Validate the response
    assert response.status_code == expected_status, f"Expected status {expected_status}, got {response.status_code}"
    response_data = response.get_json()
    assert response_data is not None, "Expected a JSON response"
    assert "error" in response_data, "Expected 'error' key in response"
    assert response_data["error"] == expected_error, f"Unexpected error message: {response_data['error']}"



# Test to check for valid email in forget password

@pytest.mark.parametrize("email, expected_status, success", [
    ("admin@gmail.com", 200, True),  #  Valid user - should return 200
    ("invalid@example.com", 404, False),  #  Invalid user - should return 404
])
def test_submit_email(client, email, expected_status, success):
    """Test email submission for password reset."""
    response = client.post('/api/forget_password', json={"email": email})

    assert response.status_code == expected_status
    data = response.get_json()
    if success:
        assert data["success"] is True
        assert data["message"] == "Email verified"
    else:
        assert data["success"] is False
        assert data["error"] == "Email not found"



# Test Password Reset functionality; Password must match
@pytest.mark.parametrize("new_password, confirm_password, expected_status, expected_response", [
    ("NewPass123!", "NewPass123!", 200, {"success": True, "message": "Password updated successfully!"}),  # Matching passwords
    ("NewPass123!", "WrongPass!", 400, {"success": False, "error": "Passwords must match"}),  #  Mismatched passwords
])
def test_password_reset(client, new_password, confirm_password, expected_status, expected_response):
    """Test password reset without actually modifying the database."""

    with patch("application.routes.db.session.commit") as mock_commit, \
         patch("application.routes.generate_password_hash", return_value="MOCKED_HASH") as mock_hash:
        
        response = client.post('/api/forget_password', json={
            "email": "admin@gmail.com",
            "new_password": new_password,
            "confirm_password": confirm_password
        })

        assert response.status_code == expected_status
        assert response.get_json() == expected_response

 

# Test for invalid user reset password
def test_password_reset_invalid_user(client):
    """Test password reset for a user that does not exist."""
    response = client.post('/api/forget_password', json={
        "email": "unknown@example.com",
        "new_password": "SomePass123!",
        "confirm_password": "SomePass123!"
    })

    assert response.status_code == 404
    assert response.get_json() == {"success": False, "error": "Email not found"}

