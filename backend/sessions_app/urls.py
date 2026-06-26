from django.urls import path
from .views import (
    SessionListView, BookSessionView, SessionDetailView,
    StartSessionView, EndSessionView, RateSessionView, MessageListView,
)

urlpatterns = [
    path('',              SessionListView.as_view(),  name='session-list'),
    path('book/',         BookSessionView.as_view(),  name='session-book'),
    path('<int:pk>/',     SessionDetailView.as_view(),name='session-detail'),
    path('<int:pk>/start/',    StartSessionView.as_view(),  name='session-start'),
    path('<int:pk>/end/',      EndSessionView.as_view(),    name='session-end'),
    path('<int:pk>/rate/',     RateSessionView.as_view(),   name='session-rate'),
    path('<int:pk>/messages/', MessageListView.as_view(),   name='session-messages'),
]
