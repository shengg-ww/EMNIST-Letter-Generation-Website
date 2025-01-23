from flask import Flask
from flask_cors import CORS
#create the Flask app
app = Flask(__name__)
CORS(app)
# load configuration from config.cfg
app.config.from_pyfile('config.cfg')
from application import routes
