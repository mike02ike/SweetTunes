import base64
from io import BytesIO
import os
import random
from flask import Flask, jsonify, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_mysqldb import MySQLdb
from flask import session
import trader
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib as mpl
mpl.use('Agg')  # Use the 'Agg' backend which does not require a GUI

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:MikeMoney2020@localhost/FinanceDB'
db = SQLAlchemy(app)

# Define the database model
class User(db.Model):
    userID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    firstName = db.Column(db.String(20), nullable=False)
    lastName = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(45), unique=True)
    phone = db.Column(db.String(12), unique=True)
    dateJoined = db.Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    username = db.Column(db.String(45), nullable=False, unique=True)
    password = db.Column(db.String(45), nullable=False)

    def __repr__(self):
        return '<User %r>' % self.username
    
# Function to establish database connection
def connect_to_database():
    # Database credentials
    host = 'localhost'
    dbname = 'FinanceDB'
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

# trader.login(days=1)
stocks = trader.get_stocks()
crypto = trader.get_crypto()
best_performers, worst_performers = trader.get_performers(stocks)

@app.route('/')
def start():
    return redirect(url_for('login'))

@app.route('/market-state')
def market_state():
    market_state = trader.market_state()
    return jsonify({'market_open': market_state == 'Open'})

@app.route('/login', methods=['GET', 'POST'])
def login():
    connection = connect_to_database()  # Establish database connection
    if connection is None:
        # Handle connection error
        return render_template('error.html', message="Failed to connect to the database")

    if request.method == 'POST':
        # Form submitted, process login
        username = request.form['username']
        password = request.form['password']

        cursor = connection.cursor(MySQLdb.cursors.DictCursor)

        # Fetch user by username from the database
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        # Check if user exists and verify password
        if user and password == user['password']:
            # Authentication successful
            # Redirect to index.html or any other page
            cursor.close()
            connection.close()
            return redirect('/index')  # Replace '/index' with the appropriate route
        else:
            # Authentication failed
            # Redirect to login page with error message
            cursor.close()
            connection.close()
            return redirect('/login')

    # Render the login page template
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    # Connect to the database
    connection = connect_to_database()  # Establish database connection
    if connection is None:
        # Handle connection error
        return render_template('error.html', message="Failed to connect to the database")
        
    if request.method == 'POST':
        # Form submitted, process sign-up
        username = request.form['username']
        password = request.form['password']
        fName =  request.form['fName']
        lName = request.form['lName']
        email = request.form['email']
        phone = request.form['phone']

        cursor = connection.cursor(MySQLdb.cursors.DictCursor)

        try:
            # Insert new user into the database
            cursor.execute("INSERT INTO users (username, password, firstName, lastName, email, phone) VALUES (%s, %s, %s, %s, %s, %s)", (username, password, fName, lName, email, phone))
            connection.commit()
        except MySQLdb.IntegrityError as e:
            # Handle duplicate username error
            if e.args[0] == 1062:
                cursor.close()
                connection.close()
                return render_template('signup.html', error="Username already exists. Please choose a different one.")
            else:
                # Handle other IntegrityError cases
                cursor.close()
                connection.close()
                return render_template('error.html', message="An error occurred while signing up. Please try again later.")

        # Close database connection
        cursor.close()
        connection.close()

        # Redirect to the login page or any other page
        return redirect('/index')

    # Render the sign-up page template
    return render_template('signup.html')

@app.route('/index')
def index():
    pie_chart = generate_pie_chart()
    best_performers, worst_performers = generate_bar_graphs()
    primary_data = get_primary_data()
    secondary_data = get_secondary_data()
    
    gifs_folder = os.path.join(app.static_folder, 'gifs')
    gifs = os.listdir(gifs_folder)
    random_gif = random.choice(gifs)
    
    return render_template('index.html', pie_chart=pie_chart, best_performers=best_performers, worst_performers=worst_performers, primary_data=primary_data, secondary_data=secondary_data, stocks=stocks, crypto=crypto, random_gif=random_gif)

@app.route('/logout')
def logout():
    # session.clear()  # Clear the session
    return redirect(url_for('login'))  # Redirect to the login page

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

