from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response
from flask_login import login_required, current_user
from . import db
from sqlalchemy import or_, and_

from .models import Attendance_Rules, App_Settings, Departments, Employee_Profiles, Departments_JobPositions, \
    Attendance_List, Notifications, UserAccounts, Employee_Tasks, Employee_Tasks_Assignments, Payroll_Payslips, \
    Employee_Payrolls, Employee_Tickets, Employee_Tickets_Chats
from .auth import check_password_hash, generate_password_hash
import datetime
from .admin import record_log

views = Blueprint('views', __name__)


# def rearrange_date(input_date):
#     day = input_date[-2:]
#     month = input_date[5:7]
#     year = input_date[:4]
#     output_date = f'{day}-{month}-{year}'
#     return output_date


def get_att_rate(employee, *month):  # find the total/monthly attendance rate of the employee
    try:
        id = employee.employee_id  # <- employee = UserAccount Model
        if month:  # Calculate Monthly
            total_attendance_this_month = Attendance_List.query.filter(
                Attendance_List.date.like('%' + month[0] + '%'),
                Attendance_List.employee_id == id
            ).count()  # <- Find the Total Attendances Count of The Employee in The Selected Month
            present_this_month = Attendance_List.query.filter(
                Attendance_List.date.like('%' + month[0] + '%'),
                Attendance_List.status == 'Present',
                Attendance_List.employee_id == id
            ).count()  # <- Find the Total PRESENT Attendance Count of the Employee in the Selected Month
            attendance_rate = (present_this_month / total_attendance_this_month) * 100  # <- Calculate the %
        else:  # Calculate Total
            total_attendance = Attendance_List.query.filter(
                Attendance_List.employee_id == id
            ).count()  # <- Find the Total Attendance Count of the Employee
            total_present = Attendance_List.query.filter(
                Attendance_List.employee_id == id,
                Attendance_List.status == 'Present'
            ).count()  # <- Find the total PRESENT Attendance Count of the Employee
            attendance_rate = (total_present / total_attendance) * 100  # <- Calculate the %
    except:
        attendance_rate = 0  # <- If UserAccount of the Employee does not exists, because maybe they haven't register
    print(round(attendance_rate, 2))
    return round(attendance_rate, 2)  # <- DataType = Float, round it off by 2 decimal digits


def get_task_rate(employee):
    try:
        id = employee.employee_id  # <- employee = UserAccount Model
        total_tasks = Employee_Tasks_Assignments.query.filter(
            Employee_Tasks_Assignments.user == id
        ).count()  # <- Find the Total Amount of Tasks being assigned to this employee
        completed_tasks = Employee_Tasks_Assignments.query.filter(
            Employee_Tasks_Assignments.user == id,
            Employee_Tasks_Assignments.like('%')
        ).count()  # <- Find the Total Amount of Tasks completed by this employee
        task_rate = (completed_tasks / total_tasks) * 100  # <- Calculate the %
    except:
        task_rate = 0
    return round(task_rate, 2)  # <- DataType = Float, round it off by 2 decimal digits


@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    record_log(f'{current_user.username} viewed /')
    if current_user.role == 'admin':
        return redirect(url_for('admin.general_settings'))
    employee_profile = Employee_Profiles.query.filter(
        Employee_Profiles.id == current_user.employee_id
    ).first()  # <- Get the Data of the logged in User (Employee)
    notifications = Notifications.query.filter(
        Notifications.receiver == employee_profile.name
    ).limit(5).all()
    if notifications:
        notifications = reversed(notifications)
    payslips = Payroll_Payslips.query.filter(
        Payroll_Payslips.payee == employee_profile.id
    ).limit(5).all()
    if payslips:
        payslips = reversed(payslips)
    response = make_response(render_template("home.html",
                                             user=current_user,
                                             username=current_user.username,
                                             profile=employee_profile,
                                             total_attendance_rate=get_att_rate(current_user),
                                             month_attendance_rate=get_att_rate(current_user,
                                                                                datetime.datetime.now().strftime(
                                                                                    '%m-%Y')),
                                             notifications=notifications,
                                             payslips=payslips
                                             ))
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    return response


