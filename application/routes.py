from application import app
from flask import render_template, request, flash, url_for ,redirect
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

def make_prediction(instances):
    data = json.dumps({"signature_name": "serving_default", "instances":
    instances.tolist()})
    headers = {"content-type": "application/json"}
    json_response = requests.post(url, data=data, headers=headers)
    predictions = json.loads(json_response.text)['predictions']
    return predictions

url = 'https://ca2-daaa2b02-2309123-limshengwei.onrender.com/v1/models/saved_cgan'


#Handles http://127.0.0.1:5000/
@app.route('/')
@app.route('/index')
@app.route('/home')
def index():
    return render_template('index.html', title="Home", css_file='css/main.css', current_page="index")


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

@app.route('/form', methods=['GET', 'POST'])
@login_required
def form():
    # Get the username of the logged-in user
    username = current_user.username
    return render_template("form.html",title='Form', form=form, css_file='css/main.css', current_page="form", username=username)


#Handles http://127.0.0.1:5000/predict
@app.route("/predict", methods=['GET','POST'])
@cross_origin(origin='localhost',headers=['Content- Type','Authorization'])
def predict():

    # Decoding and pre-processing base64 image
    img = image.img_to_array(image.load_img("output.png", color_mode="grayscale",
    target_size=(28, 28))) / 255.
    # reshape data to have a single channel
    img = img.reshape(1,28,28,1)
    predictions = make_prediction(img)
    ret = ""
    for i, pred in enumerate(predictions):
        ret = "{}".format(np.argmax(pred))
        response = ret
        return response