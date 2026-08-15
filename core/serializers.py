import os
from rest_framework import serializers
from .models import Company, JobPost, Resume, User
from rest_framework import serializers
from .models import Company, JobPost, Resume, User, Application



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


class ResumeUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = ['id', 'file', 'parsed_skills', 'uploaded_at']
        read_only_fields = ['id', 'parsed_skills', 'uploaded_at']

    def validate_file(self, value):
        max_size = 5 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError("حجم فایل نباید بیشتر از ۵ مگابایت باشد.")

        valid_extensions = ['.pdf', '.doc', '.docx']
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in valid_extensions:
            raise serializers.ValidationError("فرمت‌های مجاز برای رزومه تنها شامل PDF و Word (.pdf, .doc, .docx) می‌باشند.")

        return value


class ApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ['id', 'job_post', 'user', 'resume', 'status', 'created_at']
        read_only_fields = ['id', 'user', 'status', 'created_at']

    def validate(self, attrs):
        request = self.context.get('request')
        user = request.user if request else None
        
        job_post = attrs.get('job_post')
        resume = attrs.get('resume')

        if resume and user and resume.user != user:
            raise serializers.ValidationError({
                "resume": "شما فقط می‌توانید رزومه‌های متعلق به خودتان را ارسال کنید."
            })

        if job_post and job_post.status != 'published':
            raise serializers.ValidationError({
                "job_post": "این آگهی شغلی در حال حاضر برای دریافت درخواست استخدام فعال نیست."
            })
        
        if user and Application.objects.filter(user=user, job_post=job_post).exists():
            raise serializers.ValidationError(
                "شما قبلاً برای این آگهی شغلی درخواست ارسال کرده‌اید."
            )

        return attrs