from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .permissions import IsHRRole, IsCandidateRole, IsAdminOrReadOnly, IsHRForCompanyJob
from .models import Company, JobPost
from .serializers import CompanySerializer, JobPostSerializer

class HRTestView(APIView):
    permission_classes = [IsHRRole]

    def get(self, request):
        return Response({"message": "Hello HR! Access granted."})

class CandidateTestView(APIView):
    permission_classes = [IsCandidateRole]

    def get(self, request):
        return Response({"message": "Hello Candidate! Access granted."})

class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [IsAdminOrReadOnly]

class JobPostViewSet(viewsets.ModelViewSet):
    queryset = JobPost.objects.all()
    serializer_class = JobPostSerializer
    permission_classes = [IsAuthenticated, IsHRForCompanyJob]

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)