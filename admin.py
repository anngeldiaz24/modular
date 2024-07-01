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
    return render_template('admin/hogares-view.html', user=g.user)
