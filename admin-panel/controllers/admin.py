import uuid
from datetime import datetime

from flask import (Blueprint, render_template, request,
                   session, redirect, url_for, flash, jsonify)

from config               import Config
from models.user          import User
from services.db_service  import DatabaseService
from services.bot_service import BotService
from decorators           import login_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

db  = DatabaseService(Config.USERS_JSON, Config.DEPARTMENTS_JSON)
bot = BotService()


@admin_bp.route('/dashboard')
@login_required(role='admin')
def dashboard():
    users        = db.get_all_users()
    recent_users = sorted(users, key=lambda u: u.created_at, reverse=True)[:5]
    return render_template('admin/dashboard.html',
                           total_users  = len(users),
                           recent_users = recent_users)


# ── Users ──────────────────────────────────────────────────────

@admin_bp.route('/users')
@login_required(role='admin')
def users():
    all_users   = db.get_all_users()
    departments = db.get_all_departments()
    return render_template('admin/users.html',
                           users       = all_users,
                           departments = departments)


@admin_bp.route('/users/search')
@login_required(role='admin')
def users_search():
    query     = request.args.get('q', '').strip().lower()
    all_users = db.get_all_users()
    if query:
        all_users = [u for u in all_users
                     if query in u.username.lower()
                     or query in u.role.lower()]
    return jsonify([u.to_dict() for u in all_users])


@admin_bp.route('/users/create', methods=['POST'])
@login_required(role='admin')
def users_create():
    username   = request.form.get('username', '').strip()
    password   = request.form.get('password', '')
    role       = request.form.get('role', 'user')
    department = request.form.get('department', '').strip()
    salary_str = request.form.get('salary', '').strip()

    if len(username) < 3 or len(password) < 6:
        flash('Username min 3 chars, password min 6 chars', 'error')
        return redirect(url_for('admin.users'))

    if db.get_user_by_username(username):
        flash('Username already taken', 'error')
        return redirect(url_for('admin.users'))

    if role not in ('admin', 'user'):
        role = 'user'

    salary = 0
    if salary_str:
        try:
            salary = int(salary_str)
        except ValueError:
            salary = 0

    user = User(
        id            = str(uuid.uuid4()),
        username      = username,
        password_hash = User.hash_password(password),
        role          = role,
        created_at    = datetime.now().isoformat(),
        salary        = salary,
        department    = department,
    )
    db.save_user(user)
    bot.notify_new_user(username)
    flash(f'Employee {username} created', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/edit/<user_id>', methods=['POST'])
@login_required(role='admin')
def users_edit(user_id):
    user = db.get_user_by_id(user_id)
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('admin.users'))

    new_username = request.form.get('username', '').strip()
    new_role     = request.form.get('role', 'user')
    new_dept     = request.form.get('department', '').strip()
    salary_str   = request.form.get('salary', '').strip()

    if len(new_username) < 3:
        flash('Username must be at least 3 characters', 'error')
        return redirect(url_for('admin.users'))

    existing = db.get_user_by_username(new_username)
    if existing and existing.id != user_id:
        flash('Username already taken', 'error')
        return redirect(url_for('admin.users'))

    user.username   = new_username
    user.role       = new_role
    user.department = new_dept

    if salary_str:
        try:
            salary = int(salary_str)
            if 1 <= salary <= 50_000_000:
                user.salary = salary
            else:
                flash('Salary must be between 1 and 50,000,000', 'error')
                return redirect(url_for('admin.users'))
        except ValueError:
            flash('Salary must be a number', 'error')
            return redirect(url_for('admin.users'))
    else:
        user.salary = 0

    db.update_user(user)
    bot.notify_admin_action('edit_user', f'user_id={user_id}')
    flash(f'Employee {new_username} updated', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/delete/<user_id>', methods=['POST'])
@login_required(role='admin')
def users_delete(user_id):
    if user_id == session.get('user_id'):
        flash("You can't delete yourself", 'error')
        return redirect(url_for('admin.users'))

    deleted = db.delete_user(user_id)
    if deleted:
        bot.notify_admin_action('delete_user', f'user_id={user_id}')
        flash('Employee deleted', 'success')
    else:
        flash('Employee not found', 'error')

    return redirect(url_for('admin.users'))


# ── Departments ────────────────────────────────────────────────

@admin_bp.route('/departments')
@login_required(role='admin')
def departments():
    depts = db.get_all_departments()
    return render_template('admin/departments.html', departments=depts)


@admin_bp.route('/departments/create', methods=['POST'])
@login_required(role='admin')
def departments_create():
    name = request.form.get('name', '').strip()
    if not name:
        flash('Department name is required', 'error')
        return redirect(url_for('admin.departments'))
    db.save_department({'id': str(uuid.uuid4()), 'name': name})
    flash(f'Department "{name}" created', 'success')
    return redirect(url_for('admin.departments'))


@admin_bp.route('/departments/edit/<dept_id>', methods=['POST'])
@login_required(role='admin')
def departments_edit(dept_id):
    name = request.form.get('name', '').strip()
    if not name:
        flash('Department name is required', 'error')
        return redirect(url_for('admin.departments'))
    db.update_department(dept_id, name)
    flash('Department updated', 'success')
    return redirect(url_for('admin.departments'))


@admin_bp.route('/departments/delete/<dept_id>', methods=['POST'])
@login_required(role='admin')
def departments_delete(dept_id):
    db.delete_department(dept_id)
    flash('Department deleted', 'success')
    return redirect(url_for('admin.departments'))