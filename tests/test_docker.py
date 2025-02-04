import pytest
import requests
import base64
from application.models import User, Entry
from application import db, app
import json
import numpy as np
from sqlalchemy.exc import IntegrityError
# ------------------------------------------------------------------------#
# Test 3: Expected Failure when inputting out of range values directly into Database
# These should be expected failure because there are direct constraints for the database, faling the insertion of invalid data


@pytest.mark.parametrize("entry_data, expected_exception", [
    ({
        "user_id": 1,
        "letter": "ABC",
        "image_data": 150000000,  # Exceeds max range
    }, IntegrityError),

    # Invalid monthly premium (negative value)
    ({
        "user_id": 1,
        "letter": 1,
        "image_data": None,
    }, IntegrityError),
    # Invalid clv premium (negative value)
    ({
        "user_id": None,
        "letter": 'A'
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