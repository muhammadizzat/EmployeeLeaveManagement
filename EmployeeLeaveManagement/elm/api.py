
import datetime
from django.core.mail import EmailMultiAlternatives
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404
from django.contrib.auth.models import User
from scheduler.models import ProjectCrew
from dashboard.models import Project
from .models import Employee, EmergencyContact, Department, EmploymentCategory, EmploymentLocation, EmploymentGrade, \
    Dependent, \
    WorkExperience, Education, SkillSet, LanguageProficiency, Leave, LeavesEntitlement, LeavesType
from .serializers import EmployeeDetailSerializer, EmployeeDetailEditSerializer, EmployeeEmergencyContactSerializer, \
    EmployeeDependentSerializer, EmployeeWorkExperienceSerializer, EmployeeEducationSerializer, EmployeeSkillSerializer, \
    EmployeeSkillWriteSerializer, EmployeeProficiencySerializer, EmployeeProficiencyWriteSerializer, \
    EmployeeCreateSerializer, EmployeeDetailSerializer_Simple, EmployeeLeaveSerializer, EmployeeLeaveWriteSerializer, \
    EmployeeEntitlementSerializer, EmployeeLeadWriteSerializers
from userprofile.models import Profile
from common import networkOperations
from common.notifications import send_email
from common import utils