@views.route('/attendance', methods=['GET', 'POST'])
@login_required
def attendance():
    record_log(f'{current_user.username} viewed /attendance')
    if current_user.role == 'admin':
        return redirect(url_for('admin.general_settings'))
    from .models import Attendance_List, Attendance_Rules
    import datetime
    now = datetime.datetime.now()  # Get Current Time, is an object
    date = now.strftime("%d-%m-%Y")  # Get Current Date, e.g.: 04-04-2022
    day = now.strftime("%A")  # Get Current Day, e.g.: Monday
    time = now.strftime("%I:%M:%S %p")  # Get Current Time, e.g.: 10:59:00 PM

    current_month_main = now.strftime("%B %Y")  # Get Current Month for default view, e.g.: 04-2022
    current_finding_month = now.strftime("%%%m-%Y") \
        # Variable for the 1st value when searching for existing months, e.g.: %04-2022, used in the LIKE function in DB
    current_year = now.strftime("%Y")  # Get Current Year, e.g.: 2022
    current_month = now.strftime("%m")  # Get Current Month: e.g.: 04

    available_months = []  # Assume there are no existing records in the Attendance DB

    while True:  # Loop until no previous months found
        checking_string = str(current_month) + "-" + str(current_year) \
            # Concatenate current_month and current_year for search
        check_current_month_exist = Attendance_List.query.filter(
            and_(
                Attendance_List.date.like("%" + checking_string),
                Attendance_List.employee_id == current_user.employee_id
            )
        ).first()  # Checking whether there are any records matching with checking_string
        if check_current_month_exist:  # If the above statement exists
            appending_month = datetime.datetime(int(current_year), int(current_month), 1) \
                # Variable for getting the time object with the 1st day of current_year and current_month
            available_months.append(appending_month.strftime("%B %Y")) \
                # Insert current looping month into available_months
            current_month = int(current_month) - 1 \
                # Subtract 1 from current_month, in order to check for a previous month in the next loop
            if current_month == 0:  # After subtraction, if current_month becomes the value of 0
                current_month = 12  # Make the next looping month become 12 (December)
                current_year = int(current_year) - 1 \
                    # Subtract 1 from the current_year, checking for the previous year in the next loop
        else:
            break  # If there is no records in the Attendance DB, exit the loop and leaving available_months EMPTY

    types = Attendance_Rules.query.all()  # Get all attendance types defined in Attendance_Rules
    if request.method == 'POST':
        task = request.form.get('task')
        if task == 'sign_att':
            check = Attendance_List.query.filter_by(date=date).first()
            if check:
                check.checkout_time = time
                checkout_hour = int(time[:2])
                if "PM" in time:
                    checkout_hour += 12
                checkin_time = check.checkin_time
                if int(checkin_time[:2]) >= 9:
                    check.status = "Present"
                else:
                    check.status = "Late"
                db.session.commit()
            else:
                new_att = Attendance_List(
                    employee_id=current_user.employee_id,
                    date=date,
                    day=day,
                    checkin_time=time,
                    checkout_time="--:--",
                    status="In Work"
                )
                db.session.add(new_att)
                db.session.commit()
                flash('Successfully taken attendance.', category='success')
                return redirect(url_for('views.attendance'))

        elif task == 'chg_month':  # User (Employee) is changing month view of their attendance
            current_month_main = request.form.get('input')  # Assign new value from user selection, e.g.: March 2022
            input = current_month_main.split(' ')  # Convert to List, e.g.: ['March', '2022']
            input_month = input[0]  # First item in the list
            input_year = input[1]  # Second item in the list
            months = ['January', 'February', 'March', 'April', 'May', 'June', ' July', 'August', 'September', 'October',
                      'November', 'December'] \
                # Defining preset months, will be able to convert between number or string
            input_month = months.index(input_month) + 1 \
                # Convert input_month from string to number by identifying the index in the months list, then add 1
            # to make the month value correct (index starts from 0)
            # e.g.: March -> 2, 2 + 1 = 3
            current_finding_month = "%" + str(input_month) + "-" + str(input_year) \
                # Concatenate input_month and input_year for the next loop to check with

    employee_att = Attendance_List.query.filter(
        Attendance_List.employee_id == current_user.employee_id,
        Attendance_List.date.like(current_finding_month)
    ).all()  # Get all records of the employee's attendance matching with the selected month

    attendancetypes = Attendance_Rules.query.all()  # Get all types of attendance rules defined in AttendanceRules
    total_attendance_varieties = {}  # Assume there were no corresponding attendance records of the User (Employee)
    for row in attendancetypes:  # Loop each attendance types, e.g.: Present, Late, Absent
        att_type = row.name
        find = Attendance_List.query.filter(
            Attendance_List.employee_id == current_user.employee_id,
            Attendance_List.date.like(current_finding_month),
            Attendance_List.status == att_type
        ).count()
        total_attendance_varieties[att_type] = find \
            # Insert the value of current looping attendance type with the number of records corresponding to it
    return render_template('attendance.html',
                           user=current_user,
                           attendance=reversed(employee_att),
                           types=types,
                           total_attendance_varieties=total_attendance_varieties,
                           current_month=current_month_main,
                           available_months=available_months,
                           percentage=get_att_rate(current_user, current_finding_month[1:]))


from .admin import search_query


