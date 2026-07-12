from django.urls import path
from .views import TweetListCreateView, PersonalSummaryView, OfficeSummaryView, GenerateSummaryView, ProfileView, TeamStatusView, TeamPingView, TeamPingReplyView, SummaryTodayView, SummaryHistoryView, GenerateSummaryV1View, SummaryStatsView

urlpatterns = [
    path('tweets/', TweetListCreateView.as_view(), name='tweet-list-create'),
    path('me/', ProfileView.as_view(), name='user-profile'),
    path('team-status/', TeamStatusView.as_view(), name='team-status'),
    path('team-ping/', TeamPingView.as_view(), name='team-ping'),
    path('team-ping/reply/', TeamPingReplyView.as_view(), name='team-ping-reply'),
    path('summary/me/', PersonalSummaryView.as_view(), name='personal-summary'),
    path('summary/office/', OfficeSummaryView.as_view(), name='office-summary'),
    path('summary/generate/', GenerateSummaryView.as_view(), name='generate-summary'),
    
    # API v1
    path('v1/summary/today/', SummaryTodayView.as_view(), name='summary-today-v1'),
    path('v1/summary/history/', SummaryHistoryView.as_view(), name='summary-history-v1'),
    path('v1/summary/generate/', GenerateSummaryV1View.as_view(), name='summary-generate-v1'),
    path('v1/summary/stats/', SummaryStatsView.as_view(), name='summary-stats-v1'),
]
