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



# ------------------------------------------------------------------------#
# Test 3: Expected Failure when inputting out of range values directly into Database
# These should be expected failure because there are direct constraints for the database, faling the insertion of invalid data


@pytest.mark.parametrize("entry_data, expected_exception", [

    ({
        "user_id": 1,
        "letter": 'A',
        "image_data": None, # Invalid image data
    }, IntegrityError),
    # Invalid user_id
    ({
        "user_id": None, #no user id
        "letter": 'A',
        "image_data": base64.b64encode(b'TestImageData').decode('utf-8'),  
    }, IntegrityError),
       ({
        "user_id": 1,
        "letter": 1,
        "image_data": base64.b64encode(b'TestImageData').decode('utf-8'),  
    }, ValueError),
])

# 3 expected failures
@pytest.mark.xfail(reason="Testing database constraints", strict=True)
def test_expected_failures_with_constraints(app, entry_data, expected_exception):
    with app.app_context():
        try:
            # Create the entry object with test data
            entry = Entry(**entry_data)

            # Attempt to add and commit the entry to the database
            db.session.add(entry)
            db.session.commit()

        except Exception as e:
            # Assert that the raised exception matches the expected one
            if expected_exception and isinstance(e, expected_exception):
                print(f"Expected failure occurred: {e}")
                raise  #  xfail
            else:
                print(f"Unexpected exception occurred: {e}")
                raise
        finally:
            # Rollback the session to clean up
            db.session.rollback()

# ------------------------------------------------------------------------#
# Test 4: Checking Saving Route and Saving into Database

# Parameterized test for valid and invalid inputs
@pytest.mark.parametrize("letter, image_data, expected_status, expected_response", [
    # Invalid cases
    ("AB", base64.b64encode(b"TestImageData").decode("utf-8"), 400, {"success": False, "error": "Invalid input"}),
    ("1", base64.b64encode(b"TestImageData").decode("utf-8"), 400, {"success": False, "error": "Invalid input"}),
    ("", base64.b64encode(b"TestImageData").decode("utf-8"), 400, {"success": False, "error": "Invalid input"}),
    ("B", None, 400, {"success": False, "error": "No image data provided"})
])
def test_api_save_letter(client, letter, image_data, expected_status, expected_response):
     # Mock login for testing
    with client.session_transaction() as session:
        session['_user_id'] = 1  # Mock user ID
    payload = {
        "letter": letter,
        "image": image_data
    }

    response = client.post("/api/save", json=payload)

    assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}"
    assert response.get_json() == expected_response, f"Expected {expected_response}, got {response.get_json()}"

    # Wrap DB queries in application context
    if expected_status == 200:
        with app.app_context():
            entry = Entry.query.filter_by(user_id=1, letter=letter).first()
            assert entry is not None, "Database entry was not created."
            assert entry.image_data == image_data, "Image data does not match."


#---------------------------------------------------------------------------------------------#
# Test 5: Consistency Testing of logging in with same user
# This test is used to evaluate whether the login can return the same response for different kinds of user inputs across mutliple occurences
@pytest.mark.parametrize("credentials, expected_status, expected_message", [
    ({"username": "admin", "password": "123"}, 200, "Login successful"),  # Valid login
    ({"username": "admin", "password": "123"}, 200, "Login successful"),  # Same valid login
    ({"username": "admin", "password": "122123"}, 401, "Invalid username or password"),  # Invalid password
    ({"username": "big_admin", "password": "123"}, 401, "Invalid username or password"),  # Non-existent user
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
# Test 4: Validity Testing of duplicate users registering 
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
# Test 6: Validity Testing for retrieval of history from database where user does not exist
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
