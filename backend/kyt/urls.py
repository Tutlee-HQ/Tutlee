from django.urls import path
from .views import (
    KYTSubmitView, KYTMyApplicationView, KYTListView,
    KYTApproveView, KYTRejectView,
    KYTProficiencyView, KYTSetQuestionsView,
    KYTDemoRequestView, KYTMarkDemoView,
)

urlpatterns = [
    path('submit/',                 KYTSubmitView.as_view(),        name='kyt-submit'),
    path('me/',                     KYTMyApplicationView.as_view(), name='kyt-me'),
    path('',                        KYTListView.as_view(),          name='kyt-list'),
    path('<int:pk>/approve/',       KYTApproveView.as_view(),       name='kyt-approve'),
    path('<int:pk>/reject/',        KYTRejectView.as_view(),        name='kyt-reject'),
    path('proficiency/',            KYTProficiencyView.as_view(),   name='kyt-proficiency'),
    path('proficiency/set/',        KYTSetQuestionsView.as_view(),  name='kyt-set-questions'),
    path('demo/request/',           KYTDemoRequestView.as_view(),   name='kyt-demo-request'),
    path('<int:pk>/demo/complete/', KYTMarkDemoView.as_view(),      name='kyt-demo-complete'),
]
