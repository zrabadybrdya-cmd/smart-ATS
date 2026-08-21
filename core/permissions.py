from rest_framework import permissions
from .models import Company


class IsAdminRole(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and getattr(request.user, 'role', None) == 'admin')


class IsHRRole(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and getattr(request.user, 'role', None) == 'hr')


class IsCandidateRole(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and getattr(request.user, 'role', None) == 'candidate')


class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return obj == request.user


class IsHRForCompanyJob(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'company'):
            return obj.company.owner == request.user
        if hasattr(obj, 'job_post'):
            return obj.job_post.company.owner == request.user
        return False


class IsHRForOwnCompany(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if getattr(user, 'is_superuser', False) or getattr(user, 'role', None) == 'admin':
            return True
        return Company.objects.filter(owner=user).exists() or getattr(user, 'role', None) == 'hr'