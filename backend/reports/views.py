from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from .models import Report
from .serializers import ReportSerializer


class ReportCreateView(generics.CreateAPIView):
    serializer_class = ReportSerializer

    def perform_create(self, serializer):
        serializer.save(reporter=self.request.user)


class ReportListView(generics.ListAPIView):
    serializer_class   = ReportSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        qs    = Report.objects.select_related('reporter','accused').order_by('-created_at')
        rtype = self.request.query_params.get('type')
        stat  = self.request.query_params.get('status')
        if rtype:
            qs = qs.filter(type=rtype)
        if stat:
            qs = qs.filter(status=stat)
        return qs


class ReportActionView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk):
        try:
            report = Report.objects.get(pk=pk)
        except Report.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=404)

        action     = request.data.get('action', 'dismiss')
        admin_note = request.data.get('note', '')

        report.action_taken  = action
        report.admin_note    = admin_note
        report.resolved_by   = request.user
        report.resolved_at   = timezone.now()

        if 'ban' in action.lower():
            report.accused.is_suspended = True
            report.accused.save()
            report.status = 'resolved'
        elif 'suspend' in action.lower():
            report.accused.is_suspended = True
            report.accused.save()
            report.status = 'resolved'
        elif 'dismiss' in action.lower():
            report.status = 'dismissed'
        else:
            report.status = 'resolved'

        report.save()
        return Response(ReportSerializer(report).data)