# EMPLOYEE DISPLAY LEAVE API
class EmployeeLeavesAPI(APIView):
    def get(self, request, employee_id, selected_year, format=None):
        employee_leaves = Leave.objects.all().filter(employee=employee_id,
                                                     start_date__year=selected_year).select_related('employee',
                                                                                                    'leave_type',
                                                                                                    'approved_by',
                                                                                                    'cancel_by', )
        employee_leaves_data = {'entitlement': {}, 'leaves': []}
        serializer = EmployeeLeaveSerializer(employee_leaves, many=True)
        applied_leaves_list = serializer.data
        leave_type_list = LeavesType.objects.values()

        # POPULATING EMPLOYEE LEAVES ENTITLEMENT AND AVAILABILITY
        for leave_type in leave_type_list:
            total_entitled_days = 0
            total_leave_applied = 0
            total_available_leave_list = []
            total_available_leave = 0

            # CHECK IF EMPLOYEE IS ENTITLE FOR EACH LEAVE TYPE
            for leave in employee_leaves:
                # GET ALL DURATION OF APPLIED LEAVES FOR EACH LEAVES TYPE BUT IGNORE REJECTED & CANCELLED LEAVE
                if leave_type['leave_type'] == leave.leave_type.leave_type and leave.status != 'rejected' and leave.status != 'cancelled':
                    total_available_leave_list.append(leave.duration)
            total_leave_applied = sum(total_available_leave_list)

            # GET EMPLOYEE BASIC ENTITLEMENT DATA FILTERED BY LEAVES TYPE AND SELECTED YEAR
            employee_entitlement = LeavesEntitlement.objects.filter(employee=employee_id, leave_type=leave_type['id'],
                                                                    year=selected_year).values()
            # GET TOTAL ENTITLEMENT DAYS
            for entitlement in employee_entitlement:
                total_entitled_days = entitlement['days']

            # SET TOTAL AVAILABLE EXCEPTION FOR ABSENT & UNPAID
            if leave_type['leave_type'] == 'Absent' or leave_type['leave_type'] == 'Unpaid':
                total_available_leave = 0
            # CALCULATE TOTAL AVAILABLE LEAVE
            else:
                total_available_leave = total_entitled_days - total_leave_applied

            employee_leave_status = {
                'id': leave_type['id'],
                'total_entitled_day': total_entitled_days,
                'total_leave_applied': total_leave_applied,
                'total_available_leave': total_available_leave,
            }
            # APPEND EMPLOYEE ENTITLEMENT DATA IN API
            employee_leaves_data['entitlement'][leave_type['leave_type']
                                                ] = employee_leave_status

        # APPEND APPLIED LEAVES DATA IN API
        employee_leaves_data['leaves'] = applied_leaves_list
        return Response(employee_leaves_data)

    # EMPLOYEE CREATE LEAVE
    def post(self, request, employee_id, selected_year, format=None):
        # leave_manager_email = User.objects.filter(groups__name__in=['Leaves Manager']).values_list('email')
        serializer = EmployeeLeaveWriteSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            inst = request.data
            leave_data = Leave.objects.latest('id')
            # CAPITALIZE THE NAME WITH .title()
            employee_name = leave_data.employee.official_name.title()
            employee_email = leave_data.employee.work_email
            logged_in_user = request.user.profile.employee.official_name.title()
            leave_date_modified = leave_data.modified_date
            leave_date_modified = leave_date_modified.replace(microsecond=0)
            leave_status = leave_data.status.replace('_', " ").title()
            working_hour = leave_data.working_hour_duration.replace(
                '_', " ").title()

            try:
                report_to_email = Employee.objects.filter(id=employee_id).values_list(
                    'direct_reporting__official_name', 'indirect_reporting__official_name',
                    'direct_reporting__work_email', 'indirect_reporting__work_email')
                report_to_name_list = list(data[0] for data in report_to_email) + list(
                    data[1] for data in report_to_email)
                report_to_email_list = list(data[2] for data in report_to_email) + list(
                    data[3] for data in report_to_email)
                report_to_email_list = [
                    x for x in report_to_email_list if x is not None]
            except:
                report_to_email = []
            report_to_name_list = list(set(report_to_name_list))
            report_to_name_list = [
                x for x in report_to_name_list if x is not None]
            # report_to_email_list = report_to_email_list + list(data[0] for data in leave_manager_email)
            report_to_email_list = list(set(report_to_email_list))
            report_to_email_list.append(employee_email)
            employee_project_lead = ProjectCrew.objects.filter(employee=employee_id).values_list(
                'project__project_manager__official_name', 'project__project_manager__work_email').distinct()
            for x in employee_project_lead:
                if x[0] is not None:
                    report_to_name_list.append(x[0])
                    report_to_email_list.append(x[1])
            # ------------------------------------------------ EMAIL NOTIFICATION SETTINGS START---------------------------------------------------------------------------#
            subject = 'Leave Notification #{} : [{}] {}'.format(
                leave_data.id, leave_status, employee_name)
            text_content = 'Leave Notification #{} : [{}] {}'.format(
                leave_data.id, leave_status, employee_name)
            html_content = """
                    <table border="1" cellpadding="0" cellspacing="0" width="600" style="border-collapse: collapse;">
                            <thead></thead>
                            <tbody>
                                <tr>
                                    <th style=" text-align: left; padding: 5px 10px; width: 110px;" bgcolor="#d8d8d8">Type</td>
                                    <td style="padding: 5px 10px;">{}</td>
                                </tr>

                                <tr>
                                    <th style="text-align: left; padding: 5px 10px; width: 110px;" bgcolor="#d8d8d8">Reason</td>
                                    <td style="padding: 5px 10px;">{}</td>
                                </tr>
                                <tr>
                                    <th style="text-align: left; padding: 5px 10px; width: 110px;" bgcolor="#d8d8d8">Duration</td>
                                    <td style="padding: 5px 10px;">{} ({})</td>
                                </tr>
                                <tr>
                                    <th style="text-align: left; padding: 5px 10px; width: 110px;" bgcolor="#d8d8d8">Start Date</td>
                                    <td style="padding: 5px 10px;">{}</td>
                                </tr>
                                <tr>
                                    <th style="text-align: left; padding: 5px 10px; width: 110px;" bgcolor="#d8d8d8">End Date</td>
                                    <td style="padding: 5px 10px;">{}</td>
                                </tr>
                                <tr>
                                    <th style="text-align: left; padding: 5px 10px; width: 110px;" bgcolor="#d8d8d8">Status</td>
                                    <td style="padding: 5px 10px;">{}</td>
                                </tr>
                                <tr>
                                    <th style="text-align: left; padding: 5px 10px; width: 110px;" bgcolor="#d8d8d8">Applied By</td>
                                    <td style="padding: 5px 10px;">{}</td>
                                </tr>
                                <tr>
                                    <th style="text-align: left; padding: 5px 10px; width: 110px;" bgcolor="#d8d8d8">Applied Date</td>
                                    <td style="padding: 5px 10px;">{}</td>
                                </tr>
                                <tr>
                                    <th style="text-align: left; padding: 5px 10px; width: 110px;" bgcolor="#d8d8d8">Approved by</td>
                                    <td style="padding: 5px 10px;"></td>
                                </tr>
                                <tr>
                                    <th style="text-align: left; padding: 5px 10px; width: 110px;" bgcolor="#d8d8d8">Link</td>
                                    <td style="padding: 5px 10px;"><a href="http://lemoncore/hrm/employee/leaves_update/{}" target="_blank">Update Leave</a></td>
                                </tr>
                        """.format(leave_data.leave_type.leave_type,
                                   leave_data.comment,
                                   leave_data.duration,
                                   working_hour,
                                   leave_data.start_date,
                                   leave_data.end_date,
                                   leave_status,
                                   logged_in_user,
                                   leave_date_modified,
                                   leave_data.id)
            # ADD LEAD LIST
            html_content = html_content + """<tr>
                                                <th style="text-align: left; padding: 5px 10px; width: 110px; vertical-align : top; "bgcolor="#d8d8d8">Lead list</td>
                                                <td style="padding: 5px 10px;" colspan="2"> <ul style="padding-left : 17px">
                                            """
            for x in report_to_name_list:
                html_content = html_content + '<li>{}</li>'.format(x)
            html_content = html_content + """
                                                            </ul>
                                                        </tr>
                                                    </tbody>
                                                </table>
                                            """
            to = report_to_email_list
            # send_email(subject, text_content, html_content, to)
            # ------------------------------------------------ EMAIL NOTIFICATION SETTINGS END ---------------------------------------------------------------------------#
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LeadViewLeavesAPI(APIView):
    def get(self, request, employee_id, selected_year, format=None):
        direct_report_by = Employee.objects.filter(
            direct_reporting=employee_id).values_list('id')
        indirect_report_by = Employee.objects.filter(
            indirect_reporting=employee_id).values_list('id')
        report_by_list = list(direct_report_by) + list(indirect_report_by)
        report_by_list = [e[0] for e in report_by_list]
        lead_project = Project.objects.filter(project_manager=employee_id).exclude(
            project_stage__in=['completed', 'archived']).values_list('id')
        lead_project = [e[0] for e in lead_project]
        project_employee_list = ProjectCrew.objects.filter(
            project__in=lead_project).values_list('employee').distinct()
        project_employee_list = [e[0] for e in project_employee_list]
        report_by_list = report_by_list + project_employee_list
        report_by_list = list(set(report_by_list))
        employee_leaves = Leave.objects.filter(employee__in=report_by_list,
                                               start_date__year=selected_year).select_related('employee', 'leave_type',
                                                                                              'approved_by',
                                                                                              'cancel_by', )
        employee_leaves_data = {'leaves': []}
        serializer = EmployeeLeaveSerializer(employee_leaves, many=True)
        applied_leaves_list = serializer.data

        # APPEND APPLIED LEAVES DATA IN API
        employee_leaves_data['leaves'] = applied_leaves_list
        return Response(employee_leaves_data)


