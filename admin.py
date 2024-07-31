from flask import (
    Blueprint, flash, g, redirect, render_template, url_for, request,
)
import datetime
from werkzeug.exceptions import abort
from .auth import login_required, admin_role_required
from .db import get_db, close_db

bp = Blueprint('admin', __name__)

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
            'basico': [0] * 12,
            'premium': [0] * 12,
            'deluxe': [0] * 12
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

@bp.route('/admin-dashboard')
@login_required
@admin_role_required
def admin_index():
    return render_template('admin/admin-dashboard.html', user=g.user)

@bp.route('/admin-estadisticas')
@login_required
@admin_role_required
def admin_estadisticas():
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
    print(ventasSuscripcion2023)
    
    return render_template(
        'admin/admin-estadisticas.html', 
        user=g.user,
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
        flash(f"Ocurrió un error: {e}", 'danger')
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
            flash('¡Oops, algo salió mal!. Verifica la información', 'error')

    return redirect(url_for('admin.admin_hogares'))

@bp.route('/hogar/<int:id>/delete', methods=['POST'])
@login_required
@admin_role_required
def eliminar_hogar(id):
    db, c = get_db()
    print(id)
    c.execute('SELECT * FROM hogares WHERE id = %s', (id,))
    hogar = c.fetchone()

    if hogar is None:
        abort(404, f"Hogar id {id} no encontrado.")
    
    c.reset()
    c.execute('DELETE FROM hogares WHERE id = %s', (id,))
    db.commit()
    flash('Hogar y sus miembros han sido eliminados correctamente.', 'success')
    return redirect(url_for('admin.admin_hogares'))