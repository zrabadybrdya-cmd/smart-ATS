from rest_framework import permissions

class IsHRForCompanyJob(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.company.owner == request.user

class IsAdminRole(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and getattr(request.user, 'role', None) == 'admin'

class IsHRRole(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and getattr(request.user, 'role', None) == 'hr'

class IsCandidateRole(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and getattr(request.user, 'role', None) == 'candidate'

class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return obj == request.user