class HRMViewLeavesAPI(APIView):
    def get(self, request, employee_id, selected_year, format=None):
        employee_leaves = Leave.objects.all().filter(start_date__year=selected_year).exclude(
            employee__employment_status=6).select_related('employee', 'leave_type', 'approved_by', 'cancel_by', )
        employee_leaves_data = {'leaves': []}
        serializer = EmployeeLeaveSerializer(employee_leaves, many=True)
        applied_leaves_list = serializer.data

        # APPEND APPLIED LEAVES DATA IN API
        employee_leaves_data['leaves'] = applied_leaves_list
        return Response(employee_leaves_data)


# EMPLOYEE CHECK FOR AVAILABLE DAYS
class EmployeeLeavesFilterDateAPI(APIView):
    def post(self, request, employee_id):
        apply_status = request.data.get('apply_status', [])
        leave_id = request.data.get('leave_id', [])
        applied_start_date = request.data.get('start_date', [])
        applied_end_date = request.data.get('end_date', [])
        model_object = Leave.objects.filter(employee=employee_id).exclude(status__in=['rejected', 'cancelled']).select_related('employee',
                                                                                                                               'leave_type',
                                                                                                                               'approved_by',
                                                                                                                               'cancel_by')
        if apply_status == 'POST':
            model_object = model_object.exclude(end_date__lt=applied_start_date).exclude(
                start_date__gt=applied_end_date)
        # IGNORE SELECTED LEAVE FOR EDITING
        elif apply_status == 'PUT':
            model_object = model_object.exclude(end_date__lt=applied_start_date).exclude(
                start_date__gt=applied_end_date).exclude(id=leave_id)
        serializer = EmployeeLeaveSerializer(model_object, many=True)
        return Response(serializer.data)


