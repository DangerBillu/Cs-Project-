import flask
from flask import Flask, render_template, request, redirect
from datetime import datetime
import mysql.connector
import os
from datetime import date

app = Flask(__name__)

# Database configuration using environment variables with fallbacks
db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'Arnav@12'),
    'database': os.getenv('DB_NAME', 'RegistrationSystem')
}

# Function to establish a database connection
def get_db_connection():
    conn = mysql.connector.connect(**db_config)
    return conn

# Initialize database tables
def init_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create events table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS events (
        id INT AUTO_INCREMENT PRIMARY KEY,
        event_name VARCHAR(255) NOT NULL,
        event_date DATE NOT NULL,
        event_location VARCHAR(255) NOT NULL
    )
    ''')

    # Create participants table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS participants (
        id INT AUTO_INCREMENT PRIMARY KEY,
        event_id INT,
        participant_name VARCHAR(255) NOT NULL,
        participant_email VARCHAR(255) NOT NULL,
        participant_phone VARCHAR(50),
        FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
    )
    ''')

    conn.commit()
    cursor.close()
    conn.close()

@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch only future events (events with date later than today)
    cursor.execute('SELECT * FROM events WHERE event_date >= %s ORDER BY event_date ASC', (date.today(),))
    events = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('index.html', events=events)

@app.route('/create', methods=['POST'])
def create():
    event_name = request.form['event_name']
    event_date = request.form['event_date']
    event_location = request.form['event_location']

    # Validate event date
    if not validate_date(event_date):
        return "Invalid date format. Use YYYY-MM-DD.", 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    INSERT INTO events (event_name, event_date, event_location) 
    VALUES (%s, %s, %s)
    ''', (event_name, event_date, event_location))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/")

@app.route('/register', methods=['POST'])
def register():
    event_id = request.form['event_id']
    participant_name = request.form['participant_name']
    participant_email = request.form['participant_email']
    participant_phone = request.form['participant_phone']

    # Validate email format
    if not validate_email(participant_email):
        return "Invalid email address.", 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Insert participant registration
    cursor.execute('''
    INSERT INTO participants 
    (event_id, participant_name, participant_email, participant_phone) 
    VALUES (%s, %s, %s, %s)
    ''', (event_id, participant_name, participant_email, participant_phone))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/")

# Helper function to validate date format
def validate_date(date_text):
    try:
        datetime.strptime(date_text, '%Y-%m-%d')
        return True
    except ValueError:
        return False

# Helper function to validate email format
def validate_email(email):
    return '@' in email and '.' in email

if __name__ == '__main__':
    init_database()  # Initialize database tables
    app.run(debug=True)
