from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy_utils import database_exists, create_database
import colorama
from colorama import Fore, Style, Back
from apscheduler.schedulers.background import BackgroundScheduler
from flask_restful import Api
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

colorama.init(autoreset=True)
db = SQLAlchemy()
# Defining the variable 'db' as a SQLAlchemy engine, defining it as a global variable enables import from other views


def create_app(conf):
    print("Server IP: " + Fore.MAGENTA + conf['host'])
    print("Server Port: " + Fore.MAGENTA + conf['port'])
    print("Secret Key: " + Fore.MAGENTA + conf['secret_key'])
    print("MySQL User: " + Fore.MAGENTA + conf['mysql_user'])
    print("MySQL Password: " + Fore.MAGENTA + conf['mysql_password'])
    print("MySQL Host: " + Fore.MAGENTA + conf['mysql_host'])
    print("MySQL Port: " + Fore.MAGENTA + conf['mysql_port'])
    print("MySQL Database Name: " + Fore.MAGENTA + conf['mysql_db_name'])
    print(" ")
    # Printing out configuration values

    app = Flask(__name__)
    app.secret_key = conf['secret_key']  # Assigning secret key of the application, used to sign the CSRF Token
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://' + conf['mysql_user'] + ':' + conf['mysql_password'] + '@' + conf[
        'mysql_host'] + ':' + conf['mysql_port'] + '/' + conf['mysql_db_name']  # Assign DB URI from the config
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)  # Initialize DB in the app
    api = Api(app)  # Initialize API in the app
    limiter = Limiter(app, key_func=get_remote_address)
    csrf = CSRFProtect(app)
    csrf.init_app(app)

    from .api import EZApi
    api.add_resource(EZApi, '/ezapi')

    from .views import views
    from .auth import auth
    from .admin import admin
    # Here are 3 blueprints registered into the app
    app.register_blueprint(views, urlprefix='/')
    app.register_blueprint(auth, urlprefix='/')
    app.register_blueprint(admin)

    from .models import UserAccounts

    print("Connecting to Database... [" + Fore.YELLOW + "?" + Fore.RESET + "]")
    database_exists(app.config['SQLALCHEMY_DATABASE_URI'])
    print("Connected [" + Fore.GREEN + "OK" + Fore.RESET + "]")
    print("Checking Database..." + Fore.YELLOW + "[?]")
    if not database_exists(app.config['SQLALCHEMY_DATABASE_URI']):
        print("Database Does NOT Exists!" + Fore.RED + "[ERROR]")
        print("Creating New Database (" + Fore.CYAN + "RFID" + Fore.RESET + ") ...")
        create_database(app.config['SQLALCHEMY_DATABASE_URI'])
        print("Created Database (" + Fore.CYAN + "RFID" + Fore.RESET + ") " + Fore.GREEN + "[OK]")
    else:
        print("Database (" + Fore.CYAN + "RFID" + Fore.RESET + ") " + Fore.GREEN + "[OK]")

    print("Checking Tables..." + Fore.YELLOW + "[?]")
    with app.app_context():
        print("Making Sure all Tables are existing...")
        print("Done")
        print(" ")
        db.create_all()  # Create all tables in the DB

        print("Checking User Admin Account...")
        from .models import UserAccounts
        from .auth import generate_password_hash
        user_admin_exists = UserAccounts.query.filter_by(username="admin").first()
        # Check if there are any admin accounts in the DB
        if not user_admin_exists:  # If there are no admin accounts
            import datetime
            now = datetime.datetime.now()
            new_user_admin = UserAccounts(
                username='admin',
                role='admin',
                password=generate_password_hash('admin', method='SHA256'),
                login_attempts=0,
                created_on=now.strftime('%Y-%m-%dT%H:%M')  # last_login not needed
            )
            db.session.add(new_user_admin)  # Create a default admin account with the above details
            db.session.commit()
            print("Creating Default Admin Account...")
            print("username: " + Fore.MAGENTA + "admin")
            print("password: " + Fore.MAGENTA + "admin")
            print(Fore.YELLOW + "Make sure you change the admin password for security reasons.")
        else:
            print("User Admin Account " + Fore.GREEN + "[OK]")

        print(" ")

        print('Checking Attendance Rules...')
        from .models import Attendance_Rules
        attendance_rules_exists = Attendance_Rules.query.all()  # Check if any attendance rules exists in DB
        if not attendance_rules_exists:  # If there are no attendance rules exist
            present = Attendance_Rules(
                name='Present',
                icon='✔️',
                color='#00ff11',
                enabled='on'
            )
            db.session.add(present)
            late = Attendance_Rules(
                name='Late',
                icon='⚠️',
                color='#ffe100',
                enabled='on'
            )
            db.session.add(late)
            absent = Attendance_Rules(
                name='Absent',
                icon='❌',
                color='#ff2600',
                enabled='on'
            )
            db.session.add(absent)
            db.session.commit()  # Insert the default 3 rules - Present, Late, Absent
        else:
            print('Attendance Rules Exist!')

        print("Checking App Settings...")
        from .models import App_Settings
        app_settings_exists = App_Settings.query.all()
        if not app_settings_exists:
            print('App Settings Does Not Exists!')
            print('Setting Attendance Check Time to 00:00')
            att_check_time = App_Settings(
                var='att_check_time',
                name='Attendance Check Time',
                value='00:00'
            )
            db.session.add(att_check_time)
            db.session.commit()
        else:
            print('App Settings Exists!')

        from .models import Payroll_Modifiers
        payroll_modifiers_exists = Payroll_Modifiers.query.all()
        if not payroll_modifiers_exists:
            print('Payroll Modifiers Does Not Exist!')
            print('Setting to Default Values..')
            epf = Payroll_Modifiers(
                variable='epf',
                value=0.11
            )
            db.session.add(epf)
            socso = Payroll_Modifiers(
                variable='socso',
                value=0.02
            )
            db.session.add(socso)
            db.session.commit()
        else:
            print('Payroll Modifier Exists!')

        def check_attendance():
            from .models import Attendance_List
            import datetime
            with app.app_context():
                print("Updating All Attendances...")
                employees = Attendance_List.query.all()
                today = datetime.datetime.now()
                yesterday = (today - datetime.timedelta(days=1)).strftime("%d-%m-%Y")
                for e in employees:
                    attendance = Attendance_List.query.filter(
                        Attendance_List.employee_username == e.username,
                        Attendance_List.date == yesterday
                    ).first()
                    if attendance:
                        attendance.status = "Not Clocked Out"
                        db.session.commit()
                    else:
                        new_att = Attendance_List(
                            employee_username=e.username,
                            date=yesterday,
                            day=(today - datetime.timedelta(days=1)).strftime("%A"),
                            checkin_time='--:--:--',
                            checkout_time='--:--:--',
                            status='Absent'
                        )
                        db.session.add(new_att)
                        db.session.commit()
                print("Updated All Attendances")

        scheduler = BackgroundScheduler()  # Create a new scheduler
        from .models import App_Settings
        att_check_time = App_Settings.query.filter_by(
            var='att_check_time'
        ).first()
        att_check_time = att_check_time.value  # Retrieve Attendance Check Time from DB
        hour = int(att_check_time[:2])  # Extract the 'hour' from att_check_time
        minute = int(att_check_time[3:5])  # Extract the 'minute' from att_check_time
        scheduler.add_job(check_attendance, 'cron', day_of_week='mon-sun', hour=hour, minute=minute)  # Add new job to scheduler
        print(f"Checking Attendances at {att_check_time} Everyday, details shown in the following:")
        scheduler.print_jobs()  # Prints out the details of the scheduler's job
        scheduler.start()  # Make the scheduler work

        print(" ")
        print("Starting Server...")
        print(" ")

    login_manager = LoginManager()  # Defining the authentication handler
    login_manager.login_view = 'auth.login'  # '/login' in 'auth.py' will handle all the authentication
    login_manager.init_app(app)  # Initialize the handler

    @login_manager.user_loader
    def load_user(username):  # Users are being identified by their 'username'
        return UserAccounts.query.get(username)

    return app  # returns 'app' with additional configured data such as db, csrf, api, blueprints, login manager
