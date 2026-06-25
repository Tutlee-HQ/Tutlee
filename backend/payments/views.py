from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
from django.db.models import Sum
from django.utils import timezone
import uuid
from .models import Transaction, PayoutRequest
from .serializers import TransactionSerializer, PayoutRequestSerializer
from accounts.permissions import IsAdminOrStaff


class TransactionListView(generics.ListAPIView):
    serializer_class = TransactionSerializer

    def get_queryset(self):
        u = self.request.user
        if u.is_staff:
            return Transaction.objects.select_related('user').order_by('-created_at')
        return Transaction.objects.filter(user=u).order_by('-created_at')


class RequestPayoutView(APIView):
    """Tutor requests a payout of their current balance."""
    def post(self, request):
        try:
            tp = request.user.tutor_profile
        except Exception:
            return Response({'detail': 'Tutor profile not found.'}, status=400)

        if tp.balance <= 0:
            return Response({'detail': 'No balance to pay out.'}, status=400)

        fee_pct = getattr(settings, 'PLATFORM_FEE_PERCENT', 15)
        gross   = float(tp.balance)
        fee     = round(gross * fee_pct / 100, 2)
        net     = round(gross - fee, 2)

        # Count sessions not yet paid out
        from sessions_app.models import Session
        sessions_count = Session.objects.filter(tutor=request.user, status='completed').count()

        payout = PayoutRequest.objects.create(
            tutor          = request.user,
            sessions_count = sessions_count,
            gross          = gross,
            platform_fee   = fee,
            net            = net,
        )
        return Response(PayoutRequestSerializer(payout).data, status=201)


class PayoutListView(generics.ListAPIView):
    serializer_class   = PayoutRequestSerializer
    permission_classes = [IsAdminOrStaff]

    def get_queryset(self):
        qs = PayoutRequest.objects.select_related('tutor').order_by('-created_at')
        s  = self.request.query_params.get('status')
        if s:
            qs = qs.filter(status=s)
        return qs


class ApprovePayoutView(APIView):
    permission_classes = [IsAdminOrStaff]

    def post(self, request, pk):
        try:
            p = PayoutRequest.objects.get(pk=pk)
        except PayoutRequest.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=404)
        p.status      = 'approved'
        p.reviewed_by = request.user
        p.reviewed_at = timezone.now()
        p.save()
        # Zero out tutor balance
        try:
            p.tutor.tutor_profile.balance = 0
            p.tutor.tutor_profile.save()
        except Exception:
            pass
        # Create a payout transaction record
        Transaction.objects.create(
            user      = p.tutor,
            type      = 'payout',
            amount    = p.net,
            reference = f'PAYOUT-{p.id}-{uuid.uuid4().hex[:8].upper()}',
            status    = 'settled',
        )
        return Response(PayoutRequestSerializer(p).data)


class DeclinePayoutView(APIView):
    permission_classes = [IsAdminOrStaff]

    def post(self, request, pk):
        try:
            p = PayoutRequest.objects.get(pk=pk)
        except PayoutRequest.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=404)
        p.status      = 'declined'
        p.reviewed_by = request.user
        p.reviewed_at = timezone.now()
        p.save()
        return Response(PayoutRequestSerializer(p).data)


class RevenueStatsView(APIView):
    permission_classes = [IsAdminOrStaff]

    def get(self, request):
        from django.utils import timezone
        today = timezone.now().date()
        month_start = today.replace(day=1)

        collected = Transaction.objects.filter(
            type='session_payment', status='settled',
            created_at__date__gte=month_start,
        ).aggregate(t=Sum('amount'))['t'] or 0

        pending_payouts = PayoutRequest.objects.filter(
            status='pending'
        ).aggregate(t=Sum('net'))['t'] or 0

        fees = Transaction.objects.filter(
            type='platform_fee', status='settled',
            created_at__date__gte=month_start,
        ).aggregate(t=Sum('amount'))['t'] or 0

        paid_out = Transaction.objects.filter(
            type='payout', status='settled',
        ).aggregate(t=Sum('amount'))['t'] or 0

        return Response({
            'monthly_revenue':  float(collected),
            'pending_payouts':  float(pending_payouts),
            'platform_fees':    float(fees),
            'total_paid_out':   float(paid_out),
        })
