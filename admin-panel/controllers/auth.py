import uuid
from datetime import datetime

from flask import (Blueprint, render_template, request,
                   session, redirect, url_for, flash)

from config          import Config
from models.user     import User
from services.db_service  import DatabaseService
from services.bot_service import BotService

auth_bp = Blueprint('auth', __name__)

db  = DatabaseService(Config.USERS_JSON, Config.RECORDS_JSON)
bot = BotService()


@auth_bp.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    if session.get('role') == 'admin':
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('user.dashboard'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = db.get_user_by_username(username)
        if user and user.check_password(password):
            session['user_id']  = user.id
            session['role']     = user.role
            session['username'] = user.username

            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('user.dashboard'))

        flash('Неверный логин или пароль', 'error')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if len(username) < 3:
            flash('Имя пользователя — минимум 3 символа', 'error')
            return render_template('auth/register.html')
        if len(password) < 6:
            flash('Пароль — минимум 6 символов', 'error')
            return render_template('auth/register.html')
        if db.get_user_by_username(username):
            flash('Пользователь с таким именем уже существует', 'error')
            return render_template('auth/register.html')

        user = User(
            id            = str(uuid.uuid4()),
            username      = username,
            password_hash = User.hash_password(password),
            role          = 'user',
            created_at    = datetime.now().isoformat(),
        )
        db.save_user(user)
        bot.notify_new_user(username)

        flash('Регистрация успешна! Войдите в систему', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')