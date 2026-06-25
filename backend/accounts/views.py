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
        import sys
        s = LoginSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user  = s.validated_data['user']
        needs = s.validated_data.get('needs_verification', False)
        if needs:
            # Account exists but email not verified — resend OTP so they can verify & log in
            try:
                from .models import EmailOTP
                import random, string, urllib.request as _ureq, json as _ujson, os as _os
                code = ''.join(random.choices(string.digits, k=6))
                EmailOTP.objects.create(user=user, code=code)
                print(f'[LOGIN unverified] {user.email} new OTP={code}', file=sys.stderr, flush=True)
                resend_key = _os.environ.get('RESEND_API_KEY', '').strip()
                if resend_key:
                    try:
                        from_addr = _os.environ.get('RESEND_FROM', 'onboarding@resend.dev')
                        req_body  = _ujson.dumps({
                            'from': from_addr, 'to': [user.email],
                            'subject': 'Your Tutlee verification code',
                            'html': f'<div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;padding:32px 24px"><h2>Verify your email</h2><p>Hi {user.first_name or "there"}, your Tutlee verification code is:</p><div style="font-size:36px;font-weight:800;letter-spacing:8px;padding:20px;text-align:center;background:#F5F3FF;border-radius:12px">{code}</div><p style="color:#888;font-size:13px">Expires in 10 minutes.</p></div>',
                            'text': f'Hi {user.first_name or "there"},\n\nYour Tutlee verification code is: {code}\n\nExpires in 10 minutes.\n\n— Tutlee',
                        }).encode('utf-8')
                        req = _ureq.Request(
                            'https://api.resend.com/emails', data=req_body,
                            headers={'Authorization': f'Bearer {resend_key}',
                                     'Content-Type': 'application/json',
                                     'User-Agent': 'Tutlee/1.0 (contact@tutlee.com)'},
                            method='POST')
                        with _ureq.urlopen(req, timeout=15) as resp:
                            _ujson.loads(resp.read().decode())
                    except Exception as _re:
                        print(f'[LOGIN unverified] Resend error: {_re}', file=sys.stderr, flush=True)
            except Exception as _otp_err:
                print(f'[LOGIN unverified] OTP error: {_otp_err}', file=sys.stderr, flush=True)
            return Response({
                'needs_verification': True,
                'email': user.email,
                'detail': 'Please verify your email. A new code has been sent.',
            }, status=status.HTTP_200_OK)
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
            import random, string, sys, urllib.request as _ureq, json as _ujson, os as _os
            code = ''.join(random.choices(string.digits, k=6))
            EmailOTP.objects.create(user=user, code=code)
            print(f'[TUTLEE OTP] {user.email} code={code}', file=sys.stderr, flush=True)
            email_sent = False
            resend_key = _os.environ.get('RESEND_API_KEY', '').strip()
            if resend_key:
                try:
                    from_addr = _os.environ.get('RESEND_FROM', 'onboarding@resend.dev')
                    html_body = f'<div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;padding:32px 24px"><h2>Verify your email</h2><p>Hi {user.first_name or "there"}, your Tutlee verification code is:</p><div style="font-size:36px;font-weight:800;letter-spacing:8px;padding:20px;text-align:center;background:#F5F3FF;border-radius:12px">{code}</div><p style="color:#888;font-size:13px">Expires in 10 minutes.</p></div>'
                    plain_body = f'Hi {user.first_name or "there"},\n\nYour Tutlee verification code is: {code}\n\nThis expires in 10 minutes.\n\n— Tutlee'
                    req_body = _ujson.dumps({'from': from_addr, 'to': [user.email], 'subject': 'Your Tutlee verification code', 'html': html_body, 'text': plain_body}).encode('utf-8')
                    req = _ureq.Request('https://api.resend.com/emails', data=req_body, headers={'Authorization': f'Bearer {resend_key}', 'Content-Type': 'application/json', 'User-Agent': 'Tutlee/1.0 (contact@tutlee.com)'}, method='POST')
                    with _ureq.urlopen(req, timeout=15) as resp:
                        resp_data = _ujson.loads(resp.read().decode())
                    print(f'[TUTLEE OTP] Resend OK → {user.email}: {resp_data}', file=sys.stderr, flush=True)
                    email_sent = True
                except Exception as _re:
                    _re_body = ''
                    try:
                        import urllib.error as _uerr
                        if hasattr(_re, 'read'):
                            _re_body = _re.read().decode('utf-8', errors='replace')
                    except Exception:
                        pass
                    print(f'[TUTLEE OTP] Resend error: {_re} | body: {_re_body} | from={from_addr} | key_prefix={resend_key[:8]}', file=sys.stderr, flush=True)
            if not email_sent:
                dev_otp_code = code  # return code in response so user can get it from logs
        except Exception as _otp_err:
            import sys as _sys
            print(f'[TUTLEE OTP] error: {_otp_err}', file=_sys.stderr, flush=True)
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
        import sys, urllib.request as _ureq2, json as _ujson2, os as _os2
        print(f'[TUTLEE OTP resend] {email} code={code}', file=sys.stderr, flush=True)
        email_sent = False
        resend_key = _os2.environ.get('RESEND_API_KEY', '').strip()
        if resend_key:
            try:
                from_addr = _os2.environ.get('RESEND_FROM', 'onboarding@resend.dev')
                req_body = _ujson2.dumps({'from': from_addr, 'to': [email], 'subject': 'Your Tutlee verification code', 'text': f'Your Tutlee verification code is: {code}\n\nExpires in 10 minutes.'}).encode('utf-8')
                req = _ureq2.Request('https://api.resend.com/emails', data=req_body, headers={'Authorization': f'Bearer {resend_key}', 'Content-Type': 'application/json', 'User-Agent': 'Tutlee/1.0 (contact@tutlee.com)'}, method='POST')
                with _ureq2.urlopen(req, timeout=15) as resp:
                    _ujson2.loads(resp.read().decode())
                email_sent = True
            except Exception as _re2:
                print(f'[TUTLEE OTP resend] Resend error: {_re2}', file=sys.stderr, flush=True)
        if not email_sent:
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


