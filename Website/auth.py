from flask import Blueprint, render_template, request, flash, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from .models import UserAccounts, Employee_Profiles
from flask_login import login_user, login_required, logout_user, current_user

auth = Blueprint('auth', __name__)



@auth.route('/login', methods=['GET', 'POST'])
def login():
    data = request.form
    print(data)
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = UserAccounts.query.filter_by(username=username).first()
        if user:
            user_login_attempts = user.login_attempts
            if user_login_attempts > 10:
                flash('You have exceeded 10 failed login attempts, therefore your account has been disabled.', category='error')
            elif check_password_hash(user.password, password):
                user.login_attempts = 0
                import datetime
                now = datetime.datetime.now()
                user.last_login = now.strftime('%Y-%m-%dT%H:%M')
                db.session.commit()
                login_user(user, remember=True)
                flash('Logged in Successful as ' + username, category='success')
                if current_user.role == 'admin':
                    return redirect(url_for('admin.general_settings'))
                else:
                    return redirect(url_for('views.home'))
            else:
                user_login_attempts += 1
                user.login_attempts = user_login_attempts
                db.session.commit()
                flash('Incorrect Password.', category='error')
        else:
            flash('Username does not exist.', category='error')

    return render_template("login.html", user=current_user)


@auth.route('/logout')
@login_required
def logout():
    flash('Successfully logged out.', category='success')
    logout_user()
    return redirect(url_for('auth.login'))


@auth.route('/sign_up', methods = ['GET', 'POST'])
def sign_up():
    data = request.form
    print(data)
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        user = UserAccounts.query.filter_by(username=username).first()
        useremail = Employee_Profiles.query.filter_by(email=email).first()
        if not useremail:
            flash('Referral Email does not exist.', category='error')
        elif user:
            flash('Username already exist.', category='error')
        elif len(username) < 6:
            flash('Username must be greater than 5 characters.', category='error')
        elif len(email) < 3:
            flash('Email must be at least 3 characters.', category='error')
        elif len(password1) < 7:
            flash('Password must be at least 7 characters.', category='error')
        elif not any(char.isnumeric() for char in password1):
            flash('Password must contain at least 1 digit', category='error')
        elif not any(char.isupper() for char in password1):
            flash('Password must contain at least 1 Upper Case Character', category='error')
        elif not any(char.islower() for char in password1):
            flash('Password must contain at least 1 Lower Case Character', category='error')
        elif password1 != password2:
            flash("Passwords don't match.", category='error')
        else:
            new_user = UserAccounts(username=username,
                                   employee_id=useremail.id,
                                   email=email,
                                   role='user',
                                   password=generate_password_hash(password1, method='SHA256'),
                                   login_attempts=0)
            db.session.add(new_user)
            db.session.commit()
            flash('Registered Successfully!', category='success')
            return redirect(url_for('auth.sign_up'))
    return render_template("sign_up.html", user=current_user)