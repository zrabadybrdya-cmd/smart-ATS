from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('hr', 'HR'),
        ('candidate', 'Candidate'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='candidate')
    company = models.ForeignKey('Company', on_delete=models.SET_NULL, null=True, blank=True, related_name='employees')

class Company(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_companies')
    
    def __str__(self):
        return name

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
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title