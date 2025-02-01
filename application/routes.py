from application import app
from flask import render_template, request, flash, url_for ,redirect,jsonify
from application.forms import LoginForm,RegisterForm
from .models import User, Entry
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from flask_cors import CORS, cross_origin
from tensorflow.keras.preprocessing import image
from PIL import Image, ImageOps
from application import db
import numpy as np
import tensorflow.keras.models
from werkzeug.security import check_password_hash, generate_password_hash
import re
import base64
from io import BytesIO
from datetime import datetime
import json
import numpy as np
import requests
import pathlib, os
import json
import tensorflow as tf
import requests
import io  # 
import matplotlib.pyplot as plt  # 
from collections import Counter


#Handles http://127.0.0.1:5000/
@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title="SW Labs", css_file='css/index.css', current_page="index")


# <---------------------------------------------- FLASK-LOGIN --------------------------------------------<
# Initialize Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'index'


@login_manager.user_loader
def load_user(user_id):
   return db.session.get(User, int(user_id))


@login_manager.unauthorized_handler

def unauthorized():
    flash("You must log in to access this page.", "warning")
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        # Query the database for the user
        user = User.query.filter_by(username=username).first()

        # Check if the user exists and the password is correct
        if user and check_password_hash(user.password, password):
            login_user(user)  # Log the user in
            flash("Login successful!", "success")
            return redirect(url_for('home'))  # Redirect 
        else:
            form.username.errors.append("Invalid username or password")  

    return render_template('login.html', title="Login", css_file='css/main.css', form=form, current_page="index")


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data

        # Check for duplicate username or email
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            if existing_user.username == username:
                flash("Username already exists!", "danger")
                form.username.errors.append("Username already exists")
             
            if existing_user.email == email:
                flash("Email already exists!", "danger")
                form.email.errors.append("Email already exists")
                
            return render_template('register.html', title="Register", css_file='css/main.css', form=form, current_page='register')
             
        else:
            # Hash the password before storing it
            hashed_password = generate_password_hash(password)

            # Create a new user
            new_user = User(username=username, email=email, password=hashed_password, role="user")
            db.session.add(new_user)
            db.session.commit()

            flash("Registration successful! You can now log in.", "success")
            return redirect(url_for('index'))  # Redirect to login page

    # Flash any other form validation errors (e.g., field length, invalid input)
    if form.errors:
        for field_name, error_messages in form.errors.items():
            for error in error_messages:
                flash(f"Error in {field_name}: {error}", "danger")

    return render_template('register.html', title="Register", css_file='css/main.css', form=form, current_page='register')




@app.route('/logout')
@login_required
def logout():
    """Logout route."""
    logout_user()  # Log the user out
    flash("You have been logged out.", "info")
    return redirect(url_for('index'))

@app.route('/home')
@login_required
def home():
    # Get the username of the logged-in user
    username = current_user.username
    return render_template("home.html",title='Home', css_file='css/main.css', current_page="home", username=username)

@app.route('/generate', methods=['GET'])
@login_required
@cross_origin(origin='localhost', headers=['Content-Type', 'Authorization'])
def generate():
    """
    Renders the UI for generating images.
    """
    return render_template('generate.html', css_file='css/main.css', current_page='generate')

