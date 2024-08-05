from flask import (
    Blueprint, flash, g, redirect, render_template, url_for, request,
)
import requests
import os
from datetime import datetime
from dotenv import load_dotenv
from babel.dates import format_date
from werkzeug.exceptions import abort
from .auth import login_required, admin_role_required
from .db import get_db, close_db

bp = Blueprint('admin', __name__)
load_dotenv()

# Función para formatear la fecha al mes en español
def formatear_fecha(fecha):
    if fecha:
        return format_date(fecha, format='MMMM yyyy', locale='es')
    return None

# Función para obtener el último periodo
def get_ultimo_periodo_ventas():
    db, c = get_db()
    
    try:
        query = """
        SELECT MAX(periodo_id) as ultimo_periodo_id
        FROM codigos_acceso
        """
        
        c.execute(query)
        resultado = c.fetchone()
        
        print(f"ultimo periodo: {resultado}")
    
        return resultado['ultimo_periodo_id'] if resultado else None
    finally:
        close_db()
        
def get_consumo_ventas():
    db, c = get_db()
    
    try: 
        query = f"""
        SELECT periodo_id
        FROM codigos_acceso
        WHERE disponible = 0
        ORDER BY periodo_id
        """
        c.execute(query)
        # Obtiene los resultados de la consulta
        datos = c.fetchall()
        
        # Convierte los resultados a un formato de lista de diccionarios
        datos_grafica = [{'periodo_id': dato['periodo_id']} for dato in datos]
        
        # Consulta para obtener los consumos de los dos últimos periodos
        query_ultimos_periodos = """
        SELECT COUNT(ca.periodo_id) as consumo, ca.periodo_id, p.inicio
        FROM codigos_acceso ca
        JOIN periodos p ON ca.periodo_id = p.id
        WHERE ca.disponible = 0
        GROUP BY ca.periodo_id, p.inicio
        ORDER BY ca.periodo_id DESC
        LIMIT 2
        """
    
        c.execute(query_ultimos_periodos)
        ultimos_periodos = c.fetchall()
        print(f"Ultimos periodos: {ultimos_periodos}")
        
        if len(ultimos_periodos) < 2:
            diferencia_porcentual = None  # No hay suficientes datos para calcular la diferencia porcentual
        else:
            consumo_actual = ultimos_periodos[0]['consumo']
            consumo_anterior = ultimos_periodos[1]['consumo']
            diferencia = consumo_actual - consumo_anterior
            porcentaje_cambio = (diferencia / consumo_anterior) * 100
            diferencia_porcentual = {
                'consumo_actual': consumo_actual,
                'consumo_anterior': consumo_anterior,
                'porcentaje_cambio': round(porcentaje_cambio, 2),
                'positivo': porcentaje_cambio > 0,
                'inicio': ultimos_periodos[1]['inicio']
            }
        
        return datos_grafica, diferencia_porcentual
    finally:
        close_db()
        
def get_ingreso_ventas():
    db, c = get_db()
    
    try: 
        # Consulta para obtener los ingresos por periodo
        query = """
        SELECT ca.periodo_id, SUM(ca.precio) as ingreso, p.inicio
        FROM codigos_acceso ca
        JOIN periodos p ON ca.periodo_id = p.id
        WHERE ca.disponible = 0
        GROUP BY ca.periodo_id, p.inicio
        ORDER BY ca.periodo_id
        """
        c.execute(query)
        # Obtiene los resultados de la consulta
        datos = c.fetchall()
        
        # Convierte los resultados a un formato de lista de diccionarios para la gráfica
        datos_grafica = [{'periodo_id': dato['periodo_id'], 'ingreso': dato['ingreso']} for dato in datos]
        
        # Consulta para obtener los ingresos de los dos últimos periodos
        query_ultimos_periodos = """
        SELECT SUM(ca.precio) as ingreso, ca.periodo_id, p.inicio
        FROM codigos_acceso ca
        JOIN periodos p ON ca.periodo_id = p.id
        WHERE ca.disponible = 0
        GROUP BY ca.periodo_id, p.inicio
        ORDER BY ca.periodo_id DESC
        LIMIT 2
        """
    
        c.execute(query_ultimos_periodos)
        ultimos_periodos = c.fetchall()
        
        if len(ultimos_periodos) < 2:
            diferencia_porcentual = None  # No hay suficientes datos para calcular la diferencia porcentual
        else:
            ingreso_actual = ultimos_periodos[0]['ingreso']
            ingreso_anterior = ultimos_periodos[1]['ingreso']
            diferencia = ingreso_actual - ingreso_anterior
            porcentaje_cambio = (diferencia / ingreso_anterior) * 100
            diferencia_porcentual = {
                'ingreso_actual': ingreso_actual,
                'ingreso_anterior': ingreso_anterior,
                'porcentaje_cambio': round(porcentaje_cambio, 2),
                'positivo': porcentaje_cambio > 0,
                'inicio': ultimos_periodos[1]['inicio']
            }
        
        return datos_grafica, diferencia_porcentual
    finally:
        close_db(db)
        
