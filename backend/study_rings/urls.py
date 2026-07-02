from django.urls import path
from .views import (
    StudyRingListView, StudyRingDetailView,
    JoinRingView, LeaveRingView, FeatureRingView,
    InviteToRingView, RingPostListView,
)

urlpatterns = [
    path('',                    StudyRingListView.as_view(),   name='ring-list'),
    path('<int:pk>/',           StudyRingDetailView.as_view(), name='ring-detail'),
    path('<int:pk>/join/',      JoinRingView.as_view(),        name='ring-join'),
    path('<int:pk>/leave/',     LeaveRingView.as_view(),       name='ring-leave'),
    path('<int:pk>/feature/',   FeatureRingView.as_view(),     name='ring-feature'),
    path('<int:pk>/invite/',    InviteToRingView.as_view(),    name='ring-invite'),
    path('<int:pk>/posts/',     RingPostListView.as_view(),    name='ring-posts'),
]
