from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Q
from .models import User, TutorProfile, LearnerProfile
from .serializers import (
    UserSerializer, RegisterSerializer, LoginSerializer,
    TutorProfileSerializer, LearnerProfileSerializer, PublicTutorSerializer,
)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        s = LoginSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user    = s.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response({
            'access':  str(refresh.access_token),
            'refresh': str(refresh),
            'user':    UserSerializer(user).data,
        })


class RegisterView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class   = RegisterSerializer

    def create(self, request, *args, **kwargs):
        import sys
        # ── warm DB connection on THIS worker before any ORM call ──────────
        try:
            from django.db import connection as _dbc
            with _dbc.cursor() as _cur:
                _cur.execute('SELECT 1')
        except Exception as _db_w_err:
            print(f'[REGISTER] DB warmup err: {_db_w_err}', file=sys.stderr, flush=True)

        try:
            return self._do_register(request, *args, **kwargs)
        except Exception as _top_err:
            import traceback
            print(f'[REGISTER] top-level crash: {_top_err}', file=sys.stderr, flush=True)
            traceback.print_exc(file=sys.stderr)
            # Always return JSON — never let the worker drop the connection
            from rest_framework.response import Response as _Rsp
            from rest_framework import status as _st
            _r = _Rsp({'detail': str(_top_err)}, status=_st.HTTP_500_INTERNAL_SERVER_ERROR)
            _r['Access-Control-Allow-Origin'] = '*'
            return _r

    def _do_register(self, request, *args, **kwargs):
        import sys
        email = (request.data.get('email') or '').strip().lower()
        print(f'[REGISTER] attempt for {email}', file=sys.stderr, flush=True)
        # Idempotent: if account exists but not yet verified, just resend OTP
        existing = None
        try:
            existing = User.objects.get(email=email)
        except User.DoesNotExist:
            pass
        if existing is not None:
            # Always resend OTP — account may exist from a timed-out previous attempt
            user = existing
        else:
            s = self.get_serializer(data=request.data)
            s.is_valid(raise_exception=True)
            user = s.save()
        # Generate and send OTP for email verification
        dev_otp_code = None
        try:
            from .models import EmailOTP
            import random, string, django.conf
            code = ''.join(random.choices(string.digits, k=6))
            EmailOTP.objects.create(user=user, code=code)
            from django.core.mail import send_mail
            email_sent = False
            try:
                send_mail(
                    subject='Welcome to Tutlee — verify your email',
                    message=(
                        f'Hi {user.first_name},\n\n'
                        f'Your verification code is: {code}\n\n'
                        f'Enter this in the app to complete your signup.\n\n'
                        f'The code expires in 10 minutes.\n\n'
                        f'— Tutlee'
                    ),
                    from_email=django.conf.settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                email_sent = True
            except Exception as _email_err:
                import sys
                print(f'[TUTLEE] OTP email failed: {_email_err}', file=sys.stderr)
            # Return the code when email could not be sent so the UI can auto-fill it
            if not email_sent or django.conf.settings.DEBUG:
                dev_otp_code = code
        except Exception:
            pass  # never block registration
        refresh = RefreshToken.for_user(user)
        resp = {
            'access':  str(refresh.access_token),
            'refresh': str(refresh),
            'user':    UserSerializer(user).data,
            'email_verification_required': True,
        }
        if dev_otp_code is not None:
            resp['dev_otp_code'] = dev_otp_code
        return Response(resp, status=status.HTTP_201_CREATED)


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class UserListView(generics.ListAPIView):
    """Admin: list all users with optional role filter."""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        qs   = User.objects.select_related('tutor_profile', 'learner_profile').order_by('-created_at')
        role = self.request.query_params.get('role')
        q    = self.request.query_params.get('q')
        if role:
            qs = qs.filter(role=role)
        if q:
            qs = qs.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(email__icontains=q))
        return qs


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class   = UserSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset           = User.objects.select_related('tutor_profile', 'learner_profile')


class SuspendUserView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=404)
        user.is_suspended = not user.is_suspended
        user.save()
        return Response({'is_suspended': user.is_suspended})


class TutorMatchView(generics.ListAPIView):
    """AI match: return tutors filtered by subject and weak areas."""
    serializer_class   = PublicTutorSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        subject    = self.request.query_params.get('subject', '')
        weak_areas = self.request.query_params.getlist('weak_areas')
        qs = User.objects.filter(
            role__in=['tutor', 'both'],
            is_suspended=False,
            tutor_profile__isnull=False,
        ).select_related('tutor_profile').order_by('-tutor_profile__rating')

        if subject:
            # Filter tutors whose subjects contain the requested subject
            qs = [u for u in qs if subject in (u.tutor_profile.subjects or [])]

        if weak_areas:
            # Further filter by tutors whose specialities overlap with requested weak areas
            def overlaps(u):
                specs = set(u.tutor_profile.specialities or [])
                return bool(specs & set(weak_areas))
            qs = [u for u in qs if overlaps(u)]

        return qs


class TutorProfileUpdateView(generics.UpdateAPIView):
    serializer_class = TutorProfileSerializer

    def get_object(self):
        return self.request.user.tutor_profile


class LearnerProfileUpdateView(generics.UpdateAPIView):
    serializer_class = LearnerProfileSerializer

    def get_object(self):
        return self.request.user.learner_profile


@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def admin_stats(request):
    """Quick KPI numbers for admin dashboard."""
    from sessions_app.models import Session
    from kyt.models import KYTApplication
    from payments.models import Transaction
    from django.utils import timezone
    from django.db.models import Sum
    import datetime

    today = timezone.now().date()
    month_start = today.replace(day=1)

    total_users        = User.objects.count()
    active_sessions    = Session.objects.filter(status='live').count()
    kyt_pending        = KYTApplication.objects.filter(status='pending').count()
    monthly_revenue    = Transaction.objects.filter(
        type='session_payment',
        created_at__date__gte=month_start,
        status='settled',
    ).aggregate(total=Sum('amount'))['total'] or 0

    return Response({
        'total_users':     total_users,
        'active_sessions': active_sessions,
        'kyt_pending':     kyt_pending,
        'monthly_revenue': float(monthly_revenue),
    })


# ─── OTP VERIFICATION ────────────────────────────────────────────────────────
import random
import string
from django.core.mail import send_mail
from django.conf import settings as django_settings
from .models import EmailOTP, SiteContent


def generate_otp():
    return ''.join(random.choices(string.digits, k=6))


class SendOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'No account found with that email.'}, status=404)
        code = generate_otp()
        EmailOTP.objects.create(user=user, code=code)
        try:
            send_mail(
                subject='Your Tutlee verification code',
                message=f'Your verification code is: {code}\n\nThis code expires in 10 minutes.',
                from_email=django_settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception as e:
            import sys
            print(f'[TUTLEE] SendOTP email failed: {e}', file=sys.stderr)
            return Response({'detail': 'OTP sent', 'dev_otp_code': str(code)})
        return Response({'detail': 'OTP sent to ' + email})


class VerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        code  = request.data.get('code', '').strip()
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'No account found.'}, status=404)
        from django.utils import timezone
        import datetime
        cutoff = timezone.now() - datetime.timedelta(minutes=10)
        otp = EmailOTP.objects.filter(user=user, code=code, is_used=False, created_at__gte=cutoff).first()
        if not otp:
            return Response({'error': 'Invalid or expired code.'}, status=400)
        otp.is_used = True
        otp.save()
        user.is_active = True
        user.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'detail': 'Email verified',
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
        })


# ─── SITE CONTENT (CMS) ─────────────────────────────────────────────────────
class SiteContentView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

    def get(self, request, key='homepage'):
        try:
            obj = SiteContent.objects.get(key=key)
            return Response({'key': obj.key, 'content': obj.content, 'updated_at': obj.updated_at})
        except SiteContent.DoesNotExist:
            return Response({'key': key, 'content': '{}'})

    def post(self, request, key='homepage'):
        key = request.data.get('key', key)
        content = request.data.get('content', '{}')
        obj, _ = SiteContent.objects.update_or_create(key=key, defaults={'content': content})
        return Response({'key': obj.key, 'updated_at': obj.updated_at})

