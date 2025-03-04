from application import app
from flask import render_template, request, flash, url_for ,redirect,jsonify
from application.forms import LoginForm,RegisterForm, ForgetPasswordForm
from .models import User, Entry
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from flask_cors import CORS, cross_origin
from PIL import Image, ImageOps
from application import db
from sqlalchemy import or_
import numpy as np
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
import re 
import io  # 
import matplotlib.pyplot as plt  # 
from collections import Counter
from sqlalchemy import func, desc, case
import asyncio
import aiohttp
import os

#Handles http://127.0.0.1:5000/
@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title="SW Labs", css_file='css/index.css', current_page="index")
# TensorFlow Serving API URL
GAN_SERVER_URL = 'https://ca2-daaa2b02-2309123-limshengwei.onrender.com/v1/models/saved_cgan:predict'

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
            payload = {
                "signature_name": "serving_default",
                "instances": [{"input_13":  np.random.normal(0, 1, 100).tolist(), "input_12": [0.0]}]
            }

            response = requests.post(GAN_SERVER_URL, json=payload)
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
    return render_template("home.html",title='Home', css_file='css/home.css', current_page="home", username=username)

@app.route('/generate', methods=['GET'])
@login_required
@cross_origin(origin='localhost', headers=['Content-Type', 'Authorization'])
def generate():
    """
    Renders the UI for generating images.
    """
    return render_template('generate.html', title='Generate', css_file='css/main.css', current_page='generate')



