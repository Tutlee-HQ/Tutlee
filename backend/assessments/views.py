from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Avg, Count, Q
from .models import Assessment
from .serializers import AssessmentSerializer, SubmitAssessmentSerializer


class AssessmentListView(generics.ListAPIView):
    serializer_class = AssessmentSerializer

    def get_queryset(self):
        u = self.request.user
        if u.is_staff:
            return Assessment.objects.select_related('learner').order_by('-created_at')
        return Assessment.objects.filter(learner=u).order_by('-created_at')


class AssessmentDetailView(generics.RetrieveAPIView):
    serializer_class = AssessmentSerializer

    def get_queryset(self):
        u = self.request.user
        if u.is_staff:
            return Assessment.objects.all()
        return Assessment.objects.filter(learner=u)


class SubmitAssessmentView(APIView):
    def post(self, request, pk):
        try:
            assessment = Assessment.objects.get(pk=pk, learner=request.user, status='pending')
        except Assessment.DoesNotExist:
            return Response({'detail': 'Not found or already completed.'}, status=404)
        s = SubmitAssessmentSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        assessment.answers = s.validated_data['answers']
        score = assessment.calculate_score()
        return Response(AssessmentSerializer(assessment).data)


class AssessmentStatsView(APIView):
    """Admin analytics endpoint."""
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        total    = Assessment.objects.filter(status='completed').count()
        passed   = Assessment.objects.filter(status='completed', passed=True).count()
        avg_score = Assessment.objects.filter(status='completed').aggregate(avg=Avg('score'))['avg'] or 0
        pass_rate = round(passed / total * 100, 1) if total else 0

        # Per-subject breakdown
        subjects = Assessment.objects.filter(status='completed').values('subject').annotate(
            total=Count('id'),
            passed=Count('id', filter=Q(passed=True)),
        ).order_by('-total')
        subject_data = [
            {
                'subject':   s['subject'],
                'total':     s['total'],
                'passed':    s['passed'],
                'pass_rate': round(s['passed'] / s['total'] * 100, 1) if s['total'] else 0,
            }
            for s in subjects
        ]

        return Response({
            'total':      total,
            'passed':     passed,
            'pass_rate':  pass_rate,
            'avg_score':  round(avg_score, 1),
            'by_subject': subject_data,
        })
