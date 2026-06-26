from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from .models import KYTApplication
from .serializers import KYTApplicationSerializer
from accounts.permissions import IsAdminOrStaff


class KYTSubmitView(generics.CreateAPIView):
    """Tutor submits/updates their KYT documents."""
    serializer_class   = KYTApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(tutor=self.request.user)

    def create(self, request, *args, **kwargs):
        # If application already exists, update it
        existing = KYTApplication.objects.filter(tutor=request.user).first()
        if existing:
            s = self.get_serializer(existing, data=request.data, partial=True)
            s.is_valid(raise_exception=True)
            s.save()
            return Response(s.data)
        return super().create(request, *args, **kwargs)


class KYTMyApplicationView(generics.RetrieveAPIView):
    serializer_class = KYTApplicationSerializer

    def get_object(self):
        return KYTApplication.objects.get(tutor=self.request.user)


class KYTListView(generics.ListAPIView):
    """Admin: list all KYT applications."""
    serializer_class   = KYTApplicationSerializer
    permission_classes = [IsAdminOrStaff]

    def get_queryset(self):
        qs     = KYTApplication.objects.select_related('tutor').order_by('-submitted_at')
        status = self.request.query_params.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs


class KYTApproveView(APIView):
    permission_classes = [IsAdminOrStaff]

    def post(self, request, pk):
        try:
            app = KYTApplication.objects.get(pk=pk)
        except KYTApplication.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=404)
        app.status      = 'approved'
        app.reviewed_at = timezone.now()
        app.reviewed_by = request.user
        app.save()
        # Activate tutor profile: create if missing, set is_available so they appear in search
        from accounts.models import TutorProfile
        TutorProfile.objects.update_or_create(
            user=app.tutor,
            defaults={'is_available': True},
        )
        # Ensure user role is tutor/both so they appear in tutor match
        tutor = app.tutor
        if tutor.role not in ('tutor', 'both'):
            tutor.role = 'tutor'
            tutor.save(update_fields=['role'])
        return Response(KYTApplicationSerializer(app).data)


class KYTRejectView(APIView):
    permission_classes = [IsAdminOrStaff]

    def post(self, request, pk):
        try:
            app = KYTApplication.objects.get(pk=pk)
        except KYTApplication.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=404)
        app.status           = 'rejected'
        app.rejection_reason = request.data.get('reason', '')
        app.admin_notes      = request.data.get('notes', '')
        app.reviewed_at      = timezone.now()
        app.reviewed_by      = request.user
        app.save()
        return Response(KYTApplicationSerializer(app).data)
