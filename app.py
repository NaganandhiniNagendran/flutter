from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import datetime
from flask_sqlalchemy import SQLAlchemy
import random
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)
app.secret_key = "your_secret_key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///registrations.db'
db = SQLAlchemy(app)

# Database Model
class Registration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer)
    college = db.Column(db.String(100))
    name = db.Column(db.String(100))
    regno = db.Column(db.String(50))
    age = db.Column(db.Integer)
    department = db.Column(db.String(100))
    section = db.Column(db.String(10))
    year = db.Column(db.Integer)
    email = db.Column(db.String(120))  # Added email field
    otp = db.Column(db.String(6))  # Added OTP field

# Create the database tables
with app.app_context():
    db.create_all()

# Sample data (replace with a database for a real application)
events = [
    {'id': 1, 'name': 'Basketball Tournament', 'date': '2024-12-10', 'time': '10:00 AM', 'location': 'Main Gym'},
    {'id': 2, 'name': 'Athletics Meet', 'date': '2024-12-12', 'time': '09:00 AM', 'location': 'Stadium'},
    {'id': 3, 'name': 'Volleyball Championship', 'date': '2024-12-11', 'time': '02:00 PM', 'location': 'Indoor Arena'},
    {'id': 4, 'name': 'Swimming Competition', 'date': '2024-12-13', 'time': '11:00 AM', 'location': 'Aquatic Center'},
    {'id': 5, 'name': 'Table Tennis Tournament', 'date': '2024-12-14', 'time': '01:00 PM', 'location': 'Student Union'},
    {'id': 6, 'name': 'Chess Tournament', 'date': '2024-12-15', 'time': '10:00 AM', 'location': 'Library'},
    {'id': 7, 'name': 'Badminton Doubles', 'date': '2024-12-16', 'time': '03:00 PM', 'location': 'Sports Complex'},
    {'id': 8, 'name': 'Soccer Finals', 'date': '2024-12-17', 'time': '04:00 PM', 'location': 'Soccer Field'},
    {'id': 9, 'name': 'Cricket Match', 'date': '2024-12-18', 'time': '09:30 AM', 'location': 'Cricket Ground'},
    {'id': 10, 'name': 'Tennis Singles', 'date': '2024-12-19', 'time': '12:00 PM', 'location': 'Tennis Courts'},
]
sponsors = [
    {"name": "SportsGear Inc.", "link": "https://www.example-sportsgear.com"},
    {"name": "College Alumni Association", "link": "#"},
    {"name": "Local Sports Store", "link": "https://www.local-sports.com"},
    {"name": "Food Mart", "link": "https://www.foodmart.com"},
]

INCHARGE_USERNAME = "incharge"
INCHARGE_PASSWORD = "password"

# Email Configuration
EMAIL_ADDRESS = "your_email@gmail.com"  # Replace with your email
EMAIL_PASSWORD = "your_email_password"  # Replace with your password or app password

def generate_otp():
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])

def send_email(email, otp):
    msg = MIMEText(f"Your OTP is: {otp}")
    msg["Subject"] = "OTP Verification"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Email sending failed: {e}")
        return False

@app.route('/')
def index():
    now = datetime.datetime.now()
    return render_template('index.html', events=events, now=now)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/schedule')
def schedule():
    return render_template('schedule.html', events=events)

@app.route('/register/<int:event_id>', methods=['GET', 'POST'])
def register(event_id):
    event = next((e for e in events if e['id'] == event_id), None)
    if not event:
        return "Event not found", 404
    return render_template('register.html', event=event)

@app.route('/view')
def view():
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('login'))
    return render_template('view.html', events=events)


@app.route('/send_otp', methods=['POST'])
def send_otp():
    data = request.get_json()
    email = data.get('email')
    event_id = data.get('event_id')  # Get event_id from request
    otp = generate_otp()
    session['otp'] = otp
    session['email'] = email

    if send_email(email, otp):
        new_registration = Registration(
            event_id=event_id,
            college="",
            name="",
            regno="",
            age=0,
            department="",
            section="",
            year=0,
            email=email,
            otp=otp
        )
        db.session.add(new_registration)
        db.session.commit()
        return jsonify({'message': 'OTP sent successfully'}), 200
    else:
        return jsonify({'message': 'Failed to send OTP'}), 500

@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    entered_otp = data.get('otp')
    email = data.get('email')
    event_id = data.get('event_id')
    college = data.get('college')
    name = data.get('name')
    regno = data.get('regno')
    age = data.get('age')
    department = data.get('department')
    section = data.get('section')
    year = data.get('year')

    stored_otp = session.get('otp')
    stored_email = session.get('email')

    if stored_otp and entered_otp == stored_otp and email == stored_email:
        session.pop('otp', None)
        session.pop('email', None)

        registration = Registration.query.filter_by(email=email, event_id=event_id, otp=entered_otp).first()
        if registration:
            registration.college = college
            registration.name = name
            registration.regno = regno
            registration.age = age
            registration.department = department
            registration.section = section
            registration.year = year
            db.session.commit()
            return jsonify({'message': 'Registration successful'}), 200
        else:
            return jsonify({'message': 'Error: Registration not found or OTP mismatch'}), 404
    else:
        return jsonify({'message': 'Invalid OTP'}), 400

@app.route('/sponsor_page')
def sponsor_page():
    return render_template('sponsors.htm', sponsors=sponsors)

@app.route('/add_event', methods=['GET', 'POST'])
def add_event():
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('login'))

    if request.method == 'POST':
        event_id = len(events) + 1
        name = request.form['name']
        date = request.form['date']
        time = request.form['time']
        location = request.form['location']
        events.append({'id': event_id, 'name': name, 'date': date, 'time': time, 'location': location})
        return redirect(url_for('schedule'))
    return render_template('add_event.html')

@app.route('/event_participants/<int:event_id>')
def event_participants(event_id):
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('login'))

    event = next((e for e in events if e['id'] == event_id), None)
    if not event:
        return "Event not found", 404
    participants_list = Registration.query.filter_by(event_id=event_id).all()
    return render_template('event_participants.html', event=event, participants=participants_list)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == INCHARGE_USERNAME and password == INCHARGE_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('view'))
        else:
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html', error=None)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