@app.route('/generate_image', methods=['POST'])
def generate_image():
    try:
        data = request.get_json()
        if not data or 'prompt' not in data:
            return jsonify({"success": False, "error": "Invalid input"}), 400

        prompt = data['prompt'].strip().upper()
        if not all(char.isalpha() or char.isspace() for char in prompt):
            return jsonify({"success": False, "error": "Input must contain only letters (A-Z)."}), 400

        cmap = data.get('cmap', 'gray_r')
        available_cmaps = plt.colormaps()
        if len(prompt) > 150:
            return jsonify({"success": False, "error": "Input exceeds 150-character limit"}), 400

        if cmap not in available_cmaps:
            return jsonify({"success": False, "error": f"Invalid colormap. Choose from {available_cmaps}."}), 400

        generated_images = []

        for letter in prompt:
            if letter == " ":
                # Generate a blank image that matches the colormap
                blank_image = np.zeros((28, 28))  # Start with all zeros (low-end of cmap)
                img_bytes = io.BytesIO()
                plt.imsave(img_bytes, blank_image, cmap=cmap, format='png')
                img_bytes.seek(0)
                base64_image = base64.b64encode(img_bytes.getvalue()).decode('utf-8')
                generated_images.append(base64_image)
                continue

            class_index = [float(ord(letter) - ord('A') + 1)] if letter != "Z" else [0.0]
            z_input = np.random.normal(0, 1, 100).tolist()

            payload = {
                "signature_name": "serving_default",
                "instances": [{"input_13": z_input, "input_12": class_index}]
            }

            response = requests.post(GAN_SERVER_URL, json=payload)
            response.raise_for_status()
            result = response.json()

            if "predictions" not in result or not result["predictions"]:
                return jsonify({"success": False, "error": "Invalid response from TensorFlow Serving"}), 500

            generated_image = np.array(result["predictions"][0]).reshape(28, 28)

            img_bytes = io.BytesIO()
            plt.imsave(img_bytes, generated_image, cmap=cmap, format='png')
            img_bytes.seek(0)
            base64_image = base64.b64encode(img_bytes.getvalue()).decode('utf-8')

            generated_images.append(base64_image)

        return jsonify({"success": True, "images": generated_images})

    except requests.exceptions.RequestException as e:
        return jsonify({"success": False, "error": f"TensorFlow Serving error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

    

@app.route("/save", methods=["POST"])
@login_required  # Ensure the user is logged in
def save_text():
    data = request.json
    text = data.get("text", "").strip().upper()  # Store full text, not just one letter
    image_base64 = data.get("image")  # Base64 encoded merged image from frontend
    colormap = data.get("cmap", "").strip()  # Receive the colormap

    # Ensure user is authenticated
    user_id = current_user.id  
    if not user_id:
        return jsonify({"success": False, "error": "User not authenticated"}), 403  

    # Validate input
    if not text or not image_base64:
        print(text)
        print(image_base64)
        return jsonify({"success": False, "error": "Missing text or image data"}), 400

    if not colormap:
        return jsonify({"success": False, "error": "No colormap provided"}), 400

    # Validate colormap (ensure it's a valid colormap)
    available_cmaps = plt.colormaps()
    if colormap not in available_cmaps:
        return jsonify({"success": False, "error": f"Invalid colormap. Choose from {available_cmaps}."}), 400

    # Remove unnecessary surrounding quotes
    text = text.replace('"', '')

    try:
        # Save new entry in the database (no need to save as a PNG)
        new_entry = Entry(
            user_id=user_id,
            letter=text,  # Store full word/sentence
            image_data=image_base64,  # Store Base64 image directly
            colormap=colormap,
            timestamp=datetime.utcnow()
        )
        db.session.add(new_entry)
        db.session.commit()

        return jsonify({"success": True, "message": f'Text "{text}" saved successfully!'}), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    


@app.route("/history", methods=['GET'])
@login_required
def history():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    sort_by = request.args.get('sort_by', 'recent')
    search_query = request.args.get('search', '').strip().lower()  # Case insensitive search
    show_favorites = request.args.get('favorites', 'false').lower() == 'true'
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    colormap_filter = request.args.get('colormaps', '')

    query = Entry.query.filter_by(user_id=current_user.id)

    # 🔹 1. SEARCH FUNCTION - Allow matching **letters inside words/sentences**
    if search_query:
        query = query.filter(Entry.letter.ilike(f"%{search_query}%"))  # Case-insensitive match


    # 🔹 2. FILTER FAVORITES
    if show_favorites:
        query = query.filter(Entry.is_favorite.is_(True))

    # 🔹 3. FILTER BY DATE RANGE
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Entry.timestamp >= start_date_obj)
        except ValueError:
            return jsonify({'entries': [], 'has_next': False, 'error': 'Invalid start date format'}), 400

    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            query = query.filter(Entry.timestamp <= end_date_obj)
        except ValueError:
            return jsonify({'entries': [], 'has_next': False, 'error': 'Invalid end date format'}), 400

    # 🔹 4. FILTER BY COLORMAP
    if colormap_filter:
        colormap_list = colormap_filter.split(',')
        query = query.filter(Entry.colormap.in_(colormap_list))

    # 🔹 5. SORTING OPTIONS
    if sort_by == 'recent':
        query = query.order_by(Entry.timestamp.desc())
    elif sort_by == 'oldest':
        query = query.order_by(Entry.timestamp.asc())
    elif sort_by == 'colormap':
        query = query.order_by(Entry.colormap)

    # 🔹 6. PAGINATION
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    entries = pagination.items

    # 🔹 7. AJAX RESPONSE
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        entries_data = [{
            'id': entry.id,
            'letter': entry.letter,
            'timestamp': entry.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'is_favorite': entry.is_favorite,
            'image_data': entry.image_data,
            'colormap': entry.colormap
        } for entry in entries]

        return jsonify({
            'entries': entries_data,
            'has_next': pagination.has_next,
            'current_page': pagination.page
        })

    # 🔹 8. RENDER TEMPLATE
    return render_template('history.html',
                           title='History',
                           css_file='css/history.css',
                           current_page='history',
                           entries=entries,
                           username=current_user.username)


@app.route('/toggle_favorite/<int:entry_id>', methods=['POST'])
def toggle_favorite(entry_id):
    # Fetch the entry from the database, or return 404 if not found
    entry = Entry.query.get_or_404(entry_id)
    
    # Toggle the favorite status
    entry.is_favorite = not entry.is_favorite
    
    # Commit the changes to the database
    db.session.commit()
    
    return jsonify({'success': True, 'is_favorite': entry.is_favorite})
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

@app.route('/remove_all', methods=['POST'])
@login_required
def remove_all_entries():
    
    user_entries = Entry.query.filter_by(user_id=current_user.id).all()

    if not user_entries:
        flash("No entries to delete.", "warning")
        return redirect(url_for('history'))

    try:
        for entry in user_entries:
            db.session.delete(entry)
        db.session.commit()
        flash("All your entries have been deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting entries: {str(e)}", "danger")

    return redirect(url_for('history'))


@app.route('/profile', methods=['GET'])
@login_required
def profile():
    user_id = current_user.id

    # Combined query to fetch total predictions, favorites, first and last dates
    aggregated_data = db.session.query(
        func.count(Entry.id).label('total_predictions'),
        func.sum(case((Entry.is_favorite == True, 1), else_=0)).label('total_favorites'),
        func.min(Entry.timestamp).label('first_prediction_date'),
        func.max(Entry.timestamp).label('last_prediction_date')
    ).filter(Entry.user_id == user_id).one()

    total_predictions = aggregated_data.total_predictions
    total_favorites = aggregated_data.total_favorites or 0
    first_prediction_date = aggregated_data.first_prediction_date or 'N/A'
    last_prediction_date = aggregated_data.last_prediction_date or 'N/A'

    # Calculate favorite percentage
    favorite_percentage = (total_favorites / total_predictions) * 100 if total_predictions > 0 else 0

        # Query to find both most and least common colormap in one go
    colormap_counts = db.session.query(
        Entry.colormap, func.count(Entry.colormap).label('count')
    ).filter_by(user_id=user_id).group_by(Entry.colormap).order_by(desc('count')).all()

    # Get the most common and least common colormap
    most_common_colormap = colormap_counts[0][0] if colormap_counts else 'N/A'
    least_common_colormap = colormap_counts[-1][0] if colormap_counts else 'N/A'

    # Retrieve favorite entries for display (optional, depending on UI needs)
    favorite_entries = []
    if total_favorites > 0:
        favorite_entries = Entry.query.filter_by(user_id=user_id, is_favorite=True).all()

    return render_template('profile.html',
                           title='Profile',
                           css_file='css/profile.css',
                           username=current_user.username,
                           date_joined=current_user.date_joined,
                           total_predictions=total_predictions,
                           total_favorites=total_favorites,
                           favorite_percentage=favorite_percentage,
                           first_prediction_date=first_prediction_date,
                           last_prediction_date=last_prediction_date,
                           most_common_colormap=most_common_colormap,
                           least_common_colormap=least_common_colormap,  # Pass the least common colormap
                           favorite_entries=favorite_entries)


@app.route('/forget_password', methods=['GET', 'POST'])
def forget_password():
    form = ForgetPasswordForm()
    user = None
    error_message = None 

    email = request.form.get('email')  # Hidden input to persist email
    if email:
        user = User.query.filter_by(email=email).first()

    if form.validate_on_submit():
        if form.submit_email.data:  # Email submission
            email = form.email.data
            user = User.query.filter_by(email=email).first()
           
            if user: 
                return redirect(url_for('forget_password', email=email))

        if form.submit_password.data:  # Password reset submission
            if user:
                    new_password_hash = generate_password_hash(form.new_password.data)
                    user.password = new_password_hash
                    db.session.commit()
                    # Flash success message
                    flash('Password updated successfully!', 'success')
                    return redirect(url_for('index'))
    elif form.new_password.data != form.confirm_password.data:
                    flash('Password must match ', 'danger') 

   
    return render_template(
        'forget_pass.html',
        title='Forget Password',
        form=form,
        user=user,
        email=email,
        error_message=error_message,
        css_file='css/main.css',
        current_page='forget_password'
    )




















# --------------------------------------------------------------------------------------------------------------------------------#
# API ROUTES FOR TESTING 
# --------------------------------------------------------------------------------------------------------------------------------#
@app.route("/api/save", methods=["POST"])
@login_required  # Ensure the user is logged in
def save_text_api():
    data = request.json
    text = data.get("text", "").strip().upper()  # Ensure uppercase letters
    image_base64 = data.get("image")  # Base64 encoded image from frontend
    colormap = data.get("cmap", "").strip()  # Receive the colormap

    # Ensure user is authenticated
    user_id = current_user.id  
    if not user_id:
        return jsonify({"success": False, "error": "User not authenticated"}), 403  

    #  Validate missing fields explicitly
    if not text and not image_base64:
        return jsonify({"success": False, "error": "Missing text or image data"}), 400
    if not text:
        return jsonify({"success": False, "error": "Missing Text"}), 400  # 🔹 Match exact expected test output
    if not image_base64:
        return jsonify({"success": False, "error": "No image data provided"}), 400

    #  Validate text length (🔹 NEW: Ensure text is not longer than 150 characters)
    if len(text) > 150:
        return jsonify({"success": False, "error": "Input exceeds 150-character limit"}), 400  # New validation for long input

    # Input validation: Only letters & spaces allowed
    if not all(char.isalpha() or char.isspace() for char in text):
        return jsonify({"success": False, "error": "Invalid input"}), 400  # 🔹 Ensure "Invalid input" is returned for non-alpha characters

    if not colormap:
        return jsonify({"success": False, "error": "No colormap provided"}), 400

    # Validate colormap
    available_cmaps = plt.colormaps()
    if colormap not in available_cmaps:
        return jsonify({"success": False, "error": f"Invalid colormap. Choose from {available_cmaps}."}), 400

    #  Strip unnecessary quotes
    text = text.replace('"', '')

    try:
        # Save new entry in the database
        new_entry = Entry(
            user_id=user_id,
            letter=text,  # Store full word/sentence
            image_data=image_base64,  # Store Base64 image directly
            colormap=colormap,
            timestamp=datetime.utcnow()
        )
        db.session.add(new_entry)
        db.session.commit()

        return jsonify({"success": True, "message": f'Text "{text}" saved successfully!'}), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500  # 🔹 Fixed 5 → 500 status code for internal errors



@app.route('/api/login', methods=['POST'])
def api_login():
    try:
        # Parse the JSON payload
        data = request.json
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400

        # Query the database for the user
        user = User.query.filter_by(username=username).first()

        # Validate the user and password
        if user and check_password_hash(user.password, password):
            return jsonify({"message": "Login successful"}), 200
        else:
            return jsonify({"error": "Invalid username or password"}), 401

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/history", methods=['GET', 'POST'])
@login_required
def api_history():
    # Pagination parameters from query string (for AJAX requests)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    # Fetch entries for the current user, sorted by timestamp (most recent first)
    pagination = Entry.query.filter_by(user_id=current_user.id).order_by(Entry.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)
    entries = pagination.items

    # Check if it's an AJAX request (fetch more entries)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        entries_data = [{
            'id': entry.id,
            'letter': entry.letter,
            'timestamp': entry.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'is_favorite': entry.is_favorite,
            'image_data': entry.image_data
        } for entry in entries]

        return jsonify({
            'entries': entries_data,
            'has_next': pagination.has_next,
            'current_page': pagination.page
        })

