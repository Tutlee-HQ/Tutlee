from django.urls import path
from .views import (
    TransactionListView, RequestPayoutView,
    PayoutListView, ApprovePayoutView, DeclinePayoutView, RevenueStatsView,
)

urlpatterns = [
    path('transactions/',            TransactionListView.as_view(), name='transactions'),
    path('request-payout/',          RequestPayoutView.as_view(),   name='request-payout'),
    path('payouts/',                 PayoutListView.as_view(),      name='payout-list'),
    path('payouts/<int:pk>/approve/', ApprovePayoutView.as_view(),  name='payout-approve'),
    path('payouts/<int:pk>/decline/', DeclinePayoutView.as_view(),  name='payout-decline'),
    path('stats/',                   RevenueStatsView.as_view(),    name='revenue-stats'),
]
