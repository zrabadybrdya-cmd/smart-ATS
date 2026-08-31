import django_filters
from django.db.models import Q
from .models import Application, JobPost

class ApplicationFilter(django_filters.FilterSet):
    status = django_filters.CharFilter(field_name='status', lookup_expr='exact')
    job_post = django_filters.NumberFilter(field_name='job_post__id', lookup_expr='exact')
    company = django_filters.NumberFilter(field_name='job_post__company__id', lookup_expr='exact')
    candidate_username = django_filters.CharFilter(field_name='candidate__user__username', lookup_expr='icontains')
    candidate_email = django_filters.CharFilter(field_name='candidate__user__email', lookup_expr='icontains')
    skills = django_filters.CharFilter(method='filter_by_skills')
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = Application
        fields = [
            'status',
            'job_post',
            'company',
            'candidate_username',
            'candidate_email',
            'skills',
            'created_after',
            'created_before'
        ]

    def filter_by_skills(self, queryset, name, value):
        if not value:
            return queryset
        skills_list = [s.strip() for s in value.split(',') if s.strip()]
        skill_query = Q()
        for skill in skills_list:
            skill_query |= Q(resume__parsed_skills__icontains=skill)
        return queryset.filter(skill_query).distinct()


class JobPostFilter(django_filters.FilterSet):
    status = django_filters.CharFilter(field_name='status', lookup_expr='exact')
    company = django_filters.NumberFilter(field_name='company__id', lookup_expr='exact')
    skills = django_filters.CharFilter(method='filter_by_skills')
    title = django_filters.CharFilter(field_name='title', lookup_expr='icontains')

    class Meta:
        model = JobPost
        fields = ['status', 'company', 'skills', 'title']

    def filter_by_skills(self, queryset, name, value):
        if not value:
            return queryset
        skills_list = [s.strip() for s in value.split(',') if s.strip()]
        skill_query = Q()
        for skill in skills_list:
            skill_query |= Q(skills__icontains=skill)
        return queryset.filter(skill_query).distinct()