def generate_pie_chart():
    # Get portfolio data from trader.py
    portfolio_data = trader.get_stocks()
    pie_data = {}
    for asset, details in portfolio_data.items():
        pie_data[asset] = details['Weight']
        
    labels = list(pie_data.keys())
    pct = list(pie_data.values())
    threshold = 1
    
    # Generate explode list with the same length as sizes
    explode = tuple(0.1 for _ in range(len(pct)))

    # Number of items to display in the legend
    num_items = len(labels) // 4

    plt.figure(figsize=(9, 6))
    wedges, texts, autotexts = plt.pie(
        pct, labels=labels, autopct=lambda p: f'{p:.1f}%' if p > threshold else '', startangle=45, explode=explode
    )
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

    # Create the custom legend with only the last few items
    legend_labels = [f'{label}: {weight:.2f}%' for label, weight in zip(labels[-num_items:], pct[-num_items:])]
    legend_wedges = wedges[-num_items:]

    plt.legend(legend_wedges, legend_labels, loc='best')
    plt.title('Portfolio Equity\n')
    plt.tight_layout()
    plt.savefig('static/charts/pie_chart.png')
    
    # Save plot to BytesIO buffer
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png')
    img_buffer.seek(0)
    
    # Encode image to base64
    img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
    
    # Close plot to avoid memory leaks
    plt.close()

    return img_base64

def generate_bar_graphs():
    best_symbols = [performer[0] for performer in best_performers]
    best_percent_changes = [performer[1] for performer in best_performers]
    best_gain_today = [performer[2] for performer in best_performers]

    worst_symbols = [performer[0] for performer in worst_performers]
    worst_percent_changes = [performer[1] for performer in worst_performers]
    worst_loss_today = [performer[2] for performer in worst_performers]

    # Create BytesIO buffers to save the plots
    best_buffer = BytesIO()
    worst_buffer = BytesIO()

    # Generate Best Performing Stocks bar chart
    plt.figure(figsize=(6.25, 4))
    plt.bar(best_symbols, best_percent_changes, color='green')
    best_bars = plt.bar(best_symbols, best_percent_changes, color='green')
    
    # Annotate each bar with the amount made or lost, positioning above the bar
    for bar, gain_today in zip(best_bars, best_gain_today):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, height, f"${gain_today:.2f}", ha='center', va='bottom')

    plt.xlabel('Stock Symbol')
    plt.ylabel('Percent Change')
    plt.title('Best Performing Stocks')
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig('static/charts/best_performers_bar.png')
    plt.savefig(best_buffer, format='png')
    plt.close()

    ##################################################

    # Generate Worst Performing Stocks bar chart
    plt.figure(figsize=(6.25, 4))
    plt.bar(worst_symbols, worst_percent_changes, color='red')
    worst_bars = plt.bar(worst_symbols, worst_percent_changes, color='red')
    
    # Annotate each bar with the amount made or lost, positioning above the bar
    for bar, lost_today in zip(worst_bars, worst_loss_today):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, height, f"${lost_today:.2f}", ha='center', va='bottom')

    plt.xlabel('Stock Symbol')
    plt.ylabel('Percent Change')
    plt.title('Worst Performing Stocks')
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig('static/charts/worst_performers_bar.png')
    plt.savefig(worst_buffer, format='png')
    plt.close()

    # Encode the contents of the buffers to base64 strings
    best_base64 = base64.b64encode(best_buffer.getvalue()).decode()
    worst_base64 = base64.b64encode(worst_buffer.getvalue()).decode()

    return best_base64, worst_base64

def get_primary_data():
    account_data = trader.get_account_data()

    primary_data = {
        'Market State': trader.market_state(),
        'Money Made Today': f"${trader.amount_made_today():.2f}",
        'Buying Power': f"${float(account_data['account_buying_power']['amount']):.2f}",
        'Total Equity': f"${float(account_data['total_equity']['amount']):.2f}",
        'Total Invested': f"${trader.total_invested():.2f}"
    }

    return primary_data

def get_secondary_data():
    dividends = trader.total_dividends()
    start_date = trader.start_date()
    
    secondary_data = {
        'Total Dividends Recieved': f"${dividends:.2f}",
        'You\'ve been investing since': start_date
    }
    
    return secondary_data


if __name__ == '__main__':
    app.run(debug=True)
    