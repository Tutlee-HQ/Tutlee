from rest_framework import permissions


class IsAdminOrStaff(permissions.BasePermission):
    """
    Grants access to users who are either Django staff (is_staff=True)
    OR have role='admin' set on their Tutlee user account.
    Mirrors the admin.html login gate:
        if (!data.user.is_staff && data.user.role !== 'admin') → deny
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return bool(request.user.is_staff or getattr(request.user, 'role', None) == 'admin')