def get_nuevos_usuarios():
    db, c = get_db()
    
    try: 
        # Consulta para obtener los nuevos usuarios por periodo
        query = """
        SELECT u.periodo_id, COUNT(u.id) as nuevos_usuarios, p.inicio
        FROM users u
        JOIN periodos p ON u.periodo_id = p.id
        GROUP BY u.periodo_id, p.inicio
        ORDER BY u.periodo_id
        """
        c.execute(query)
        # Obtiene los resultados de la consulta
        datos = c.fetchall()
        
        # Convierte los resultados a un formato de lista de diccionarios para la gráfica
        datos_grafica = [{'periodo_id': dato['periodo_id'], 'nuevos_usuarios': dato['nuevos_usuarios']} for dato in datos]
        
        # Consulta para obtener los nuevos usuarios de los dos últimos periodos
        query_ultimos_periodos = """
        SELECT COUNT(u.id) as nuevos_usuarios, u.periodo_id, p.inicio
        FROM users u
        JOIN periodos p ON u.periodo_id = p.id
        GROUP BY u.periodo_id, p.inicio
        ORDER BY u.periodo_id DESC
        LIMIT 2
        """
    
        c.execute(query_ultimos_periodos)
        ultimos_periodos = c.fetchall()
        
        if len(ultimos_periodos) < 2:
            diferencia_porcentual = None  # No hay suficientes datos para calcular la diferencia porcentual
        else:
            nuevos_usuarios_actual = ultimos_periodos[0]['nuevos_usuarios']
            nuevos_usuarios_anterior = ultimos_periodos[1]['nuevos_usuarios']
            diferencia = nuevos_usuarios_actual - nuevos_usuarios_anterior
            porcentaje_cambio = (diferencia / nuevos_usuarios_anterior) * 100
            diferencia_porcentual = {
                'nuevos_usuarios_actual': nuevos_usuarios_actual,
                'nuevos_usuarios_anterior': nuevos_usuarios_anterior,
                'porcentaje_cambio': round(porcentaje_cambio, 2),
                'positivo': porcentaje_cambio > 0,
                'inicio': ultimos_periodos[1]['inicio']
            }
            
        return datos_grafica, diferencia_porcentual
    finally:
        close_db(db)
        
def get_cantidad_hogares():
    db, c = get_db()
    
    try:    
        query = """
        SELECT COUNT(id) as total
        FROM hogares
        """
        
        c.execute(query)
        # Obtiene los resultados de la consulta
        hogares = c.fetchone()
        
        return hogares
    finally:
        close_db()
        
def get_cantidad_usuarios():
    db, c = get_db()
    
    try:    
        query = """
        SELECT COUNT(id) as total
        FROM users
        """
        
        c.execute(query)
        # Obtiene los resultados de la consulta
        usuarios = c.fetchone()
        
        return usuarios
    finally:
        close_db()
        
def get_cantidad_dispositivos():
    db, c = get_db()
    
    try:    
        query = """
        SELECT COUNT(id) as total
        FROM dispositivos
        """
        
        c.execute(query)
        # Obtiene los resultados de la consulta
        dispositivos = c.fetchone()
        
        return dispositivos
    finally:
        close_db()
        
def get_cantidad_paquetes_vendidos():
    db, c = get_db()
    
    try:    
        query = """
        SELECT COUNT(id) as total
        FROM codigos_acceso
        WHERE disponible = 0
        """
        
        c.execute(query)
        # Obtiene los resultados de la consulta
        paquetes_vendidos = c.fetchone()
        
        return paquetes_vendidos
    finally:
        close_db()
        
def get_estatus_hogares():
    db, c = get_db()
    
    try:
        # Consulta para obtener los dispositivos del hogar por hogar
        query = """
        SELECT estatus, COUNT(id) as total
        FROM hogares
        GROUP BY estatus
        """
        
        c.execute(query)
        # Obtiene los resultados de la consulta
        estatus_todos = c.fetchall()
        
        estatus_tipos = [estatus['estatus'] for estatus in estatus_todos]
        estatus_cantidades = [estatus['total'] for estatus in estatus_todos]
        
        return estatus_tipos, estatus_cantidades
    finally:
        close_db()
        
