import keyword

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import db
from sqlalchemy import or_, and_, not_
import os
from werkzeug.utils import secure_filename

from .models import Attendance_Rules, App_Settings, Departments, Employee_Profiles, Departments_JobPositions, \
    Attendance_List, Notifications, UserAccounts, Employee_Tasks, Employee_Tasks_Assignments, Payroll_Payslips, \
    Employee_Payrolls, Employee_Tickets, Employee_Tickets_Chats, Payroll_Modifiers
from .auth import check_password_hash, generate_password_hash
import datetime

admin = Blueprint('admin', __name__, url_prefix='/admin_panel')

from .views import UPLOAD_FOLDER, allowed_file

now = datetime.datetime.now()  # Define global variable, can then be used in every function


@admin.route('/general_settings', methods=['GET', 'POST'])
@login_required
def general_settings():
    if current_user.role == 'user':
        return redirect(url_for('views.home'))
    attendance_rules = Attendance_Rules.query.all()  # Get all data from AttendanceRules
    departments = Departments.query.all()  # Get all data from Departments
    app_settings = App_Settings.query.all()  # Get all data from AppSettings
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'new_attendance_rule':  # Adding a new Attendance Rule
            name_exist = Attendance_Rules.query.filter(
                Attendance_Rules.name == request.form.get('name')
            ).first()
            icon_exist = Attendance_Rules.query.filter(
                Attendance_Rules.color == request.form.get('color')
            ).first()
            if name_exist:
                flash('Name Already Exist', category='error')
            elif icon_exist:
                flash('Icon Already Exist', category='error')
            else:
                enabled = request.form.get('enabled')
                if enabled != 'on':
                    enabled = 'off'
                new_attendance_rule = Attendance_Rules(
                    name=request.form.get('name'),
                    icon=request.form.get('icon'),
                    color=request.form.get('color'),
                    enabled=enabled
                )
                db.session.add(new_attendance_rule)
                db.session.commit()
        elif action == 'new_department':  # Adding new department & positions
            department_name = request.form.get('department_name')
            days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']  # Defining preset days, to be chose for workdays
            workdays = []  # First, there are no workdays selected yet
            for day in days:  # Looping each value in days
                if request.form.get(day) == 'on':  # If user ticks the day in the form
                    workdays.append(day)  # The ticked day will be added into workdays
            workdays = ', '.join(workdays)  # Concatenating workdays from List to String
            work_time = request.form.get('start_time') + ' - ' + request.form.get('end_time') \
                # Concatenating work start_time and end_time
            available_positions = request.form.get('positions').split('\r\n') \
                # Positions inputted from user are in various lines of string, convert them into a List
            new_department = Departments(
                name=department_name,
                work_days=workdays,
                work_time=work_time
            )  # Laying out the data ready to be inserted into the DB
            db.session.add(new_department)  # Insert the data into the DB
            db.session.commit()  # Commit DB Changes
            for line in available_positions:
                new_position = Departments_JobPositions(
                    department_id=new_department.id,
                    name=line
                )
                db.session.add(new_position)  # For each line of positions input by user, insert into DB
            db.session.commit()
            flash('New Department Added Successfully.', category='success')
        return redirect(url_for('admin.general_settings')) \
            # Redirect User back to /admin_panel/general_settings to see the changes made
    return render_template('admin_general_settings.html',
                           user=current_user,
                           attendance_rules=attendance_rules,
                           departments=departments,
                           app_settings=app_settings
                           )


def search_query(model_class, search_value, **kwargs):  # A function to search for records
    filters = []  # Creating a List to store queries, to be returned later

    search_columns = kwargs['search_columns']
    if search_columns:
        if type(search_columns) == list:  # If the data type of search_columns is a List
            for i in search_columns:  # Loop the List
                filters.append(getattr(model_class, i).like('%' + search_value + '%')) \
                    # Insert the looped item into filters parsed as a SQLAlchemy search pattern
        else:  # If data type of search_columns is not a List (non-loop value)
            filters.append(getattr(model_class, search_columns).like('%' + search_value + '%')) \
                # Insert it directly into filters parsed as a SQLAlchemy search pattern
    try:  # If the keyword argument join_tables exist, meaning there are columns from other tables that must\
        # be joined to perform the search
        join_tables = kwargs['join_tables']  # Is a Dictionary Variable
        for j in join_tables:  # Loop the Dictionary
            if type(join_tables[j]) == list:  # If the data type of the looped item's value is a List
                for i in j:  # Loop the list
                    filters.append(
                        getattr(j, i).like('%' + search_value + '%'))  # Insert the loop item into filters
            else:  # If the data type of the looped item's value is not a List
                filters.append(getattr(j, join_tables[j]).like('%' + search_value + '%'))  # Insert directly
    except:
        pass

    return filters  # Return the final results


