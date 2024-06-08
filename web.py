from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('admin-dashboard.html')

@app.route('/register')
def register():
    return render_template('auth/login.html')