# EMPLOYEE EDIT/DELETE LEAVE
class EmployeeSelectedLeavesAPI(APIView):
    def get_object(self, leave_id):
        try:
            return Leave.objects.get(pk=leave_id)
        except Leave.DoesNotExist:
            raise Http404

    def get(self, request, leave_id, format=None, **kwargs):
        model_object = self.get_object(leave_id)
        serializer = EmployeeLeaveWriteSerializer(model_object)
        return Response(serializer.data)

    def put(self, request, leave_id):
        model_object = self.get_object(leave_id)
        serializer = EmployeeLeaveWriteSerializer(
            model_object, data=request.data)
        # leave_manager_email = User.objects.filter(groups__name__in=['Leaves Manager']).values_list('email')
        if serializer.is_valid():
            employee_id = model_object.employee.id
            # CAPITALIZE THE NAME WITH .title()
            employee_name = model_object.employee.official_name.title()
            employee_email = model_object.employee.work_email
            logged_in_user = request.user.profile.employee.official_name.title()

            # PREVIOUS DATA
            previous_leave_status = model_object.status.replace(
                '_', " ").title()
            previous_working_hour = model_object.working_hour_duration.replace(
                '_', " ").title()
            previous_leave_type = model_object.leave_type.leave_type
            previous_comment = model_object.comment
            previous_duration = model_object.duration
            previous_start_date = model_object.start_date
            previous_end_date = model_object.end_date

            # UPDATED DATA
            updated_leave_status = request.data.get('status', [])
            updated_leave_status = updated_leave_status.replace(
                '_', " ").title()
            updated_working_hour = request.data.get(
                'working_hour_duration', [])
            updated_working_hour = updated_working_hour.replace(
                '_', " ").title()
            updated_leave_type = request.data.get('leave_type_name', [])
            updated_comment = request.data.get('comment', [])
            updated_duration = request.data.get('duration', [])
            updated_start_date = request.data.get('start_date', [])
            updated_end_date = request.data.get('end_date', [])
            try:
                updated_lead_comment = request.data.get('lead_comment', [])
            except:
                updated_lead_comment = ''
            leave_date_modified = request.data.get('modified_date', [])
            leave_date_modified = datetime.datetime.today().replace(microsecond=0)

            try:
                report_to_email = Employee.objects.filter(id=employee_id).values_list(
                    'direct_reporting__official_name', 'indirect_reporting__official_name',
                    'direct_reporting__work_email', 'indirect_reporting__work_email')
                report_to_name_list = list(data[0] for data in report_to_email) + list(
                    data[1] for data in report_to_email)
                report_to_email_list = list(data[2] for data in report_to_email) + list(
                    data[3] for data in report_to_email)
                report_to_email_list = [
                    x for x in report_to_email_list if x is not None]
            except:
                report_to_email = []
            report_to_name_list = list(set(report_to_name_list))
            report_to_name_list = [
                x for x in report_to_name_list if x is not None]
            # report_to_email_list = report_to_email_list + list(data[0] for data in leave_manager_email)
            report_to_email_list = list(set(report_to_email_list))
            report_to_email_list.append(employee_email)
            employee_project_lead = ProjectCrew.objects.filter(employee=employee_id).values_list(
                'project__project_manager__official_name', 'project__project_manager__work_email').distinct()
            for x in employee_project_lead:
                if x[0] is not None:
                    report_to_name_list.append(x[0])
                    report_to_email_list.append(x[1])
            # ------------------------------------------------ EMAIL NOTIFICATION SETTINGS START---------------------------------------------------------------------------#
            subject = 'Leave Notification #{} : [{}] {}'.format(
                model_object.id, updated_leave_status, employee_name)
            text_content = 'Leave Notification #{} : [{}] {}'.format(model_object.id, updated_leave_status,
                                                                     employee_name)
            html_content = """
                    <table border="1" cellpadding="0" cellspacing="0" width="600" style="border-collapse: collapse;">
                            <thead>
                                <th></th>
                                <th>Updated</th>
                                <th>Previous</th>
                            </thead>
                            <tbody>
                                <tr>
                                    <th style="text-align: left; padding: 5px 10px; width: 110px;" bgcolor="#d8d8d8">Type</td>
                                    <td style="padding: 5px 10px;" bgcolor="#ccffcc">{}</td>
                                    <td style="padding: 5px 10px;" bgcolor="#ff9999">{}</td>
                                </tr>

                                <tr>
                                    <th style="text-align: left; padding: 5px 10px; width: 110px;" bgcolor="#d8d8d8">Reason</td>
                                    <td style="padding: 5px 10px;" bgcolor="#ccffcc">{}</td>
                                    <td style="padding: 5px 10px;" bgcolor="#ff9999">{}</td>
                                </tr>
                                <tr>
                                    <th style="text-align: left; padding: 5px 10px; width: 110px;" bgcolor="#d8d8d8">Duration</td>
                                    <td style="padding: 5px 10px;" bgcolor="#ccffcc">{} ({})</td>
                                    <td style="padding: 5px 10px;" bgcolor="#ff9999">{} ({})</td>
                                </tr>
                                <tr>
                                    <th style="text-align: left; padding: 5px 10px; width: 110px;" bgcolor="#d8d8d8">Start Date</td>
                                    <td style="padding: 5px 10px;" bgcolor="#ccffcc">{}</td>
                                    <td style="padding: 5px 10px;" bgcolor="#ff9999">{}</td>
                                </tr>
                                <tr>
                                    <th style="text-align: left; padding: 5px 10px; width: 110px;" bgcolor="#d8d8d8">End Date</td>
                                    <td style="padding: 5px 10px;" bgcolor="#ccffcc">{}</td>
                                    <td style="padding: 5px 10px;" bgcolor="#ff9999">{}</td>
                                </tr>
                                <tr>
                                    <th style="text-align: left; padding: 5px 10px; width: 110px;" bgcolor="#d8d8d8">Status</td>
                                    <td style="padding: 5px 10px;" bgcolor="#ccffcc">{}</td>
                                    <td style="padding: 5px 10px;" bgcolor="#ff9999">{}</td>
                                </tr>
                                <tr>
                                    <th style="text-align: left; padding: 5px 10px; width: 110px;" bgcolor="#d8d8d8">Updated By</td>
                                    <td style="padding: 5px 10px;" colspan="2">{}</td>
                                </tr>
                                <tr>
                                    <th style="text-align: left; padding: 5px 10px; width: 110px;" bgcolor="#d8d8d8">Updated Date</td>
                                    <td style="padding: 5px 10px;" colspan="2">{}</td>
                                </tr>

                        """.format(
                updated_leave_type,
                previous_leave_type,
                updated_comment,
                previous_comment,
                updated_duration,
                updated_working_hour,
                previous_duration,
                previous_working_hour,
                updated_start_date,
                previous_start_date,
                updated_end_date,
                previous_end_date,
                updated_leave_status,
                previous_leave_status,
                logged_in_user,
                leave_date_modified)
            if updated_leave_status == 'Pending Approval':
                html_content = html_content + """
                                <tr>
                                    <th style="text-align: left; padding: 5px 10px; width: 110px;" bgcolor="#d8d8d8">Link</td>
                                    <td style="padding: 5px 10px;" colspan="2"><a href="http://lemoncore/hrm/employee/leaves_update/{}" target="_blank">Update Leave</a></td>
                                </tr>
                """.format(leave_id)
            if updated_leave_status != 'Pending Approval':
                html_content = html_content + """
                                <tr>
                                    <th style="text-align: left; padding: 5px 10px; width: 110px;" bgcolor="#d8d8d8">Reason for Approval/Reject</td>
                                    <td style="padding: 5px 10px;" colspan="2">{}</td>
                                </tr>
                """.format(updated_lead_comment)
            # ADD LEAD LIST
            html_content = html_content + """<tr>
                                                <th style="text-align: left; padding: 5px 10px; width: 110px; vertical-align : top; "bgcolor="#d8d8d8">Lead list</td>
                                                <td style="padding: 5px 10px;" colspan="2"> <ul style="padding-left : 17px">
                                            """
            for x in report_to_name_list:
                html_content = html_content + '<li>{}</li>'.format(x)
            html_content = html_content + """
                                                            </ul>
                                                        </tr>
                                                    </tbody>
                                                </table>
                                            """
            to = report_to_email_list
            # send_email(subject, text_content, html_content, to)
            # ------------------------------------------------ EMAIL NOTIFICATION SETTINGS END ---------------------------------------------------------------------------#
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, leave_id):
        model_object = self.get_object(leave_id)
        employee_id = model_object.employee.id
        employee_lead = model_object.employee.direct_reporting
        if employee_lead != None:
            # CAPITALIZE THE NAME WITH .title()
            employee_name = model_object.employee.official_name.title()
            employee_name = employee_name
            employee_email = model_object.employee.work_email
            logged_in_user = request.user.profile.employee.official_name
            logged_in_user = logged_in_user.title()
            leave_date_modified = model_object.modified_date
            leave_date_modified = leave_date_modified.replace(microsecond=0)
            leave_status = model_object.status.replace('_', " ").title()
            working_hour = model_object.working_hour_duration.replace(
                '_', " ").title()
            try:
                report_to_email = Employee.objects.filter(id=employee_id).values_list(
                    'direct_reporting__official_name', 'indirect_reporting__official_name', 'direct_reporting__work_email',
                    'indirect_reporting__work_email')
                report_to_name_list = list(data[0].title() for data in report_to_email) + list(
                    data[1].title() for data in report_to_email)
                report_to_email_list = list(
                    data[2] for data in report_to_email) + list(data[3] for data in report_to_email)
            except:
                report_to_email = Employee.objects.filter(id=employee_id).values_list(
                    'direct_reporting__official_name', 'direct_reporting__work_email', )
                report_to_name_list = list(
                    data[0].title() for data in report_to_email)
                report_to_email_list = list(data[1]
                                            for data in report_to_email)
            else:
                report_to_email = []

            report_to_name_list = list(set(report_to_name_list))
            report_to_email_list = list(set(report_to_email_list))
            report_to_email_list.append(employee_email)
            employee_project_lead = ProjectCrew.objects.filter(employee=employee_id).values_list(
                'project__project_manager__official_name', 'project__project_manager__work_email').distinct()
            for x in employee_project_lead:
                if x[0] is not None:
                    report_to_name_list.append(x[0])
                    report_to_email_list.append(x[1])
            # ------------------------------------------------ EMAIL NOTIFICATION SETTINGS START---------------------------------------------------------------------------#
            subject = 'Leave Notification #{} : [DELETED] {}'.format(
                model_object.id, employee_name)
            text_content = 'Leave Notification #{} : [DELETED] {}'.format(
                model_object.id, employee_name)
            html_content = """
                    <table border="1" cellpadding="0" cellspacing="0" width="600" style="border-collapse: collapse;">
                            <thead></thead>
                            <tbody>
                                <tr>
                                    <th style="text-align: left; padding: 5px 10px; width: 110px;" bgcolor="#d8d8d8">Type</td>
                                    <td style="padding: 5px 10px;">{}</td>
                                </tr>

                                <tr>
                                    <th style="text-align: left; padding: 5px 10px; width: 110px;" bgcolor="#d8d8d8">Reason</td>
                                    <td style="padding: 5px 10px;">{}</td>
                                </tr>
                                <tr>
                                    <th style="text-align: left; padding: 5px 10px; width: 110px;" bgcolor="#d8d8d8">Duration</td>
                                    <td style="padding: 5px 10px;">{} ({})</td>
                                </tr>
                                <tr>
                                    <th style="text-align: left; padding: 5px 10px; width: 110px;" bgcolor="#d8d8d8">Start Date</td>
                                    <td style="padding: 5px 10px;">{}</td>
                                </tr>
                                <tr>
                                    <th style="text-align: left; padding: 5px 10px; width: 110px;" bgcolor="#d8d8d8">End Date</td>
                                    <td style="padding: 5px 10px;">{}</td>
                                </tr>
                                <tr>
                                    <th style="text-align: left; padding: 5px 10px; width: 110px;" bgcolor="#d8d8d8">Status</td>
                                    <td style="padding: 5px 10px;">Deleted</td>
                                </tr>
                                <tr>
                                    <th style="text-align: left; padding: 5px 10px; width: 110px;" bgcolor="#d8d8d8">Deleted By</td>
                                    <td style="padding: 5px 10px;">{}</td>
                                </tr>
                                <tr>
                                    <th style="text-align: left; padding: 5px 10px; width: 110px;" bgcolor="#d8d8d8">Deleted Date</td>
                                    <td style="padding: 5px 10px;">{}</td>
                                </tr>
                        """.format(model_object.leave_type.leave_type,
                                   model_object.comment,
                                   model_object.duration,
                                   working_hour,
                                   model_object.start_date,
                                   model_object.end_date,
                                   logged_in_user,
                                   leave_date_modified)

            # ADD LEAD LIST
            html_content = html_content + """<tr>
                                                <th style="text-align: left; padding: 5px 10px; width: 110px; vertical-align : top; "bgcolor="#d8d8d8">Lead list</td>
                                                <td style="padding: 5px 10px;" colspan="2"> <ul style="padding-left : 17px">
                                            """
            for x in report_to_name_list:
                html_content = html_content + '<li>{}</li>'.format(x)
            html_content = html_content + """
                                                            </ul>
                                                        </tr>
                                                    </tbody>
                                                </table>
                                            """
            to = report_to_email_list
            # send_email(subject, text_content, html_content, to)
            # ------------------------------------------------ EMAIL NOTIFICATION SETTINGS END ---------------------------------------------------------------------------#
        model_object.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# EMPLOYEE LATEST LEAVES
