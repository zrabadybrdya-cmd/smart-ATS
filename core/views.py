from django.http import HttpResponse
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, status, viewsets, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import Company, JobPost, Application, Resume, Candidate, ApplicationHistory
from .serializers import (
    CompanySerializer,
    JobPostSerializer,
    CandidateProfileSerializer,
    ResumeUploadSerializer,
    ApplicationSerializer,
    ApplicationStatusUpdateSerializer,
)
from .permissions import IsHRForCompanyJob, IsHRRole, IsCandidateRole, IsAdminRole, IsOwner
from .state_machine import ApplicationStateMachine


def home_view(request):
    return HttpResponse(
        "<h1>Welcome to Smart ATS API Platform</h1>"
        "<p>Server is running successfully. Use <a href='/api/'>/api/</a> for endpoints.</p>"
    )


@extend_schema_view(
    list=extend_schema(summary="دریافت لیست شرکت‌ها", tags=["Companies"]),
    retrieve=extend_schema(summary="دریافت جزئیات یک شرکت", tags=["Companies"]),
    create=extend_schema(summary="ایجاد شرکت جدید", tags=["Companies"]),
    update=extend_schema(summary="ویرایش کامل پروفایل شرکت", tags=["Companies"]),
    partial_update=extend_schema(summary="ویرایش جزئی پروفایل شرکت", tags=["Companies"]),
    destroy=extend_schema(summary="حذف شرکت", tags=["Companies"]),
)
class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsAdminRole()]
        return [permissions.AllowAny()]


@extend_schema_view(
    list=extend_schema(summary="دریافت لیست آگهی‌های شغلی", tags=["Job Posts"]),
    retrieve=extend_schema(summary="دریافت جزئیات آگهی شغلی", tags=["Job Posts"]),
    create=extend_schema(summary="ایجاد آگهی شغلی جدید", tags=["Job Posts"]),
    update=extend_schema(summary="ویرایش کامل آگهی شغلی", tags=["Job Posts"]),
    partial_update=extend_schema(summary="ویرایش جزئی آگهی شغلی", tags=["Job Posts"]),
    destroy=extend_schema(summary="حذف آگهی شغلی", tags=["Job Posts"]),
)
class JobPostViewSet(viewsets.ModelViewSet):
    queryset = JobPost.objects.all()
    serializer_class = JobPostSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsHRRole(), IsHRForCompanyJob()]
        return [permissions.IsAuthenticatedOrReadOnly()]

    def perform_create(self, serializer):
        user = self.request.user
        company = getattr(user, 'company', None)
        if not company:
            raise permissions.exceptions.PermissionDenied("کاربر متصل به هیچ شرکتی نیست.")
        serializer.save(company=company)


@extend_schema(
    summary="مدیریت پروفایل کارجو",
    description="مشاهده و ویرایش مشخصات پروفایل کارجو.",
    tags=["Candidate Profile"]
)
class CandidateProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = CandidateProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_object(self):
        candidate, _ = Candidate.objects.get_or_create(user=self.request.user)
        return candidate


class ResumeUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsCandidateRole]

    @extend_schema(
        summary="آپلود فایل رزومه جدید",
        description="ارسال فایل رزومه (PDF یا Word) توسط کارجو.",
        request=ResumeUploadSerializer,
        responses={201: ResumeUploadSerializer},
        tags=["Resumes"]
    )
    def post(self, request, *args, **kwargs):
        serializer = ResumeUploadSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            resume = serializer.save()
            return Response(
                {
                    "message": "رزومه با موفقیت آپلود شد.",
                    "resume_id": resume.id,
                    "file_url": resume.file.url if resume.file else None
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    list=extend_schema(summary="دریافت لیست درخواست‌های استخدام", tags=["Applications"]),
    retrieve=extend_schema(summary="دریافت جزئیات درخواست استخدام", tags=["Applications"]),
    create=extend_schema(summary="ثبت درخواست استخدام جدید", tags=["Applications"]),
    partial_update=extend_schema(summary="تغییر وضعیت درخواست استخدام", tags=["Applications"]),
)
class ApplicationViewSet(viewsets.ModelViewSet):
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'role') and user.role == 'hr' and hasattr(user, 'company'):
            return Application.objects.filter(job_post__company=user.company)
        elif hasattr(user, 'candidate'):
            return Application.objects.filter(candidate=user.candidate)
        return Application.objects.none()

    def perform_create(self, serializer):
        candidate, _ = Candidate.objects.get_or_create(user=self.request.user)
        serializer.save(candidate=candidate)


class HRTestView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsHRRole]

    @extend_schema(summary="تست دسترسی نقش HR", tags=["RBAC Tests"])
    def get(self, request):
        return Response({"message": "دسترسی HR تایید شد."})


class CandidateTestView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsCandidateRole]

    @extend_schema(summary="تست دسترسی نقش Candidate", tags=["RBAC Tests"])
    def get(self, request):
        return Response({"message": "دسترسی Candidate تایید شد."})


class ApplicationStatusUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        application = get_object_or_404(Application, pk=pk)
        
        serializer = ApplicationStatusUpdateSerializer(data=request.data)
        if serializer.is_valid():
            new_status = serializer.validated_data['status']
            note = serializer.validated_data.get('note', '')
            
            current_status = application.status
            
            machine = ApplicationStateMachine()
            
            # بررسی صحت انتقال وضعیت با در نظر گرفتن هر دو شیوه پیاده‌سازی متداول متد
            is_allowed = False
            if hasattr(machine, 'can_transition_to'):
                try:
                    is_allowed = machine.can_transition_to(current_status, new_status)
                except TypeError:
                    machine.current_state = current_status
                    is_allowed = machine.can_transition_to(new_status)
            elif hasattr(machine, 'is_valid_transition'):
                is_allowed = machine.is_valid_transition(current_status, new_status)
            else:
                is_allowed = True
            
            if not is_allowed:
                return Response(
                    {"error": f"امکان تغییر وضعیت از '{current_status}' به '{new_status}' وجود ندارد."},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            try:
                with transaction.atomic():
                    application.status = new_status
                    application.save()
                    
                    ApplicationHistory.objects.create(
                        application=application,
                        status=new_status,
                        changed_by=request.user,
                        note=note
                    )
            except Exception as e:
                return Response(
                    {"error": "خطایی در پردازش اطلاعات رخ داد."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            return Response(
                {
                    "message": "وضعیت درخواست با موفقیت به‌روزرسانی شد.",
                    "application_id": application.id,
                    "new_status": new_status,
                    "note": note
                },
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)