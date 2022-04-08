function loadPositions(id){
	var url = "/ezapi?category=departments&id=" + id;
	$.ajax({
		url: url,
		type: "GET",
		dataType: "json",
		success: function(data){
			$(job_position).replaceWith(data)
		}
	});
}

function changeInputPlaceholder(value){
    document.getElementsByName("salary_amount").value="";
    if (value == "Full Time"){
        document.getElementById("salary_amount").placeholder="Monthly Wages";
    }
    else {
        document.getElementById("salary_amount").placeholder="Hourly Rate";
    }
}

function searchSupervisor(value) {
    if (value == ''){
        $(found_supervisor).hide();
    }
    else {
        $(found_supervisor).show();
        $.ajax({
            url: '/ezapi?category=employee&search=' + value,
            type: "GET",
            dataType: "json",
            success: function(data){
                $(found_supervisor).replaceWith(data);
            }
        });
    }
}

function searchReceivers(value) {
    if (value == ''){
        $(receivers).hide()
    }
    else {
        for (let i = 0; i < search_count; i++){
            var button_id = 'search_item_' + i;
            exclude_array.push($('#' + button_id).val());
        }
        var exclude_string = total_receivers_array.join('-');
        $(receivers).show()
        $.ajax({
            url: '/ezapi?category=receivers&search=' + value + '&exclude_search=' + exclude_string,
            type: 'GET',
            dataType: "json",
            success: function(data){
                $(receivers).replaceWith(data);
            }
        });
    }
}

function addReceivers(value, category){
    var button_id = 'search_item_' + search_count
    var item = '<button type="button" class="btn btn-info" value="' + value + '" onclick="remove(' + "'" + button_id + "', '"  + value + "'" + ')" id="' + button_id + '" style="margin:2px;">' + value + '  ❌</button>';
    $(appended_receivers).append(item);
    $(search_receiver).val('');
    $(receivers).hide();
    total_receivers_category_array.push(category);
    total_receivers_array.push(value);
    $(total_receivers).val(total_receivers_array.join(', '));
    $(total_receivers_category).val(total_receivers_category_array.join(', '));
    console.log($(total_receivers).val());
    console.log($(total_receivers_category).val());
    search_count += 1;
}

function remove(button_id, value){
    $('#' + button_id).remove();
    for (let i = 0; i < total_receivers_array.length; i ++){
        if (total_receivers_array[i] == value){
            for (let j = i; j < total_receivers_array.length; j++){
                total_receivers_array[j] = total_receivers_array[j+1];
            }
            for (let j = i; j < total_receivers_category_array.length; j++){
                total_receivers_category_array[j] = total_receivers_category_array[j+1];
            }
            break;
        }
    }
    total_receivers_array.pop();
    total_receivers_category_array.pop();
    $(total_receivers).val(total_receivers_array.join(', '));
    $(total_receivers_category).val(total_receivers_category_array.join(', '));
    console.log($(total_receivers).val());
    console.log($(total_receivers_category).val());
}

function readNotification(id){
	$.ajax({
		url: "/ezapi?category=notifications&read=" + id,
		type: "GET",
		dataType: "json",
		success: function(data){
			$(notification_content).replaceWith(data);
		}
	});
}

function redirectProfile(id){
    $('#view_notification_modal').modal('hide');
    $('.modal-backdrop').remove()
    return viewEmployeeProfile(id)
}

function readTask(id){
	$.ajax({
		url: "/ezapi?category=tasks&read=" + id,
		type: "GET",
		dataType: "json",
		success: function(data){
			$(task_content).replaceWith(data);
		}
	});
}

function editFormulaVariable(id){
    $('#variable_value_' + id).attr('readonly', false);
    $('#variable_button_' + id).replaceWith('<button class="btn btn-success" type="submit">Save</button>')
}

function calculateSalary(){
    let base_salary = Number($('#salary_calculator_salary').val());
    let epf = Number($('#variable_value_1').val());
    let socso = Number($('#variable_value_2').val());
    let allowance = Number($('#salary_calculator_allowance').val());
    let bonus = Number($('#salary_calculator_bonus').val());
    let salary = base_salary - (base_salary * (epf + socso)) + allowance + bonus;
    $('#salary_calculator_result').val(salary);
}

function readPayslip(id){
	$.ajax({
		url: "/ezapi?category=payslips&read=" + id,
		type: "GET",
		dataType: "json",
		success: function(data){
			$(payslip_content).replaceWith(data);
		}
	});
}

function searchAttendance(){
    url = '/admin_panel/attendance_list?search=' + $('#search_value').val();
    window.location.href = url;
}

function searchEmployee(){
    url = '/admin_panel/employee_profiles?search=' + $('#search_value').val();
    window.location.href = url;
}

function searchTickets(){
    url = '/admin_panel/employee_tickets?search=' + $('#search_value').val();
    window.location.href = url;
}

function searchNotification(){
    url = '/admin_panel/notification_center?search=' + $('#search_value').val();
    window.location.href = url;
}

function searchTask(){
    url = '/admin_panel/task_assignment?search=' + $('#search_value').val();
    window.location.href = url;
}

function viewEmployeeProfile(id, action){
    url = '/admin_panel/employee_profiles?id=' + id + '&action=' + action;
    window.location.href = url;
}