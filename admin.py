from flask import (
    Blueprint, flash, g, redirect, render_template, url_for, request,
    current_app
)
import requests
import os
import random
from datetime import datetime
import imutils
import numpy as np
import cv2
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
    
        return resultado['ultimo_periodo_id'] if resultado else None
    finally:
        close_db()
        
def get_consumo_ventas():
    db, c = get_db()

    try: 
        # Consulta para obtener los consumos por periodo
        query = """
        SELECT periodo_id
        FROM codigos_acceso
        WHERE disponible = 0
        ORDER BY periodo_id
        """
        c.execute(query)
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

        # Caso 1: No hay datos disponibles
        if len(ultimos_periodos) == 0:
            return datos_grafica, {'ventas_actuales': None}

        # Caso 2: Solo hay un periodo disponible
        elif len(ultimos_periodos) == 1:
            ventas_actuales = ultimos_periodos[0]['consumo']
            return datos_grafica, {
                'ventas_actuales': ventas_actuales,
                'ventas_anteriores': None,
                'porcentaje_cambio': 0.00,
                'positivo': False,
                'inicio': ultimos_periodos[0]['inicio']  # Fecha del único periodo disponible
            }

        # Caso 3: Hay al menos dos periodos disponibles
        else:
            ventas_actuales = ultimos_periodos[0]['consumo']
            ventas_anteriores = ultimos_periodos[1]['consumo']
            diferencia = ventas_actuales - ventas_anteriores
            porcentaje_cambio = (diferencia / ventas_anteriores) * 100

            return datos_grafica, {
                'ventas_actuales': ventas_actuales,
                'ventas_anteriores': ventas_anteriores,
                'porcentaje_cambio': round(porcentaje_cambio, 2),
                'positivo': porcentaje_cambio > 0,
                'inicio': ultimos_periodos[1]['inicio']  # Fecha del periodo anterior
            }
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

        # Caso 1: No hay datos disponibles
        if len(ultimos_periodos) == 0:
            return datos_grafica, {'ingresos_actuales': None}

        # Caso 2: Solo hay un periodo disponible
        elif len(ultimos_periodos) == 1:
            ingresos_actual = ultimos_periodos[0]['ingreso']
            return datos_grafica, {
                'ingresos_actuales': ingresos_actual,
                'ingresos_anteriores': None,
                'porcentaje_cambio': 0.00,
                'positivo': False,
                'inicio': ultimos_periodos[0]['inicio']  # Fecha del único periodo disponible
            }

        # Caso 3: Hay al menos dos periodos disponibles
        else:
            ingresos_actual = ultimos_periodos[0]['ingreso']
            ingresos_anterior = ultimos_periodos[1]['ingreso']
            diferencia = ingresos_actual - ingresos_anterior
            porcentaje_cambio = (diferencia / ingresos_anterior) * 100

            return datos_grafica, {
                'ingresos_actuales': ingresos_actual,
                'ingresos_anteriores': ingresos_anterior,
                'porcentaje_cambio': round(porcentaje_cambio, 2),
                'positivo': porcentaje_cambio > 0,
                'inicio': ultimos_periodos[1]['inicio']  # Fecha del periodo anterior
            }

    finally:
        close_db(db)
        
