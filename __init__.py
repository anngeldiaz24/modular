from flask import Flask, render_template, redirect, url_for, jsonify
import os
from . import db

def create_app():
    app = Flask(__name__)

    app.config.from_mapping(
        SECRET_KEY='Cucei_Udg',
        DATABASE_HOST=os.environ.get('FLASK_DATABASE_HOST'),
        DATABASE_PASSWORD=os.environ.get('FLASK_DATABASE_PASSWORD'),
        DATABASE_USER=os.environ.get('FLASK_DATABASE_USER'),
        DATABASE=os.environ.get('FLASK_DATABASE'),
        DATABASE_PORT=os.environ.get('FLASK_PORT'),
    )

    db.init_app(app)
    
    from . import auth
    from . import admin
    
    app.register_blueprint(auth.bp)
    app.register_blueprint(admin.bp)

    @app.errorhandler(401)
    def unauthorized(error):
        response = jsonify({'error': 'Unauthorized', 'message': 'No estás autorizado para acceder a esta página.'})
        response.status_code = 401
        return response
    
    @app.route('/user-dashboard')
    def user_dashboard():
        return render_template('user-dashboard.html')

    @app.route('/home')
    def home():
        return render_template('home.html')
    
    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))

    return app
