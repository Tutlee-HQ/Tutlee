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


class KYTProficiencyView(APIView):
    """
    GET  — tutor retrieves the questions set by admin (answer_key stripped out).
    POST — tutor submits their answers; score is auto-calculated.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            app = KYTApplication.objects.get(tutor=request.user)
        except KYTApplication.DoesNotExist:
            return Response({'detail': 'No KYT application found. Submit your documents first.'}, status=404)
        # Strip answer_key before sending to tutor
        questions = [
            {k: v for k, v in q.items() if k != 'answer_key'}
            for q in (app.proficiency_questions or [])
        ]
        return Response({
            'questions': questions,
            'has_questions': bool(questions),
            'already_submitted': app.proficiency_score is not None,
            'score': app.proficiency_score,
        })

    def post(self, request):
        try:
            app = KYTApplication.objects.get(tutor=request.user)
        except KYTApplication.DoesNotExist:
            return Response({'detail': 'No KYT application found.'}, status=404)
        if not app.proficiency_questions:
            return Response({'detail': 'No proficiency test is currently available.'}, status=400)
        answers = request.data.get('answers', [])
        if not isinstance(answers, list):
            return Response({'detail': 'answers must be a list.'}, status=400)
        app.proficiency_answers = answers
        app.proficiency_score = app.calculate_proficiency_score()
        app.save(update_fields=['proficiency_answers', 'proficiency_score'])
        return Response({'score': app.proficiency_score, 'submitted': True})


class KYTSetQuestionsView(APIView):
    """Admin: set the proficiency test questions (applies to all pending applicants)."""
    permission_classes = [IsAdminOrStaff]

    def post(self, request):
        questions = request.data.get('questions', [])
        if not isinstance(questions, list):
            return Response({'detail': 'questions must be a list.'}, status=400)
        # Validate each question has the required fields
        for i, q in enumerate(questions):
            if 'question' not in q or 'options' not in q or 'answer_key' not in q:
                return Response({'detail': f'Question {i+1} must have question, options, and answer_key.'}, status=400)
        # Apply to all applications that have not yet submitted answers
        updated = KYTApplication.objects.filter(proficiency_answers=[]).update(
            proficiency_questions=questions,
            proficiency_score=None,
        )
        return Response({'set': True, 'applications_updated': updated, 'question_count': len(questions)})


class KYTDemoRequestView(APIView):
    """Tutor requests a live demo session inside Tutlee."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            app = KYTApplication.objects.get(tutor=request.user)
        except KYTApplication.DoesNotExist:
            return Response({'detail': 'No KYT application found. Submit your documents first.'}, status=404)
        if app.demo_session_done:
            return Response({'detail': 'Your demo session has already been completed.'})
        app.demo_session_requested = True
        app.save(update_fields=['demo_session_requested'])
        return Response({'requested': True, 'message': 'Your demo session request has been received. The admin team will contact you to schedule it.'})


class KYTMarkDemoView(APIView):
    """Admin: mark a tutor's demo session as completed."""
    permission_classes = [IsAdminOrStaff]

    def post(self, request, pk):
        try:
            app = KYTApplication.objects.get(pk=pk)
        except KYTApplication.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=404)
        app.demo_session_done = True
        app.save(update_fields=['demo_session_done'])
        return Response(KYTApplicationSerializer(app).data)
