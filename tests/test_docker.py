import pytest
import requests
import base64
from application.models import User, Entry
from application import db, app
import json
import numpy as np
from sqlalchemy.exc import IntegrityError



# ------------------------------------------------------------------------#
# Validity Test of Tensorflow Server

# Base URL of TensorFlow server
BASE_URL = "https://ca2-daaa2b02-2309123-limshengwei.onrender.com/v1/models/saved_cgan:predict"

# Function to generate the payload in the correct format
def generate_payload(prompt):
    if prompt == "Z":
        class_index = [0.0]
    else:
        class_index = [float(ord(prompt) - ord('A') + 1)]

    z_input = np.random.normal(0, 1, 100).tolist()  # Noise vector

    payload = {
        "signature_name": "serving_default",
        "instances": [{
            "input_13": z_input,  # Noise input
            "input_12": class_index  # Class index
        }]
    }
    return payload

# Test for different class prompts
@pytest.mark.parametrize("prompt", ["A", "M", "Z",'S','B'])
def test_model_prediction(prompt):
    payload = generate_payload(prompt)
    
    response = requests.post(BASE_URL, json=payload)
    
    assert response.status_code == 200, f"Prediction request failed with status code {response.status_code}"
    
    result = response.json()
    assert "predictions" in result, "No predictions found in the response"
    assert len(result["predictions"]) == 1, "Unexpected number of predictions returned"

    print(f"Prediction Output for class '{prompt}':", result["predictions"])

# ------------------------------------------------------------------------#
# Validity Test for Invalid Entry for Tensorflow Server
@pytest.mark.parametrize("invalid_payload", [
    # Missing 'input_12' (class index)
    {
        "signature_name": "serving_default",
        "instances": [{
            "input_13": np.random.normal(0, 1, 100).tolist()
        }]
    },

    # Incorrect data type for 'input_12' (should be a float list, not a string)
    {
        "signature_name": "serving_default",
        "instances": [{
            "input_13": np.random.normal(0, 1, 100).tolist(),
            "input_12": ["invalid_string"]
        }]
    },

    # Missing 'input_13' (noise vector)
    {
        "signature_name": "serving_default",
        "instances": [{
            "input_12": [1.0]
        }]
    },

    # Incorrect shape of 'input_13' (should be 100-dimensional)
    {
        "signature_name": "serving_default",
        "instances": [{
            "input_13": np.random.normal(0, 1, 50).tolist(),  # Only 50 elements instead of 100
            "input_12": [1.0]
        }]
    },

    # Completely malformed payload
    {
        "invalid_key": "invalid_value"
    }
])

def test_model_prediction_invalid(invalid_payload):
    response = requests.post(BASE_URL, json=invalid_payload)
    
     # Expecting a 400 Bad Request response for invalid inputs
    assert response.status_code == 400, f"Expected 400 Bad Request but got {response.status_code}"
