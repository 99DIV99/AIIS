from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from .models import Tweet, DailySummary, UserProfile, Ping, PingReply
from .serializers import TweetSerializer, DailySummarySerializer, UserSerializer, PingSerializer, PingReplySerializer
from .utils import generate_daily_summaries
from .tasks import update_user_status_task

class TweetListCreateView(generics.ListCreateAPIView):
    serializer_class = TweetSerializer
    
    def get_queryset(self):
        return Tweet.objects.filter(user=self.request.user).order_by('-created_at')
        
    def perform_create(self, serializer):
        tweet = serializer.save(user=self.request.user)
        update_user_status_task.delay(tweet.id)

class PersonalSummaryView(generics.RetrieveAPIView):
    serializer_class = DailySummarySerializer
    
    def get_object(self):
        today = timezone.now().date()
        return DailySummary.objects.filter(
            user=self.request.user, 
            date=today, 
            summary_type='personal'
        ).first()

class OfficeSummaryView(generics.RetrieveAPIView):
    serializer_class = DailySummarySerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_object(self):
        today = timezone.now().date()
        return DailySummary.objects.filter(
            date=today, 
            summary_type='office'
        ).first()


class SummaryTodayView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        today = timezone.now().date()
        # Get team summary
        team = DailySummary.objects.filter(target_date=today, summary_type='team').first()
        # Get individual summary
        individual = DailySummary.objects.filter(target_date=today, summary_type='individual', user=request.user).first()
        
        return Response({
            "team": DailySummarySerializer(team).data if team else None,
            "individual": DailySummarySerializer(individual).data if individual else None
        })

class SummaryHistoryView(generics.ListAPIView):
    serializer_class = DailySummarySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Return all summaries grouped by date? No, just list them.
        # Usually frontend wants individual history for the user and team history for everyone.
        return DailySummary.objects.filter(
            models.Q(summary_type='team') | models.Q(summary_type='individual', user=self.request.user)
        ).order_by('-target_date', '-created_at')

class GenerateSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            generate_daily_summaries()
            return Response({"detail": "Summaries generated successfully."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GenerateSummaryV1View(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            generate_daily_summaries()
            today = timezone.now().date()
            team = DailySummary.objects.filter(target_date=today, summary_type='team').first()
            individual = DailySummary.objects.filter(target_date=today, summary_type='individual', user=request.user).first()
            
            return Response({
                "detail": "Summaries generated successfully.",
                "team": DailySummarySerializer(team).data if team else None,
                "individual": DailySummarySerializer(individual).data if individual else None
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ProfileView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    
    def get_object(self):
        return self.request.user

class TeamStatusView(generics.ListAPIView):
    serializer_class = UserSerializer
    queryset = User.objects.all().select_related('profile')
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Fallback: Check if any user has a tweet newer than their status update
        # and trigger a manual update if Celery isn't processing them.
        from django.utils import timezone
        from .utils import extract_status
        import threading
        
        users = self.get_queryset()
        for user in users:
            profile, _ = UserProfile.objects.get_or_create(user=user)
            latest_tweet = Tweet.objects.filter(user=user).order_by('-created_at').first()
            
            if latest_tweet:
                # If no status yet OR tweet is newer than last update (with 2s buffer)
                is_stale = not profile.current_status or \
                           (latest_tweet.created_at > profile.last_status_update + timezone.timedelta(seconds=2))
                
                if is_stale:
                    if user == request.user:
                        extract_status(latest_tweet.id)
                    else:
                        threading.Thread(target=extract_status, args=(latest_tweet.id,)).start()

        return super().get(request, *args, **kwargs)

class TeamPingView(APIView):
    def post(self, request):
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer
        
        question = request.data.get('question')
        if not question:
            return Response({"detail": "Question is required."}, status=status.HTTP_400_BAD_REQUEST)
            
        expires_at = timezone.now() + timezone.timedelta(seconds=60)
        ping = Ping.objects.create(
            sender=request.user,
            question=question,
            expires_at=expires_at
        )
        
        serializer = PingSerializer(ping)
        
        # Broadcast to team
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "team_ping",
            {
                "type": "team_ping_message",
                "data": serializer.data
            }
        )
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class TeamPingReplyView(APIView):
    def post(self, request):
        ping_id = request.data.get('ping_id')
        reply_text = request.data.get('reply') # 'yes' or 'no'
        
        try:
            ping = Ping.objects.get(id=ping_id)
        except Ping.DoesNotExist:
            return Response({"detail": "Ping not found."}, status=status.HTTP_404_NOT_FOUND)
            
        if timezone.now() > ping.expires_at:
            return Response({"detail": "Ping has expired."}, status=status.HTTP_410_GONE)
            
        reply, created = PingReply.objects.update_or_create(
            ping=ping,
            user=request.user,
            defaults={'reply': reply_text}
        )
        
        return Response({"detail": "Reply recorded."}, status=status.HTTP_200_OK)

class SummaryStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        today = timezone.now().date()
        total_summaries = DailySummary.objects.filter(
            models.Q(summary_type='team') | models.Q(summary_type='individual', user=request.user)
        ).count()
        
        individual_count = DailySummary.objects.filter(summary_type='individual', user=request.user).count()
        team_count = DailySummary.objects.filter(summary_type='team').count()
        
        has_today_individual = DailySummary.objects.filter(target_date=today, summary_type='individual', user=request.user).exists()
        has_today_team = DailySummary.objects.filter(target_date=today, summary_type='team').exists()
        
        # New: Activity count for today
        today_updates_count = Tweet.objects.filter(user=request.user, created_at__date=today).count()
        
        return Response({
            "total_count": total_summaries,
            "individual_count": individual_count,
            "team_count": team_count,
            "has_today_individual": has_today_individual,
            "has_today_team": has_today_team,
            "today_updates_count": today_updates_count
        })
