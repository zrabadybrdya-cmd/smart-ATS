from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CompanyViewSet, JobPostViewSet, CandidateProfileView, HRTestView, CandidateTestView

router = DefaultRouter()
router.register(r'companies', CompanyViewSet, basename='company')
router.register(r'job-posts', JobPostViewSet, basename='jobpost')

urlpatterns = [
    path('', include(router.urls)),
    path('profile/', CandidateProfileView.as_view(), name='candidate-profile'),
    path('test-hr/', HRTestView.as_view(), name='test-hr'),
    path('test-candidate/', CandidateTestView.as_view(), name='test-candidate'),
]