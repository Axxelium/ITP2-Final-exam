import uuid
from datetime import datetime

from flask import (Blueprint, render_template, request,
                   session, redirect, url_for, flash)

from config               import Config
from services.db_service  import DatabaseService
from models.record        import Record
from decorators           import login_required

user_bp = Blueprint('user', __name__, url_prefix='/user')

db = DatabaseService(Config.USERS_JSON, Config.RECORDS_JSON)


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
            flash('Пароль — минимум 6 символов', 'error')
            return redirect(url_for('user.profile'))

        from models.user import User
        user.password_hash = User.hash_password(new_password)
        db.update_user(user)
        flash('Пароль успешно обновлён', 'success')
        return redirect(url_for('user.profile'))

    records_count = len(db.get_records_by_user(user.id))
    return render_template('user/profile.html',
                           user          = user,
                           records_count = records_count)


@user_bp.route('/records/add', methods=['POST'])
@login_required()
def records_add():
    name         = request.form.get('name', '').strip()
    department   = request.form.get('department', '').strip()
    salary_str   = request.form.get('salary', '')
    worked_since = request.form.get('worked_since', '')

    if not all([name, department, salary_str, worked_since]):
        flash('Заполните все поля', 'error')
        return redirect(url_for('user.dashboard'))

    try:
        salary       = int(salary_str)
        worked_since = int(worked_since)
    except ValueError:
        flash('Зарплата и год должны быть числами', 'error')
        return redirect(url_for('user.dashboard'))

    if not (1 <= salary <= 50_000_000):
        flash('Зарплата должна быть от 1 до 50 000 000', 'error')
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
    flash('Сотрудник добавлен', 'success')
    return redirect(url_for('user.dashboard'))