@admin.route('/attendance_list', methods=['GET', 'POST'])
@login_required
def attendance_list():
    attendance_list = Attendance_List.query.all()  # Get all data from AttendanceList
    if request.method == 'GET':
        search = request.args.get('search')
        if search:  # If ?search= argument exists in the url
            filters = search_query(Attendance_List,
                                   search,
                                   search_columns=['date',
                                                   'date',
                                                   'checkin_time',
                                                   'checkout_time',
                                                   'status'],
                                   join_tables={Employee_Profiles: 'name'})  # Map all queries needed accordingly
            attendance_list = Attendance_List.query.filter(
                or_(
                    *filters  # Apply the filters into the query
                )
            ).all()  # Get all DB records based on the query
        else:  # No arguments in the url
            search = ''  # No need to search
    return render_template('admin_attendance_list.html',
                           user=current_user,
                           search_value=search,
                           attendance_list=reversed(attendance_list)
                           )


@admin.route('/employee_profiles', methods=['GET', 'POST'])
@login_required
def employee_profiles():
    employee_profiles = Employee_Profiles.query.all()  # Get all data from EmployeeProfiles
    departments = Departments.query.all()  # Get all data from Departments
    search = ''
    if request.method == 'GET':
        search = request.args.get('search')
        action = request.args.get('action')
        if search:  # If search?= exists in the url
            filters = search_query(Employee_Profiles,
                                   search,
                                   search_columns=['email',
                                                   'date_of_birth',
                                                   'address',
                                                   'contact',
                                                   'marital_status',
                                                   'gender',
                                                   'date_recruited'],
                                   join_tables={Departments: 'name', Departments_JobPositions: 'name'})  # Map Filters
            employee_profiles = Employee_Profiles.query.filter(
                or_(
                    *filters  # Apply Filters
                )
            ).all()
        elif action:  # If action?= exists in the url
            id = request.args.get('id')
            profile = Employee_Profiles.query.filter(
                Employee_Profiles.id == id
            ).first()  # Get employee data based on the id
            useraccount = UserAccounts.query.filter(
                UserAccounts.employee_id == id
            ).first()  # Get user account data based on the id
            supervisees = Employee_Profiles.query.filter(
                Employee_Profiles.supervisor_id == id
            ).all()  # Get supervisor id based on the id
            payroll = Employee_Payrolls.query.filter(
                Employee_Payrolls.employee_id == id
            ).first()  # Get payroll data based on the id
            from .views import get_att_rate, get_task_rate
            if action == 'view':  # If action?=view exists in the url
                return render_template('admin_view_profile_details.html',
                                       user=current_user,
                                       profile=profile,
                                       registered=useraccount,
                                       action=action,
                                       supervisees=supervisees,
                                       payroll=payroll,
                                       attendance_rate=get_att_rate(useraccount),
                                       task_rate=get_task_rate(useraccount))  # Return all data to display on the page
            elif action == 'edit':  # If action?=edit exists in the url
                gender_options = ['Male', 'Female', 'Prefer Not To Say']  # Defining preset choices for gender_options
                marital_status_options = ['Single', 'Engaged', 'Married', 'Separated', 'Divorced', 'Widowed'] \
                    # Defining preset choices for marital_status_options
                salary_method_options = ['Full Time', 'Part Time']  # Defining preset choices for salary_method_options
                gender_options.remove(profile.gender)  # Remove the value of the profile's gender from gender_options
                marital_status_options.remove(profile.marital_status) \
                    # Remove the value of the profile's marital_status from marital_status_options
                departments = Departments.query.filter(
                    Departments.id != profile.department
                ).all()  # Get data of all departments excluding the department of the current profile
                job_positions = Departments_JobPositions.query.filter(
                    Departments_JobPositions.department_id == profile.department,
                    Departments_JobPositions.id != profile.position
                ).all()  # Get data of all job positions in the current department excluding the job position of the \
                # current profile
                return render_template('admin_view_profile_details.html',
                                       user=current_user,
                                       profile=profile,
                                       registered=useraccount,
                                       action=action,
                                       supervisees=supervisees,
                                       payroll=payroll,
                                       attendance_rate=get_att_rate(useraccount),
                                       gender_options=gender_options,
                                       marital_status_options=marital_status_options,
                                       salary_method_options=salary_method_options,
                                       departments=departments,
                                       job_positions=job_positions)
        else:
            search = ''  # Viewing all employee profiles
    elif request.method == 'POST':
        action = request.form.get('action')
        if action == 'new_employee':
            if 'file' not in request.files:
                flash('No File Selected', category='error')
                return redirect(request.url)  # Refresh page
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_extension = filename.split(".")[1]  # Get the extension of the file, e.g.: picture.png - >  \
                # ['picture', 'png'] -> 'png'
                email = request.form.get('email')
                name = request.form.get('name')
                date_of_birth = request.form.get('date_of_birth')
                age = int(now.strftime('%Y')) - int(date_of_birth[:4])  # Year of current time minus the year from \
                # date_of_birth, e.g.: 2022 - '2000-08-28'[:4] -> 2022 - 2000 -> 22 years old
                address = request.form.get('address')
                contact = request.form.get('contact')
                date_recruited = request.form.get('date_recruited')
                department = request.form.get('department')
                job_position = request.form.get('job_position')
                supervisor = request.form.get('supervisor')
                if supervisor == '':  # The employee has no supervisor
                    supervisor = None  # Assign a None value instead of '' (blank string), because '' still means it contains value
                else:
                    supervisor = int(supervisor)  # Convert string to number (id of the employee's supervisor), \
                    # e.g.: '25' -> 25
                salary_amount = request.form.get('salary_amount')
                gender = request.form.get('gender')
                marital_status = request.form.get('marital_status')
                check_email = Employee_Profiles.query.filter(
                    Employee_Profiles.email == email
                ).first()  # Find whether the given email address matches any of the email addresses in the DB
                if check_email:  # If exist
                    flash('Email Already Exist', category='error')  # Return error, email must be unique
                else:
                    new_employee = Employee_Profiles(
                        email=email,
                        name=name,
                        date_of_birth=date_of_birth,
                        age=age,
                        address=address,
                        contact=contact,
                        date_recruited=date_recruited,
                        department=int(department),
                        position=job_position,
                        gender=gender,
                        marital_status=marital_status,
                        supervisor_id=supervisor
                    )  # Mapping data accordingly to EmployeeProfiles
                    db.session.add(new_employee)  # Insert new_employee into DB
                    db.session.commit()
                    new_employee_payroll = Employee_Payrolls(
                        employee_id=new_employee.id,
                        base_salary=salary_amount,
                        allowance=0,  # Default value
                        bonus=0  # Default value
                    )  # Mapping data accordingly to EmployeePayrolls
                    db.session.add(new_employee_payroll)  # Insert new_employee_payroll into DB
                    db.session.commit()
                    file.save(os.path.join(UPLOAD_FOLDER, str(new_employee.id) + "." + file_extension)) \
                        # After assigning the file name (followed by the employee_id) of the profile picture, \
                    # save the profile picture into the directory
                    flash('New Employee Added Successfully.', category='success')
                    return redirect(url_for('admin.employee_profiles'))
        elif action == 'edit_employee_details':  # Updating the info of the employee
            print(request.form)
            editing_employee = Employee_Profiles.query.filter(
                Employee_Profiles.id == request.form.get('id')
            ).first()
            editing_employee.name = request.form.get('name')
            editing_employee.email = request.form.get('email')
            editing_employee.contact = request.form.get('contact')
            editing_employee.gender = request.form.get('gender')
            editing_employee.date_of_birth = request.form.get('date_of_birth')
            editing_employee.age = int(now.strftime('%Y')) - int(request.form.get('date_of_birth')[:4])
            editing_employee.marital_status = request.form.get('marital_status')
            editing_employee.address = request.form.get('address')
            editing_employee.date_recruited = request.form.get('date_recruited')
            editing_employee.department = int(request.form.get('department'))
            editing_employee.position = int(request.form.get('job_position'))
            editing_employee.salary_method = request.form.get('salary_method')
            editing_employee.salary_amount = request.form.get('salary_amount')
            try:
                editing_employee.supervisor_id = int(request.form.get('supervisor'))
            except:
                editing_employee.supervisor_id = None
            editing_employee_payroll = Employee_Payrolls.query.filter(
                Employee_Payrolls.employee_id == editing_employee.id
            ).first()
            editing_employee_payroll.base_salary = request.form.get('base_salary')
            editing_employee_payroll.allowance = request.form.get('allowance')
            editing_employee_payroll.bonus = request.form.get('bonus')
            db.session.commit()
            flash('Saved', category='success')
            return redirect((request.url[:-4] + 'view'))  # /employeeprofiles?id=(id)&action=view
    return render_template('admin_employee_profiles.html',
                           user=current_user,
                           search_value=search,
                           employee_profiles=employee_profiles,
                           departments=departments
                           )


