from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import pandas as pd
import numpy as np
import os
import joblib

import pymysql
pymysql.install_as_MySQLdb()

# Initialize Flask App
app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'supersecretkey'  # Change this for security

# MySQL Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://ccu_admin:securepassword@localhost/ccu_dashboard'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize Extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# ------------------ DATABASE MODELS ------------------ #

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    encounterId = db.Column(db.String(100), unique=True, nullable=False)
    end_tidal_co2 = db.Column(db.Float, nullable=True)
    feed_vol = db.Column(db.Float, nullable=True)
    oxygen_flow_rate = db.Column(db.Float, nullable=True)
    bmi = db.Column(db.Float, nullable=True)
    resp_rate = db.Column(db.Float, nullable=True)
    referral = db.Column(db.Boolean, default=False)
    watch_flag = db.Column(db.Boolean, default=False)  # watch_flag

# Create tables
with app.app_context():
    db.create_all()

# ------------------ ENFORCE LOGIN ON ALL PAGES ------------------ #

@app.before_request
def require_login():
    allowed_routes = ['login', 'register', 'static']
    if 'user' not in session and request.endpoint not in allowed_routes:
        return redirect(url_for('login'))

# ------------------ AUTHENTICATION ROUTES ------------------ #

@app.route('/')
def home():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template("homepage.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            session['user'] = username
            return redirect(url_for('home'))
        return "Invalid Credentials", 403
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        if User.query.filter_by(username=username).first():
            return "Username already exists!", 400
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

# ------------------ PROTECTED PAGE ROUTES ------------------ #

@app.route('/view_patientdata')
def view_patient_data():
    return render_template('view_patientdata.html')

@app.route('/upload_patient_data')
def upload_patient_data():
    return render_template('upload.patient.data.html')

@app.route('/analyse_patient_data')
def analyse_patient_data():
    return render_template('analyse.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/help')
def help():
    return render_template('help.html')

# ------------------ FIXED UPLOAD & DATA ROUTES ------------------ #

def safe_float(value):
    try:
        if pd.isna(value) or value in ["nan", "NaN", ""]:
            return None
        return float(value)
    except (ValueError, TypeError):
        return None

@app.route('/upload', methods=['POST']) #ML integration
def upload_csv():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        df = pd.read_csv(file)

        # Try to predict referral if model available
        if 'referral' not in df.columns:
            model = joblib.load('referral_model.pkl')
            scaler = joblib.load('referral_scaler.pkl')
            required_features = ['bmi', 'feed_vol', 'oxygen_flow_rate', 'resp_rate']
            if all(col in df.columns for col in required_features):
                df_clean = df.dropna(subset=required_features)
                X = scaler.transform(df_clean[required_features])

                probas = model.predict_proba(X)[:, 1] # flag

                referrals = (probas >= 0.7).astype(int)
                watches = ((probas >= 0.6) & (probas < 0.7)).astype(int)

                df.loc[df_clean.index, 'referral'] = referrals
                df.loc[df_clean.index, 'watch_flag'] = watches


            else:
                return jsonify({"error": "Missing features for model prediction."}), 400

        for _, row in df.iterrows():
            encounter_id = str(row.get('encounterId', '')).strip()
            if not encounter_id:
                continue

            existing = Patient.query.filter_by(encounterId=encounter_id).first()
            if existing:
                continue

            patient = Patient(
                encounterId=encounter_id,
                end_tidal_co2=safe_float(row.get('end_tidal_co2')),
                feed_vol=safe_float(row.get('feed_vol')),
                oxygen_flow_rate=safe_float(row.get('oxygen_flow_rate')),
                bmi=safe_float(row.get('bmi')),
                resp_rate=safe_float(row.get('resp_rate')),
                referral=bool(int(row.get('referral', 0))),
                watch_flag=bool(int(row.get('watch_flag', 0)))
            )
            db.session.add(patient)

        db.session.commit()
        return jsonify({"message": "File uploaded and predictions saved."})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/patients', methods=['GET'])
def get_patients():
    patients = Patient.query.all()
    return jsonify([{ 
        "id": p.id, 
        "encounterId": p.encounterId,
        "end_tidal_co2": p.end_tidal_co2,
        "feed_vol": p.feed_vol,
        "oxygen_flow_rate": p.oxygen_flow_rate,
        "bmi": p.bmi,
        "resp_rate": p.resp_rate,
        "referral": p.referral
    } for p in patients])

@app.route('/patients/referred', methods=['GET'])
def get_referred_patients():
    patients = Patient.query.filter((Patient.referral == True) | (Patient.watch_flag == True)).all()
    return jsonify([{ 
        "id": p.id, 
        "encounterId": p.encounterId,
        "bmi": p.bmi,
        "oxygen_flow_rate": p.oxygen_flow_rate,
        "feed_vol": p.feed_vol,
        "resp_rate": p.resp_rate,
        "referral": p.referral,
        "watch_flag": p.watch_flag
    } for p in patients])

# ------------------ RUN THE APP ------------------ #

if __name__ == "__main__":
    app.run(debug=True)
