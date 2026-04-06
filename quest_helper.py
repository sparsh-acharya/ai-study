"""
Quest Helper Functions
Handles assignment, progress tracking, and fulfillment of daily quests.
"""

import random
from datetime import date
from django.utils import timezone
from pdf.models import DailyQuest, UserDailyQuest

def seed_default_quests():
    """Seed initial pool of daily quests if none exist"""
    quests = [
        # Activity Quests
        {
            'title': "Scholar's Sprint",
            'description': "Complete 2 study activities today.",
            'quest_type': 'ACTIVITY',
            'goal_count': 2,
            'reward_xp': 50
        },
        {
            'title': "Knowledge Grind",
            'description': "Finish 3 activities in your study plan.",
            'quest_type': 'ACTIVITY',
            'goal_count': 3,
            'reward_xp': 75
        },
        # Quiz Quests
        {
            'title': "Ancient Quiz Master",
            'description': "Answer 5 questions correctly in quizzes.",
            'quest_type': 'QUIZ',
            'goal_count': 5,
            'reward_xp': 60
        },
        {
            'title': "Flawless Victory",
            'description': "Complete 1 quiz perfectly (100%).",
            'quest_type': 'QUIZ',
            'goal_count': 1,
            'reward_xp': 100
        },
        # Login/Misc Quests
        {
            'title': "Daily Devotion",
            'description': "Check your study dashboard today.",
            'quest_type': 'LOGIN',
            'goal_count': 1,
            'reward_xp': 25
        },
    ]
    
    for q_data in quests:
        DailyQuest.objects.get_or_create(
            title=q_data['title'],
            defaults=q_data
        )

def get_or_create_daily_quests(user):
    """Ensure user has 3 active quests for today"""
    today = date.today()
    
    # Check if quests already assigned for today
    user_quests = UserDailyQuest.objects.filter(user=user, date=today)
    
    if user_quests.exists():
        return user_quests
        
    # Seed if needed
    if not DailyQuest.objects.exists():
        seed_default_quests()
        
    # Pick 3 random quests
    all_quests = list(DailyQuest.objects.all())
    if len(all_quests) < 3:
        selected_quests = all_quests
    else:
        # Try to vary types if possible
        selected_quests = random.sample(all_quests, min(3, len(all_quests)))
        
    new_user_quests = []
    for q in selected_quests:
        uq, created = UserDailyQuest.objects.get_or_create(
            user=user,
            quest=q,
            date=today
        )
        new_user_quests.append(uq)
        
    return new_user_quests

def update_quest_progress(user, quest_type, amount=1):
    """Update progress for quests of a certain type"""
    today = date.today()
    active_quests = UserDailyQuest.objects.filter(
        user=user, 
        date=today, 
        quest__quest_type=quest_type,
        is_completed=False
    )
    
    updates = []
    for uq in active_quests:
        uq.current_count += amount
        if uq.current_count >= uq.quest.goal_count:
            uq.current_count = uq.quest.goal_count
            uq.is_completed = True
        uq.save()
        updates.append(uq)
        
    return updates