# TensorFlow Serving API URL
GAN_SERVER_URL = 'https://ca2-daaa2b02-2309123-limshengwei.onrender.com/v1/models/saved_cgan:predict'
@app.route('/proxy_generate', methods=['GET','POST'])
def proxy_generate():
    try:
        # Parse input JSON from frontend
        data = request.get_json()
        if not data or 'prompt' not in data:
            return jsonify({"success": False, "error": "Invalid input"}), 400

        # Validate input letter
        prompt = data['prompt'].strip().upper()
        if len(prompt) != 1 or not prompt.isalpha():
            return jsonify({"success": False, "error": "Input must be a single letter (A-Z)."}), 400
        # ✅ Convert letter to class index based on your model's convention
        if prompt == "Z":
                class_index =[0.0]
        else:
                class_index =[float(ord(prompt) - ord('A')+1)] 

        z_input = np.random.normal(0, 1, 100).tolist()  # Shape: (100,)

        # Construct payload for TensorFlow Serving
        payload = {
            "signature_name": "serving_default",
            "instances": [{
                "input_13": z_input,  # Noise input
                "input_12": class_index  # Class index
            }]
        }

        # Send request to TensorFlow Serving
        response = requests.post(GAN_SERVER_URL, json=payload)
        response.raise_for_status()  # Raise error for bad responses
        result = response.json()

        if "predictions" not in result or not result["predictions"]:
            return jsonify({"success": False, "error": "Invalid response from TensorFlow Serving"}), 500

        # Extract generated image tensor and reshape
        generated_image = np.array(result["predictions"][0]).reshape(28, 28)

        # Convert image to Base64 for frontend display
        img_bytes = io.BytesIO()
        plt.imsave(img_bytes, generated_image, cmap="gray_r", format='png')
        img_bytes.seek(0)
        base64_image = base64.b64encode(img_bytes.getvalue()).decode('utf-8')

        # Return Base64 encoded image
        return jsonify({"success": True, "image": base64_image})

    except requests.exceptions.RequestException as e:
        return jsonify({"success": False, "error": f"TensorFlow Serving error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    
        
@app.route("/save", methods=["POST"])
@login_required  # Ensure the user is logged in
def save_letter():
    data = request.json
    letter = data.get("letter", "").strip().upper()  # Strip spaces and enforce uppercase
    image_base64 = data.get("image")  # Base64 encoded image from frontend

     # Remove unnecessary surrounding quotes if they exist
    if letter.startswith('"') and letter.endswith('"'):
        letter = letter[1:-1]

    if not letter or not letter.isalpha() or len(letter) != 1:
        flash("Invalid input! Please enter a single letter.", "danger")
        return jsonify({"success": False, "error": "Invalid input"}), 400

    # Get the logged-in user ID
    user_id = current_user.id  

    # Ensure user_id is not None
    if not user_id:
        flash("User not authenticated.", "danger")
        return jsonify({"success": False, "error": "User not authenticated"}), 403  # Forbidden
    
    if not image_base64:
        return jsonify({"success": False, "error": "No image data provided"}), 400

    # Save new entry
    new_entry = Entry(user_id=user_id, letter=letter,image_data=image_base64,  timestamp=datetime.utcnow())
    db.session.add(new_entry)
    db.session.commit()

    flash(f"Letter '{letter}' saved successfully!", "success")
    return jsonify({"success": True, "message": "Saved successfully!"}), 200
    

@app.route("/history", methods=['GET','POST'])
@login_required
def history():
    entries = Entry.query.filter_by(user_id=current_user.id).all()
    # Display most recent letters first
    sorted_entries = sorted(entries, key=lambda x: x.timestamp, reverse=True)
    # Get the username of the logged-in user
    username = current_user.username
    return render_template('history.html', title='History', css_file='css/index.css', current_page='history', entries=sorted_entries, username=username)


@app.route('/toggle_favorite/<int:entry_id>', methods=['POST'])
def toggle_favorite(entry_id):
    # Fetch the entry from the database, or return 404 if not found
    entry = Entry.query.get_or_404(entry_id)
    
    # Toggle the favorite status
    entry.is_favorite = not entry.is_favorite
    
    # Commit the changes to the database
    db.session.commit()
    
    return redirect(url_for('history'))

# route for removing entries
@app.route('/remove/<int:entry_id>', methods=['POST'])
@login_required
def remove_entry(entry_id):
    entry = Entry.query.get_or_404(entry_id)
    print(entry)
    if entry.user_id != current_user.id:
        flash("You don't have permission to delete this record.", "danger")
        return redirect(url_for('history'))

    try:
        db.session.delete(entry)
        db.session.commit()
        flash(f"Entry with ID {entry.id} deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting entry: {str(e)}", "danger")

    return redirect(url_for('history'))

@app.route('/profile', methods=['GET'])
@login_required
def profile():
    # Fetch all entries for the current user
    user_entries = Entry.query.filter_by(user_id=current_user.id).all()

    # Total Predictions
    total_predictions = len(user_entries)
    
    # Favorite Predictions
    favorite_entries = [entry for entry in user_entries if entry.is_favorite]
    total_favorites = len(favorite_entries)
    
    # Favorite Percentage
    favorite_percentage = (total_favorites / total_predictions) * 100 if total_predictions > 0 else 0

    # Most Predicted Letter
    letters = [entry.letter for entry in user_entries]
  
    letter_counts = Counter(letters)

    # Most and least predicted letters
    most_predicted_letter = letter_counts.most_common(1)[0][0] if letter_counts else 'N/A'
    least_predicted_letter = letter_counts.most_common()[-1][0] if letter_counts else 'N/A'

    # First Prediction Date
    first_prediction_date = min((entry.timestamp for entry in user_entries), default='N/A')


    # Last Prediction Date (to show recent activity)
    last_prediction_date = max((entry.timestamp for entry in user_entries), default='N/A')


    return render_template('profile.html',
                            title='Profile',
                            css_file='css/index.css',
                           username=current_user.username,
                           date_joined=current_user.date_joined,
                           total_predictions=total_predictions,
                           total_favorites=total_favorites,
                           favorite_percentage=favorite_percentage,
                           most_predicted_letter=most_predicted_letter,
                           least_predicted_letter=least_predicted_letter,
                           first_prediction_date=first_prediction_date,
                           last_prediction_date=last_prediction_date,
                           favorite_entries=favorite_entries)