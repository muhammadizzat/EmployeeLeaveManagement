import csv
import datetime
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404, HttpResponseRedirect
from django.core.exceptions import ObjectDoesNotExist
from .form import (EmployeeDetailsForm, EmployeeContactDetailsForm, EmergencyContactForm, LeavesDetailForm,
                   DependentForm, JobForm, EducationForm,
                   WorkExperienceForm, SkillSetForm, LanguageProficiencyForm, SurveyForm
                   )
from scheduler.models import ProjectCrew
from dashboard.models import Project
from .models import Employee, LeavesType, Leave, LeavesEntitlement, Skill, Language, Survey, Department, Designation
from django.http import HttpResponse

from django.views.decorators.clickjacking import xframe_options_exempt
from django.db.models import F


def employee_leaves(request):
    """
   My Leaves view
    :param request:
    :return:
    """
    selected_user = get_object_or_404(Employee, id=request.user.id)
    print(request.user.id)
    print(selected_user)
    all_users = Employee.objects.all().exclude(employment_status=6).select_related(
        'designation').order_by("official_name").values('id', text=F('official_name'))
    all_users = list(all_users)
    lead_assigned = 'false'
    # GET ALL EMPLOYEE LEAD
    employee_report_to = Employee.objects.filter(id=request.user.id).values_list(
        'direct_reporting__id', 'indirect_reporting__id')
    employee_lead_list = list(
        data[0] for data in employee_report_to) + list(data[1] for data in employee_report_to)
    employee_lead_list = list(set(employee_lead_list))
    employee_lead_list = [x for x in employee_lead_list if x is not None]
    print(employee_lead_list)
    if len(employee_lead_list) != 0:
        lead_assigned = 'true'
    # GET ALL EMPLOYEE UNDERLINGS
    direct_report_by = Employee.objects.filter(
        direct_reporting=request.user.id).values_list('id')
    indirect_report_by = Employee.objects.filter(
        indirect_reporting=request.user.id).values_list('id')
    report_by_list = list(direct_report_by) + list(indirect_report_by)
    report_by_list = [e[0] for e in report_by_list]
    lead_users = Employee.objects.filter(id__in=report_by_list).exclude(employment_status=6).select_related(
        'designation').order_by("official_name").values('id', text=F('official_name'))
    lead_users = list(lead_users)
    all_leave_type = LeavesType.objects.all().order_by("order")
    context = {'selected_user': selected_user,
               'lead_assigned': lead_assigned,
               'lead_users': lead_users,
               'all_users': all_users,
               'all_leave_type': all_leave_type,
               }
    return render(request, 'elm/templates/leaves.html', context=context)


def employee_entitlement(request, selected_view,):
    """
    Entitlement view
    :param request:
    :return:
    """
    all_leave_type = LeavesType.objects.all().order_by("order")
    selected_user = get_object_or_404(Employee, id=request.user.id)
    context = {'selected_user': selected_user,
               'selected_view': selected_view,
               'all_leave_type': all_leave_type,
               }
    return render(request, 'elm/templates/entitlement.html', context=context)


def employee_leaves_update(request, leave_id):
    """
    Leaves Update view
    :param request:
    :return:
    """
    selected_user = get_object_or_404(Employee, id=request.user.id)
    leave_data = Leave.objects.values_list('id', 'employee__id', 'employee__official_name', 'leave_type', 'leave_type__leave_type',
                                           'status', 'start_date', 'end_date', 'duration', 'working_hour_duration', 'comment').filter(id=leave_id)
    is_lead = 'false'
    is_hr = 'false'
    for data in leave_data:
        employee_id = data[1]
    employee_report_to = Employee.objects.filter(id=employee_id).values_list(
        'direct_reporting__id', 'indirect_reporting__id')
    leave_manager_list = User.objects.filter(
        groups__name__in=['Leaves Manager']).values_list('id')
    employee_lead_list = list(
        data[0] for data in employee_report_to) + list(data[1] for data in employee_report_to)
    employee_lead_list = list(set(employee_lead_list))
    project_manager_list = ProjectCrew.objects.filter(employee=employee_id).exclude(
        project__project_stage__in=['completed', 'archived']).values_list('project__project_manager__id').distinct()
    project_manager_list = list(data[0] for data in project_manager_list)
    employee_lead_list = list(set(project_manager_list + employee_lead_list))
    employee_lead_list = [x for x in employee_lead_list if x is not None]
    elm_list = list(data[0] for data in leave_manager_list)
    #  ALLOW LEAD TO EDIT BUT PREVENT LOGIN LEAD TO EDIT THEIR OWN LEAVE
    if selected_user.id in employee_lead_list and selected_user.id != employee_id:
        is_lead = 'true'

    if elm_list:
        is_hr = 'true'

    context = {'selected_user': selected_user,
               'leave_id': leave_id,
               'leave_data': leave_data,
               'is_lead': is_lead,
               'is_hr': is_hr,
               }
    return render(request, 'elm/templates/leaves_detail_update.html', context=context)