@views.route('/notifications', methods=['GET'])
@login_required
def notifications():
    record_log(f'{current_user.username} viewed /notifications')
    if current_user.role == 'admin':
        return redirect(url_for('admin.general_settings'))
    employee_name = Employee_Profiles.query.filter(
        Employee_Profiles.id == current_user.employee_id
    ).first().name
    notifications = Notifications.query.filter(
        Notifications.receiver == employee_name
    ).all()
    if notifications:
        notifications = reversed(notifications)
    search = ''
    if request.method == 'GET':
        search = request.args.get('search')
        if search:
            filters = search_query(Notifications,
                                   search,
                                   search_columns=['receiver',
                                                   'date',
                                                   'day',
                                                   'time',
                                                   'title'],
                                   join_tables={UserAccounts: 'username'})
            notifications = Notifications.query.filter(
                or_(
                    *filters
                )
            ).all()
        else:
            search = ''
    return render_template('notifications.html',
                           user=current_user,
                           notifications=notifications,
                           search=search)


@views.route('/tasks', methods=['GET', 'POST'])
@login_required
def tasks():
    record_log(f'{current_user.username} viewed /tasks')
    if current_user.role == 'admin':
        return redirect(url_for('admin.general_settings'))
    tasks_assignments = Employee_Tasks_Assignments.query.filter(
        Employee_Tasks_Assignments.user == current_user.employee_id
    ).all()
    tasks = []
    for task in tasks_assignments:
        main_task = Employee_Tasks.query.filter(
            Employee_Tasks.id == task.task_id
        ).first()
        tasks.append(main_task)
    if tasks:
        tasks = reversed(tasks)
    return render_template('tasks.html',
                           user=current_user,
                           tasks=tasks)


@views.route('/support', methods=['GET', 'POST'])
@login_required
def support():
    record_log(f'{current_user.username} viewed /support')
    if current_user.role == 'admin':
        return redirect(url_for('admin.general_settings'))
    tickets = Employee_Tickets.query.filter(
        Employee_Tickets.created_by == current_user.username
    ).all()
    if tickets:
        tickets = reversed(tickets)
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'new_ticket':
            title = request.form.get('title')
            message = request.form.get('message')
            import datetime
            now = datetime.datetime.now()
            date_created = now.strftime("%d-%m-%Y")
            time_created = now.strftime("%I:%M:%S %p")
            new_ticket = Employee_Tickets(
                created_by=current_user.username,
                title=title,
                status="Waiting for Admin's reply",
                time_created=time_created,
                date_created=date_created
            )
            db.session.add(new_ticket)
            db.session.commit()
            new_chat = Employee_Tickets_Chats(
                ticket_id=new_ticket.id,
                message=message,
                time=time_created,
                date=date_created
            )
            db.session.add(new_chat)
            db.session.commit()
            record_log(f'{current_user.username} created a new support ticket #{new_ticket.id}')
            flash('Successfully created a new support ticket.', category='success')
            return redirect(url_for('views.support'))
        # elif action == 'reply':

    return render_template('support.html',
                           user=current_user,
                           tickets=tickets)


@views.route('/profile', methods=['GET', 'POST'])
def profile():
    profile = Employee_Profiles.query.filter(
        Employee_Profiles.id == current_user.employee_id
    ).first()
    supervisees = Employee_Profiles.query.filter(
        Employee_Profiles.supervisor_id == current_user.employee_id
    ).all()  # Get supervisor id based on the id
    payroll = Employee_Payrolls.query.filter(
        Employee_Payrolls.employee_id == current_user.employee_id
    ).first()  # Get payroll data based on the id
    return render_template('profile.html',
                           user=current_user,
                           profile=profile,
                           registered=current_user,
                           supervisees=supervisees,
                           payroll=payroll,
                           attendance_rate=get_att_rate(current_user),
                           task_rate=get_task_rate(current_user)
    )

@views.route('/account_settings', methods=['GET', 'POST'])
@login_required
def account_settings():
    record_log(f'{current_user.username} viewed /account_settings')
    username = current_user.username
    email = current_user.email
    password = current_user.password
    return render_template('account_settings.html',
                           user=current_user,
                           username=username,
                           email=email,
                           password=password)


@views.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    record_log(f'{current_user.username} viewed /change_password')
    username = current_user.username
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password1 = request.form.get('new_password1')
        new_password2 = request.form.get('new_password2')
        userpasswordhash = current_user.password
        if not check_password_hash(userpasswordhash, current_password):
            flash('Password Incorrect', category='error')
        elif len(new_password1) < 7:
            flash('Password must be at least 7 characters.', category='error')
        elif not any(char.isnumeric() for char in new_password1):
            flash('Password must contain at least 1 digit', category='error')
        elif not any(char.isupper() for char in new_password1):
            flash('Password must contain at least 1 Upper Case Character', category='error')
        elif not any(char.islower() for char in new_password1):
            flash('Password must contain at least 1 Lower Case Character', category='error')
        elif new_password1 != new_password2:
            flash("Passwords don't match.", category='error')
        else:
            current_user.password = generate_password_hash(new_password1, method='SHA256') \
                # After validation, generate a new hash value by using SHA-256
            db.session.commit()  # Make changes to the DB
            record_log(f'{current_user.username} changed password successfully')
            flash("Successfully changed password.", category='success')
            return redirect(url_for('views.account_settings'))
    return render_template('change_password.html', user=current_user, username=username)
