from flask import (
    Blueprint, flash, g, redirect, render_template, url_for, request,
)
import datetime
from werkzeug.exceptions import abort
from .auth import login_required, admin_role_required
from .db import get_db

bp = Blueprint('admin', __name__)

@bp.route('/admin-dashboard')
@login_required
@admin_role_required
def admin_index():
    return render_template('admin/admin-dashboard.html', user=g.user)

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