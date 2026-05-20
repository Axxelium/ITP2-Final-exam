from flask import (Blueprint, render_template, request,
                   session, redirect, url_for, flash)

from config               import Config
from services.db_service  import DatabaseService
from decorators           import login_required

user_bp = Blueprint('user', __name__, url_prefix='/user')

db = DatabaseService(Config.USERS_JSON, Config.RECORDS_JSON,
                     Config.DEPARTMENTS_JSON)


@user_bp.route('/dashboard')
@login_required()
def dashboard():
    return redirect(url_for('user.profile'))


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

    # все коллеги кроме самого себя, без зарплаты
    colleagues = [u for u in db.get_all_users() if u.id != user.id]

    return render_template('user/profile.html',
                           user       = user,
                           colleagues = colleagues)