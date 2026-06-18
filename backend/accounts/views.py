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
        # Generate and send OTP for email verification via Resend
        try:
            from .models import EmailOTP
            import random, string
            code = ''.join(random.choices(string.digits, k=6))
            EmailOTP.objects.create(user=user, code=code)
            _send_otp_email(user.email, user.first_name or 'there', code)
        except Exception:
            pass  # never block registration
        refresh = RefreshToken.for_user(user)
        resp = {
            'access':  str(refresh.access_token),
            'refresh': str(refresh),
            'user':    UserSerializer(user).data,
            'email_verification_required': True,
        }
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
import os
import json
import urllib.request
from django.conf import settings as django_settings
from .models import EmailOTP, SiteContent


def generate_otp():
    return ''.join(random.choices(string.digits, k=6))


def _send_otp_email(to_email, first_name, code):
    """
    Send OTP email via Resend (official SDK) or SMTP fallback.
    Returns True on success, False on failure.
    """
    import sys

    subject = 'Your Tutlee verification code'
    html_body = f"""<div style="font-family:'Segoe UI',Arial,sans-serif;max-width:480px;margin:0 auto;padding:32px 24px;background:#fff;border-radius:16px;border:1px solid #EDE9FE">
      <div style="text-align:center;margin-bottom:24px">
        <div style="display:inline-block;background:#7C3AED;border-radius:10px;padding:10px 18px">
          <span style="color:#fff;font-size:20px;font-weight:800;letter-spacing:-.4px">Tut<span style="color:#4ADE80">lee</span></span>
        </div>
      </div>
      <h2 style="font-size:22px;font-weight:800;color:#0F0720;margin:0 0 8px">Verify your email</h2>
      <p style="font-size:14px;color:#6456A0;margin:0 0 24px">Hi {first_name}, use the code below to complete your signup:</p>
      <div style="background:#F5F3FF;border:2px solid #7C3AED;border-radius:12px;padding:20px;text-align:center;margin-bottom:24px">
        <span style="font-size:36px;font-weight:800;color:#7C3AED;letter-spacing:8px">{code}</span>
      </div>
      <p style="font-size:13px;color:#8B7EC0;margin:0">This code expires in 10 minutes. If you didn't create a Tutlee account, ignore this email.</p>
    </div>"""
    plain_body = f'Hi {first_name},\n\nYour Tutlee verification code is: {code}\n\nThis code expires in 10 minutes.\n\n— Tutlee'

    # ── 1. Try Resend SDK ────────────────────────────────────────────────────
    resend_key = os.environ.get('RESEND_API_KEY', '').strip()
    if resend_key:
        try:
            import resend as resend_sdk
            resend_sdk.api_key = resend_key
            from_addr = os.environ.get('RESEND_FROM', 'onboarding@resend.dev')
            params = {
                'from': from_addr,
                'to': [to_email],
                'subject': subject,
                'html': html_body,
                'text': plain_body,
            }
            resp = resend_sdk.Emails.send(params)
            print(f'[TUTLEE] Resend SDK OK → {to_email}: {resp}', file=sys.stderr)
            return True
        except Exception as resend_err:
            print(f'[TUTLEE] Resend SDK error ({type(resend_err).__name__}): {resend_err}', file=sys.stderr)

    # ── 2. Fall back to Django SMTP ──────────────────────────────────────────
    smtp_user = os.environ.get('EMAIL_HOST_USER', '').strip()
    smtp_pass = os.environ.get('EMAIL_HOST_PASSWORD', '').strip()
    if smtp_user and smtp_pass:
        try:
            from django.core.mail import send_mail
            send_mail(
                subject=subject,
                message=plain_body,
                from_email=django_settings.DEFAULT_FROM_EMAIL,
                recipient_list=[to_email],
                fail_silently=False,
                html_message=html_body,
            )
            print(f'[TUTLEE] SMTP OK → {to_email}', file=sys.stderr)
            return True
        except Exception as smtp_err:
            print(f'[TUTLEE] SMTP error ({type(smtp_err).__name__}): {smtp_err}', file=sys.stderr)

    print('[TUTLEE] No email provider configured — check RESEND_API_KEY in Render', file=sys.stderr)
    return False


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
        user_name = user.first_name or 'there'
        ok = _send_otp_email(email, user_name, code)
        if not ok:
            return Response({'detail': 'OTP sent'})
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



