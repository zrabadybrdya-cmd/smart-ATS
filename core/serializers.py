import os
from rest_framework import serializers
from .models import Company, JobPost, Resume, User, Application, ApplicationStatus, Candidate


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
        fields = ['id', 'job_post', 'candidate', 'resume', 'status', 'created_at']
        read_only_fields = ['id', 'candidate', 'status', 'created_at']

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

        if user and hasattr(user, 'candidate') and Application.objects.filter(candidate=user.candidate, job_post=job_post).exists():
            raise serializers.ValidationError(
                "شما قبلاً برای این آگهی شغلی درخواست ارسال کرده‌اید."
            )

        return attrs


class ApplicationStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=ApplicationStatus.choices if hasattr(ApplicationStatus, 'choices') else [
            ('pending', 'Pending'),
            ('reviewed', 'Reviewed'),
            ('interview', 'Interview'),
            ('rejected', 'Rejected'),
            ('hired', 'Hired'),
        ],
        required=True,
        error_messages={
            'required': 'وارد کردن وضعیت جدید الزامی است.',
            'invalid_choice': 'وضعیت انتخاب شده معتبر نمی‌باشد.'
        }
    )
    note = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True
    )

class CandidateLiteSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    email = serializers.EmailField(source='user.email', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Candidate
        fields = ['id', 'username', 'full_name', 'email', 'phone']

    def get_full_name(self, obj):
        if obj.user:
            name = f"{obj.user.first_name} {obj.user.last_name}".strip()
            return name if name else obj.user.username
        return ""


class KanbanJobPostLiteSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)

    class Meta:
        model = JobPost
        fields = ['id', 'title', 'company_name']


class KanbanApplicationSerializer(serializers.ModelSerializer):
    candidate = CandidateLiteSerializer(read_only=True)
    job_post = KanbanJobPostLiteSerializer(read_only=True)
    resume_url = serializers.FileField(source='resume.file', read_only=True)

    class Meta:
        model = Application
        fields = ['id', 'job_post', 'candidate', 'resume_url', 'status', 'created_at']