from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash


#create the Flask app
app = Flask(__name__)
CORS(app, supports_credentials=True)
# load configuration from config.cfg
app.config.from_pyfile('config.cfg')


app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///ca2_database.db"  

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# instantiate SQLAlchemy to handle db process
db = SQLAlchemy()



with app.app_context():
    db.init_app(app)
    from .models import User, Entry
    db.create_all()  # Create all tables
    print('Created all Tables in Database')

    # Check if admin user exists
    admin_username = "admin"
    admin_password = "123"  # Default admin password
    admin_email='admin@gmail.com'
    admin_role = "admin"


    existing_admin = User.query.filter_by(username=admin_username).first()

    if not existing_admin:
        # Create the admin user
        hashed_password = generate_password_hash(admin_password)
        admin_user = User(username=admin_username, email=admin_email, password=hashed_password, role=admin_role)
        db.session.add(admin_user)
        db.session.commit()
        print(f"Admin user '{admin_username}' created.")
    else:
        print(f"Admin user '{admin_username}' already exists.")



from application import routes
