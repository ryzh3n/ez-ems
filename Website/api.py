from flask_restful import Resource, abort, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import jsonify, render_template

from .models import Departments_JobPositions, Departments, Employee_Profiles, Notifications, Employee_Tasks, \
                    Employee_Tasks_Assignments, Payroll_Payslips


def reaarange_date_for_html(input_date):
    day = input_date[:2]
    month = input_date[3:5]
    year = input_date[-4:]
    output_date = f'{year}-{month}-{day}'
    return output_date


class EZApi(Resource):
    # decorators = [limiter.limit("10/minute", error_message="Too much requests!")]
    def get(self):
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
            return jsonify('', render_template('interactive_search.html',
                                               category='read_notification',
                                               data=reading,
                                               multi=multi,
                                               receivers=receivers))
        elif category == 'tasks':
            read = request.args.get('read')
            reading = Employee_Tasks.query.filter(
                Employee_Tasks.id == int(read)
            ).first()
            tasks = Employee_Tasks_Assignments.query.filter(
                Employee_Tasks_Assignments.task_id == reading.id
            ).all()
            return jsonify('', render_template('interactive_search.html',
                                               category='read_task',
                                               data=reading,
                                               tasks=tasks))

        elif category == 'payslips':
            read = request.args.get('read')
            data = Payroll_Payslips.query.filter(
                Payroll_Payslips.id == int(read)
            ).first()
            return jsonify('', render_template('interactive_search.html',
                                               data=data,
                                               category='read_payslip'))

        else:
            abort(404, message='Unknown URL')

