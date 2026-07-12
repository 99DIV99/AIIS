from celery import shared_task
from .utils import generate_daily_summaries, extract_status

@shared_task(name="run_daily_summaries")
def run_daily_summaries():
    generate_daily_summaries()

@shared_task(name="update_user_status_task")
def update_user_status_task(tweet_id):
    extract_status(tweet_id)
