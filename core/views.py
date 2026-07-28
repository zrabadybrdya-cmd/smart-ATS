from rest_framework.views import APIView
from rest_framework.response import Response
from .permissions import IsHRRole, IsCandidateRole

class HRTestView(APIView):
    permission_classes = [IsHRRole]

    def get(self, request):
        return Response({"message": "Hello HR! Access granted."})

class CandidateTestView(APIView):
    permission_classes = [IsCandidateRole]

    def get(self, request):
        return Response({"message": "Hello Candidate! Access granted."})