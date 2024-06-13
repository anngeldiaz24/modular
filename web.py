from flask import Flask, render_template
import datetime

app = Flask(__name__)

@app.route('/admin-dashboard')
def admin_dashboard():
    return render_template('admin-dashboard.html')

@app.route('/user-dashboard')
def user_dashboard():
    return render_template('user-dashboard.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/')
def index():
    return render_template('auth/login.html')

@app.route('/register')
def register():
    current_year = datetime.datetime.now().year
    return render_template('auth/register.html', current_year=current_year)
