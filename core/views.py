from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status, viewsets, generics
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Company, JobPost, Resume
from .permissions import (
    IsAdminRole,
    IsCandidateRole,
    IsHRForCompanyJob,
    IsHRRole,
    IsOwner,
)
from .serializers import (
    CandidateProfileSerializer,
    CompanySerializer,
    JobPostSerializer,
    ResumeUploadSerializer,
)


def home_view(request):
    return HttpResponse(
        "<h1>Welcome to Smart ATS API Platform</h1>"
        "<p>Server is running successfully. Use <a href='/api/'>/api/</a> for endpoints.</p>"
    )


class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
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
    description="مشاهده (GET) و ویرایش جزئیات پروفایل (PATCH/PUT) برای کاربر واردشده.",
)
class CandidateProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = CandidateProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_object(self):
        return self.request.user


class ResumeUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsCandidateRole]

    @extend_schema(
        summary="آپلود رزومه کارجو",
        description="ارسال فایل رزومه (PDF یا Word) با بررسی محدودیت حجم و پسوند.",
    )
    def post(self, request, *args, **kwargs):
        serializer = ResumeUploadSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(
                {
                    "message": "رزومه با موفقیت آپلود و ذخیره شد.",
                    "data": serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class HRTestView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsHRRole]

    def get(self, request):
        return Response({"message": "Welcome HR!"})


class CandidateTestView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsCandidateRole]

    def get(self, request):
        return Response({"message": "Welcome Candidate!"})