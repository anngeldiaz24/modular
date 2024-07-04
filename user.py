from flask import (
    Blueprint, flash, g, redirect, render_template, url_for, 
)
from werkzeug.exceptions import abort
from .auth import login_required, user_role_required
from .db import get_db
from .raspberry import funciones
import logging
import datetime

# Configurar el logging para este módulo
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

bp = Blueprint('user', __name__, url_prefix='/user-dashboard')

@bp.route('')
@login_required
@user_role_required
def user_index():
    return render_template('user-dashboard.html', user=g.user)

@bp.route('/welcome')
def user_welcome():
    return render_template('user/welcome.html', current_year=datetime.datetime.now().year, user=g.user)

@bp.route('/encender-luces-domesticas')
@login_required
def encender_luces_domesticas():
    logger.info('Entrando a Encender luces domesticas llamado')
    funciones.encenderLucesDomesticas()
    logger.info('Saliendo de Encender luces domesticas llamado')
    return redirect(url_for('user.user_index'))

@bp.route('/apagar-luces-domesticas')
@login_required
def apagar_luces_domesticas():
    logger.info('Entrando a Apagar luces domesticas llamado')
    funciones.apagarLucesDomesticas()
    logger.info('Saliendo de Apagar luces domesticas llamado')
    return redirect(url_for('user.user_index'))

@bp.route('/activar-alarma')
@login_required
def activar_alarma():
    logger.info('Entrando a Activar alarma llamado')
    funciones.activarAlarma()
    logger.info('Saliendo de Activar alarma llamado')
    return redirect(url_for('user.user_index'))
    
@bp.route('/desactivar-alarma')
@login_required
def desactivar_alarma():
    logger.info('Entrando a Desactivar alarma llamado')
    funciones.desactivarAlarma()
    logger.info('Saliendo de Desactivar alarma llamado')
    return redirect(url_for('user.user_index'))

@bp.route('/bloquear-puertas')
@login_required
def bloquear_puertas():
    logger.info('Entrando a Bloquear puertas llamado')
    funciones.bloquearPuertas()
    logger.info('Saliendo de Bloquear puertas llamado')
    return redirect(url_for('user.user_index'))
    
@bp.route('/desbloquear-puertas')
@login_required
def desbloquear_puertas():
    logger.info('Entrando a Desbloquear puertas llamado')
    funciones.desbloquearPuertas()
    logger.info('Saliendo de Desbloquear puertas llamado')
    return redirect(url_for('user.user_index'))

@bp.route('/llamar-policia')
@login_required
def llamar_policia():
    logger.info('Entrando a Llamar policia llamado')
    # llamada_policia.llamarPoliciaCel()
    funciones.llamarPolicia()
    logger.info('Saliendo de Llamar policia llamado')
    return redirect(url_for('user.user_index'))
    
@bp.route('/grabar-contenido')
@login_required
def grabar_contenido():
    logger.info('Entrando a Grabar contenido llamado')
    funciones.grabarContenido()
    logger.info('Saliendo de Grabar contenido llamado')
    return redirect(url_for('user.user_index'))
