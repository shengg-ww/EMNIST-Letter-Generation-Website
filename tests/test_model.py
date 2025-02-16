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

# Validity Test for generation image words
@pytest.mark.parametrize("prompt, cmap, expected_status, expected_response", [
    ("A", "gray_r", 200, {"success": True}),  #  Valid single letter
    ("HELLO", "viridis", 200, {"success": True}),  #  Valid multi-letter input
    ("123", "gray_r", 400, {"success": False, "error": "Input must contain only letters (A-Z)."}),  #  Numbers not allowed
    ("A" * 151, "gray_r", 400, {"success": False, "error": "Input exceeds 150-character limit"}),  #  Exceed 150 letter limit
    ("HELLO", "invalid_cmap", 400, {"success": False, "error": "Invalid colormap"}),  #  Invalid colormap
])
def test_generate_image(client, prompt, cmap, expected_status, expected_response):
    """Test the model generation API with valid and invalid inputs."""
    response = client.post('/api/generate_image', json={"prompt": prompt, "cmap": cmap})

    assert response.status_code == expected_status
    assert response.get_json()["success"] == expected_response["success"]

    if "error" in expected_response:
        assert expected_response["error"] in response.get_json()["error"]  #  Now correctly matches the error message
