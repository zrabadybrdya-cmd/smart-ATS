import uuid
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

class BaseModel(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="شناسه یکتا (UUID)"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="تاریخ و زمان ایجاد رکورد"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="تاریخ و زمان آخرین بروزرسانی"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="وضعیت فعال یا غیرفعال بودن رکورد"
    )

    class Meta:
        abstract = True

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    username = models.CharField(max_length=150, unique=True, null=True, blank=True)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=50, default='candidate')

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='core_user_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='core_user_permissions_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  

    objects = CustomUserManager()

    def __str__(self):
        return self.email

class Company(BaseModel):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='companies', null=True, blank=True)
    logo = models.ImageField(upload_to='company_logos/', null=True, blank=True)

    def __str__(self):
        return self.name

class Candidate(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='candidate_profile')
    phone = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return self.user.email