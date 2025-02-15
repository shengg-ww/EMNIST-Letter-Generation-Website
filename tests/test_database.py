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
# Test: Checking Saving Route and Saving into Database

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