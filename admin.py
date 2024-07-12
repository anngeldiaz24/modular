from flask import (
    Blueprint, flash, g, redirect, render_template, url_for, 
)
from werkzeug.exceptions import abort
from .auth import login_required, admin_role_required
from .db import get_db

bp = Blueprint('admin', __name__)

@bp.route('/admin-dashboard')
@login_required
@admin_role_required
def admin_index():
    return render_template('admin-dashboard.html', user=g.user)

@bp.route('/hogares')
@login_required
@admin_role_required
def admin_hogares():
    db, c = get_db()
    
    try:
        # Obtener todos los hogares, los usuarios que pertenecen a estos, y el paquete del código de acceso
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

        # Organizar los datos en una estructura adecuada para la plantilla
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
        # Manejar la excepción y posiblemente renderizar una plantilla de error
        flash(f"Ocurrió un error: {e}", 'danger')

    return render_template('admin/hogares-view.html', user=g.user, hogares=hogares)