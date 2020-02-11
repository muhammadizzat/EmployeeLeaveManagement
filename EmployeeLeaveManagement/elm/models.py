from django.db import models
from model_utils.fields import MonitorField


class Employee(models.Model):
    """
    This will be create as a table in database
    """
    activation = models.BooleanField(default=False)
    employee_id = models.CharField(max_length=6, unique=True)
    official_name = models.CharField(max_length=200)
    nick_name = models.CharField(max_length=50, null=True, blank=True)
    account_id = models.CharField(max_length=50, null=True, blank=True)

    # def save(self, *args, **kwargs):
    #     employee_id_list = [e[0] for e in Employee.objects.values_list('employee_id')]
    #     if employee_id_list:
    #         x = [int(e[2:]) for e in employee_id_list]
    #         latest_id = max(x)
    #         new_id = latest_id + 1
    #         new_employee_id = 'LS%04d' % new_id
    #     else:
    #         new_employee_id = 'LS0000'
    #     self.employee_id = new_employee_id
    #     super(Employee, self).save(*args, **kwargs)

    def upload_photo_dir(self, filename):
        ext = filename.split('.')[-1]
        path = 'hrm/employees/photo/{}.{}'.format(self.employee_id, ext)
        return path

    photo = models.ImageField(
        upload_to=upload_photo_dir, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender_choice = (('male', 'Male'),  ('female', 'Female'))
    gender = models.CharField(
        max_length=10, choices=gender_choice, null=True, blank=True)
    marital_choice = (('single', 'Single'), ('married', 'Married'))
    marital_status = models.CharField(
        max_length=10, choices=marital_choice, null=True, blank=True)
    passport_ic = models.CharField(max_length=50, null=True, blank=True)
    socso_number = models.CharField(max_length=50, null=True, blank=True)
    epf_number = models.CharField(max_length=50, null=True, blank=True)

    race = models.CharField(max_length=50, null=True, blank=True)
    religion = models.CharField(max_length=50, null=True, blank=True)

    food_choices = (('vegetarian', 'Vegetarian'), ('non-beef',
                                                   'Non-Beef'), ('halal', 'Halal'), ('none', 'None'))
    food_pref = models.CharField(
        max_length=10, choices=food_choices, null=True, blank=True)

    size_choice = (('xs', 'X-Small'), ('sm', 'Small'), ('m', 'Medium'),
                   ('l', 'Large'), ('xl', 'X-Large'), ('xxl', 'XX-Large'))
    tshirt_size = models.CharField(
        max_length=5, choices=size_choice, null=True, blank=True)

    # contact details
    nationality = models.ForeignKey(
        "Nationality", on_delete=models.CASCADE, null=True, blank=True)
    address_1 = models.CharField(max_length=200, null=True, blank=True)
    address_2 = models.CharField(max_length=200, null=True, blank=True)
    address_city = models.CharField(max_length=100, null=True, blank=True)
    address_state = models.CharField(max_length=50, null=True, blank=True)
    address_zip = models.CharField(max_length=50, null=True, blank=True)
    address_country = models.CharField(max_length=50, null=True, blank=True)
    work_email = models.CharField(max_length=50, null=True, blank=True)
    other_email = models.CharField(max_length=50, null=True, blank=True)
    phone = models.CharField(max_length=50, null=True, blank=True)

    # Jobs Details
    output_score = models.FloatField(default=1.0, null=True, blank=True)
    employment_grade = models.ForeignKey("EmploymentGrade", on_delete=models.CASCADE, related_name='employment_grade',
                                         null=True, blank=True)
    direct_reporting = models.ForeignKey(
        "Employee", on_delete=models.CASCADE, blank=True, null=True, related_name='+')
    indirect_reporting = models.ManyToManyField(
        "Employee", blank=True, related_name='+')
    employment_location = models.ForeignKey("EmploymentLocation", on_delete=models.CASCADE, related_name='employment_location',
                                            null=True, blank=True)
    employment_status = models.ForeignKey("EmploymentStatus", on_delete=models.CASCADE, related_name='employment_status',
                                          null=True, blank=True)
    employment_category = models.ForeignKey("EmploymentCategory", on_delete=models.CASCADE, related_name='employment_category',
                                            null=True, blank=True)
    designation = models.ForeignKey(
        "Designation", on_delete=models.CASCADE, related_name='+', null=True, blank=True)
    parent_department = models.ForeignKey("ParentDepartment", on_delete=models.CASCADE, related_name='+', null=True,
                                          blank=True)
    department = models.ForeignKey(
        "Department", on_delete=models.CASCADE, related_name='+', null=True, blank=True)
    joining_date = models.DateField(null=True, blank=True)
    confirm_date = models.DateField(null=True, blank=True)
    contract_start_date = models.DateField(null=True, blank=True)
    contract_end_date = models.DateField(null=True, blank=True)
    notice_period = models.IntegerField(null=True, blank=True)
    contract_terminate_date = models.DateField(null=True, blank=True)
    last_working_day = models.DateField(null=True, blank=True)

    # Employee Immigration information
    passport_number = models.CharField(max_length=50, null=True, blank=True)
    passport_issue_country = models.CharField(
        max_length=50, null=True, blank=True)
    passport_issue_date = models.DateField(null=True, blank=True)
    passport_expire_date = models.DateField(null=True, blank=True)
    visa_number = models.CharField(max_length=50, null=True, blank=True)
    visa_approved_date = models.DateField(null=True, blank=True)
    visa_expired_date = models.DateField(null=True, blank=True)
    mdec_number = models.CharField(max_length=50, null=True, blank=True)

    # salary info
    income_tax_number = models.CharField(max_length=50, null=True, blank=True)
    bank_name = models.CharField(max_length=50, null=True, blank=True)
    bank_type = models.CharField(max_length=50, null=True, blank=True)
    bank_account_number = models.CharField(
        max_length=50, null=True, blank=True)
    salary_amount = models.CharField(max_length=50, null=True, blank=True)
    pay_frequency = models.CharField(max_length=50, null=True, blank=True)
    skill = models.ManyToManyField("Skill", blank=True)

    # NOTICE
    notice_policy = models.BooleanField(default=False)
    handbook = models.BooleanField(default=False)

    def __str__(self):
        if self.official_name:
            return self.official_name
        return self.employee_id


class LeavesType(models.Model):
    leave_type = models.CharField(max_length=50)
    order = models.PositiveSmallIntegerField(null=True, blank=True)

    def __str__(self):
        return self.leave_type


class LeavesEntitlement(models.Model):
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='+')
    leave_type = models.ForeignKey(
        LeavesType, on_delete=models.CASCADE, related_name='+')
    comment = models.CharField(max_length=255, null=True, blank=True)
    days = models.FloatField(null=True, blank=True)
    year = models.PositiveIntegerField()

    def __str__(self):
        return '%s - %s' % (self.employee, self.leave_type)

    class Meta:
        unique_together = ("employee", "leave_type", "year")


