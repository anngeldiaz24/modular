from flask import (
    Blueprint, flash, g, redirect, render_template, url_for, request, session, jsonify, Response
)
from werkzeug.exceptions import abort
from .auth import login_required, user_role_required
from .db import get_db
from .raspberry import funciones
import logging
import datetime
import cv2 
import threading
from .db import get_db
import requests
import re 
from babel.dates import format_date
from dotenv import load_dotenv
from datetime import datetime
import os
from werkzeug.security import generate_password_hash
from mysql.connector import Error as MySQLError

# Configurar el logging para este módulo
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Variable global para controlar la grabación
is_recording = False
output_file = 'output.avi'
video_writer = None

bp = Blueprint('user', __name__)
load_dotenv()

@bp.route('/inicio-usuario')
@login_required
@user_role_required
def home():
    db, c = get_db()
    current_hour = datetime.now().hour
    
    if 5 <= current_hour < 12:
        greeting = "Buenos días"
    elif 12 <= current_hour < 18:
        greeting = "Buenas tardes"
    else:
        greeting = "Buenas noches"
    
    # Obtener la información del hogar del usuario
    c.execute('SELECT * FROM hogares WHERE id = %s', (g.user['hogar_id'],))
    hogar_usuario = c.fetchone()
    
    if not hogar_usuario:
        flash('Hogar no encontrado', 'error')
        return redirect(url_for('main.index'))
    
    estado_hogar = hogar_usuario['estado']
    
    # Obtener la información del código de acceso del hogar del usuario
    c.execute('SELECT * FROM codigos_acceso WHERE id = %s', (hogar_usuario['id'],))
    codigo_acceso = c.fetchone()
    
    if codigo_acceso:
        inicio = format_date(codigo_acceso['inicio'], format='long', locale='es') if codigo_acceso['inicio'] else "N/A"
        fecha_actual = format_date(datetime.now(), format='long', locale='es')
        fin = format_date(codigo_acceso['fin'], format='long', locale='es') if codigo_acceso['fin'] else "N/A"
    else:
        inicio = "N/A"
        fin = "N/A"
        
    # Obtener la temperatura actual del estado del hogar del usuario
    api_key = os.getenv('OPENWEATHER_API_KEY')
    weather_url = f'http://api.openweathermap.org/data/2.5/weather?q={estado_hogar},MX&appid={api_key}&units=metric'
    response = requests.get(weather_url)
    
    if response.status_code == 200:
        weather_data = response.json()
        temperature = round(weather_data['main']['temp'])
    else:
        temperature = "N/A"
    
    return render_template('user/user-inicio.html', 
                            user=g.user, 
                            role=g.user['rol'], 
                            greeting=greeting, 
                            estado_hogar=estado_hogar,
                            temperature=temperature,
                            codigo_acceso=codigo_acceso,
                            inicio=inicio,
                            fin=fin,
                            fecha_actual=fecha_actual)

@bp.route('/hogar')
@login_required
@user_role_required
def user_index():
    return render_template('user/user-home.html', user=g.user, role=g.user['rol'])

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
        flash(f"Ocurrió un error al obtener el paquete del código de acceso: {e}", 'error')
    
    try:
        # Obtener los estados de la base de datos
        c.execute('SELECT nombre FROM estados')
        estados = c.fetchall()
    except Exception as e:
        flash(f"Ocurrió un error al obtener los estados: {e}", 'error')

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
                return redirect(url_for('user.home'))
            except Exception as e:
                db.rollback()
                error = f"Ocurrió un error al guardar la dirección: {e}"
                flash(error, 'error')
        else:
            flash(error, 'error')

    return render_template('user/welcome.html', current_year=datetime.datetime.now().year, user=g.user, paquete=paquete, estados=estados, tamanios=tamanios)

@bp.route('/miembros-hogar')
@login_required
def miembros_hogar():
    db, c = get_db()
    hogar_id = g.user['hogar_id']

    c.execute("""
        SELECT u.id, u.nombre, u.apellidos, u.email, u.telefono, u.rol
        FROM users u
        WHERE u.hogar_id = %s
    """, (hogar_id,))

    miembros = c.fetchall()

    return render_template('user/miembros-hogar.html', miembros=miembros, current_year=datetime.now().year, user=g.user, role=g.user['rol'])