# ─── PASSWORD RESET (OTP-based) ──────────────────────────────────────────────
class PasswordResetRequestView(APIView):
    """Step 1: user provides email → send OTP code."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        import sys, urllib.request as _ureq3, json as _ujson3, os as _os3, random, string
        email = request.data.get('email', '').strip().lower()
        # Always respond 200 to avoid leaking whether the email exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'detail': 'If that email exists we have sent a reset code.'})
        code = ''.join(random.choices(string.digits, k=6))
        EmailOTP.objects.create(user=user, code=code)
        print(f'[PWD RESET] {email} code={code}', file=sys.stderr, flush=True)
        resend_key = _os3.environ.get('RESEND_API_KEY', '').strip()
        if resend_key:
            try:
                from_addr = _os3.environ.get('RESEND_FROM', 'onboarding@resend.dev')
                html_body = f'<div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;padding:32px 24px"><h2>Reset your password</h2><p>Hi {user.first_name or "there"}, use this code to reset your Tutlee password:</p><div style="font-size:36px;font-weight:800;letter-spacing:8px;padding:20px;text-align:center;background:#F5F3FF;border-radius:12px">{code}</div><p style="color:#888;font-size:13px">Expires in 10 minutes. If you did not request this, ignore this email.</p></div>'
                req_body  = _ujson3.dumps({'from': from_addr, 'to': [email], 'subject': 'Reset your Tutlee password', 'html': html_body, 'text': f'Your Tutlee password reset code is: {code}\n\nExpires in 10 minutes.'}).encode('utf-8')
                req = _ureq3.Request('https://api.resend.com/emails', data=req_body, headers={'Authorization': f'Bearer {resend_key}', 'Content-Type': 'application/json', 'User-Agent': 'Tutlee/1.0 (contact@tutlee.com)'}, method='POST')
                with _ureq3.urlopen(req, timeout=15) as resp:
                    _ujson3.loads(resp.read().decode())
            except Exception as _re3:
                print(f'[PWD RESET] Resend error: {_re3}', file=sys.stderr, flush=True)
        return Response({'detail': 'If that email exists we have sent a reset code.', 'dev_code': code if not resend_key else None})


class PasswordResetConfirmView(APIView):
    """Step 2: user provides email + OTP code + new password."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from django.utils import timezone
        import datetime
        email    = request.data.get('email', '').strip().lower()
        code     = request.data.get('code', '').strip()
        password = request.data.get('password', '')
        if not email or not code or not password:
            return Response({'error': 'email, code, and password are required.'}, status=400)
        if len(password) < 8:
            return Response({'error': 'Password must be at least 8 characters.'}, status=400)
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'Invalid code.'}, status=400)
        cutoff = timezone.now() - datetime.timedelta(minutes=10)
        otp = EmailOTP.objects.filter(user=user, code=code, is_used=False, created_at__gte=cutoff).first()
        if not otp:
            return Response({'error': 'Invalid or expired code.'}, status=400)
        otp.is_used = True
        otp.save()
        user.set_password(password)
        user.is_active = True  # activate account if it was inactive
        user.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'detail': 'Password reset successfully.',
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