@admin.route('/employee_tickets', methods=['GET', 'POST'])
@login_required
def employee_tickets():
    employee_tickets = Employee_Tickets.query.all()
    if request.method == 'GET':
        search = request.args.get('search')
        if search:
            filters = search_query(Employee_Tickets,
                                   search,
                                   search_columns=['title',
                                                   'refer_item',
                                                   'status',
                                                   'time_created',
                                                   'date_crated'],
                                   join_tables={UserAccounts: 'username'})
            employee_tickets = Employee_Tickets.query.filter(
                or_(
                    *filters
                )
            ).all()
        else:
            search = ''
    return render_template('admin_employee_tickets.html',
                           user=current_user,
                           search_value=search,
                           employee_tickets=employee_tickets
                           )


def process_receivers(**outer_kwargs):
    # Function to send notification, task or payslip to each employee of a (department/job position) without duplication
    receivers_names = outer_kwargs['receivers_names']
    receivers_categories = outer_kwargs['receivers_categories']
    category = outer_kwargs['category']
    total_receivers = []  # List to store the names of the total receivers
    already_sent = []  # List to store the names of employee who has already received the same message
    for i in receivers_names:  # Loop each employee name in the List
        total_receivers.append([(receivers_categories[receivers_names.index(i)]), i])
        # e.g.: [(receivers_categories[receivers_names.index('Lai Zhen')]), 'Lai Zhen']
        # ->    [(receivers_categories[0]), 'Lai Zhen']
        # ->    ['e', 'Lai Zhen']
        # Segment each receivers corresponding to their group type into a List, then insert it into total_receivers,
        # which means total_receivers is a nested List,
        # e.g.: -> [['e', 'Lai Zhen'], ['d', 'Information Technology Department']]

    def distribute(**inner_kwargs):
        # This is where is starts to send messages to each individuals
        # the variable 't' is a for loop variable at line 425,
        # so this function can only be used in the designated for loop
        # 't' stands for each List in total_receivers (the nested List)
        if inner_kwargs['class_model'] == Departments:  # To send message in a department
            department_id = Departments.query.filter(
                Departments.name == t[1]  # To get the second value in the List, in this case it is the department name
            ).first().id  # Get the department's id
            total_receivers_in_this_category = Employee_Profiles.query.filter(
                Employee_Profiles.department == department_id
            ).all()  # Get all employees that are in this department
        elif inner_kwargs['class_model'] == Departments_JobPositions:
            job_position_id = Departments_JobPositions.query.filter(
                Departments_JobPositions.name == t[1]
                # To get the second value in the List, in this case it is the job position name
            ).first().id
            total_receivers_in_this_category = Employee_Profiles.query.filter(
                Employee_Profiles.position == job_position_id
            ).all()  # Get all employees that has this job title
        elif inner_kwargs['class_model'] == Employee_Profiles:
            total_receivers_in_this_category = Employee_Profiles.query.filter(
                Employee_Profiles.name == t[1]
                # To get the second value in the List, in this case it is the employee name
            ).all()  # Get the DB record of the employee
        for employee in total_receivers_in_this_category:  # Loop through each employee name in the List
            if employee.name not in already_sent:  # If the looped name is not in the 'already_sent' List,
                # meaning that this employee has not received the message yet
                already_sent.append(employee.name)  # Insert the looped name into 'already_sent' List,
                # so the next loop will not send the message to the employee again
                # DUPLICATION MITIGATED
                # Below are just inserting data into the DB according to the category
                if category == 'notifications':
                    new_notification = Notifications(
                        sender=current_user.username,
                        receiver=employee.name,
                        date=now.strftime('%d-%m-%Y'),
                        day=now.strftime('%A'),
                        time=now.strftime('%I:%M:%S %p'),
                        title=outer_kwargs['title'],
                        message=outer_kwargs['message']
                    )
                    db.session.add(new_notification)
                elif category == 'tasks':
                    new_task_assignment = Employee_Tasks_Assignments(
                        task_id=outer_kwargs['new_task'].id,
                        user=employee.id
                    )
                    db.session.add(new_task_assignment)
                elif category == 'payslip':
                    new_payslip = Payroll_Payslips(
                        formula_used='Custom',
                        total_pay_amount=outer_kwargs['amount'],
                        payee=employee.id,
                        datetime=now.strftime('%Y-%m-%dT%H:%M'),
                        description=outer_kwargs['description'],
                        generated_by=current_user.username
                    )
                    db.session.add(new_payslip)

    for t in total_receivers:
        if t[0] == 'd':  # If Type is Department
            distribute(class_model=Departments)
        elif t[0] == 'p':  # If Type is Position
            distribute(class_model=Departments_JobPositions)
        elif t[0] == 'e':  # If Type is Employee
            distribute(class_model=Employee_Profiles)
    db.session.commit()


