from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import filters, generics, permissions, status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .filters import ApplicationFilter, JobPostFilter
from .models import Application, ApplicationHistory, Candidate, Company, JobPost, Resume
from .permissions import (
    IsAdminRole,
    IsCandidateRole,
    IsHRForCompanyJob,
    IsHRForOwnCompany,
    IsHRRole,
    IsOwner,
)
from .serializers import (
    ApplicationSerializer,
    ApplicationStatusUpdateSerializer,
    CandidateProfileSerializer,
    CompanySerializer,
    JobPostSerializer,
    KanbanApplicationSerializer,
    ResumeUploadSerializer,
)
from .state_machine import ApplicationStateMachine
from .tasks import send_notification_email


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
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'owner__username', 'owner__email']
    ordering_fields = ['name']

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
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = JobPostFilter
    search_fields = ['title', 'description', 'skills', 'company__name']
    ordering_fields = ['created_at', 'title']

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
    queryset = Application.objects.select_related("candidate__user", "job_post__company", "resume").all()
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ApplicationFilter
    search_fields = [
        "candidate__user__username",
        "candidate__user__email",
        "candidate__user__first_name",
        "candidate__user__last_name",
        "job_post__title",
        "job_post__description",
        "resume__parsed_skills",
    ]
    ordering_fields = ["created_at", "status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        base_qs = Application.objects.select_related("candidate__user", "job_post__company", "resume")
        if hasattr(user, "role") and user.role == "hr" and hasattr(user, "company") and user.company:
            return base_qs.filter(job_post__company=user.company)
        elif hasattr(user, "candidate"):
            return base_qs.filter(candidate=user.candidate)
        elif getattr(user, "role", None) == "admin":
            return base_qs.all()
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

                    candidate_email = (
                        application.candidate.user.email
                        if hasattr(application, 'candidate') and application.candidate
                        else getattr(application, 'user', request.user).email
                    )
                    candidate_name = (
                        application.candidate.user.get_full_name() or application.candidate.user.username
                        if hasattr(application, 'candidate') and application.candidate
                        else getattr(application, 'user', request.user).username
                    )
                    job_title = application.job_post.title
                    company_name = application.job_post.company.name

                    template_map = {
                        'interview': 'emails/interview_invite.html',
                        'hired': 'emails/accepted.html',
                        'rejected': 'emails/rejected.html',
                    }
                    template_name = template_map.get(new_status, 'emails/interview_invite.html')

                    context_data = {
                        'candidate_name': candidate_name,
                        'job_title': job_title,
                        'company_name': company_name,
                        'interview_date': 'هماهنگی از طریق تماس',
                        'meeting_link': 'https://meet.smart-ats.local',
                    }

                    transaction.on_commit(
                        lambda: send_notification_email.delay(
                            subject=f"بروزرسانی وضعیت درخواست: {job_title}",
                            template_name=template_name,
                            context=context_data,
                            recipient_list=[candidate_email]
                        )
                    )

            except Exception:
                return Response(
                    {"error": "خطایی در پردازش اطلاعات رخ داد."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            return Response(
                {
                    "message": "وضعیت درخواست با موفقیت به‌روزرسانی شد و ایمیل اطلاع‌رسانی در صف ارسال قرار گرفت.",
                    "application_id": application.id,
                    "new_status": new_status,
                    "note": note
                },
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class KanbanBoardView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsHRForOwnCompany]

    @extend_schema(
        summary="واکشی بهینه درخواست‌ها برای بورد کانبان با تفکیک شرکت",
        description="واکشی کلیه درخواست‌ها با رفع مشکل N+1 و فیلتر خودکار بر اساس شرکت کاربر HR لاگین‌شده.",
        parameters=[
            OpenApiParameter(name='job_id', type=int, required=False, description='شناسه آگهی شغلی جهت فیلتر'),
        ],
        tags=["Kanban Board"]
    )
    def get(self, request):
        user = request.user
        company = getattr(user, 'company', None)

        if not company:
            raise PermissionDenied("کاربر متصل به هیچ شرکتی نیست و امکان دسترسی به بورد کانبان را ندارد.")

        job_id = request.query_params.get('job_id')

        queryset = Application.objects.select_related(
            "candidate__user",
            "job_post__company",
            "resume"
        ).filter(job_post__company=company)

        if job_id:
            queryset = queryset.filter(job_post_id=job_id)

        columns = {
            'pending': [],
            'reviewed': [],
            'interview': [],
            'rejected': [],
            'hired': []
        }

        serializer = KanbanApplicationSerializer(queryset, many=True)
        for app in serializer.data:
            app_status = app.get('status')
            if app_status in columns:
                columns[app_status].append(app)

        return Response({
            "company": company.name,
            "total_applications": len(serializer.data),
            "columns": columns
        }, status=status.HTTP_200_OK)