class EmployeeLatestLeavesAPI(APIView):
    def get(self, request, format=None, **kwargs):
        leave_data = Leave.objects.latest('id')
        model_object = Leave.objects.get(pk=leave_data.id)
        serializer = EmployeeLeaveSerializer(model_object)
        return Response(serializer.data)


# EMPLOYEE ENTITLEMENT
class EmployeeEntitlementAPI(APIView):
    def get(self, request, selected_view, employee_id, selected_year, format=None):
        entitlement_list = []
        if selected_view == 'employee':
            employee_list = Employee.objects.filter(id=employee_id).exclude(employment_status=6).values_list('id',
                                                                                                             'employee_id',
                                                                                                             'official_name',
                                                                                                             'department__department',
                                                                                                             'gender')
        elif selected_view == 'lead':
            direct_report_by = Employee.objects.filter(
                direct_reporting=employee_id).values_list('id')
            indirect_report_by = Employee.objects.filter(
                indirect_reporting=employee_id).values_list('id')
            report_by_list = list(direct_report_by) + list(indirect_report_by)
            report_by_list = [e[0] for e in report_by_list]
            employee_list = Employee.objects.filter(id__in=report_by_list).exclude(employment_status=6).values_list(
                'id', 'employee_id', 'official_name', 'department__department', 'gender')
        elif selected_view == 'hrm':
            employee_list = Employee.objects.exclude(employment_status=6).values_list('id', 'employee_id',
                                                                                      'official_name',
                                                                                      'department__department',
                                                                                      'gender')
        leave_type_list = LeavesType.objects.order_by("order").values()
        for employee in employee_list:
            employee_entitlement_data = {
                'id': employee[0],
                'employee_id': employee[1],
                'official_name': employee[2],
                'department': employee[3],
                'gender': employee[4],
                'entitlement': {}
            }
            entitlement_list.append(employee_entitlement_data)
            #  EXCLUDE REJECTED & CANCELLED LEAVES
            employee_leaves = Leave.objects.all().filter(employee=employee[0], start_date__year=selected_year).exclude(
                status__in=["rejected", "cancelled"]).select_related('employee', 'leave_type', 'approved_by', 'cancel_by', ).values_list(
                'leave_type__leave_type', 'duration')
            employee_entitlement = LeavesEntitlement.objects.filter(
                employee=employee[0], year=selected_year).values()
            # POPULATING EMPLOYEE LEAVES ENTITLEMENT AND AVAILABILITY
            for leave_type in leave_type_list:
                total_entitled_days = 0
                total_leave_applied = 0
                total_available_leave_list = []
                total_available_leave = 0

                # CHECK IF EMPLOYEE IS ENTITLE FOR EACH LEAVE TYPE
                for leave in employee_leaves:
                    # GET ALL DURATION OF APPLIED LEAVES FOR EACH LEAVES TYPE
                    if leave_type['leave_type'] == leave[0]:
                        total_available_leave_list.append(leave[1])
                total_leave_applied = sum(total_available_leave_list)

                # GET EMPLOYEE BASIC ENTITLEMENT DATA FILTERED BY LEAVES TYPE AND SELECTED YEAR

                # GET TOTAL ENTITLEMENT DAYS
                for entitlement in employee_entitlement:
                    if leave_type['id'] == entitlement['leave_type_id']:
                        total_entitled_days = entitlement['days']

                # SET TOTAL AVAILABLE EXCEPTION FOR ABSENT & UNPAID
                if leave_type['leave_type'] != 'Absent' and leave_type['leave_type'] != 'Unpaid':
                    total_available_leave = total_entitled_days - total_leave_applied
                    employee_leave_status = {
                        'id': leave_type['id'],
                        'total_entitled_day': total_entitled_days,
                        'total_available_leave': total_available_leave,
                    }
                # CALCULATE TOTAL AVAILABLE LEAVE
                else:
                    employee_leave_status = {
                        'id': leave_type['id'],
                        'total_leave_applied': total_leave_applied,
                    }

                # APPEND EMPLOYEE ENTITLEMENT DATA IN API
                leave_title = leave_type['leave_type'].replace(
                    " ", "_").lower()
                employee_entitlement_data['entitlement'][leave_title] = employee_leave_status

        return Response(entitlement_list)


