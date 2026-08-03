from rest_framework import serializers
from .models import JobPost, Company, User

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['id', 'name', 'owner']

class JobPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobPost
        fields = ['id', 'title', 'description', 'skills', 'status', 'company', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("عنوان آگهی شغلی نمی‌تواند خالی باشد.")
        return value

    def validate_skills(self, value):
        if not value.strip():
            raise serializers.ValidationError("وارد کردن مهارت‌های مورد نیاز الزامی است.")
        return value

class CandidateProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone']