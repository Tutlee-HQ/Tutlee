from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import StudyRing, RingPost
from .serializers import StudyRingSerializer, RingPostSerializer
from accounts.permissions import IsAdminOrStaff


class StudyRingListView(generics.ListCreateAPIView):
    serializer_class = StudyRingSerializer

    def get_permissions(self):
        # Anyone can browse rings; only authenticated users can create
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        qs = StudyRing.objects.prefetch_related('members').filter(is_active=True)
        subject = self.request.query_params.get('subject')
        if subject:
            qs = qs.filter(subject__icontains=subject)
        return qs

    def perform_create(self, serializer):
        ring = serializer.save(creator=self.request.user)
        ring.members.add(self.request.user)


class StudyRingDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = StudyRingSerializer
    queryset         = StudyRing.objects.prefetch_related('members')

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH', 'DELETE'):
            return [IsAdminOrStaff()]
        return [permissions.AllowAny()]


class JoinRingView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            ring = StudyRing.objects.get(pk=pk)
        except StudyRing.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=404)
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


class RingPostListView(generics.ListCreateAPIView):
    serializer_class = RingPostSerializer

    def get_queryset(self):
        return RingPost.objects.filter(ring_id=self.kwargs['pk']).select_related('author')

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, ring_id=self.kwargs['pk'])