class EntitlementDetailsAPI(APIView):
    def get_object(self, employee_id, selected_year):
        try:
            return LeavesEntitlement.objects.all().filter(employee=employee_id, year=selected_year)
        except LeavesEntitlement.DoesNotExist:
            raise Http404

    def get(self, request, employee_id, selected_year, format=None, **kwargs):
        model_object = self.get_object(employee_id, selected_year)
        serializer = EmployeeEntitlementSerializer(model_object, many=True)
        return Response(serializer.data)


class ValidateEntitlementAPI(APIView):
    def post(self, request, employee_id):
        leave_type_id = request.data.get('leave_type_id', [])
        days = request.data.get('days', [])
        selected_year = request.data.get('year', [])
        comment = request.data.get('comment', [])

        updateEntitlementData = {
            "comment": comment,
            "days": days,
            "employee": employee_id,
            "year": selected_year,
            "leave_type": leave_type_id
        }
        # VALIDATE ENTITLEMENT
        # IF DATA EXIST THEN EDIT [PUT]
        try:
            entitlement_data = LeavesEntitlement.objects.values('id').get(employee=employee_id,
                                                                          leave_type=leave_type_id,
                                                                          year=selected_year)
            model_object = LeavesEntitlement.objects.get(
                id=entitlement_data['id'])
            serializer = EmployeeEntitlementSerializer(
                model_object, data=updateEntitlementData)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # ELSE CREATE A NEW ONE [POST]
        except LeavesEntitlement.DoesNotExist:
            serializer = EmployeeEntitlementSerializer(
                data=updateEntitlementData)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response()


class EmployeeLeadWriteAPI(APIView):
    def get_object(self, employee_id):
        try:
            return Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            raise Http404

    def get(self, request, employee_id, format=None, **kwargs):
        lead_list = Employee.objects.all().filter(id=employee_id)
        employee_lead_serializer = EmployeeLeadWriteSerializers(
            lead_list, many=True)
        return Response(employee_lead_serializer.data)

    def put(self, request, employee_id):
        model_object = self.get_object(employee_id)
        serializer = EmployeeLeadWriteSerializers(
            model_object, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
