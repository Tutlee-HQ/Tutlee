from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from .models import Session, SessionRating
from .serializers import SessionSerializer, BookSessionSerializer, SessionRatingSerializer


class IsAdminOrReadOwn(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        u = request.user
        return u.is_staff or obj.learner == u or obj.tutor == u


class SessionListView(generics.ListAPIView):
    serializer_class = SessionSerializer

    def get_queryset(self):
        u  = self.request.user
        qs = Session.objects.select_related('learner', 'tutor', 'rating')

        if u.is_staff:
            # Admin sees all; supports filters
            status_f  = self.request.query_params.get('status')
            subject_f = self.request.query_params.get('subject')
            q         = self.request.query_params.get('q')
            if status_f:
                qs = qs.filter(status=status_f)
            if subject_f:
                qs = qs.filter(subject__iexact=subject_f)
            if q:
                qs = qs.filter(
                    Q(learner__first_name__icontains=q) |
                    Q(tutor__first_name__icontains=q)   |
                    Q(subject__icontains=q)
                )
        else:
            # Regular user sees only their own sessions
            qs = qs.filter(Q(learner=u) | Q(tutor=u))

        return qs.order_by('-scheduled_at')


class BookSessionView(generics.CreateAPIView):
    serializer_class = BookSessionSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx


class SessionDetailView(generics.RetrieveUpdateAPIView):
    serializer_class   = SessionSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOwn]

    def get_queryset(self):
        return Session.objects.select_related('learner', 'tutor', 'rating')


class StartSessionView(APIView):
    def post(self, request, pk):
        try:
            s = Session.objects.get(pk=pk)
        except Session.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=404)
        if s.tutor != request.user and not request.user.is_staff:
            return Response({'detail': 'Forbidden.'}, status=403)
        s.status = 'live'
        s.save()
        return Response(SessionSerializer(s).data)


def _generate_assessment_questions(subject, topic=''):
    """Generate 5 subject-specific comprehension questions for post-session assessment."""
    t = topic or subject
    return [
        {
            'text': f'Which statement best describes a core concept you worked on in this {t} session?',
            'options': [
                f'A fundamental principle within {subject}',
                'An unrelated concept from a different field',
                f'A technique not applicable to {subject}',
                'None of the above',
            ],
            'answer': 0,
        },
        {
            'text': f'In the context of {t}, which approach most effectively reinforces understanding?',
            'options': [
                'Memorising definitions without applying them',
                'Practising problems that apply the concepts covered',
                'Skipping foundational material and jumping ahead',
                'Reading theory only, without any practice',
            ],
            'answer': 1,
        },
        {
            'text': f'After a session on {t}, what is the best immediate next step?',
            'options': [
                'Move on to a completely new topic immediately',
                'Review your notes and attempt practice questions',
                'Avoid revisiting any of the material',
                'Watch a general video unrelated to the session',
            ],
            'answer': 1,
        },
        {
            'text': f'Which statement about mastering {subject} is most accurate?',
            'options': [
                f'Consistent practice and repetition are essential to mastering {subject}',
                f'{subject} can be fully learned in a single session',
                f'Prior knowledge is never needed for {subject}',
                f'All topics within {subject} are completely independent of each other',
            ],
            'answer': 0,
        },
        {
            'text': f'To improve your performance in {subject}, which action would be most beneficial?',
            'options': [
                'Booking a follow-up session focused on your identified weak areas',
                'Avoiding further practice until the next scheduled session',
                'Relying solely on a textbook without any guided help',
                'Skipping the assessment review and moving forward',
            ],
            'answer': 0,
        },
    ]


class EndSessionView(APIView):
    def post(self, request, pk):
        try:
            s = Session.objects.get(pk=pk)
        except Session.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=404)
        if s.tutor != request.user and not request.user.is_staff:
            return Response({'detail': 'Forbidden.'}, status=403)
        s.status = 'completed'
        s.save()
        # Update tutor session count
        try:
            tp = s.tutor.tutor_profile
            tp.total_sessions += 1
            tp.save()
        except Exception:
            pass
        # Auto-create assessment if one doesn't exist yet
        try:
            from assessments.models import Assessment
            if not Assessment.objects.filter(session=s).exists():
                questions = _generate_assessment_questions(s.subject, s.topic)
                Assessment.objects.create(
                    session=s,
                    learner=s.learner,
                    subject=s.subject,
                    questions=questions,
                )
        except Exception as _ae:
            import sys
            print(f'[ASSESSMENT] auto-create failed: {_ae}', file=sys.stderr)
        return Response(SessionSerializer(s).data)


class RateSessionView(generics.CreateAPIView):
    serializer_class = SessionRatingSerializer

    def perform_create(self, serializer):
        session_id = self.kwargs['pk']
        session    = Session.objects.get(pk=session_id)
        rating     = serializer.save(rater=self.request.user, session=session)
        # Recalculate tutor rating
        try:
            tp    = session.tutor.tutor_profile
            all_r = SessionRating.objects.filter(session__tutor=session.tutor)
            avg   = sum(r.overall for r in all_r) / all_r.count()
            tp.rating       = round(avg, 2)
            tp.rating_count = all_r.count()
            tp.save()
        except Exception:
            pass