@app.route('/api/register', methods=['POST'])
def api_register():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400

        form = RegisterForm(data=data)

        if not form.validate():
            return jsonify({"errors": form.errors}), 400

        # Check for duplicate username or email
        existing_user = User.query.filter(
            (User.username == form.username.data) | (User.email == form.email.data)
        ).first()
        if existing_user:
            if existing_user.username == form.username.data:
                return jsonify({"error": "Username already exists"}), 400
            if existing_user.email == form.email.data:
                return jsonify({"error": "Email already exists"}), 400

        # Simulate registration (do not persist during testing)
        new_user = User(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data 
        )
        return jsonify({"message": "User registered successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route('/api/history/<int:user_id>', methods=['GET'])
@login_required
def get_user_history(user_id):
    try:
        # Use Session.get() instead of Query.get()
        user = db.session.get(User, user_id)  # Updated for SQLAlchemy 2.0
        if not user:
            return jsonify({"error": "User not found"}), 404

        history = Entry.query.filter_by(user_id=user_id).all()
        if not history:
            return jsonify({"error": "No prediction history available"}), 404

        history_data = [
            {"id": entry.id, "prediction": entry.prediction, "date_created": entry.date_created}
            for entry in history
        ]
        return jsonify({"user": user.username, "history": history_data}), 200

    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500
    
@app.route('/api/forget_password', methods=['POST'])
def api_forget_password():
    """API Endpoint for Password Reset"""
    data = request.get_json()

    if not data:
        return jsonify({"success": False, "error": "Invalid request"}), 400

    email = data.get("email")
    new_password = data.get("new_password")
    confirm_password = data.get("confirm_password")

    if not email:
        return jsonify({"success": False, "error": "Email is required"}), 400

    # Check if the user exists
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"success": False, "error": "Email not found"}), 404

    # If only email is provided (initial verification step)
    if not new_password and not confirm_password:
        return jsonify({"success": True, "message": "Email verified"}), 200

    # Validate password match
    if new_password != confirm_password:
        return jsonify({"success": False, "error": "Passwords must match"}), 400  

    # Mocking the password hash without updating the database
    hashed_password = generate_password_hash(new_password)

    return jsonify({"success": True, "message": "Password updated successfully!"}), 200



