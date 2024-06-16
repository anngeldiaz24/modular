from flask import Flask, render_template, redirect, url_for
import os
from . import db
from . import funciones

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
    
    app.register_blueprint(auth.bp)

    @app.route('/admin-dashboard')
    def admin_dashboard():
        return render_template('admin-dashboard.html')
    
    """ RUTAS: /user-dashboard """
    
    @app.route('/user-dashboard')
    def user_dashboard():
        return render_template('user-dashboard.html')
    
    @app.route('/user-dashboard/encender-luces-domesticas')
    def encender_luces_domesticas():
        app.logger.info('Entrando a Encender luces domesticas llamado')
        funciones.encenderLucesDomesticas()
        app.logger.info('Saliendo de Encender luces domesticas llamado')
        return redirect(url_for('user_dashboard'))
    
    @app.route('/user-dashboard/apagar-luces-domesticas')
    def apagar_luces_domesticas():
        app.logger.info('Entrando a Apagar luces domesticas llamado')
        funciones.apagarLucesDomesticas()
        app.logger.info('Saliendo de Apagar luces domesticas llamado')
        return redirect(url_for('user_dashboard'))
    
    @app.route('/user-dashboard/activar-alarma')
    def activar_alarma():
        app.logger.info('Entrando a Activar alarma llamado')
        funciones.activarAlarma()
        app.logger.info('Saliendo de Activar alarma llamado')
        return redirect(url_for('user_dashboard'))
    
    @app.route('/user-dashboard/desactivar-alarma')
    def desactivar_alarma():
        app.logger.info('Entrando a Desactivar alarma llamado')
        funciones.desactivarAlarma()
        app.logger.info('Saliendo de Desactivar alarma llamado')
        return redirect(url_for('user_dashboard'))
    
    @app.route('/user-dashboard/bloquear-puertas')
    def bloquear_puertas():
        app.logger.info('Entrando a Bloquear puertas llamado')
        funciones.bloquearPuertas()
        app.logger.info('Saliendo de Bloquear puertas llamado')
        return redirect(url_for('user_dashboard'))
    
    @app.route('/user-dashboard/desbloquear-puertas')
    def desbloquear_puertas():
        app.logger.info('Entrando a Desbloquear puertas llamado')
        funciones.desbloquearPuertas()
        app.logger.info('Saliendo de Desbloquear puertas llamado')
        return redirect(url_for('user_dashboard'))
    
    @app.route('/user-dashboard/llamar-policia')
    def llamar_policia():
        app.logger.info('Entrando a Llamar policia llamado')
        funciones.llamarPolicia()
        app.logger.info('Saliendo de Llamar policia llamado')
        return redirect(url_for('user_dashboard'))
    
    @app.route('/user-dashboard/grabar-contenido')
    def grabar_contenido():
        app.logger.info('Entrando a Grabar contenido llamado')
        funciones.grabarContenido()
        app.logger.info('Saliendo de Grabar contenido llamado')
        return redirect(url_for('user_dashboard'))

    @app.route('/home')
    def home():
        return render_template('home.html')
    
    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))

    return app
