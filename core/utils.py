from google import genai
from groq import Groq
import requests
import json
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from .models import Tweet, DailySummary, UserProfile

def call_llm(prompt):
    """
    Attempts to generate content using Gemini first, 
    with a fallback to Groq if Gemini fails.
    """
    # 1. Try Gemini
    try:
        print("Attempting Gemini...")
        gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
        
        # Determine model
        available_models = [m.name for m in gemini_client.models.list() if 'flash' in m.name.lower()]
        if 'models/gemini-2.0-flash' in available_models:
            model_name = 'gemini-2.0-flash'
        elif 'models/gemini-1.5-flash' in available_models:
            model_name = 'gemini-1.5-flash'
        elif available_models:
            model_name = available_models[0].replace('models/', '')
        else:
            model_name = 'gemini-1.5-flash'

        response = gemini_client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        content = response.text.strip()
        if content:
            print(f"Gemini Success using {model_name}.")
            return content
    except Exception as e:
        print(f"Gemini failed: {e}")

    # 2. Try Groq Fallback
    try:
        print("Attempting Groq fallback...")
        groq_client = Groq(api_key=settings.GROQ_API_KEY)
        
        # Using llama3-70b-8192 as a reliable fallback
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama3-70b-8192",
        )
        content = chat_completion.choices[0].message.content.strip()
        if content:
            print("Groq Success!")
            return content
    except Exception as e:
        print(f"Groq failed: {e}")

    # 3. Try OpenRouter Fallback
    try:
        print("Attempting OpenRouter fallback...")
        api_key = getattr(settings, 'OPENROUTER_API_KEY', None)
        if not api_key:
             # Fallback to direct env fetch if settings didn't reload yet
             import os
             api_key = os.getenv('OPENROUTER_API_KEY')
             
        if api_key:
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                },
                data=json.dumps({
                    "model": "deepseek/deepseek-r1-0528:free",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ]
                })
            )
            if response.status_code == 200:
                content = response.json()['choices'][0]['message']['content'].strip()
                if content:
                    print("OpenRouter Success!")
                    return content
            else:
                print(f"OpenRouter API error: {response.status_code} - {response.text}")
        else:
            print("OpenRouter API key not found.")
    except Exception as e:
        print(f"OpenRouter failed: {e}")

    return None

def generate_daily_summaries():
    print("Starting summary generation with Multi-LLM failover and role awareness...")
    
    today = timezone.now().date()
    all_users = User.objects.all()
    print(f"Checking for tweets on {today} for {all_users.count()} users.")
    
    office_tweets = []
    
    for user in all_users:
        user_tweets = Tweet.objects.filter(user=user, created_at__date=today)
        print(f"User {user.username}: found {user_tweets.count()} tweets.")
        if not user_tweets.exists():
            continue
            
        tweet_contents = [t.content for t in user_tweets]
        # Lazily ensure profile exists
        profile, _ = UserProfile.objects.get_or_create(user=user)
        role_display = profile.get_role_display()
        
        office_tweets.extend([f"{user.username} ({role_display}): {content}" for content in tweet_contents])
        
        # Generate Personal Summary
        tweets_text = ' ; '.join(tweet_contents)
        personal_prompt = (
            "You are an upbeat, supportive project assistant. Analyze the following micro-updates posted today by a team member. "
            "Extract their core achievements, but maintain a friendly, encouraging tone. Output a clean Markdown report with exactly these sections:\n"
            "1. 🚀 Tasks Completed: (Specific features, fixes, or deliverables finished today).\n"
            "2. 🚧 Work in Progress: (What they are currently building or researching).\n"
            "3. 🛑 Blockers: (Any issues slowing them down. If none, write 'Smooth sailing today!').\n"
            "4. 🌟 The Vibe: (One short, lighthearted sentence praising their effort or commenting on their day based on their tweets).\n\n"
            f"Employee Log: {tweets_text}"
        )
        
        summary_content = call_llm(personal_prompt)
        if summary_content:
            DailySummary.objects.update_or_create(
                user=user,
                target_date=today,
                summary_type='individual',
                defaults={'content': summary_content}
            )
        else:
            print(f"Failed to generate personal summary for {user.username} using any provider.")

    # Generate Office Summary
    if office_tweets:
        print(f"Generating office summary with {len(office_tweets)} total tweets...")
        office_tweets_text = '\n'.join(office_tweets)
        office_prompt = (
            "You are an upbeat, collaborative project assistant. Review the following individual daily summaries from the team. "
            "Synthesize a cohesive daily office report that tracks velocity but feels like a friendly end-of-day wrap-up. "
            "Output a clean Markdown report with these sections:\n"
            "1. 🏆 Today's Core Achievements: (Macro-view bulleted list of the team's biggest wins today).\n"
            "2. 🤝 Team Bottlenecks: (Consolidated list of blockers, framed as 'Where we need to help each other').\n"
            "3. ☕ The Watercooler: (A fun, 2-sentence summary of the team's overall mood or random non-work things mentioned today).\n"
            "4. 👥 Member Highlights: (A 1-sentence casual shoutout for each person's primary focus).\n\n"
            f"Team Summaries:\n{office_tweets_text}"
        )
        
        office_summary_content = call_llm(office_prompt)
        if office_summary_content:
            DailySummary.objects.update_or_create(
                user=None,
                target_date=today,
                summary_type='team',
                defaults={'content': office_summary_content}
            )
        else:
            print("Failed to generate office summary using any provider.")
    else:
        print("No office tweets found, skipping office summary.")
def extract_status(tweet_id):
    """
    Reads a tweet and extracts a short, third-person status.
    Updates the user's UserProfile.
    """
    tweet = Tweet.objects.get(id=tweet_id)
    user = tweet.user
    profile, _ = UserProfile.objects.get_or_create(user=user)
    
    # Avoid re-processing if the status is already newer than this tweet
    if profile.current_status and profile.last_status_update > tweet.created_at:
        return
        
    content = tweet.content
    
    prompt = (
        f"You are a helpful assistant that extracts a short, third-person current status from an employee's activity log.\n\n"
        f"Input: '{content}'\n"
        f"Goal: Extract a short, professional, third-person status (max 10 words).\n"
        f"Example Output: 'Finished responsive login button; currently smoking.'\n"
        f"Example Output: 'Working on database migrations for the new roles.'\n\n"
        f"Output only the status string, nothing else."
    )
    
    status_content = call_llm(prompt)
    if status_content:
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.current_status = status_content
        profile.save()
        print(f"Status updated for {user.username}: {status_content}")
    else:
        print(f"Failed to extract status for {user.username}")