@app.route('/api/generate_image', methods=['POST'])
def api_generate_image():
    try:
        data = request.get_json()
        if not data or 'prompt' not in data:
            return jsonify({"success": False, "error": "Invalid input"}), 400

        prompt = data['prompt'].strip().upper()
        if not all(char.isalpha() or char.isspace() for char in prompt):
            return jsonify({"success": False, "error": "Input must contain only letters (A-Z)."}), 400

        cmap = data.get('cmap', 'gray_r')
        available_cmaps = plt.colormaps()
        if len(prompt) > 150:
            return jsonify({"success": False, "error": "Input exceeds 150-character limit"}), 400

        if cmap not in available_cmaps:
            return jsonify({"success": False, "error": f"Invalid colormap. Choose from {available_cmaps}."}), 400

        generated_images = []

        for letter in prompt:
            if letter == " ":
                # Generate a blank image that matches the colormap
                blank_image = np.zeros((28, 28))  # Start with all zeros (low-end of cmap)
                img_bytes = io.BytesIO()
                plt.imsave(img_bytes, blank_image, cmap=cmap, format='png')
                img_bytes.seek(0)
                base64_image = base64.b64encode(img_bytes.getvalue()).decode('utf-8')
                generated_images.append(base64_image)
                continue

            class_index = [float(ord(letter) - ord('A') + 1)] if letter != "Z" else [0.0]
            z_input = np.random.normal(0, 1, 100).tolist()

            payload = {
                "signature_name": "serving_default",
                "instances": [{"input_13": z_input, "input_12": class_index}]
            }

            response = requests.post(GAN_SERVER_URL, json=payload)
            response.raise_for_status()
            result = response.json()

            if "predictions" not in result or not result["predictions"]:
                return jsonify({"success": False, "error": "Invalid response from TensorFlow Serving"}), 500

            generated_image = np.array(result["predictions"][0]).reshape(28, 28)

            img_bytes = io.BytesIO()
            plt.imsave(img_bytes, generated_image, cmap=cmap, format='png')
            img_bytes.seek(0)
            base64_image = base64.b64encode(img_bytes.getvalue()).decode('utf-8')

            generated_images.append(base64_image)

        return jsonify({"success": True, "images": generated_images})

    except requests.exceptions.RequestException as e:
        return jsonify({"success": False, "error": f"TensorFlow Serving error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
