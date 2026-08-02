from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CompanyViewSet, JobPostViewSet, HRTestView, CandidateTestView

router = DefaultRouter()
router.register(r'companies', CompanyViewSet, basename='company')
router.register(r'job-posts', JobPostViewSet, basename='job-post')

urlpatterns = [
    path('', include(router.urls)),
    path('test-hr/', HRTestView.as_view(), name='test-hr'),
    path('test-candidate/', CandidateTestView.as_view(), name='test-candidate'),
]