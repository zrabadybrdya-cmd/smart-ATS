from rest_framework import serializers
from .models import Company, JobPost

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['id', 'name', 'owner']

class JobPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobPost
        fields = ['id', 'title', 'description', 'skills', 'status', 'company']
        read_only_fields = ['id', 'created_at']

    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("عنوان آگهی شغلی نمی‌تواند خالی باشد.")
        return value

    def validate_skills(self, value):
        if not value.strip():
            raise serializers.ValidationError("وارد کردن مهارت‌های مورد نیاز الزامی است.")
        return value