def get_ventas_mensuales_por_paquete2023():
    db, c = get_db()
    
    try:
        query = """
        SELECT
            MONTH(p.inicio) as mes,
            c.paquete,
            COUNT(c.id) as total
        FROM
            codigos_acceso c
        JOIN
            periodos p ON c.periodo_id = p.id
        WHERE
            YEAR(p.inicio) = 2023
        GROUP BY
            MONTH(p.inicio), c.paquete
        ORDER BY
            MONTH(p.inicio), c.paquete
        """
        
        c.execute(query)
        resultados = c.fetchall()

        # Inicializar diccionario para almacenar los datos
        ventas = {
            'Básico': [0] * 12,
            'Premium': [0] * 12,
            'Deluxe': [0] * 12
        }

        for resultado in resultados:
            mes = resultado['mes'] - 1  # ajustar para el índice de la lista
            ventas[resultado['paquete']][mes] = resultado['total']
        
        return ventas
    finally:
        close_db()
        
def get_ventas_mensuales_por_suscripcion2023():
    db, c = get_db()
    
    try:
        query = """
        SELECT
            MONTH(p.inicio) as mes,
            c.tipo_suscripcion,
            COUNT(c.id) as total
        FROM
            codigos_acceso c
        JOIN
            periodos p ON c.periodo_id = p.id
        WHERE
            YEAR(p.inicio) = 2023
        GROUP BY
            MONTH(p.inicio), c.tipo_suscripcion
        ORDER BY
            MONTH(p.inicio), c.tipo_suscripcion
        """
        
        c.execute(query)
        resultados = c.fetchall()

        # Inicializar diccionario para almacenar los datos
        suscripciones = {
            'semestral': [0] * 12,
            'anual': [0] * 12
        }

        for resultado in resultados:
            mes = resultado['mes'] - 1  # ajustar para el índice de la lista
            suscripciones[resultado['tipo_suscripcion']][mes] = resultado['total']
        
        return suscripciones
    finally:
        close_db()

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
    # CARD VENTAS
    datos_grafica_ventas, card_ventas = get_consumo_ventas()
    fecha_venta = card_ventas['inicio']

    fecha_venta_formateada = formatear_fecha(fecha_venta)
    
    # CARD INGRESOS
    datos_grafica_ingresos, card_ingresos = get_ingreso_ventas()
    fecha_ingresos = card_ingresos['inicio']
    
    fecha_ingresos_formateada = formatear_fecha(fecha_ingresos)
    
    # CARD USUSARIOS
    datos_grafica_usuarios, card_usuarios = get_nuevos_usuarios()
    fecha_usuarios = card_usuarios['inicio']
    
    fecha_usuarios_formateada = formatear_fecha(fecha_usuarios)

    # TOTAL DE HOGARES
    total_hogares = get_cantidad_hogares()
    
    # TOTAL DE USUARIOS
    total_usuarios = get_cantidad_usuarios()
    
    # TOTAL DE DISPOSITIVOS
    total_dispositivos = get_cantidad_dispositivos()
    
    # TOTAL DE PAQUETES VENDIDOS
    total_paquetes_vendidos = get_cantidad_paquetes_vendidos()
    
    # ESTATUS DE HOGARES
    estatus_tipos, estatus_cantidades = get_estatus_hogares()
    
    # GRÁFICA STACK BAR - VENTAS POR MES 2023
    ventasPaquete2023 = get_ventas_mensuales_por_paquete2023()
    ventasSuscripcion2023 = get_ventas_mensuales_por_suscripcion2023()
    
    return render_template(
        'admin/admin-estadisticas.html', 
        user=g.user,
        # CARD VENTAS
        card_ventas=card_ventas,
        fecha_venta_formateada=fecha_venta_formateada,
        # CARD INGRESOS
        card_ingresos=card_ingresos,
        fecha_ingresos_formateada=fecha_ingresos_formateada,
        # CARD USUARIOS
        card_usuarios=card_usuarios,
        fecha_usuarios_formateada=fecha_usuarios_formateada,
        # TABLA ADMINISTRACIÓN
        total_hogares=total_hogares['total'],
        total_usuarios=total_usuarios['total'],
        total_dispositivos=total_dispositivos['total'],
        total_paquetes_vendidos=total_paquetes_vendidos['total'],
        # GRÁFICA STACK BAR - VENTAS POR MES 2023
        ventasPaquete2023=ventasPaquete2023,
        ventasSuscripcion2023=ventasSuscripcion2023,
        # GRÁFICA PIE - TIPOS ESTATUS HOGAR
        estatus_tipos=estatus_tipos,
        estatus_cantidades=estatus_cantidades
        )

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