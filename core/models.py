from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('backend', 'Backend Developer'),
        ('frontend', 'Frontend Developer'),
        ('product_manager', 'Product Manager'),
        ('uiux_designer', 'UIUX Designer'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='backend')
    current_status = models.TextField(blank=True, null=True)
    last_status_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

class Ping(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_pings')
    question = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def __str__(self):
        return f"Ping from {self.sender.username}: {self.question[:30]}"

class PingReply(models.Model):
    ping = models.ForeignKey(Ping, on_delete=models.CASCADE, related_name='replies')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reply = models.CharField(max_length=10, choices=(('yes', 'Yes'), ('no', 'No')))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('ping', 'user')

class Tweet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tweets')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.content[:50]}"

class DailySummary(models.Model):
    SUMMARY_TYPES = (
        ('individual', 'Individual'),
        ('team', 'Team'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='summaries', null=True, blank=True)
    target_date = models.DateField(default=timezone.now)
    summary_type = models.CharField(max_length=20, choices=SUMMARY_TYPES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Daily Summaries"
        unique_together = ('user', 'target_date', 'summary_type')

    def __str__(self):
        return f"{self.summary_type} summary for {self.user.username if self.user else 'Team'} on {self.target_date}"
