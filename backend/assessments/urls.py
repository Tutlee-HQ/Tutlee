from django.urls import path
from .views import AssessmentListView, AssessmentDetailView, SubmitAssessmentView, AssessmentStatsView

urlpatterns = [
    path('',              AssessmentListView.as_view(),  name='assessment-list'),
    path('stats/',        AssessmentStatsView.as_view(), name='assessment-stats'),
    path('<int:pk>/',     AssessmentDetailView.as_view(),name='assessment-detail'),
    path('<int:pk>/submit/', SubmitAssessmentView.as_view(), name='assessment-submit'),
]