# ─── PASSWORD RESET ──────────────────────────────────────────────────────────
class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        import sys, secrets
        email = request.data.get('email', '').strip().lower()
        print(f'[TUTLEE] Password reset requested for: {email}', file=sys.stderr)
        # Always return 200 to avoid leaking whether email exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            print(f'[TUTLEE] Password reset: user not found for {email}', file=sys.stderr)
            return Response({'detail': 'If that email exists, a reset link has been sent.'})

        from .models import PasswordResetToken
        token = secrets.token_urlsafe(32)
        PasswordResetToken.objects.create(user=user, token=token)

        # Build reset URL — points to the frontend
        frontend = os.environ.get('FRONTEND_URL', 'https://tutlee-hq.github.io')
        reset_url = f'{frontend}/?reset={token}'
        print(f'[TUTLEE] Password reset URL: {reset_url}', file=sys.stderr)

        subject = 'Reset your Tutlee password'
        html_body = f"""<div style="font-family:'Segoe UI',Arial,sans-serif;max-width:480px;margin:0 auto;padding:32px 24px;background:#fff;border-radius:16px;border:1px solid #EDE9FE">
  <div style="text-align:center;margin-bottom:24px">
    <div style="display:inline-block;background:#7C3AED;border-radius:10px;padding:10px 18px">
      <span style="color:#fff;font-size:20px;font-weight:800;letter-spacing:-.4px">Tut<span style="color:#4ADE80">lee</span></span>
    </div>
  </div>
  <h2 style="font-size:22px;font-weight:800;color:#0F0720;margin:0 0 8px">Reset your password</h2>
  <p style="font-size:14px;color:#6456A0;margin:0 0 24px">Hi {user.first_name or 'there'}, click the button below to set a new password. This link expires in 1 hour.</p>
  <div style="text-align:center;margin-bottom:24px">
    <a href="{reset_url}" style="display:inline-block;background:#7C3AED;color:#fff;text-decoration:none;padding:14px 32px;border-radius:10px;font-size:15px;font-weight:700">Reset my password</a>
  </div>
  <p style="font-size:13px;color:#8B7EC0;margin:0">If you didn't request this, you can safely ignore this email. Your password won't change.</p>
</div>"""
        plain_body = (f"Hi {user.first_name or 'there'},\n\n"
                      f"Click this link to reset your Tutlee password:\n{reset_url}\n\n"
                      "This link expires in 1 hour. If you didn't request this, ignore this email.\n\n"
                      "— Tutlee")

        resend_key = os.environ.get('RESEND_API_KEY', '').strip()
        print(f'[TUTLEE] RESEND_API_KEY present: {bool(resend_key)}', file=sys.stderr)
        if resend_key:
            try:
                import resend as resend_sdk
                resend_sdk.api_key = resend_key
                from_addr = os.environ.get('RESEND_FROM', 'onboarding@resend.dev')
                print(f'[TUTLEE] Sending reset email from {from_addr} to {email}', file=sys.stderr)
                resp = resend_sdk.Emails.send({'from': from_addr, 'to': [email], 'subject': subject, 'html': html_body, 'text': plain_body})
                print(f'[TUTLEE] Password reset email sent → {email}: {resp}', file=sys.stderr)
            except Exception as e:
                print(f'[TUTLEE] Password reset email error ({type(e).__name__}): {e}', file=sys.stderr)
        else:
            print('[TUTLEE] RESEND_API_KEY not set — reset email NOT sent', file=sys.stderr)

        return Response({'detail': 'If that email exists, a reset link has been sent.'})


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from django.utils import timezone
        import datetime
        from .models import PasswordResetToken
        token_str = request.data.get('token', '').strip()
        password  = request.data.get('password', '').strip()

        if not token_str or not password:
            return Response({'detail': 'Token and password are required.'}, status=400)
        if len(password) < 8:
            return Response({'detail': 'Password must be at least 8 characters.'}, status=400)

        cutoff = timezone.now() - datetime.timedelta(hours=1)
        try:
            reset = PasswordResetToken.objects.get(token=token_str, is_used=False, created_at__gte=cutoff)
        except PasswordResetToken.DoesNotExist:
            return Response({'detail': 'This reset link is invalid or has expired. Please request a new one.'}, status=400)

        reset.user.set_password(password)
        reset.user.save()
        reset.is_used = True
        reset.save()

        return Response({'detail': 'Password updated successfully.'})
