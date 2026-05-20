import uuid
from datetime import datetime

from flask import (Blueprint, render_template, request,
                   session, redirect, url_for, flash, abort, jsonify)

from config               import Config
from models.user          import User
from services.db_service  import DatabaseService
from services.bot_service import BotService
from decorators           import login_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

db  = DatabaseService(Config.USERS_JSON, Config.RECORDS_JSON)
bot = BotService()

PER_PAGE = 10


@admin_bp.route('/dashboard')
@login_required(role='admin')
def dashboard():
    users   = db.get_all_users()
    records = db.get_all_records()

    recent_users = sorted(users, key=lambda u: u.created_at, reverse=True)[:5]

    return render_template('admin/dashboard.html',
                           total_users   = len(users),
                           total_records = len(records),
                           recent_users  = recent_users)


@admin_bp.route('/users')
@login_required(role='admin')
def users():
    all_users = db.get_all_users()
    return render_template('admin/users.html', users=all_users)


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
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    role     = request.form.get('role', 'user')

    if len(username) < 3 or len(password) < 6:
        flash('Логин — мин. 3 символа, пароль — мин. 6 символов', 'error')
        return redirect(url_for('admin.users'))

    if db.get_user_by_username(username):
        flash('Пользователь с таким именем уже существует', 'error')
        return redirect(url_for('admin.users'))

    if role not in ('admin', 'user'):
        role = 'user'

    user = User(
        id            = str(uuid.uuid4()),
        username      = username,
        password_hash = User.hash_password(password),
        role          = role,
        created_at    = datetime.now().isoformat(),
    )
    db.save_user(user)
    bot.notify_new_user(username)

    flash(f'Employees {username} created', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/delete/<user_id>', methods=['POST'])
@login_required(role='admin')
def users_delete(user_id):
    if user_id == session.get('user_id'):
        flash('You cant delete yourself', 'error')
        return redirect(url_for('admin.users'))

    db.delete_records_by_user(user_id)
    deleted = db.delete_user(user_id)

    if deleted:
        bot.notify_admin_action('delete_user', f'user_id={user_id}')
        flash('Employee and his records deleted', 'success')
    else:
        flash('Employee not found', 'error')

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

    if len(new_username) < 3:
        flash('Username must be at least 3 characters', 'error')
        return redirect(url_for('admin.users'))

    existing = db.get_user_by_username(new_username)
    if existing and existing.id != user_id:
        flash('Username already taken', 'error')
        return redirect(url_for('admin.users'))

    user.username = new_username
    user.role     = new_role
    db.update_user(user)

    bot.notify_admin_action('edit_user', f'user_id={user_id} new_username={new_username}')
    flash(f'User {new_username} updated successfully', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/data')
@login_required(role='admin')
def data():
    all_records = db.get_all_records()
    all_users   = {u.id: u.username for u in db.get_all_users()}

    page     = request.args.get('page', 1, type=int)
    total    = len(all_records)
    pages    = max(1, (total + PER_PAGE - 1) // PER_PAGE)
    page     = max(1, min(page, pages))
    start    = (page - 1) * PER_PAGE
    records  = all_records[start:start + PER_PAGE]

    return render_template('admin/data.html',
                           records   = records,
                           users_map = all_users,
                           page      = page,
                           pages     = pages,
                           total     = total)