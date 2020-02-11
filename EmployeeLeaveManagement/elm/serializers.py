from rest_framework import serializers
from .models import Employee, EmergencyContact, Dependent, WorkExperience, Education, SkillSet, LanguageProficiency, Leave, LeavesEntitlement


class EmployeeLeaveSerializer(serializers.ModelSerializer):
    employee = EmployeeDetailSimpleSerializer()
    approved_by = EmployeeDetailSimpleSerializer()

    class Meta:
        model = Leave
        fields = '__all__'
        depth = 1


class EmployeeLeaveWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Leave
        fields = '__all__'
        depth = 0


class EmployeeEntitlementSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeavesEntitlement
        fields = '__all__'
        depth = 0


class EmployeeLeadWriteSerializers(serializers.ModelSerializer):
    indirect_reporting = serializers.PrimaryKeyRelatedField(many=True, read_only=False, queryset=Employee.objects.all(),
                                                            required=False)

    def update(self, instance, validated_data):
        for k, v in validated_data.items():
            if k == 'indirect_reporting':
                setattr(instance, k, v)  # use this to replace
        instance.save()
        return instance

    class Meta:
        model = Employee
        fields = ('id', 'indirect_reporting')
        depth = 0
