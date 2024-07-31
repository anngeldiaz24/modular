from flask import (
    Blueprint, flash, g, redirect, render_template, url_for, request,
)
import requests
import os
from datetime import datetime
from werkzeug.exceptions import abort
from .auth import login_required, admin_role_required
from .db import get_db
from dotenv import load_dotenv

bp = Blueprint('admin', __name__)
load_dotenv()

@bp.route('/inicio')
@login_required
@admin_role_required
def admin_index():
    # Determinar el saludo basado en la hora del día
    current_hour = datetime.now().hour
    if 5 <= current_hour < 12:
        greeting = "Buenos días"
    elif 12 <= current_hour < 18:
        greeting = "Buenas tardes"
    else:
        greeting = "Buenas noches"

    # Obtener la temperatura actual de Guadalajara
    api_key = os.getenv('OPENWEATHER_API_KEY')
    weather_url = f'http://api.openweathermap.org/data/2.5/weather?q=Guadalajara,MX&appid={api_key}&units=metric'
    response = requests.get(weather_url)
    weather_data = response.json()
    temperature = round(weather_data['main']['temp']) if response.status_code == 200 else "N/A"

    # Obtener todas las casas activas
    db, c = get_db()
    c.execute('SELECT * FROM hogares WHERE estatus = "activo"')
    hogares = c.fetchall()
    total_activos = len(hogares)

    # Obtener coordenadas para cada casa
    google_maps_api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    for hogar in hogares:
        direccion = f"{hogar['calle']} {hogar['numero_exterior']}, {hogar['colonia']}, {hogar['municipio']}, {hogar['estado']}, {hogar['codigo_postal']}"
        geocoding_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={direccion}&key={google_maps_api_key}"
        response = requests.get(geocoding_url)
        geocode_result = response.json()
        if geocode_result['status'] == 'OK':
            location = geocode_result['results'][0]['geometry']['location']
            hogar['lat'] = location['lat']
            hogar['lng'] = location['lng']
        else:
            hogar['lat'] = None
            hogar['lng'] = None

    # Obtener los 4 estados con mayor número de casas activas
    c.execute('''
        SELECT estado, COUNT(*) as num_casas
        FROM hogares
        WHERE estatus = 'activo'
        GROUP BY estado
        ORDER BY num_casas DESC
        LIMIT 4
    ''')
    estados_mayores = c.fetchall()

    return render_template(
        'admin/admin-inicio.html',
        user=g.user,
        greeting=greeting,
        temperature=temperature,
        hogares=hogares,
        total_activos=total_activos,
        google_maps_api_key=google_maps_api_key,
        estados_mayores=estados_mayores
    )

@bp.route('/admin-estadisticas')
@login_required
@admin_role_required
def admin_estadisticas():
    return render_template('admin/admin-estadisticas.html', user=g.user)

def get_hogares():
    db, c = get_db()
    
    try:
        c.execute('''
            SELECT 
                h.id AS hogar_id, h.codigo_postal, h.calle, h.numero_exterior, h.numero_interior, 
                h.colonia, h.municipio, h.estado, h.informacion_adicional, h.estatus,
                u.id AS user_id, u.nombre, u.apellidos,
                ca.paquete
            FROM 
                hogares h
            LEFT JOIN 
                users u ON h.id = u.hogar_id
            LEFT JOIN
                codigos_acceso ca ON u.codigo_acceso = ca.id
        ''')
        data = c.fetchall()

        hogares = {}
        for row in data:
            hogar_id = row['hogar_id']
            if hogar_id not in hogares:
                hogares[hogar_id] = {
                    'direccion': f"{row['calle']} {row['numero_exterior']} {row['numero_interior']}, {row['colonia']}, {row['municipio']}, {row['estado']} - {row['codigo_postal']}",
                    'estatus': row['estatus'],
                    'paquete': row['paquete'],
                    'usuarios': []
                }
            if row['user_id'] is not None:
                hogares[hogar_id]['usuarios'].append({
                    'nombre': row['nombre'],
                    'apellidos': row['apellidos']
                })
    except Exception as e:
        flash(f"Ocurrió un error: {e}", 'error')
        hogares = {}

    return hogares

@bp.route('/hogares')
@login_required
@admin_role_required
def admin_hogares():
    hogares = get_hogares()
    return render_template('admin/hogares-view.html', user=g.user, hogares=hogares)

@bp.route('/hogar/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_role_required
def editar_hogar(id):
    if request.method == 'POST':
        paquete = request.form['paquete']
        estatus = request.form['estatus']
                
        error = None

        if not paquete:
            error = 'El paquete es requerido.'
        elif not estatus:
            error = 'El estatus es requerido.'

        if error is None:
            try:
                db, c = get_db()
                
                # Obtener información del hogar y el código de acceso
                c.execute('''
                    SELECT 
                        ca.id AS codigo_acceso_id, ca.paquete, h.id AS hogar_id
                    FROM 
                        hogares h
                    LEFT JOIN 
                        users u ON h.id = u.hogar_id
                    LEFT JOIN
                        codigos_acceso ca ON u.codigo_acceso = ca.id
                    WHERE
                        h.id = %s
                ''', (id,))
                hogar = c.fetchone()
            
                if hogar is None:
                    abort(404, f"Hogar id {id} no encontrado.")

                c.reset()
                # Actualizar el paquete en la tabla de códigos de acceso
                c.execute('UPDATE codigos_acceso SET paquete = %s WHERE id = %s', (paquete, hogar['codigo_acceso_id']))
                # Actualizar el estatus en la tabla de hogares
                c.execute('UPDATE hogares SET estatus = %s WHERE id = %s', (estatus, id))

                db.commit()

                flash('¡Hogar actualizado correctamente!', 'success')

                return redirect(url_for('admin.admin_hogares'))

            except Exception as e:
                db.rollback()

        else:
            flash(error, 'error')

    return redirect(url_for('admin.admin_hogares'))

@bp.route('/hogar/<int:id>/delete', methods=['POST'])
@login_required
@admin_role_required
def eliminar_hogar(id):
    db, c = get_db()
    c.execute('SELECT * FROM hogares WHERE id = %s', (id,))
    hogar = c.fetchone()

    if hogar is None:
        abort(404, f"Hogar id {id} no encontrado.")
    
    c.reset()
    c.execute('DELETE FROM hogares WHERE id = %s', (id,))
    db.commit()
    flash('Hogar y sus miembros han sido eliminados correctamente.', 'success')
    return redirect(url_for('admin.admin_hogares'))