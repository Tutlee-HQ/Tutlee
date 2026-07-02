from django.core.mail import send_mail
from django.conf import settings as django_settings
from django.db.models import Q
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import StudyRing, RingPost
from .serializers import StudyRingSerializer, RingPostSerializer
from accounts.permissions import IsAdminOrStaff


class StudyRingListView(generics.ListCreateAPIView):
    serializer_class = StudyRingSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        qs = StudyRing.objects.prefetch_related('members', 'invited_members').filter(is_active=True)
        subject = self.request.query_params.get('subject')
        if subject:
            qs = qs.filter(subject__icontains=subject)
        if user.is_authenticated:
            # Show public rings + private rings where user is creator or invited
            qs = qs.filter(
                Q(is_private=False) |
                Q(creator=user) |
                Q(invited_members=user) |
                Q(members=user)
            ).distinct()
        else:
            qs = qs.filter(is_private=False)
        return qs

    def perform_create(self, serializer):
        ring = serializer.save(creator=self.request.user)
        ring.members.add(self.request.user)


class StudyRingDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = StudyRingSerializer
    queryset         = StudyRing.objects.prefetch_related('members', 'invited_members')

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH', 'DELETE'):
            return [IsAdminOrStaff()]
        return [permissions.AllowAny()]

    def get_object(self):
        obj = super().get_object()
        # Block access to private rings for non-members/non-invited
        if obj.is_private:
            user = self.request.user
            if not user.is_authenticated:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('This is a private ring.')
            if not (
                obj.creator_id == user.pk or
                obj.members.filter(pk=user.pk).exists() or
                obj.invited_members.filter(pk=user.pk).exists()
            ):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('You have not been invited to this private ring.')
        return obj


class JoinRingView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            ring = StudyRing.objects.get(pk=pk)
        except StudyRing.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=404)
        # Private ring — must be invited or creator
        if ring.is_private and ring.creator_id != request.user.pk:
            if not ring.invited_members.filter(pk=request.user.pk).exists():
                return Response({'detail': 'You need an invite to join this private ring.'}, status=403)
        ring.members.add(request.user)
        return Response({'joined': True, 'member_count': ring.member_count})


class LeaveRingView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            ring = StudyRing.objects.get(pk=pk)
        except StudyRing.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=404)
        ring.members.remove(request.user)
        return Response({'joined': False, 'member_count': ring.member_count})


class FeatureRingView(APIView):
    permission_classes = [IsAdminOrStaff]

    def post(self, request, pk):
        try:
            ring = StudyRing.objects.get(pk=pk)
        except StudyRing.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=404)
        ring.is_featured = not ring.is_featured
        ring.save()
        return Response({'is_featured': ring.is_featured})


class InviteToRingView(APIView):
    """Creator sends invite to an existing platform user by email or username."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            ring = StudyRing.objects.get(pk=pk)
        except StudyRing.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=404)

        if ring.creator_id != request.user.pk:
            return Response({'detail': 'Only the ring creator can invite members.'}, status=403)

        identifier = (request.data.get('email_or_username') or '').strip()
        if not identifier:
            return Response({'detail': 'Provide an email or username.'}, status=400)

        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            invitee = User.objects.get(Q(email=identifier) | Q(username=identifier))
        except User.DoesNotExist:
            return Response({'detail': 'No Tutlee account found for that email or username.'}, status=404)
        except User.MultipleObjectsReturned:
            invitee = User.objects.filter(Q(email=identifier) | Q(username=identifier)).first()

        if ring.members.filter(pk=invitee.pk).exists():
            return Response({'detail': f'{invitee.full_name or invitee.email} is already a member.'}, status=400)

        ring.invited_members.add(invitee)

        # Send email notification
        invite_url = f'https://tutlee.com/?ring={ring.pk}'
        try:
            send_mail(
                subject='You\'re invited to join "{}" on Tutlee'.format(ring.name),
                message=(
                    'Hi {},\n\n{} has invited you to join the study ring "{}" ({}) on Tutlee.\n\n'
                    'Click the link below to join:\n{}\n\nSee you there!'
                ).format(
                    invitee.first_name or 'there',
                    request.user.full_name or request.user.email,
                    ring.name, ring.subject, invite_url
                ),
                from_email=django_settings.DEFAULT_FROM_EMAIL,
                recipient_list=[invitee.email],
                fail_silently=True,
            )
        except Exception:
            pass  # email failure must not block the API response

        return Response({
            'invited': True,
            'invitee': {'id': invitee.pk, 'full_name': invitee.full_name or invitee.email, 'email': invitee.email},
        })


class RingPostListView(generics.ListCreateAPIView):
    serializer_class = RingPostSerializer

    def get_queryset(self):
        return RingPost.objects.filter(ring_id=self.kwargs['pk']).select_related('author')

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, ring_id=self.kwargs['pk'])