@bp.route('/crear-miembro-hogar', methods=['POST'])
@login_required
def crear_miembro():
    hogar_id = g.user['hogar_id']
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellidos = request.form['apellidos']
        email = request.form['email']
        password = request.form['password']
        telefono = request.form['telefono']
        rol = request.form['rol']
        acepto_terminos = 1 

        db, c = get_db()
        error = None

        # Validaciones
        if not isinstance(nombre, str) or not nombre or len(nombre) < 3:
            error = 'El nombre es requerido y debe ser una cadena de al menos 3 caracteres.'
        elif not isinstance(apellidos, str) or not apellidos or len(apellidos) < 3:
            error = 'Los apellidos son requeridos y deben ser una cadena de al menos 3 caracteres.'
        elif not isinstance(email, str) or not email or not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            error = 'El email es requerido y debe ser una dirección de correo electrónico válida.'
        elif not isinstance(password, str) or not password or len(password) < 8 or not any(char.isdigit() for char in password) or not any(char.isalpha() for char in password) or not any(char in "!@#$%^&*()-_=+{}[]|;:<>,.?/" for char in password):
            error = 'La contraseña es requerida y debe tener al menos 8 caracteres, incluir números y caracteres especiales.'
        elif not isinstance(telefono, str) or not telefono or len(telefono) > 13:
            error = 'El teléfono es requerido y no puede tener más de 13 dígitos.'

        # Verificar duplicación de correo dentro del mismo hogar
        c.execute(
            "SELECT id FROM users WHERE email = %s AND hogar_id = %s",
            (email, hogar_id)
        )
        user = c.fetchone()
        if user is not None:
            error = 'Ya existe un usuario con ese correo electrónico en el hogar.'

        # Verificar duplicación de correo en toda la base de datos
        c.execute(
            "SELECT id FROM users WHERE email = %s",
            (email,)
        )
        user_global = c.fetchone()
        if user_global is not None:
            error = 'El correo electrónico ya ha sido registrado.'

        if error is None:
            try:
                hashed_password = generate_password_hash(password)
                c.execute(
                    "INSERT INTO users (nombre, apellidos, email, telefono, password, rol, acepto_terminos, hogar_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    (nombre, apellidos, email, telefono, hashed_password, rol, acepto_terminos, hogar_id)
                )
                db.commit()
                flash('¡Miembro añadido existosamente!', 'success')
                return redirect(url_for('user.miembros_hogar'))
            except Exception as e:
                db.rollback()
                error = str(e)
                flash(error, 'error')
        else:
            flash(error, 'error')
    return redirect(url_for('user.miembros_hogar'))

@bp.route('/miembro/<int:id>/delete', methods=['POST'])
@login_required
def eliminar_miembro(id):
    db, c = get_db()
    c.execute('SELECT * FROM users WHERE id = %s', (id,))
    miembro = c.fetchone()

    if miembro is None:
        abort(404, f"Miembro {id} no encontrado.")
    
    c.reset()
    c.execute('DELETE FROM users WHERE id = %s', (id,))
    db.commit()
    flash('Miembro eliminado exitosamente.', 'success')
    return redirect(url_for('user.miembros_hogar'))

@bp.route('/miembro/<int:id>/edit', methods=['POST'])
@login_required
def editar_miembro(id):
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellidos = request.form['apellidos']
        email = request.form['email']
        telefono = request.form['telefono']
        rol = request.form['rol']
        acepto_terminos = 1  

        db, c = get_db()
        error = None

        if not isinstance(nombre, str) or not nombre or len(nombre) < 3:
            error = 'El nombre es requerido y debe ser una cadena de al menos 3 caracteres.'
        elif not isinstance(apellidos, str) or not apellidos or len(apellidos) < 3:
            error = 'Los apellidos son requeridos y deben ser una cadena de al menos 3 caracteres.'
        elif not isinstance(email, str) or not email or not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            error = 'El email es requerido y debe ser una dirección de correo electrónico válida.'
        elif not isinstance(telefono, str) or not telefono or len(telefono) > 13:
            error = 'El teléfono es requerido y no puede tener más de 13 dígitos.'

        c.execute(
            "SELECT id FROM users WHERE email = %s AND hogar_id = %s AND id != %s",
            (email, g.user['hogar_id'], id)
        )
        user = c.fetchone()
        if user is not None:
            error = 'Ya existe un usuario con ese correo electrónico en el hogar.'

        c.execute(
            "SELECT id FROM users WHERE email = %s AND id != %s",
            (email, id)
        )
        user_global = c.fetchone()
        if user_global is not None:
            error = 'El correo electrónico ya ha sido registrado.'

        if error is None:
            try:
                c.execute(
                    "UPDATE users SET nombre = %s, apellidos = %s, email = %s, telefono = %s, rol = %s, acepto_terminos = %s WHERE id = %s",
                    (nombre, apellidos, email, telefono, rol, acepto_terminos, id)
                )
                db.commit()
                flash('¡Miembro actualizado exitosamente!', 'success')
                return redirect(url_for('user.miembros_hogar'))
            except Exception as e:
                db.rollback()
                error = str(e)
                flash(error, 'error')
        else:
            flash(error, 'error')
    return redirect(url_for('user.miembros_hogar'))

