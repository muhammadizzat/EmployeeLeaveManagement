from django.contrib import admin
from .models import *


class EmployeeFields(admin.ModelAdmin):
    list_display = [f.name for f in Employee._meta.fields]


admin.site.register(Employee, EmployeeFields)


class DependentFields(admin.ModelAdmin):
    list_display = [f.name for f in Dependent._meta.fields]


admin.site.register(Dependent, DependentFields)
admin.site.register(EmploymentCategory)
admin.site.register(EmergencyContact)
admin.site.register(LeavesType)
admin.site.register(Department)
admin.site.register(ParentDepartment)
admin.site.register(Designation)
admin.site.register(EmploymentGrade)
admin.site.register(EmploymentLocation)
admin.site.register(EmploymentStatus)
admin.site.register(Skill)
admin.site.register(LeavesEntitlement)
admin.site.register(Education)
admin.site.register(WorkExperience)
admin.site.register(SkillSet)
admin.site.register(Language)
admin.site.register(LanguageProficiency)
admin.site.register(Survey)


class LeaveFields(admin.ModelAdmin):
    list_display = [f.name for f in Leave._meta.fields]


admin.site.register(Leave, LeaveFields)


class AttendanceFields(admin.ModelAdmin):
    list_display = [f.name for f in Attendance._meta.fields]


admin.site.register(Attendance, AttendanceFields)
