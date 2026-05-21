import uuid
from datetime import datetime

from flask import (Blueprint, render_template, request,
                   session, redirect, url_for, flash, abort)

from config               import Config
from models.record        import Record
from models.user          import User
from services.db_service  import DatabaseService
from decorators           import login_required

user_bp = Blueprint('user', __name__, url_prefix='/user')


class UserController:

    def __init__(self):
        self.db = DatabaseService(Config.USERS_JSON,
                                  Config.DEPARTMENTS_JSON,
                                  Config.RECORDS_JSON)

    def dashboard(self):
        records = self.db.get_records_by_user(session['user_id'])
        return render_template('user/dashboard.html',
                               records     = records,
                               departments = self.db.get_all_departments())

    def profile(self):
        user = self.db.get_user_by_id(session['user_id'])

        if request.method == 'POST':
            new_password = request.form.get('password', '')
            if len(new_password) < 6:
                flash('Password must be at least 6 characters', 'error')
                return redirect(url_for('user.profile'))

            user.password_hash = User.hash_password(new_password)
            self.db.update_user(user)
            flash('Password updated successfully', 'success')
            return redirect(url_for('user.profile'))

        records_count = len(self.db.get_records_by_user(user.id))
        return render_template('user/profile.html',
                               user          = user,
                               records_count = records_count)

    # ── Валидация полей записи ────────────────────────────────────

    def _parse_record_form(self):
        """Возвращает (data, error). data=None если есть ошибка."""
        name         = request.form.get('name', '').strip()
        department   = request.form.get('department', '').strip()
        salary_str   = request.form.get('salary', '')
        worked_since = request.form.get('worked_since', '')

        if not all([name, department, salary_str, worked_since]):
            return None, 'Please fill in all fields'

        try:
            salary       = int(salary_str)
            worked_since = int(worked_since)
        except ValueError:
            return None, 'Salary and year must be numbers'

        if not (1 <= salary <= 50_000_000):
            return None, 'Salary must be between 1 and 50,000,000'

        return {
            'name':         name,
            'department':   department,
            'salary':       salary,
            'worked_since': worked_since,
        }, None

    def _owned_record_or_403(self, record_id):
        """Запись принадлежит текущему юзеру, иначе 403/redirect."""
        record = self.db.get_record_by_id(record_id)
        if not record:
            flash('Record not found', 'error')
            return None
        if record.user_id != session['user_id']:
            abort(403)
        return record

    def records_add(self):
        data, error = self._parse_record_form()
        if error:
            flash(error, 'error')
            return redirect(url_for('user.dashboard'))

        record = Record(
            id           = str(uuid.uuid4()),
            name         = data['name'],
            salary       = data['salary'],
            department   = data['department'],
            worked_since = data['worked_since'],
            user_id      = session['user_id'],
            created_at   = datetime.now().isoformat(),
        )
        self.db.save_record(record)
        flash('Record added successfully', 'success')
        return redirect(url_for('user.dashboard'))

    def records_edit(self, record_id):
        record = self._owned_record_or_403(record_id)
        if not record:
            return redirect(url_for('user.dashboard'))

        data, error = self._parse_record_form()
        if error:
            flash(error, 'error')
            return redirect(url_for('user.dashboard'))

        record.name         = data['name']
        record.department   = data['department']
        record.salary       = data['salary']
        record.worked_since = data['worked_since']
        self.db.update_record(record)
        flash('Record updated successfully', 'success')
        return redirect(url_for('user.dashboard'))

    def records_delete(self, record_id):
        record = self._owned_record_or_403(record_id)
        if not record:
            return redirect(url_for('user.dashboard'))

        self.db.delete_record(record_id)
        flash('Record deleted', 'success')
        return redirect(url_for('user.dashboard'))


_ctrl = UserController()

@user_bp.route('/dashboard')
@login_required()
def dashboard():
    return _ctrl.dashboard()

@user_bp.route('/profile', methods=['GET', 'POST'])
@login_required()
def profile():
    return _ctrl.profile()

@user_bp.route('/records/add', methods=['POST'])
@login_required()
def records_add():
    return _ctrl.records_add()

@user_bp.route('/records/edit/<record_id>', methods=['POST'])
@login_required()
def records_edit(record_id):
    return _ctrl.records_edit(record_id)

@user_bp.route('/records/delete/<record_id>', methods=['POST'])
@login_required()
def records_delete(record_id):
    return _ctrl.records_delete(record_id)