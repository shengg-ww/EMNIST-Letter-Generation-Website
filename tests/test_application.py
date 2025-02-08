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
        "letter": "ABC", #invalid length
        "image_data": base64.b64encode(b'TestImageData').decode('utf-8'),  
    }, IntegrityError),

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
    }, IntegrityError),
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



#---------------------------------------------------------------------------------------------#
# Test 6: Range Testing of retriveing history data 
# This test is used to evaluate whether the application can handle the large amount of history data, to also test chunk retrival of inifnite scrolling
def test_history_performance(client, app):
    with client.session_transaction() as session:
        session['_user_id'] = 1  # Mock user ID

    # Insert 100,000 predictions with valid image data
    inserted_entries = []  # To store references to the inserted entries
    with app.app_context():
        dummy_image_data = base64.b64encode(b"DummyImageData").decode('utf-8')
        for _ in range(100000):
            entry = Entry(
                user_id=1,
                letter=random.choice(string.ascii_uppercase),
                image_data=dummy_image_data,
                timestamp=datetime.now()
            )
            db.session.add(entry)
            inserted_entries.append(entry)  # Track inserted entry

        db.session.commit()

    # Measure the response time of the /history route
    start_time = time.time()
    response = client.get('/history')
    end_time = time.time()

    response_time = end_time - start_time

    # Check if the response is successful
    assert response.status_code == 200

    # Assert that the response time is within an acceptable range (e.g., < 1 seconds)
    assert response_time < 1, f"Response time was too slow: {response_time:.2f} seconds"

    # Cleanup: Delete only the mock entries inserted during the test
    with app.app_context():
        # Use the IDs or timestamps of the inserted entries to delete only those
        for entry in inserted_entries:
            db.session.delete(entry)  # Delete each inserted entry individually

        db.session.commit()