@admin.route('/notification_center', methods=['GET', 'POST'])
@login_required
def notification_center():
    notifications = Notifications.query.all()
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
    elif request.method == 'POST':
        process_receivers(receivers_names=request.form.get('total_receivers').split(', '),
                          # Passing the receiver_names as a List
                          receivers_categories=request.form.get('total_receivers_category').split(', '),
                          # Passing the receiver_categories as a List
                          category='notifications',  # Specifying the sending category
                          title=request.form.get('title'),
                          message=request.form.get('message')
                          )
        return redirect(url_for('admin.notification_center'))
    return render_template('admin_notification_center.html',
                           user=current_user,
                           search_value=search,
                           notifications=reversed(notifications)
                           )


@admin.route('/task_assignment', methods=['GET', 'POST'])
@login_required
def task_assignment():
    employee_tasks = Employee_Tasks.query.all()
    search = request.args.get('search')
    if request.method == 'GET':
        if search:
            filters = search_query(Employee_Tasks,
                                   search,
                                   search_columns=['title',
                                                   'created_by',
                                                   'date_time_created',
                                                   'date_time_ended',
                                                   'due_date_time',
                                                   'status',
                                                   'type'],
                                   join_tables={UserAccounts: 'username'})
            employee_tasks = Employee_Tasks.query.filter(
                or_(
                    *filters
                )
            ).all()
        else:
            search = ''
    elif request.method == 'POST':
        new_task = Employee_Tasks(
            title=request.form.get('title'),
            message=request.form.get('message'),
            created_by=current_user.username,
            date_time_created=now.strftime('%Y-%m-%dT%H:%M'),
            due_date_time=request.form.get('due_date_time'),
            receivers=request.form.get('total_receivers'),
            status='Pending',
            type=request.form.get('type')
        )
        db.session.add(new_task)
        process_receivers(receivers_names=request.form.get('total_receivers').split(', '),
                          receivers_categories=request.form.get('total_receivers_category').split(', '),
                          category='tasks',
                          new_task=new_task
                          )
        return redirect(url_for('admin.task_assignment'))
    return render_template('admin_task_assignment.html',
                           user=current_user,
                           search=search,
                           employee_tasks=reversed(employee_tasks)
                           )


