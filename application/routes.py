from application import app
from flask import render_template, request, flash, url_for ,redirect
from application.forms import LoginForm,RegisterForm
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from flask_cors import CORS, cross_origin
from tensorflow.keras.preprocessing import image
from PIL import Image, ImageOps
import numpy as np
import tensorflow.keras.models
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
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        # # Query the database for the user
        # user = User.query.filter_by(username=username).first()

        # # Check if the user exists and the password is correct
        # if user and check_password_hash(user.password, password):
        #     login_user(user)  # Log the user in
        #     flash("Login successful!", "success")
        #     return redirect(url_for('home'))  # Redirect to the home page
        # else:
        #     form.username.errors.append("Invalid username or password")  

    return render_template('index.html', title="Login", css_file='css/main.css', form=form, current_page="index")
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