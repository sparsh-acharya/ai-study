"""
Gamification Helper Functions
Handles XP rewards, achievement unlocking, and streak tracking
"""

from pdf.models import UserProfile, Achievement, UserAchievement, StudySession
from django.utils import timezone


# XP Reward Constants
XP_REWARDS = {
    'activity_completed': 10,
    'week_completed': 50,
    'video_watched': 5,
    'study_plan_completed': 500,
    'daily_login': 5,
}


def get_or_create_profile(user):
    """Get or create user profile for gamification"""
    profile, created = UserProfile.objects.get_or_create(user=user)
    return profile


def award_xp(user, xp_amount, reason=""):
    """Award XP to user and check for level up"""
    profile = get_or_create_profile(user)
    leveled_up = profile.add_xp(xp_amount)
    
    # Update streak
    profile.update_streak()
    
    # Check for achievements
    check_and_unlock_achievements(user)
    
    return {
        'xp_awarded': xp_amount,
        'total_xp': profile.total_xp,
        'level': profile.level,
        'leveled_up': leveled_up,
        'reason': reason
    }


def check_and_unlock_achievements(user):
    """Check if user has unlocked any new achievements"""
    profile = get_or_create_profile(user)
    newly_unlocked = []
    
    # Get all achievements
    all_achievements = Achievement.objects.all()
    
    # Get already unlocked achievement IDs
    unlocked_ids = UserAchievement.objects.filter(user=user).values_list('achievement_id', flat=True)
    
    for achievement in all_achievements:
        if achievement.id in unlocked_ids:
            continue
            
        # Check criteria
        criteria = achievement.criteria
        unlocked = False
        
        if 'streak_days' in criteria:
            if profile.current_streak >= criteria['streak_days']:
                unlocked = True
        
        if 'activities_completed' in criteria:
            if profile.total_activities_completed >= criteria['activities_completed']:
                unlocked = True
        
        if 'weeks_completed' in criteria:
            if profile.total_weeks_completed >= criteria['weeks_completed']:
                unlocked = True
        
        if 'videos_watched' in criteria:
            if profile.total_videos_watched >= criteria['videos_watched']:
                unlocked = True
        
        if 'level' in criteria:
            if profile.level >= criteria['level']:
                unlocked = True
        
        if 'study_plans_completed' in criteria:
            # Count completed study plans
            from pdf.models import StudyPlan
            completed_plans = StudyPlan.objects.filter(
                user=user,
                weeks__is_completed=True
            ).distinct().count()
            if completed_plans >= criteria['study_plans_completed']:
                unlocked = True

        # Quiz achievements
        if 'quizzes_completed' in criteria:
            if profile.total_quizzes_completed >= criteria['quizzes_completed']:
                unlocked = True

        if 'perfect_scores' in criteria:
            if profile.total_perfect_scores >= criteria['perfect_scores']:
                unlocked = True

        if 'quiz_streak' in criteria:
            if profile.current_quiz_streak >= criteria['quiz_streak']:
                unlocked = True

        if unlocked:
            # Unlock achievement
            user_achievement = UserAchievement.objects.create(
                user=user,
                achievement=achievement,
                is_new=True
            )
            newly_unlocked.append(achievement)
            
            # Award XP for achievement
            profile.add_xp(achievement.xp_reward)
    
    return newly_unlocked


def handle_activity_completion(user, activity):
    """Handle gamification when an activity is completed"""
    profile = get_or_create_profile(user)
    
    # Update stats
    profile.total_activities_completed += 1
    profile.save()
    
    # Award XP
    result = award_xp(user, XP_REWARDS['activity_completed'], f"Completed: {activity.description[:30]}")
    
    return result


def handle_week_completion(user, week):
    """Handle gamification when a week is completed"""
    profile = get_or_create_profile(user)
    
    # Update stats
    profile.total_weeks_completed += 1
    profile.save()
    
    # Award XP
    result = award_xp(user, XP_REWARDS['week_completed'], f"Completed Week {week.week_number}: {week.topic}")
    
    return result


def handle_video_watched(user, resource):
    """Handle gamification when a video is watched"""
    profile = get_or_create_profile(user)
    
    # Update stats
    profile.total_videos_watched += 1
    profile.save()
    
    # Award XP
    result = award_xp(user, XP_REWARDS['video_watched'], f"Watched: {resource.title[:30]}")
    
    return result


def handle_quiz_completion(user, quiz_attempt):
    """Handle gamification when a quiz is completed"""
    profile = get_or_create_profile(user)

    # Update quiz stats
    profile.total_quizzes_completed += 1

    if quiz_attempt.passed:
        profile.total_quizzes_passed += 1
        profile.current_quiz_streak += 1

        # Update longest streak
        if profile.current_quiz_streak > profile.longest_quiz_streak:
            profile.longest_quiz_streak = profile.current_quiz_streak
    else:
        # Reset streak on failure
        profile.current_quiz_streak = 0

    # Check for perfect score
    if quiz_attempt.percentage == 100:
        profile.total_perfect_scores += 1

    profile.save()

    # Check for achievements
    check_and_unlock_achievements(user)

    return {
        'quizzes_completed': profile.total_quizzes_completed,
        'quizzes_passed': profile.total_quizzes_passed,
        'perfect_scores': profile.total_perfect_scores,
        'quiz_streak': profile.current_quiz_streak
    }


def get_user_stats(user):
    """Get comprehensive user statistics for dashboard"""
    profile = get_or_create_profile(user)

    # Get recent achievements
    recent_achievements = UserAchievement.objects.filter(user=user).order_by('-unlocked_at')[:5]

    # Get new achievements count
    new_achievements_count = UserAchievement.objects.filter(user=user, is_new=True).count()

    return {
        'profile': profile,
        'level': profile.level,
        'total_xp': profile.total_xp,
        'xp_for_next_level': profile.xp_for_next_level,
        'xp_progress_percentage': profile.xp_progress_percentage,
        'current_streak': profile.current_streak,
        'longest_streak': profile.longest_streak,
        'total_activities_completed': profile.total_activities_completed,
        'total_weeks_completed': profile.total_weeks_completed,
        'total_videos_watched': profile.total_videos_watched,
        'total_quizzes_completed': profile.total_quizzes_completed,
        'total_quizzes_passed': profile.total_quizzes_passed,
        'total_perfect_scores': profile.total_perfect_scores,
        'current_quiz_streak': profile.current_quiz_streak,
        'recent_achievements': recent_achievements,
        'new_achievements_count': new_achievements_count,
    }

