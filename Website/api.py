from flask_restful import Resource, abort, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import jsonify, render_template
from . import db
import datetime
from .views import current_user
from .admin import record_log

from .models import Departments_JobPositions, Departments, Employee_Profiles, Notifications, Employee_Tasks, \
    Employee_Tasks_Assignments, Payroll_Payslips, Attendance_Machines, Attendance_List, \
    Employee_Tickets, Employee_Tickets_Chats, UserAccounts


def reaarange_date_for_html(input_date):
    day = input_date[:2]
    month = input_date[3:5]
    year = input_date[-4:]
    output_date = f'{year}-{month}-{day}'
    return output_date


class EZApi(Resource):
    # decorators = [limiter.limit("10/minute", error_message="Too much requests!")]
    def get(self):
        now = datetime.datetime.now()
        from .admin import search_query, or_
        category = request.args.get('category')
        search = request.args.get('search')

        if category == 'departments':
            department_id = request.args.get('id')
            results = Departments_JobPositions.query.filter(
                Departments_JobPositions.department_id == department_id
            ).all()
            return jsonify('', render_template('interactive_search.html',
                                               category='job_positions',
                                               job_positions=results))

        elif category == 'employee':
            filters = search_query(Employee_Profiles,
                                   search,
                                   search_columns=['id',
                                                   'email',
                                                   'name',
                                                   'date_of_birth',
                                                   'age',
                                                   'address',
                                                   'contact',
                                                   'date_recruited'])
            results = Employee_Profiles.query.filter(
                or_(
                    *filters
                )
            ).all()
            return jsonify('', render_template('interactive_search.html',
                                               category='supervisors',
                                               supervisors=results))
        elif category == 'receivers':
            exclude_search = request.args.get('exclude_search')
            if exclude_search:
                exclude_search = exclude_search.split('-')
            else:
                exclude_search = []
            search_value = '%' + search + '%'
            profile_results = Employee_Profiles.query.filter(
                or_(
                    Employee_Profiles.name.like(search_value),
                    Employee_Profiles.email.like(search_value)
                )
            ).all()
            department_results = Departments.query.filter(
                Departments.name.like(search_value)
            ).all()
            position_results = Departments_JobPositions.query.filter(
                Departments_JobPositions.name.like(search_value)
            ).all()
            results = []
            for i in profile_results:
                results.append(['e', i])
            for i in department_results:
                results.append(['d', i])
            for i in position_results:
                results.append(['p', i])
            return jsonify('', render_template('interactive_search.html',
                                               category='receivers',
                                               exclude_search=exclude_search,
                                               results=results))
        elif category == 'notifications':
            read = request.args.get('read')
            reading = Notifications.query.filter(
                Notifications.id == int(read)
            ).first()
            receiver_list = reading.receiver.split(', ')
            if len(receiver_list) != 1:
                multi = True
                receivers = []
                for i in receiver_list:
                    item = Employee_Profiles.query.filter(
                        Employee_Profiles.name == i
                    ).first()
                    receivers.append(item)
            else:
                multi = False
                receiver_id = Employee_Profiles.query.filter(
                    Employee_Profiles.name == reading.receiver
                ).first().id
                receivers = receiver_id
            record_log(f'{current_user.username} read details of Notification #{read}')
            return jsonify('', render_template('interactive_search.html',
                                               category='read_notification',
                                               data=reading,
                                               multi=multi,
                                               receivers=receivers))
        elif category == 'tasks':
            action = request.args.get('action')
            if action == 'read':
                read = request.args.get('read')
                reading = Employee_Tasks.query.filter(
                    Employee_Tasks.id == int(read)
                ).first()
                tasks = Employee_Tasks_Assignments.query.filter(
                    Employee_Tasks_Assignments.task_id == reading.id
                ).all()
                record_log(f'{current_user.username} read details of Task #{read}')
                return jsonify('', render_template('interactive_search.html',
                                                   category='read_task',
                                                   data=reading,
                                                   tasks=tasks,
                                                   user=current_user))
            elif action == 'handin':
                task_assignment_id = request.form.get('item_id')
                handing_in = Employee_Tasks_Assignments.query.filter(
                    Employee_Tasks_Assignments.task_id == task_assignment_id
                ).first()
                handing_in.date_time_ended = now.strftime('%Y-%m-%dT%H:%M')
                db.session.commit()

        elif category == 'payslips':
            read = request.args.get('read')
            data = Payroll_Payslips.query.filter(
                Payroll_Payslips.id == int(read)
            ).first()
            record_log(f'{current_user.username} read details of Payslip #{read}')
            return jsonify('', render_template('interactive_search.html',
                                               data=data,
                                               category='read_payslip'))

        elif category == 'tickets':
            read = request.args.get('read')
            ticket = Employee_Tickets.query.filter(
                Employee_Tickets.id == read
            ).first()
            chats = Employee_Tickets_Chats.query.filter(
                Employee_Tickets_Chats.ticket_id == ticket.id
            ).all()
            employee_id = UserAccounts.query.filter(
                UserAccounts.username == ticket.created_by
            ).first().employee_id
            employee = Employee_Profiles.query.filter(
                Employee_Profiles.id == employee_id
            ).first()
            record_log(f'{current_user.username} read details of Ticket #{read}')
            return jsonify('', render_template('interactive_search.html',
                                               ticket=ticket,
                                               chats=chats,
                                               employee=employee,
                                               category='read_ticket'))

        elif category == 'att_mach':
            auth_key = request.args.get('auth_key')
            check_auth = Attendance_Machines.query.filter(
                Attendance_Machines.auth_key == auth_key
            ).first()
            if check_auth:
                action = request.args.get('action')
                record_log(f'[Attendance Machine] \'{check_auth.name}\' authenticated')
                if action == 'update':
                    employee_profiles = Employee_Profiles.query.count()
                    return employee_profiles
                elif action == 'attendance':
                    id = request.args.get('id')
                    employee = Employee_Profiles.query.filter(
                        Employee_Profiles.id == id
                    ).first()
                    department = Departments.query.filter(
                        Departments.id == employee.department
                    ).first().name
                    position = Departments_JobPositions.query.filter(
                        Departments_JobPositions.id == employee.position
                    ).first().name
                    date = now.strftime('%d-%m-%Y')
                    time = now.strftime('%I:%M:%S %p')
                    day = now.strftime('%A')
                    check_attendance = Attendance_List.query.filter(
                        Attendance_List.date == date
                    ).first()
                    if not check_attendance:
                        new_attendance = Attendance_List(
                            employee_id=int(id),
                            date=date,
                            day=day,
                            checkin_time=time,
                            checkout_time='--:--:--',
                            status='Pending'
                        )
                        db.session.add(new_attendance)
                        db.session.commit()
                        record_log(f'[Attendance Machine] \'{check_auth.name}\' recorded a new attendance #{new_attendance.id}')
                    else:
                        check_attendance.checkout_time = time
                        db.session.commit()
                        record_log(f'[Attendance Machine] \'{check_auth.name}\' updated attendance record #{check_attendance.id}')
                    return jsonify(name=employee.name,
                                   department=department,
                                   position=position,
                                   date=date,
                                   time=time,
                                   day=day)
            else:
                record_log(f'[Attendance Machine] Failed to authenticate')
                return jsonify('Invalid Authentication Key')


        else:
            abort(404, message='Unknown URL')

    def post(self):
        print(request.form)
        ticket_id = request.form.get('ticket_id')
        msg = request.form.get('msg')
        new_msg = Employee_Tickets_Chats(
            ticket_id=ticket_id,
            message=msg,
            date=datetime.datetime.now().strftime('%d-%m-%Y'),
            time=datetime.datetime.now().strftime('%I:%M:%S %p')
        )
        db.session.add(new_msg)
        db.session.commit()
        return jsonify('success')
