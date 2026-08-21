from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    CandidateProfileView,
    CandidateTestView,
    CompanyViewSet,
    HRTestView,
    JobPostViewSet,
    ResumeUploadView,
    ApplicationViewSet,
    ApplicationStatusUpdateView,
)

router = DefaultRouter()
router.register(r'companies', CompanyViewSet, basename='company')
router.register(r'job-posts', JobPostViewSet, basename='jobpost')
router.register(r'applications', ApplicationViewSet, basename='application')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', CandidateProfileView.as_view(), name='candidate-profile'),
    path('resume/upload/', ResumeUploadView.as_view(), name='resume-upload'),
    path('test-hr/', HRTestView.as_view(), name='test-hr'),
    path('test-candidate/', CandidateTestView.as_view(), name='test-candidate'),
    path('applications/<int:pk>/status/', ApplicationStatusUpdateView.as_view(), name='application-status-update'),
]