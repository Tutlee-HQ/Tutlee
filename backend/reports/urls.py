from django.urls import path
from .views import ReportCreateView, ReportListView, ReportActionView

urlpatterns = [
    path('',                   ReportCreateView.as_view(), name='report-create'),
    path('all/',               ReportListView.as_view(),   name='report-list'),
    path('<int:pk>/action/',   ReportActionView.as_view(), name='report-action'),
]