@bp.route('/mi-cuenta', methods=['GET'])
@login_required
def mi_cuenta():
    db, c = get_db()
    
    # Consulta para obtener la información del hogar y el código de acceso
    c.execute('''
        SELECT h.id as hogar_id, h.codigo_postal, h.calle, h.numero_exterior, h.numero_interior,
            h.colonia, h.municipio, h.estado, h.informacion_adicional, u.codigo_acceso
        FROM users u
        JOIN hogares h ON u.hogar_id = h.id
        WHERE u.id = %s
    ''', (g.user['id'],))
    hogar = c.fetchone()
    hogar_id = hogar['hogar_id']

    if not hogar:
        return "No se encontró la información del hogar.", 404

    # Si el usuario no tiene un codigo_acceso, buscar uno existente en el hogar
    if not hogar['codigo_acceso']:
        c.execute('''
            SELECT codigo_acceso
            FROM users
            WHERE hogar_id = %s AND codigo_acceso IS NOT NULL
            LIMIT 1
        ''', (hogar['hogar_id'],))
        codigo_acceso = c.fetchone()
        hogar['codigo_acceso'] = codigo_acceso['codigo_acceso'] if codigo_acceso else None

    # Obtener el paquete del código de acceso
    paquete = 'N/A'
    if hogar['codigo_acceso']:
        c.execute('SELECT paquete FROM codigos_acceso WHERE id = %s', (hogar['codigo_acceso'],))
        codigo_acceso = c.fetchone()
        paquete = codigo_acceso['paquete'] if codigo_acceso else 'N/A'

    # Construir la dirección completa
    direccion = f"{hogar['calle']} {hogar['numero_exterior']}, {hogar['colonia']}, {hogar['municipio']}, {hogar['estado']}, {hogar['codigo_postal']}"

    # Hacer una solicitud a la API de Geocoding de Google
    google_maps_api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    geocoding_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={direccion}&key={google_maps_api_key}"
    response = requests.get(geocoding_url)
    geocode_result = response.json()

    # Obtener las coordenadas
    if geocode_result['status'] == 'OK':
        location = geocode_result['results'][0]['geometry']['location']
        latitud = location['lat']
        longitud = location['lng']
    else:
        latitud = None
        longitud = None

    return render_template('user/mi-cuenta.html', user=g.user, hogar=hogar, hogar_id=hogar_id, role=g.user['rol'], latitud=latitud, longitud=longitud, google_maps_api_key=google_maps_api_key, paquete=paquete)

@bp.route('/cancelar-suscripcion/<int:id>', methods=['POST'])
@login_required
def cancelar_suscripcion(id):
    db, c = get_db()

    try:
        c.execute("""
            UPDATE hogares
            SET estatus = 'cancelado'
            WHERE id = %s
        """, (id,))
        db.commit()
        
    except Exception as e:
        # Manejo de errores en la base de datos
        db.rollback()
        error = str(e)
        flash(f"Error al actualizar el estatus del hogar: {error}", 'error')
        return redirect(url_for('user.mi_cuenta'))

    # Cierra la sesión del usuario
    session.clear()
    
    # Redirige a la página de inicio de sesión
    return redirect(url_for('auth.login'))
    
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

def start_recording():
    global is_recording, video_writer, cap
    is_recording = True

    now = datetime.now()
    nombre_video = now.strftime("%Y-%m-%d_%H-%M-%S") + '.mp4'
    carpeta = 'records'
    ruta_carpeta = os.path.join(os.getcwd(), carpeta)
    
    if not os.path.exists(ruta_carpeta):
        os.makedirs(ruta_carpeta)
    
    ruta_video = os.path.join(ruta_carpeta, nombre_video)

    # Configuración del VideoCapture
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: No se puede abrir la cámara.")
        return
    
    # Configuración del VideoWriter
    video_writer = cv2.VideoWriter(ruta_video, cv2.VideoWriter_fourcc(*'mp4v'), 10.0, (650, 350))
    if not video_writer.isOpened():
        print("Error: No se puede abrir el escritor de video.")
        cap.release()
        return

    while is_recording:
        ret, frame = cap.read()
        if ret:
            frame = cv2.resize(frame, (650, 350))
            video_writer.write(frame)
        else:
            print("Error al capturar el frame.")
            break

    cap.release()
    video_writer.release()

def stop_recording():
    global is_recording
    is_recording = False

@bp.route('/start-recording', methods=['POST'])
@login_required
def start_video_recording():
    global is_recording
    if not is_recording:
        threading.Thread(target=start_recording).start()
    return jsonify({"status": "recording started"})

@bp.route('/stop-recording', methods=['POST'])
@login_required
def stop_video_recording():
    if is_recording:
        stop_recording()
    return jsonify({"status": "recording stopped"})