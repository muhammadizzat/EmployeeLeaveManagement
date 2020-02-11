from django.conf.urls import url
from . import views
from . import api

urlpatterns = [
    # API URL
    # EMPLOYEE LEAVES
    url(r'^api/hrm/employee/leave/(?P<employee_id>\d+)/(?P<selected_year>\d+)/$', api.EmployeeLeavesAPI.as_view(),
        name='employee_leave'),
    url(r'^api/hrm/lead/leave/(?P<employee_id>\d+)/(?P<selected_year>\d+)/$', api.LeadViewLeavesAPI.as_view(),
        name='lead_leave'),
    url(r'^api/hrm/leave/(?P<employee_id>\d+)/(?P<selected_year>\d+)/$', api.HRMViewLeavesAPI.as_view(),
        name='hrm_leave'),
    url(r'^api/hrm/leave_detail/(?P<leave_id>\d+)/$', api.EmployeeSelectedLeavesAPI.as_view(),
        name='employee_leave_detail'),
    url(r'^api/hrm/leave_detail/latest/$', api.EmployeeLatestLeavesAPI.as_view(),
        name='employee_latest_leave_detail'),
    #  FILTER LEAVES
    url(r'^api/hrm/employee/leave/filter/(?P<employee_id>\d+)/$', api.EmployeeLeavesFilterDateAPI.as_view(),
        name='employee_leave_filter'),

    # EMPLOYEE ENTITLEMENT
    url(r'^api/hrm/entitlement/(?P<selected_view>[\w-]+)/(?P<employee_id>\d+)/(?P<selected_year>\d+)/$', api.EmployeeEntitlementAPI.as_view(),
        name='hrm_entitlement'),
    url(r'^api/hrm/entitlement_detail/(?P<employee_id>\d+)/(?P<entitlement_id>\d+)/(?P<selected_year>\d+)/$', api.EntitlementDetailsAPI.as_view(),
        name='entitlement_detail'),
    url(r'^api/hrm/validate_entitlement/(?P<employee_id>\d+)/$', api.ValidateEntitlementAPI.as_view(),
        name='validate_entitlement'),
    url(r'^api/hrm/leave_viewer/$', api.LeaveSchedulerAPI.as_view(),
        name='leave_viewer'),


    #  EMPLOYEE LEAD API
    # url(r'^api/hrm/lead_list/$', api.EmployeeLeadListAPI.as_view(),name='hrm_lead_list'),
    url(r'^api/hrm/lead_detail/(?P<employee_id>\d+)/$',
        api.EmployeeLeadWriteAPI.as_view(), name='hrm_lead_detail'),

    # MY INFO URL PATH
    url(r'^hrm/employee/leaves/$', views.employee_leaves, name='leaves_view'),
    url(r'^hrm/employee/leaves_update/(?P<leave_id>\d+)/$',
        views.employee_leaves_update, name='leaves_update_view'),
    url(r'^hrm/employee/entitlement/(?P<selected_view>[\w-]+)/$',
        views.employee_entitlement, name='leaves_view'),
    url(r'^hrm/employee/leave_viewer/$',
        views.leave_viewer, name='leave_viewer'),

]
