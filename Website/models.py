from flask_login import UserMixin
from sqlalchemy.sql import func
from . import db


class App_Settings(db.Model):
    __tablename__ = 'app_settings'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    var = db.Column(db.String(30))
    name = db.Column(db.String(30))
    value = db.Column(db.String(30))


class UserAccounts(db.Model, UserMixin):
    __tablename__ = 'useraccounts'

    def get_id(self):
        return self.username

    username = db.Column(db.String(20), primary_key=True, unique=True)
    role = db.Column(db.String(10))
    employee_id = db.Column(db.Integer, db.ForeignKey('employee_profiles.id'))
    email = db.Column(db.String(50))
    password = db.Column(db.String(1000))
    login_attempts = db.Column(db.Integer)
    created_on = db.Column(db.String(25))
    last_login = db.Column(db.String(25))


class Admin_SystemLog(db.Model):
    __tablename__ = 'admin_systemlog'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date = db.Column(db.String(10))
    time = db.Column(db.String(12))
    action = db.Column(db.String(1000))


class Departments(db.Model):
    __tablename__ = 'departments'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100))
    work_days = db.Column(db.String(50))
    work_time = db.Column(db.String(30))
    relationship_employees = db.relationship('Employee_Profiles', backref=db.backref('departments', lazy=True))
    relationship_jobpositions = db.relationship('Departments_JobPositions', backref=db.backref('departments', lazy=True))


class Departments_JobPositions(db.Model):
    __tablename__ = 'departments_jobpositions'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    name = db.Column(db.String(100))
    relationship_employee = db.relationship('Employee_Profiles', backref=db.backref('jobposition', lazy=True))


class Employee_Profiles(db.Model):
    __tablename__ = 'employee_profiles'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(50))
    name = db.Column(db.String(50))
    date_of_birth = db.Column(db.String(10))
    age = db.Column(db.Integer)
    address = db.Column(db.String(150))
    contact = db.Column(db.String(20))
    marital_status = db.Column(db.String(30))
    gender = db.Column(db.String(30))
    date_recruited = db.Column(db.String(10))
    department = db.Column(db.Integer, db.ForeignKey('departments.id'))
    position = db.Column(db.Integer, db.ForeignKey('departments_jobpositions.id'))
    supervisor_id = db.Column(db.Integer, db.ForeignKey('employee_profiles.id'))
    relationship_supervisors = db.relationship('Employee_Profiles', backref=db.backref('supervisor', remote_side=[id]))
    relationship_credential_profile = db.relationship('UserAccounts', backref=db.backref('employee_profile', lazy=True))
    relationship_per_task = db.relationship('Employee_Tasks_Assignments', backref=db.backref('task', lazy=True))
    relationship_salary = db.relationship('Employee_Payrolls', backref=db.backref('salary', lazy=True))
    relationship_payslip = db.relationship('Payroll_Payslips', backref=db.backref('payslip', lazy=True))
    relationship_attendance = db.relationship('Attendance_List', backref=db.backref('profile', lazy=True))


class Employee_Payrolls(db.Model):
    __tablename__ = 'employee_payrolls'
    employee_id = db.Column(db.Integer, db.ForeignKey('employee_profiles.id'), primary_key=True)
    base_salary = db.Column(db.Integer)
    allowance = db.Column(db.Integer)
    bonus = db.Column(db.Integer)


class Employee_Tasks(db.Model):
    __tablename__ = 'employee_tasks'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200))
    message = db.Column(db.String(1000))
    created_by = db.Column(db.String(20), db.ForeignKey('useraccounts.username'))
    date_time_created = db.Column(db.String(25))
    date_time_ended = db.Column(db.String(25))
    due_date_time = db.Column(db.String(25))
    receivers = db.Column(db.String(1000))
    status = db.Column(db.String(30))
    type = db.Column(db.String(100))


class Employee_Tasks_Assignments(db.Model):
    __tablename__ = 'employee_tasks_assignments'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    task_id = db.Column(db.Integer, db.ForeignKey('employee_tasks.id'))
    user = db.Column(db.Integer, db.ForeignKey('employee_profiles.id'))
    date_time_ended = db.Column(db.String(25))


class Employee_Tickets(db.Model):
    __tablename__ = 'employee_tickets'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_by = db.Column(db.String(20), db.ForeignKey('useraccounts.username'))
    refer_item = db.Column(db.String(10))
    title = db.Column(db.String(200))
    status = db.Column(db.String(30))
    time_created = db.Column(db.String(12))
    date_created = db.Column(db.String(10))


class Employee_Tickets_Chats(db.Model):
    __tablename__ = 'employee_tickets_chats'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('employee_tickets.id'))
    message = db.Column(db.String(1000))
    time = db.Column(db.String(12))
    date = db.Column(db.String(10))


class Attendance_Rules(db.Model):
    __tablename__ = 'attendance_rules'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), unique=True)
    icon = db.Column(db.String(20))
    color = db.Column(db.String(20))
    enabled = db.Column(db.String(10))


class Attendance_List(db.Model):
    __tablename__ = 'attendance_list'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee_profiles.id'))
    date = db.Column(db.String(10))
    day = db.Column(db.String(10))
    checkin_time = db.Column(db.String(15))
    checkout_time = db.Column(db.String(15))
    status = db.Column(db.String(20))


class Attendance_Machines(db.Model):
    __tablename__ = 'attendance_machines'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100))
    location = db.Column(db.String(100))
    installation_date = db.Column(db.String(10))
    installation_time = db.Column(db.String(15))


class Notifications(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sender = db.Column(db.String(20), db.ForeignKey('useraccounts.username'))
    receiver = db.Column(db.String(100))
    date = db.Column(db.String(10))
    day = db.Column(db.String(10))
    time = db.Column(db.String(15))
    title = db.Column(db.String(200))
    message = db.Column(db.String(1000))


class Payroll_Modifiers(db.Model):
    __tablename__ = 'payroll_modifiers'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    variable = db.Column(db.String(50))
    value = db.Column(db.DECIMAL(10, 2))


class Payroll_Payslips(db.Model):
    __tablename__ = 'payroll_payslips'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    formula_used = db.Column(db.String(500))
    total_pay_amount = db.Column(db.Integer)
    payee = db.Column(db.Integer, db.ForeignKey('employee_profiles.id'))
    datetime = db.Column(db.String(25))
    description = db.Column(db.String(1000))
    generated_by = db.Column(db.String(20), db.ForeignKey('useraccounts.username'))
