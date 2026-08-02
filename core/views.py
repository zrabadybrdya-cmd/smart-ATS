from rest_framework import viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import JobPost, Company
from .serializers import JobPostSerializer
from .permissions import IsHRForCompanyJob, IsAdminRole, IsHRRole, IsCandidateRole

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

class HRTestView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsHRRole]

    def get(self, request):
        return Response({"message": "Welcome HR!"})

class CandidateTestView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsCandidateRole]

    def get(self, request):
        return Response({"message": "Welcome Candidate!"})