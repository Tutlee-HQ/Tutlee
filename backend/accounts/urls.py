from django.urls import path
from .views import (
    RegisterView, MeView,
    UserListView, UserDetailView, SuspendUserView,
    TutorMatchView, TutorProfileUpdateView, LearnerProfileUpdateView,
    admin_stats,
    SendOTPView, VerifyOTPView, SiteContentView,
    PasswordResetRequestView, PasswordResetConfirmView,
)

urlpatterns = [
    path('register/',          RegisterView.as_view(),          name='register'),
    path('me/',                MeView.as_view(),                name='me'),
    path('me/tutor-profile/',  TutorProfileUpdateView.as_view(), name='tutor-profile'),
    path('me/learner-profile/',LearnerProfileUpdateView.as_view(),name='learner-profile'),
    # AI match
    path('tutors/match/',      TutorMatchView.as_view(),        name='tutor-match'),
    # Admin
    path('users/',             UserListView.as_view(),          name='user-list'),
    path('users/<int:pk>/',    UserDetailView.as_view(),        name='user-detail'),
    path('users/<int:pk>/suspend/', SuspendUserView.as_view(), name='user-suspend'),
    path('stats/',             admin_stats,                     name='admin-stats'),
    path('otp/send/',          SendOTPView.as_view(),         name='otp-send'),
    path('otp/verify/',        VerifyOTPView.as_view(),       name='otp-verify'),
    path('site-content/',       SiteContentView.as_view(),     name='site-content'),
    # Password reset (OTP-based)
    path('password-reset/',         PasswordResetRequestView.as_view(),  name='password-reset-request'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(),  name='password-reset-confirm'),
]

