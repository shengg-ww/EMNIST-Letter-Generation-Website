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
# from tensorflow.keras.datasets.mnist import load_data
import json
import numpy as np
import requests
import pathlib, os
import json
import tensorflow as tf
import requests
import io  # ✅ Fix for handling image conversion
import matplotlib.pyplot as plt  # ✅ Fix for displaying images


# URL of the server-hosted CGAN model
GAN_SERVER_URL = 'https://ca2-daaa2b02-2309123-limshengwei.onrender.com/v1/models/saved_cgan:predict'



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
            return redirect(url_for('form'))  # Redirect 
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
def form():
    # Get the username of the logged-in user
    username = current_user.username
    return render_template("home.html",title='Home', css_file='css/main.css', current_page="home", username=username)
# ✅ Load the CGAN model locally

saved_model_path = "ModelDev/saved_cgan/1737551983"  # Update the path
loaded_model = tf.saved_model.load(saved_model_path)

@app.route('/generate', methods=['GET', 'POST'])
@cross_origin(origin='localhost', headers=['Content-Type', 'Authorization'])
def generate():
    """
    Handles both UI rendering (GET) and image generation via the locally saved CGAN model.
    """
    if request.method == 'GET':
        return render_template('generate.html', css_file='css/main.css', current_page='generate')

    if request.method == 'POST':
        try:
            # ✅ Parse input JSON from frontend
            data = request.get_json()
            if not data or 'prompt' not in data:
                return jsonify({"success": False, "error": "Invalid input"}), 400

            # ✅ Validate and preprocess input letter
            prompt = data['prompt'].strip().upper()
            if len(prompt) != 1 or not prompt.isalpha():
                return jsonify({"success": False, "error": "Input must be a single letter (A-Z)."}), 400

            # ✅ Convert letter to class index based on your model's convention
            if prompt == "Z":
                class_index = np.array([[0]], dtype=np.float32).reshape(1, 1)
            else:
                class_index = np.array([[float(ord(prompt) - ord('A') + 1)]], dtype=np.float32).reshape(1, 1)


            # ✅ Generate a latent vector (Shape: [1, 100])
            z_input = np.random.randn(1, 100).astype(np.float32).reshape(1, 100)

            # ✅ Run inference using the locally loaded model
            infer = loaded_model.signatures["serving_default"]
            result = infer(
                input_13=tf.convert_to_tensor(z_input), 
                input_12=tf.convert_to_tensor(class_index)
            )

            # ✅ Extract the generated image tensor
            generated_image = result["conv2d_12"].numpy().reshape(28, 28)  # Reshape to 28x28

            # ✅ Convert image to Base64 for frontend display
            img_bytes = io.BytesIO()
            plt.imsave(img_bytes, generated_image, cmap="gray_r", format='png')
            img_bytes.seek(0)
            base64_image = base64.b64encode(img_bytes.getvalue()).decode('utf-8')

            # ✅ Return Base64 encoded image
            return jsonify({"success": True, "image": base64_image})

        except Exception as e:
            # Log the error for debugging
            print(f"🔥 Exception occurred: {e}")
            return jsonify({"success": False, "error": str(e)}), 500
@app.route("/history", methods=['GET','POST'])
@login_required
def history():
    entries = Entry.query.filter_by(user_id=current_user.id).all()
    return render_template('history.html', title='History', css_file='css/main.css', current_page='history', entries=entries)