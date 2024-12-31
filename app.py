from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import smtplib

import requests

# Sheety API Endpoint
SHEETY_ENDPOINT = "https://api.sheety.co/93f98d84f7d027c5d1a305fee19f6db7/conVo25/workouts"

def save_to_google_sheets(name, category, topic, email, phone):
    try:
        # Prepare the data payload
        data = {
            "workout": {  # Replace 'workout' with the key Sheety expects (check your API docs)
                "name": name,
                "category": category,
                "topic": topic,
                "email": email,
                "phone": phone
            }
        }

        # POST request to Sheety API
        response = requests.post(SHEETY_ENDPOINT, json=data)
        print(response)

        # Check if the data was successfully added
        if response.status_code == 201:
            print("Data added to Google Sheets successfully!")
        else:
            print("Failed to add data to Google Sheets:", response.text)

    except Exception as e:
        print(f"Error adding data to Google Sheets: {e}")


app = Flask(__name__)

# Configuration for SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///registrations.db'  # SQLite database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db = SQLAlchemy(app)

email = "lokesh1234student@gmail.com"
password = "paxl cyxg ycug jmme"

# Database model for registrations
class Registration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    topic = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    phone = db.Column(db.String(20), nullable=False, unique=True)

    def __repr__(self):
        return f'<Registration {self.name}>'

# Create the database schema
with app.app_context():
    db.create_all()



def sendEmail(name, category, topic, email, phone):
    # Establish connection with the SMTP server
    connection = smtplib.SMTP("smtp.gmail.com", port=587)
    connection.starttls()

    # Login to your email account
    connection.login(user="lokesh1234student@gmail.com", password=password)

    # Compose the email subject and message body
    subject = f"New Registration for ConVo25 - {name}"
    message = (f"Subject: {subject}\n\n"
               f"New Registration Details:\n\n"
               f"Name: {name}\n"
               f"Category: {category}\n"
               f"Topic: {topic}\n"
               f"Email: {email}\n"
               f"Phone: {phone}\n\n"
               f"Regards,\nConVo25 Team")

    # Send the email to you (receiver)
    connection.sendmail(from_addr="lokesh78531@gmail.com",
                        to_addrs="huzaifa7.horizon@gmail.com",
                        msg=message)

    # Close the connection
    connection.close()


# Route for the index page
@app.route('/')
def index_page():
    return render_template('index.html')

# Route for the rules page
@app.route('/rules')
def rules_page():
    return render_template('rules.html')

# Route for the registration page
@app.route('/register')
def register_page():
    return render_template('register.html')

# Handle registration form submission
@app.route('/submit-registration', methods=['POST'])
def register():
    try:
        # Collect form data
        name = request.form.get('participantName')
        category = request.form.get('categoryDropdown')
        topic = request.form.get('topicInput')
        email = request.form.get('emailAddress')
        phone = request.form.get('phoneNumber')

        # Validation: Ensure no fields are empty
        if not name or not category or not topic or not email or not phone:
            return jsonify({'error': 'Missing form data! Please fill all fields.'}), 400

        # Ensure uniqueness of email and phone
        existing_email = Registration.query.filter_by(email=email).first()
        existing_phone = Registration.query.filter_by(phone=phone).first()
        if existing_email or existing_phone:
            return jsonify({'error': 'Email or phone number already registered!'}), 409

        # Save data to the database
        new_registration = Registration(
            name=name,
            category=category,
            topic=topic,
            email=email,
            phone=phone
        )
        db.session.add(new_registration)
        db.session.commit()

        sendEmail(name , category , topic , email , phone)
        save_to_google_sheets(name, category, topic, email, phone)

        # Return success message
        return jsonify({'message': 'Registration Successful!'}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'An error occurred during registration. Please try again later.'}), 500

# Route for the admin panel
@app.route('/admin')
def admin_panel():
    registrations = Registration.query.all()
    return render_template('admin.html', registrations=registrations)

# Route to delete a single entry
@app.route('/delete/<int:registration_id>', methods=['POST'])
def delete_registration(registration_id):
    try:
        registration = Registration.query.get(registration_id)
        if not registration:
            return jsonify({'error': 'Registration not found'}), 404

        db.session.delete(registration)
        db.session.commit()
        return redirect(url_for('admin_panel'))

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'An error occurred while deleting the entry.'}), 500

# Route to delete all entries
@app.route('/delete_all', methods=['POST'])
def delete_all():
    try:
        num_deleted = db.session.query(Registration).delete()
        db.session.commit()
        if num_deleted == 0:
            return jsonify({'message': 'No registrations to delete.'}), 200

        return redirect(url_for('admin_panel'))

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'An error occurred while deleting all entries.'}), 500

# Error handler for 404
@app.errorhandler(404)
def page_not_found(e):
    return jsonify({'error': 'Page not found'}), 404

# Error handler for 500
@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error occurred. Please try again later.'}), 500

if __name__ == '__main__':
    app.run(debug=False)
