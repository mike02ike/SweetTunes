from datetime import datetime as dt
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from flask_mysqldb import MySQLdb
from werkzeug.security import check_password_hash
from flask_bcrypt import Bcrypt
import musicbrainzngs as mb

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:MikeMoney2020@localhost/SweetTunesDB'
app.secret_key = 'KnicksIn7andSpursForTop4'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)

# Set the useragent for your application
mb.set_useragent(
    "SweetTunes",  # Nname of the Flask app
    "1.0",  # Version of the Flask app
    "ikemike2468@yahoo.com"  # Contact email
)

# Set up authentication with MusicBrainz
mb.auth("MusicMike02", "Knicksin7")

# Define the database model
class Users(UserMixin, db.Model):
    u_id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False, unique=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(30), nullable=False)
    last_name = db.Column(db.String(30), nullable=False)
    date_of_birth = db.Column(db.Date)
    profile_picture = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=dt.utcnow, nullable=False)
    last_logged_in = db.Column(db.DateTime, default=dt.utcnow, onupdate=dt.utcnow, nullable=False)
    
    # Store favorite artists, albums, and songs
    favorite_artists = db.Column(db.JSON)
    favorite_albums = db.Column(db.JSON)
    favorite_songs = db.Column(db.JSON)
    
    def __repr__(self):
        return '<Users %r>' % self.username
    def get_id(self):
        return self.u_id

# Function to establish database connection
def connect_to_database():
    # Database credentials
    host = 'localhost'
    dbname = 'SweetTunesDB'
    username = 'root'
    password = 'MikeMoney2020'

    # Attempt to connect to the database
    try:
        connection = MySQLdb.connect(
            host=host,
            database=dbname,
            user=username,
            password=password,
        )
        return connection
    except MySQLdb.Error as error:
        print("Error: Could not connect to the database.", error)
        return None

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('welcome.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Retrieve username and password from the form data
    username = request.form.get('username')
    password = request.form.get('password')

    # Query the database to find the user by username
    user = Users.query.filter_by(username=username).first()

    if user and bcrypt.check_password_hash(user.password_hash, password):
        # Update the last_logged_in field with the current timestamp
        user.last_logged_in = dt.utcnow()
        db.session.commit()  # Commit the changes to the database
        
        # Store the username in the session
        session['username'] = username
        user = Users.query.filter_by(username=username).first()
        login_user(user)
        # Password is correct; redirect to home
        return redirect(url_for('home'))
    else:
        # Either user doesn't exist or password is incorrect; display an error message
        flash('Invalid username or password.', 'error')
        return redirect(url_for('index'))

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    # Connect to the database
    connection = connect_to_database()
    if connection is None:
        # Handle connection error
        return render_template('error.html', message="Failed to connect to the database")
    
    if request.method == 'POST':
        # Form submitted, process sign-up
        username = request.form['username']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')  # Hash the password
        fName = request.form['fName']
        lName = request.form['lName']
        email = request.form['email']
        dob = request.form['dob']

        cursor = connection.cursor()

        dob = request.form['dob']
        # Check if dob is empty
        if not dob:
            dob = None  # Set dob to None if it's empty
        try:
            # Insert new user into the database
            cursor.execute("INSERT INTO users (username, password_hash, first_name, last_name, email, date_of_birth) VALUES (%s, %s, %s, %s, %s, %s)",
                        (username, password, fName, lName, email, dob))
            connection.commit()
        except MySQLdb.IntegrityError as e:
            # Handle duplicate username error
            if e.args[0] == 1062:
                return render_template('signup.html', error="Username already exists. Please choose a different one.")
            else:
                # Handle other IntegrityError cases
                return render_template('error.html', message="An error occurred while signing up. Please try again later.")

        # Close database connection
        cursor.close()
        connection.close()

        # Redirect to the welcome page or any other page
        return redirect(url_for('index'))

    # Render the sign-up page template
    return render_template('signup.html')

@app.route('/home')
def home():
    # Example 1: If the username is stored in the session
    username = session.get('username')

    # Example 2: If you are using Flask-Login and have a current_user object
    if current_user.is_authenticated:
        username = current_user.username
    else:
        username = None  # Or any default value if user is not logged in

    return render_template('home.html', username=username)

if __name__ == '__main__':
    app.run(debug=True, port=8000)