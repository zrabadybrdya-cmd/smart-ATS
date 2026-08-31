from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

try:
    from pgvector.django import VectorField, HnswIndex
except ImportError:
    class VectorField(models.JSONField):
        def __init__(self, *args, dimensions=None, **kwargs):
            self.dimensions = dimensions
            super().__init__(*args, **kwargs)
    HnswIndex = None


class ApplicationStatus(models.TextChoices):
    PENDING = 'pending', _('در انتظار بررسی')
    REVIEWING = 'reviewing', _('در حال بررسی')
    SHORTLISTED = 'shortlisted', _('لیست کوتاه')
    ACCEPTED = 'accepted', _('تایید شده')
    REJECTED = 'rejected', _('رد شده')


class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('hr', 'HR'),
        ('candidate', 'Candidate'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='candidate')
    company = models.ForeignKey('Company', on_delete=models.SET_NULL, null=True, blank=True, related_name='employees')


class Candidate(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='candidate_profile')
    phone = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return self.user.username


class Company(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_companies')
    
    def __str__(self):
        return self.name


class JobPost(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('closed', 'Closed'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='job_posts')
    title = models.CharField(max_length=255)
    description = models.TextField()
    skills = models.TextField()
    skills_embedding = VectorField(dimensions=1536, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            HnswIndex(
                name='jobpost_skills_hnsw_idx',
                fields=['skills_embedding'],
                m=16,
                ef_construction=64,
                opclasses=['vector_cosine_ops'],
            )
        ] if HnswIndex else []

    def __str__(self):
        return self.title


class Resume(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resumes', verbose_name="کارجو")
    file = models.FileField(upload_to='resumes/', verbose_name="فایل رزومه")
    parsed_skills = models.TextField(blank=True, null=True, verbose_name="مهارت‌های استخراج‌شده")
    skills_embedding = VectorField(dimensions=1536, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ آپلود")

    class Meta:
        indexes = [
            HnswIndex(
                name='resume_skills_hnsw_idx',
                fields=['skills_embedding'],
                m=16,
                ef_construction=64,
                opclasses=['vector_cosine_ops'],
            )
        ] if HnswIndex else []

    def __str__(self):
        return f"Resume of {self.user.username} - {self.id}"


class Application(models.Model):
    job_post = models.ForeignKey(
        'JobPost', 
        on_delete=models.CASCADE, 
        related_name='applications'
    )
    user = models.ForeignKey(
        'User', 
        on_delete=models.CASCADE, 
        related_name='applications'
    )
    candidate = models.ForeignKey(
        'Candidate',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='applications'
    )
    resume = models.ForeignKey(
        'Resume', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='applications'
    )
    status = models.CharField(
        max_length=20, 
        choices=ApplicationStatus.choices, 
        default=ApplicationStatus.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('job_post', 'user')

    def __str__(self):
        return f"{self.user.username} - {self.job_post.title} ({self.get_status_display()})"


class ApplicationHistory(models.Model):
    application = models.ForeignKey(
        'Application',
        on_delete=models.CASCADE,
        related_name='history',
        verbose_name='درخواست استخدام'
    )
    status = models.CharField(
        max_length=20, 
        choices=ApplicationStatus.choices, 
        verbose_name='وضعیت جدید'
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='status_changes_made',
        verbose_name='تغییر داده شده توسط'
    )
    note = models.TextField(
        blank=True, 
        null=True, 
        verbose_name='يادداشت / توضیحات'
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name='تاریخ و زمان تغییر'
    )

    class Meta:
        verbose_name = 'تاریخچه درخواست'
        verbose_name_plural = 'تاریخچه درخواست‌ها'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.application} - {self.get_status_display()} at {self.created_at.strftime("%Y-%m-%d %H:%M")}'