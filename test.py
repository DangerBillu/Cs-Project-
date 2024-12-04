from flask import Flask, render_template, request, redirect, url_for
from datetime import date
import mysql.connector

app = Flask(__name__)

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'arnav',
    'database': 'test'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

def init_database():
    # Create the events table if it doesn't exist
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(''' 
    CREATE TABLE IF NOT EXISTS events (
        id INT AUTO_INCREMENT PRIMARY KEY,
        event_name VARCHAR(255) NOT NULL UNIQUE,
        event_date DATE NOT NULL,
        event_location VARCHAR(255) NOT NULL
    )
    ''')
    conn.commit()
    cursor.close()
    conn.close()

def create_event_table(event_name):
    # Create a table for participants of a specific event
    table_name = event_name.replace(" ", "_").lower()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f'''
    CREATE TABLE IF NOT EXISTS `{table_name}` (
        id INT AUTO_INCREMENT PRIMARY KEY,
        participant_name VARCHAR(255) NOT NULL,
        participant_email VARCHAR(255) NOT NULL,
        participant_phone VARCHAR(50) NOT NULL
    )
    ''')
    conn.commit()
    cursor.close()
    conn.close()

@app.route('/')
def index():
    # Display upcoming events
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM events WHERE event_date >= %s ORDER BY event_date ASC', (date.today(),))
    events = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('index.html', events=events)

@app.route('/create', methods=['POST'])
def create():
    # Create a new event
    if 'event_name' not in request.form:
        return "Error: Missing event_name in the form submission.", 400

    event_name = request.form['event_name']
    event_date = request.form['event_date']
    event_location = request.form['event_location']

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(''' 
    INSERT INTO events (event_name, event_date, event_location)
    VALUES (%s, %s, %s)
    ''', (event_name, event_date, event_location))
    conn.commit()
    create_event_table(event_name)

    cursor.close()
    conn.close()

    return redirect('/')

@app.route('/register', methods=['POST'])
def register_participant():
    # Retrieve event_name and other form data
    event_name = request.form.get('event_name')
    participant_name = request.form['participant_name']
    participant_email = request.form['participant_email']
    participant_phone = request.form['participant_phone']

    # Check if event_name is provided
    if not event_name:
        return "Error: Missing event_name in the form submission.", 400

    # Sanitize event_name for use as a table name: replace spaces with underscores, and make it lowercase
    table_name = event_name.replace(" ", "_").lower()

    # Ensure the table name is not empty or malformed
    if not table_name:
        return "Error: Invalid event_name.", 400

    # Establish database connection and insert the participant into the respective table
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Insert the participant's data into the specific event table
        cursor.execute(f'''
        INSERT INTO `{table_name}` (participant_name, participant_email, participant_phone)
        VALUES (%s, %s, %s)
        ''', (participant_name, participant_email, participant_phone))
        conn.commit()
    except mysql.connector.Error as e:
        return f"Database error: {e}", 500
    finally:
        cursor.close()
        conn.close()

    return redirect('/')

@app.route('/event/<event_name>')
def view_event_participants(event_name):
    # View participants of a specific event
    table_name = event_name.replace(" ", "_").lower()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute('SELECT * FROM events WHERE event_name = %s', (event_name,))
    event = cursor.fetchone()
    cursor.execute(f'SELECT * FROM `{table_name}`')
    participants = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('event_details.html', event=event, participants=participants)

@app.route('/edit_participant/<event_name>/<int:participant_id>', methods=['GET', 'POST'])
def edit_participant(event_name, participant_id):
    # Edit participant details
    table_name = event_name.replace(" ", "_").lower()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        participant_name = request.form['participant_name']
        participant_email = request.form['participant_email']
        participant_phone = request.form['participant_phone']

        cursor.execute(f'''
        UPDATE `{table_name}` 
        SET participant_name = %s, participant_email = %s, participant_phone = %s 
        WHERE id = %s
        ''', (participant_name, participant_email, participant_phone, participant_id))
        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for('view_event_participants', event_name=event_name))

    # Get the participant details to pre-fill the form
    cursor.execute(f'SELECT * FROM `{table_name}` WHERE id = %s', (participant_id,))
    participant = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template('edit_participant.html', event_name=event_name, participant=participant)

@app.route('/delete_participant/<event_name>/<int:participant_id>', methods=['POST'])
def delete_participant(event_name, participant_id):
    # Delete participant from the event
    table_name = event_name.replace(" ", "_").lower()

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(f'DELETE FROM `{table_name}` WHERE id = %s', (participant_id,))
    conn.commit()

    cursor.close()
    conn.close()

    return redirect(url_for('view_event_participants', event_name=event_name))

if __name__ == '__main__':
    init_database()
    app.run(debug=True)