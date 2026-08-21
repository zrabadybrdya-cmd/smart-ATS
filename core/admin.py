from django.contrib import admin
from .models import Company, JobPost, Application, ApplicationHistory

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'owner')
    search_fields = ('name', 'owner__username')

@admin.register(JobPost)
class JobPostAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'company', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'company__name')

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('id', 'job_post', 'user', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'job_post__title')

@admin.register(ApplicationHistory)
class ApplicationHistoryAdmin(admin.ModelAdmin):
    list_display = ('application', 'status', 'changed_by', 'created_at')
    list_filter = ('status', 'created_at')