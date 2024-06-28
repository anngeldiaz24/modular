from flask import Flask, render_template, redirect, url_for, jsonify, g
import os
import json
from . import db
from .raspberry import funciones
from .raspberry import llamada_policia


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
    from . import user
    
    app.register_blueprint(auth.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(user.bp)

    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))
    
    @app.route('/home')
    def home():
        return render_template('home.html', user=g.user)
    
    @app.route('/user-domotica')
    def user_domotica():
        # Pasar los datos a la plantilla
        return render_template('user-domotica.html', user=g.user)
    
    
    # Manejador de error 404 [Rutas no definidas]
    @app.errorhandler(404)
    def pagina_no_encontrada(error):
        return render_template('404.html', user=g.user), 404

    return app
