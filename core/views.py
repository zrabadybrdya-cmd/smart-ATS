from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import viewsets
from .permissions import IsHRRole, IsCandidateRole, IsAdminOrReadOnly
from .models import Company
from .serializers import CompanySerializer

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