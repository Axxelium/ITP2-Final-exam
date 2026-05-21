import uuid
from datetime import datetime

from flask import (Blueprint, render_template, request,
                   session, redirect, url_for, flash)

from config               import Config
from models.record        import Record
from services.db_service  import DatabaseService
from decorators           import login_required

user_bp = Blueprint('user', __name__, url_prefix='/user')

db = DatabaseService(Config.USERS_JSON, Config.DEPARTMENTS_JSON,
                     Config.RECORDS_JSON)


@user_bp.route('/dashboard')
@login_required()
def dashboard():
    records = db.get_records_by_user(session['user_id'])
    return render_template('user/dashboard.html', records=records)


@user_bp.route('/profile', methods=['GET', 'POST'])
@login_required()
def profile():
    user = db.get_user_by_id(session['user_id'])

    if request.method == 'POST':
        new_password = request.form.get('password', '')
        if len(new_password) < 6:
            flash('Password must be at least 6 characters', 'error')
            return redirect(url_for('user.profile'))

        from models.user import User as UserModel
        user.password_hash = UserModel.hash_password(new_password)
        db.update_user(user)
        flash('Password updated successfully', 'success')
        return redirect(url_for('user.profile'))

    records_count = len(db.get_records_by_user(user.id))
    colleagues    = [u for u in db.get_all_users() if u.id != user.id]
    departments   = db.get_all_departments()

    return render_template('user/profile.html',
                           user          = user,
                           records_count = records_count,
                           colleagues    = colleagues,
                           departments   = departments)


@user_bp.route('/records/add', methods=['POST'])
@login_required()
def records_add():
    name         = request.form.get('name', '').strip()
    department   = request.form.get('department', '').strip()
    salary_str   = request.form.get('salary', '')
    worked_since = request.form.get('worked_since', '')

    if not all([name, department, salary_str, worked_since]):
        flash('Please fill in all fields', 'error')
        return redirect(url_for('user.dashboard'))

    try:
        salary       = int(salary_str)
        worked_since = int(worked_since)
    except ValueError:
        flash('Salary and year must be numbers', 'error')
        return redirect(url_for('user.dashboard'))

    if not (1 <= salary <= 50_000_000):
        flash('Salary must be between 1 and 50,000,000', 'error')
        return redirect(url_for('user.dashboard'))

    record = Record(
        id           = str(uuid.uuid4()),
        name         = name,
        salary       = salary,
        department   = department,
        worked_since = worked_since,
        user_id      = session['user_id'],
        created_at   = datetime.now().isoformat(),
    )
    db.save_record(record)
    flash('Record added successfully', 'success')
    return redirect(url_for('user.dashboard'))