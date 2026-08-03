from rest_framework import viewsets, permissions, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from .models import JobPost, Company
from .serializers import JobPostSerializer, CandidateProfileSerializer
from .permissions import IsHRForCompanyJob, IsAdminRole, IsHRRole, IsCandidateRole, IsOwner

class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = JobPostSerializer  
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class JobPostViewSet(viewsets.ModelViewSet):
    queryset = JobPost.objects.all()
    serializer_class = JobPostSerializer
    
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status']
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        if not user.is_authenticated or getattr(user, 'role', None) == 'candidate':
            queryset = queryset.filter(status='published')
            
        return queryset

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)

@extend_schema(
    summary="مدیریت پروفایل کارجو",
    description="مشاهده (GET) و ویرایش جزئیات پروفایل (PATCH/PUT) برای کاربر واردشده."
)
class CandidateProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = CandidateProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_object(self):
        return self.request.user

class HRTestView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsHRRole]

    def get(self, request):
        return Response({"message": "Welcome HR!"})

class CandidateTestView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsCandidateRole]

    def get(self, request):
        return Response({"message": "Welcome Candidate!"})