@admin.route('/payroll_settings', methods=['GET', 'POST'])
@login_required
def payroll_settings():
    formula = 'base_salary - base_salary(epf + socso) + allowance + bonus'  # Fixed Formula
    payroll_modifiers = Payroll_Modifiers.query.all()  # Get all data from PayrollModifiers
    payroll_payslips = Payroll_Payslips.query.all()  # Get all data from PayrollPayslips
    if request.method == 'POST':
        print(request.form)
        section = request.form.get('section')
        if section == 'formula':
            epf = Payroll_Modifiers.query.filter(
                Payroll_Modifiers.id == 1
            ).first()  # Fetch the DB record containing the value of epf
            socso = Payroll_Modifiers.query.filter(
                Payroll_Modifiers.id == 2
            ).first()  # Fetch the DB record containing the value of socso
            epf.value = request.form.get('variable_value_1')  # Update the value of epf
            socso.value = request.form.get('variable_value_2')  # Update the value of socso
            db.session.commit()
        elif section == 'payslip':
            process_receivers(receivers_names=request.form.get('total_receivers').split(', '),
                              receivers_categories=request.form.get('total_receivers_category').split(', '),
                              category='payslip',
                              amount=request.form.get('amount'),
                              description=request.form.get('description'))
        return redirect(url_for('admin.payroll_settings'))
    return render_template('admin_payroll_settings.html',
                           user=current_user,
                           formula=formula,
                           payroll_modifiers=payroll_modifiers,
                           payroll_payslips=reversed(payroll_payslips)
                           )