def get_total_cancelaciones():
    db, c = get_db()
    
    try: 
        # Consulta para obtener los hogares cancelados con su periodo_id
        query = f"""
        SELECT DISTINCT u.periodo_id
        FROM hogares h
        JOIN users u ON h.id = u.hogar_id
        WHERE h.estatus = 'cancelado'
        ORDER BY u.periodo_id
        """
        c.execute(query)
        # Obtiene los resultados de la consulta
        datos = c.fetchall()
        
        # Convierte los resultados a un formato de lista de diccionarios
        datos_grafica = [{'periodo_id': dato['periodo_id']} for dato in datos]
        
        # Consulta para obtener las cancelaciones de los dos últimos periodos
        query_ultimos_periodos = """
        SELECT COUNT(DISTINCT h.id) as cancelaciones, u.periodo_id, p.inicio
        FROM hogares h
        JOIN users u ON h.id = u.hogar_id
        JOIN periodos p ON u.periodo_id = p.id
        WHERE h.estatus = 'cancelado'
        GROUP BY u.periodo_id, p.inicio
        ORDER BY u.periodo_id DESC
        LIMIT 2
        """
    
        c.execute(query_ultimos_periodos)
        ultimos_periodos = c.fetchall()
        
        # Si no hay datos
        if len(ultimos_periodos) == 0:
            return datos_grafica, {'cancelaciones_actuales': None}
        
        elif len(ultimos_periodos) == 1:
            cancelaciones_actuales = ultimos_periodos[0]['cancelaciones']
            return datos_grafica, {
                'cancelaciones_actuales': cancelaciones_actuales,
                'cancelaciones_anteriores': None,
                'porcentaje_cambio': 0.00,
                'positivo': False,
                'inicio': ultimos_periodos[0]['inicio']
            }
        
        else:
            cancelaciones_actuales = ultimos_periodos[0]['cancelaciones']
            cancelaciones_anteriores = ultimos_periodos[1]['cancelaciones']
            diferencia = cancelaciones_actuales - cancelaciones_anteriores
            porcentaje_cambio = (diferencia / cancelaciones_anteriores) * 100 if cancelaciones_anteriores else 0.00
            diferencia_porcentual = {
                'cancelaciones_actuales': cancelaciones_actuales,
                'cancelaciones_anteriores': cancelaciones_anteriores,
                'porcentaje_cambio': round(porcentaje_cambio, 2),
                'positivo': porcentaje_cambio > 0,
                'inicio': ultimos_periodos[1]['inicio']
            }
        
        return datos_grafica, diferencia_porcentual
    finally:
        close_db()
        
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

        # Caso 1: No hay datos disponibles
        if len(ultimos_periodos) == 0:
            return datos_grafica, {'usuarios_actuales': None}

        # Caso 2: Solo hay un periodo disponible
        elif len(ultimos_periodos) == 1:
            usuarios_actual = ultimos_periodos[0]['nuevos_usuarios']
            return datos_grafica, {
                'usuarios_actuales': usuarios_actual,
                'usuarios_anteriores': None,
                'porcentaje_cambio': 0.00,
                'positivo': False,
                'inicio': ultimos_periodos[0]['inicio']  # Fecha del único periodo disponible
            }

        # Caso 3: Hay al menos dos periodos disponibles
        else:
            usuarios_actual = ultimos_periodos[0]['nuevos_usuarios']
            usuarios_anterior = ultimos_periodos[1]['nuevos_usuarios']
            diferencia = usuarios_actual - usuarios_anterior
            porcentaje_cambio = (diferencia / usuarios_anterior) * 100

            return datos_grafica, {
                'usuarios_actuales': usuarios_actual,
                'usuarios_anteriores': usuarios_anterior,
                'porcentaje_cambio': round(porcentaje_cambio, 2),
                'positivo': porcentaje_cambio > 0,
                'inicio': ultimos_periodos[1]['inicio']  # Fecha del periodo anterior
            }

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
            paq.nombre as paquete,
            COUNT(c.id) as total
        FROM
            codigos_acceso c
        JOIN
            periodos p ON c.periodo_id = p.id
        JOIN
            paquetes paq ON c.paquete_id = paq.id
        WHERE
            YEAR(p.inicio) = 2023
        GROUP BY
            MONTH(p.inicio), paq.nombre
        ORDER BY
            MONTH(p.inicio), paq.nombre
        """
        
        c.execute(query)
        resultados = c.fetchall()

        # Inicializar diccionario para almacenar los datos
        paquetes = [row['paquete'] for row in resultados]
        paquetes_unicos = list(set(paquetes))
        ventas = {paquete: [0] * 12 for paquete in paquetes_unicos}

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
    
def validar_card(card_data, tipo_card):
    """
    Función para validar los datos de una card (ventas, ingresos, cancelaciones) y retornar mensajes de error.
    
    Args:
        card_data (dict): Diccionario con los datos de la card.
        tipo_card (str): Tipo de card, para usar en los mensajes de error.
        
    Returns:
        tuple: fecha_formateada, inicio_anterior, mensaje_error (si aplica)
    """
    fecha_formateada = 'N/A'
    inicio_anterior = None
    mensaje_error = None

    # Verificar si card_data tiene datos
    if card_data:
        # Obtener la fecha del periodo anterior (si existe)
        fecha = card_data.get('inicio', None)
        fecha_formateada = formatear_fecha(fecha) if fecha else 'N/A'
        inicio_anterior = card_data.get('inicio')
        
    # Construir dinámicamente los nombres de los campos a validar, basados en el tipo de card
    campo_actuales = f"{tipo_card}_actuales"
    campo_anteriores = f"{tipo_card}_anteriores"

    # Validaciones de cancelaciones actuales y anteriores
    if card_data.get(campo_actuales) is None:
        mensaje_error = f'No hay datos disponibles para el último periodo de {tipo_card}.'
    elif card_data.get(campo_anteriores) is None:
        mensaje_error = f'No existe un registro del periodo anterior para {tipo_card}.'

    return fecha_formateada, inicio_anterior, mensaje_error

@bp.route('/admin-estadisticas')
@login_required
@admin_role_required
def admin_estadisticas():
    # CARD VENTAS
    datos_grafica_ventas, card_ventas = get_consumo_ventas()
    fecha_venta_formateada, inicio_anterior_ventas, mensaje_error_ventas = validar_card(card_ventas, "ventas")

    if mensaje_error_ventas:
        flash(mensaje_error_ventas, 'error')
    
    # CARD INGRESOS
    datos_grafica_ingresos, card_ingresos = get_ingreso_ventas()
    fecha_ingresos_formateada, inicio_anterior_ingresos, mensaje_error_ingresos = validar_card(card_ingresos, "ingresos")

    if mensaje_error_ingresos:
        flash(mensaje_error_ingresos, 'error')
    
    # CARD CANCELACIONES
    datos_grafica_cancelaciones, card_cancelaciones = get_total_cancelaciones()
    fecha_cancelaciones_formateada, inicio_anterior_cancelaciones, mensaje_error_cancelaciones = validar_card(card_cancelaciones, "cancelaciones")
    if mensaje_error_cancelaciones:
        flash(mensaje_error_cancelaciones, 'error')
    
    # CARD USUARIOS
    datos_grafica_usuarios, card_usuarios = get_nuevos_usuarios()
    fecha_usuarios_formateada, inicio_anterior_usuarios, mensaje_error_usuarios = validar_card(card_usuarios, "usuarios")
    if mensaje_error_usuarios:
        flash(mensaje_error_usuarios, 'error')

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
        # CARD CANCELACIONES
        card_cancelaciones=card_cancelaciones,
        fecha_cancelaciones_formateada=fecha_cancelaciones_formateada,
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
                p.nombre AS paquete
            FROM 
                hogares h
            LEFT JOIN 
                users u ON h.id = u.hogar_id
            LEFT JOIN
                codigos_acceso ca ON u.codigo_acceso = ca.id
            LEFT JOIN
                paquetes p ON ca.paquete_id = p.id
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
        paquete_nombre = request.form['paquete']
        estatus = request.form['estatus']
                
        error = None

        if not paquete_nombre:
            error = 'El paquete es requerido.'
        elif not estatus:
            error = 'El estatus es requerido.'

        if error is None:
            try:
                db, c = get_db()
                
                # Obtener el ID del paquete basado en el nombre
                c.execute('SELECT id FROM paquetes WHERE nombre = %s', (paquete_nombre,))
                paquete = c.fetchone()

                if paquete is None:
                    error = 'El paquete seleccionado no es válido.'
                    flash(error, 'error')
                    return redirect(url_for('admin.admin_hogares'))

                paquete_id = paquete['id']
                
                # Obtener información del hogar y el código de acceso
                c.execute('''
                    SELECT 
                        ca.id AS codigo_acceso_id, ca.paquete_id, h.id AS hogar_id
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
                  
                # Se asegura de completar la lectura de los resultados antes de hacer la siguiente consulta  
                c.reset()

                # Actualizar el paquete_id en la tabla de códigos de acceso
                c.execute('UPDATE codigos_acceso SET paquete_id = %s WHERE id = %s', (paquete_id, hogar['codigo_acceso_id']))
                # Actualizar el estatus en la tabla de hogares
                c.execute('UPDATE hogares SET estatus = %s WHERE id = %s', (estatus, id))

                db.commit()

                flash('¡Hogar actualizado correctamente!', 'success')

                return redirect(url_for('admin.admin_hogares'))

            except Exception as e:
                db.rollback()
                flash(f"Ocurrió un error: {e}", 'error')

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
        
    try:
        # Elimina los registros del consumo de agua asociados al hogar
        c.execute('DELETE FROM consumo_agua WHERE hogar_id = %s', (id, ))
        
        # Elimina los registros del consumo de energía asociados al hogar
        c.execute('DELETE FROM consumo_energia WHERE hogar_id = %s', (id, ))
        
        # Elimina los dispositivos asociados al hogar
        c.execute('DELETE FROM dispositivos WHERE hogar_id = %s', (id, ))
        
        # Elimina los registros de eventos asociados al hogar
        c.execute('DELETE FROM registros_eventos WHERE hogar_id = %s', (id, ))
    
        # Elimina el hogar
        c.execute('DELETE FROM hogares WHERE id = %s', (id,))
        
        c.reset()
        db.commit()
        flash('Hogar y sus miembros han sido eliminados correctamente.', 'success')
    except Exception as e:
        db.rollback()
        flash(f"Ocurrió un error al eliminar el hogar: {e}", 'error')
        
    return redirect(url_for('admin.admin_hogares'))

def get_paquetes():
    db, c = get_db()
    
    try:
        c.execute('''
            SELECT 
                id, nombre, descripcion
            FROM 
                paquetes
        ''')
        data = c.fetchall()

        paquetes = {}
        for row in data:
            paquetes[row['id']] = {
                'nombre': row['nombre'],
                'descripcion': row['descripcion']
            }
    except Exception as e:
        flash(f"Ocurrió un error: {e}", 'error')
        paquetes = {}

    return paquetes

@bp.route('/paquetes')
@login_required
@admin_role_required
def admin_paquetes():
    paquetes = get_paquetes()
    
    # Define una lista de colores
    colores = [
        'text-primary-500 bg-blue-500', 'text-success-500 bg-green-500', 'text-warning-500 bg-warning-500', 
        'text-red-500 bg-red-500', 'text-info-500 bg-info-500'
    ]
    
    # Asigna un color basado en el ID del paquete
    color_count = len(colores)
    for i, (paquete_id, paquete) in enumerate(paquetes.items()):
        paquete['color'] = colores[i % color_count]
        
    return render_template('admin/paquetes-view.html', user=g.user, paquetes=paquetes)

@bp.route('/crear-paquete', methods=['POST'])
@login_required
@admin_role_required
def crear_paquete():
    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']

        db, c = get_db()
        error = None

        # Validaciones
        if not isinstance(nombre, str) or not nombre:
            error = 'El nombre es requerido.'
        elif not isinstance(descripcion, str) or not descripcion or len(descripcion) < 3:
            error = 'La descripcion es requerida y debe ser una cadena de al menos 3 caracteres.'

        if error is None:
            try:
                c.execute(
                    "INSERT INTO paquetes (nombre, descripcion) VALUES (%s, %s)",
                    (nombre, descripcion)
                )
                db.commit()
                flash('Paquete añadido existosamente!', 'success')
                return redirect(url_for('admin.admin_paquetes'))
            except Exception as e:
                db.rollback()
                error = str(e)
                flash(error, 'error')
        else:
            flash(error, 'error')
    return redirect(url_for('admin.admin_paquetes'))

@bp.route('/paquete/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_role_required
def editar_paquete(id):
    if request.method == 'POST':
        paquete_nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        
                
        error = None

        if not paquete_nombre:
            error = 'El nombre del paquete es requerido.'
        elif not descripcion:
            error = 'La descripcion es requerida.'

        if error is None:
            try:
                db, c = get_db()
                
                # Obtener el paquete basado en el ID
                c.execute('SELECT id FROM paquetes WHERE id = %s', (id,))
                paquete = c.fetchone()

                if paquete is None:
                    error = 'El paquete seleccionado no es válido.'
                    flash(error, 'error')
                    return redirect(url_for('admin.admin_paquetes'))

                # Se asegura de completar la lectura de los resultados antes de hacer la siguiente consulta  
                c.reset()

                # Actualizar el nombre y la descripción del paquete
                c.execute('UPDATE paquetes SET nombre = %s, descripcion = %s WHERE id = %s', (paquete_nombre, descripcion, id))

                db.commit()

                flash('¡Paquete actualizado correctamente!', 'success')

                return redirect(url_for('admin.admin_paquetes'))

            except Exception as e:
                db.rollback()
                flash(f"Ocurrió un error: {e}", 'error')

        else:
            flash(error, 'error')

    return redirect(url_for('admin.admin_paquetes'))

@bp.route('/paquete/<int:id>/delete', methods=['POST'])
@login_required
@admin_role_required
def eliminar_paquete(id):
    db, c = get_db()
    c.execute('SELECT * FROM paquetes WHERE id = %s', (id,))
    paquete = c.fetchone()

    if paquete is None:
        abort(404, f"Paquete id {id} no encontrado.")
        
    try:
        # Actualizar los códigos de acceso para desvincularlos del paquete que se va a eliminar
        # Aquí puedes establecer paquete_id a NULL o a un paquete_id predeterminado
        paquete_predeterminado_id = None  # O el ID de un paquete predeterminado

        c.execute('UPDATE codigos_acceso SET paquete_id = %s WHERE paquete_id = %s', (paquete_predeterminado_id, id))
    
        # Elimina el paquete
        c.execute('DELETE FROM paquetes WHERE id = %s', (id,))
        
        c.reset()
        db.commit()
        flash('El paquete ha sido eliminado correctamente.', 'success')
    except Exception as e:
        db.rollback()
        flash(f"Ocurrió un error al eliminar el paquete: {e}", 'error')
        
    return redirect(url_for('admin.admin_paquetes'))

@bp.route('/procesar-rostros', methods=['POST'])
@login_required
@admin_role_required
def crear_modelo():
    dataPath = 'C:\\Users\\Angel Diaz\\Desktop\\Modular\\Data'  # Cambia a la ruta donde hayas almacenado Data
    hogaresList = os.listdir(dataPath)
    print('Lista de hogares: ', hogaresList)

    labels = []
    facesData = []
    label = 0

    # Procesar imágenes por hogar y usuario
    for hogar_id in hogaresList:
        hogar_path = os.path.join(dataPath, hogar_id)

        if os.path.isdir(hogar_path):
            print(f'Procesando hogar: {hogar_id}')
            for usuario in os.listdir(hogar_path):
                personPath = os.path.join(hogar_path, usuario)
                print(f'Leyendo las imágenes de {usuario} en {hogar_id}')

                if os.path.isdir(personPath):  # Verificar que sea un directorio
                    for fileName in os.listdir(personPath):
                        print(f'Rostros: {usuario}/{fileName}')
                        labels.append(label)
                        facesData.append(cv2.imread(os.path.join(personPath, fileName), 0))

                    label += 1  # Aumentar la etiqueta después de cada usuario

    # Crear y entrenar el reconocedor de rostros
    face_recognizer = cv2.face.LBPHFaceRecognizer_create()

    print("Entrenando...")
    face_recognizer.train(facesData, np.array(labels))

    # Almacenando el modelo obtenido
    model_path = os.path.join(dataPath, 'Modelo', 'modeloLBPHFace.xml')
    if not os.path.exists(os.path.dirname(model_path)):
        os.makedirs(os.path.dirname(model_path))
        
    face_recognizer.write(model_path)
    print("Modelo almacenado en: ", model_path)

    flash('Rostros procesados con éxito.', 'success')
    return redirect(url_for('admin.admin_hogares'))