class Leave(models.Model):
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='+')
    leave_type = models.ForeignKey(
        LeavesType, on_delete=models.CASCADE, related_name='+')
    status = (('pending_approval', 'Pending Approval'),
              ('approved', 'Approved'),
              ('expired', 'Expired'),
              ('rejected', 'Rejected'),
              ('cancelled', 'Cancelled'),
              )
    status = models.CharField(
        max_length=50, choices=status, default='pending_approval')
    start_date = models.DateField()
    end_date = models.DateField()
    duration = models.FloatField(null=True, blank=True)
    working_hour_CHOICES = (('first_half', '1st half of the Day'),
                            ('second_half', '2nd half of the Day'),
                            ('full_day', 'Full Day'),
                            )
    working_hour_duration = models.CharField(
        max_length=20, choices=working_hour_CHOICES, default='full_day')
    comment = models.CharField(max_length=255)
    applied_date = models.DateField(auto_now_add=True)

    approved_by = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='leave_approved_by', null=True, blank=True)
    approved_date = fields.MonitorField(
        monitor='approved_by', null=True, blank=True)

    cancel_by = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_cancel_by', null=True,
                                  blank=True)
    cancel_date = fields.MonitorField(
        monitor='cancel_by', null=True, blank=True)
    modified_date = models.DateTimeField(auto_now=True)
    lead_comment = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        unique_together = ("employee", "leave_type", "start_date",
                           "end_date", "duration", "working_hour_duration")
