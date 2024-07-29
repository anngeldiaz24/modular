from flask import (
    Blueprint, flash, g, redirect, render_template, url_for, request, session
)
from werkzeug.exceptions import abort
from .auth import login_required, user_role_required
from .db import get_db
from .raspberry import funciones
import logging
import datetime
from .db import get_db

# Configurar el logging para este módulo
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

bp = Blueprint('user', __name__, url_prefix='/user-dashboard')

@bp.route('')
@login_required
@user_role_required
def user_index():
    return render_template('user/user-dashboard.html', user=g.user)

@login_required
@user_role_required
@bp.route('/welcome', methods=['GET', 'POST'])
def user_welcome():
    db, c = get_db()
    
    paquete = None
    estados = []
    tamanios = ['pequeño', 'mediano', 'grande']

    try:
        # Obtener el paquete del código de acceso utilizado por el owner
        c.execute('SELECT ca.paquete FROM codigos_acceso ca JOIN users u ON u.codigo_acceso = ca.id WHERE u.id = %s', (g.user['id'],))
        paquete = c.fetchone()
    except Exception as e:
        flash(f"Ocurrió un error al obtener el paquete del código de acceso: {e}", 'danger')
    
    try:
        # Obtener los estados de la base de datos
        c.execute('SELECT nombre FROM estados')
        estados = c.fetchall()
    except Exception as e:
        flash(f"Ocurrió un error al obtener los estados: {e}", 'danger')

    if request.method == 'POST':
        codigo_postal = request.form['codigo_postal']
        calle = request.form['calle']
        numero_exterior = request.form['numero_exterior']
        numero_interior = request.form.get('numero_interior')
        colonia = request.form['colonia']
        municipio = request.form['municipio']
        estado = request.form['estado']
        tamanio = request.form['tamanio']
        informacion_adicional = request.form.get('informacion_adicional')

        # Validaciones
        error = None

        if not codigo_postal.isdigit() or len(codigo_postal) != 5:
            error = 'El código postal debe ser un número de 5 dígitos.'
        elif not calle:
            error = 'La calle es obligatoria.'
        elif not numero_exterior:
            error = 'El número exterior es obligatorio.'
        elif numero_interior and not numero_interior.isalnum():
            error = 'El número interior debe ser alfanumérico.'
        elif not colonia:
            error = 'La colonia es obligatoria.'
        elif not municipio:
            error = 'El municipio es obligatorio.'
        elif not estado:
            error = 'El estado es obligatorio.'
        elif not tamanio:
            error = 'El tamaño es obligatorio.'

        if error is None:
            try:
                # Insertar en la tabla hogares
                c.execute('INSERT INTO hogares (codigo_postal, calle, numero_exterior, numero_interior, colonia, municipio, estado, tamanio, informacion_adicional, estatus) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                    (codigo_postal, calle, numero_exterior, numero_interior, colonia, municipio, estado, tamanio, informacion_adicional, 'activo'))
                hogar_id = c.lastrowid

                # Actualizar la tabla users con el hogar_id
                c.execute('UPDATE users SET hogar_id = %s WHERE id = %s', (hogar_id, g.user['id']))
                db.commit()

                flash('¡Bienvenido a SSafeZone!', 'success')
                return redirect(url_for('user.user_index'))
            except Exception as e:
                db.rollback()
                error = f"Ocurrió un error al guardar la dirección: {e}"
                flash(error, 'danger')
        else:
            flash(error, 'danger')

    return render_template('user/welcome.html', current_year=datetime.datetime.now().year, user=g.user, paquete=paquete, estados=estados, tamanios=tamanios)

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
