from flask import (
    Blueprint, flash, g, redirect, render_template, url_for, 
)
from werkzeug.exceptions import abort
from .auth import login_required
from .db import get_db

bp = Blueprint('admin', __name__)

@bp.route('/admin-dashboard')
@login_required
def admin_index():
    return render_template('admin-dashboard.html', user=g.user)

