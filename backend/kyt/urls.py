from django.urls import path
from .views import KYTSubmitView, KYTMyApplicationView, KYTListView, KYTApproveView, KYTRejectView

urlpatterns = [
    path('submit/',          KYTSubmitView.as_view(),       name='kyt-submit'),
    path('me/',              KYTMyApplicationView.as_view(), name='kyt-me'),
    path('',                 KYTListView.as_view(),          name='kyt-list'),
    path('<int:pk>/approve/', KYTApproveView.as_view(),      name='kyt-approve'),
    path('<int:pk>/reject/',  KYTRejectView.as_view(),       name='kyt-reject'),
]
