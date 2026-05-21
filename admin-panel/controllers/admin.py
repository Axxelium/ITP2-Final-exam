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

PER_PAGE = 10


class AdminController:

    def __init__(self):
        self.db  = DatabaseService(Config.USERS_JSON,
                                   Config.DEPARTMENTS_JSON,
                                   Config.RECORDS_JSON)
        self.bot = BotService()

    def dashboard(self):
        users        = self.db.get_all_users()
        records      = self.db.get_all_records()
        recent_users = sorted(users, key=lambda u: u.created_at, reverse=True)[:5]
        return render_template('admin/dashboard.html',
                               total_users   = len(users),
                               total_records = len(records),
                               recent_users  = recent_users)

    def users(self):
        return render_template('admin/users.html',
                               users = self.db.get_all_users())

    def users_search(self):
        query     = request.args.get('q', '').strip().lower()
        all_users = self.db.get_all_users()
        if query:
            all_users = [u for u in all_users
                         if query in u.username.lower()
                         or query in u.role.lower()]
        return jsonify([u.to_dict() for u in all_users])

    def users_create(self):
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        role     = request.form.get('role', 'user')

        if len(username) < 3 or len(password) < 6:
            flash('Username min 3 chars, password min 6 chars', 'error')
            return redirect(url_for('admin.users'))
        if self.db.get_user_by_username(username):
            flash('Username already taken', 'error')
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
        self.db.save_user(user)
        self.bot.notify_new_user(username)
        flash(f'User {username} created', 'success')
        return redirect(url_for('admin.users'))

    def users_edit(self, user_id):
        user = self.db.get_user_by_id(user_id)
        if not user:
            flash('User not found', 'error')
            return redirect(url_for('admin.users'))

        new_username = request.form.get('username', '').strip()
        new_role     = request.form.get('role', 'user')

        if len(new_username) < 3:
            flash('Username must be at least 3 characters', 'error')
            return redirect(url_for('admin.users'))

        existing = self.db.get_user_by_username(new_username)
        if existing and existing.id != user_id:
            flash('Username already taken', 'error')
            return redirect(url_for('admin.users'))

        if new_role not in ('admin', 'user'):
            new_role = 'user'

        user.username = new_username
        user.role     = new_role

        self.db.update_user(user)
        self.bot.notify_admin_action('edit_user', f'user_id={user_id}')
        flash(f'User {new_username} updated', 'success')
        return redirect(url_for('admin.users'))

    def users_delete(self, user_id):
        if user_id == session.get('user_id'):
            flash("You can't delete yourself", 'error')
            return redirect(url_for('admin.users'))

        self.db.delete_records_by_user(user_id)
        deleted = self.db.delete_user(user_id)
        if deleted:
            self.bot.notify_admin_action('delete_user', f'user_id={user_id}')
            flash('User and their records deleted', 'success')
        else:
            flash('User not found', 'error')
        return redirect(url_for('admin.users'))

    def data(self):
        all_records = self.db.get_all_records()
        users_map   = {u.id: u.username for u in self.db.get_all_users()}

        page    = request.args.get('page', 1, type=int)
        total   = len(all_records)
        pages   = max(1, (total + PER_PAGE - 1) // PER_PAGE)
        page    = max(1, min(page, pages))
        start   = (page - 1) * PER_PAGE
        records = all_records[start:start + PER_PAGE]

        return render_template('admin/data.html',
                               records   = records,
                               users_map = users_map,
                               page      = page,
                               pages     = pages,
                               total     = total)


_ctrl = AdminController()

@admin_bp.route('/dashboard')
@login_required(role='admin')
def dashboard():
    return _ctrl.dashboard()

@admin_bp.route('/users')
@login_required(role='admin')
def users():
    return _ctrl.users()

@admin_bp.route('/users/search')
@login_required(role='admin')
def users_search():
    return _ctrl.users_search()

@admin_bp.route('/users/create', methods=['POST'])
@login_required(role='admin')
def users_create():
    return _ctrl.users_create()

@admin_bp.route('/users/edit/<user_id>', methods=['POST'])
@login_required(role='admin')
def users_edit(user_id):
    return _ctrl.users_edit(user_id)

@admin_bp.route('/users/delete/<user_id>', methods=['POST'])
@login_required(role='admin')
def users_delete(user_id):
    return _ctrl.users_delete(user_id)

@admin_bp.route('/data')
@login_required(role='admin')
def data():
    return _ctrl.data()