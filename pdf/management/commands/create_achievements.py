from django.core.management.base import BaseCommand
from pdf.models import Achievement


class Command(BaseCommand):
    help = 'Create initial achievement badges for gamification'

    def handle(self, *args, **kwargs):
        achievements = [
            # Streak Achievements
            {
                'name': '🔥 First Flame',
                'description': 'Complete your first study session',
                'achievement_type': 'streak',
                'rarity': 'common',
                'icon': 'ri-fire-line',
                'xp_reward': 10,
                'criteria': {'streak_days': 1}
            },
            {
                'name': '🔥 Week Warrior',
                'description': 'Maintain a 7-day study streak',
                'achievement_type': 'streak',
                'rarity': 'rare',
                'icon': 'ri-fire-fill',
                'xp_reward': 100,
                'criteria': {'streak_days': 7}
            },
            {
                'name': '🔥 Month Master',
                'description': 'Maintain a 30-day study streak',
                'achievement_type': 'streak',
                'rarity': 'epic',
                'icon': 'ri-fire-fill',
                'xp_reward': 500,
                'criteria': {'streak_days': 30}
            },
            {
                'name': '🔥 Unstoppable Force',
                'description': 'Maintain a 100-day study streak',
                'achievement_type': 'streak',
                'rarity': 'legendary',
                'icon': 'ri-fire-fill',
                'xp_reward': 2000,
                'criteria': {'streak_days': 100}
            },
            
            # Completion Achievements
            {
                'name': '✅ First Steps',
                'description': 'Complete your first activity',
                'achievement_type': 'completion',
                'rarity': 'common',
                'icon': 'ri-checkbox-circle-line',
                'xp_reward': 10,
                'criteria': {'activities_completed': 1}
            },
            {
                'name': '✅ Getting Started',
                'description': 'Complete your first week',
                'achievement_type': 'completion',
                'rarity': 'common',
                'icon': 'ri-calendar-check-line',
                'xp_reward': 25,
                'criteria': {'weeks_completed': 1}
            },
            {
                'name': '✅ Dedicated Learner',
                'description': 'Complete 50 activities',
                'achievement_type': 'completion',
                'rarity': 'rare',
                'icon': 'ri-medal-line',
                'xp_reward': 200,
                'criteria': {'activities_completed': 50}
            },
            {
                'name': '✅ Course Crusher',
                'description': 'Complete an entire study plan',
                'achievement_type': 'completion',
                'rarity': 'epic',
                'icon': 'ri-trophy-line',
                'xp_reward': 500,
                'criteria': {'study_plans_completed': 1}
            },
            {
                'name': '✅ Knowledge Seeker',
                'description': 'Complete 100 activities',
                'achievement_type': 'completion',
                'rarity': 'epic',
                'icon': 'ri-star-fill',
                'xp_reward': 750,
                'criteria': {'activities_completed': 100}
            },
            
            # Video Achievements
            {
                'name': '📺 Video Viewer',
                'description': 'Watch your first learning video',
                'achievement_type': 'dedication',
                'rarity': 'common',
                'icon': 'ri-youtube-line',
                'xp_reward': 10,
                'criteria': {'videos_watched': 1}
            },
            {
                'name': '📺 Binge Learner',
                'description': 'Watch 25 learning videos',
                'achievement_type': 'dedication',
                'rarity': 'rare',
                'icon': 'ri-youtube-fill',
                'xp_reward': 150,
                'criteria': {'videos_watched': 25}
            },
            {
                'name': '📺 Video Master',
                'description': 'Watch 100 learning videos',
                'achievement_type': 'dedication',
                'rarity': 'epic',
                'icon': 'ri-movie-2-fill',
                'xp_reward': 500,
                'criteria': {'videos_watched': 100}
            },
            
            # Quiz Achievements
            {
                'name': '📝 Quiz Rookie',
                'description': 'Complete your first quiz',
                'achievement_type': 'quiz',
                'rarity': 'common',
                'icon': 'ri-file-list-3-line',
                'xp_reward': 15,
                'criteria': {'quizzes_completed': 1}
            },
            {
                'name': '💯 Perfect Score',
                'description': 'Get 100% on any quiz',
                'achievement_type': 'quiz',
                'rarity': 'rare',
                'icon': 'ri-medal-line',
                'xp_reward': 100,
                'criteria': {'perfect_scores': 1}
            },
            {
                'name': '📝 Quiz Master',
                'description': 'Complete 10 quizzes',
                'achievement_type': 'quiz',
                'rarity': 'rare',
                'icon': 'ri-file-list-3-fill',
                'xp_reward': 200,
                'criteria': {'quizzes_completed': 10}
            },
            {
                'name': '🎯 Ace Student',
                'description': 'Pass 5 quizzes in a row',
                'achievement_type': 'quiz',
                'rarity': 'epic',
                'icon': 'ri-trophy-line',
                'xp_reward': 300,
                'criteria': {'quiz_streak': 5}
            },
            {
                'name': '💯 Perfectionist',
                'description': 'Get 100% on 5 different quizzes',
                'achievement_type': 'quiz',
                'rarity': 'epic',
                'icon': 'ri-star-fill',
                'xp_reward': 500,
                'criteria': {'perfect_scores': 5}
            },
            {
                'name': '📝 Quiz Legend',
                'description': 'Complete 50 quizzes',
                'achievement_type': 'quiz',
                'rarity': 'legendary',
                'icon': 'ri-vip-diamond-fill',
                'xp_reward': 1000,
                'criteria': {'quizzes_completed': 50}
            },

            # Milestone Achievements
            {
                'name': '⭐ Rising Star',
                'description': 'Reach Level 5',
                'achievement_type': 'milestone',
                'rarity': 'rare',
                'icon': 'ri-star-line',
                'xp_reward': 100,
                'criteria': {'level': 5}
            },
            {
                'name': '⭐ Shining Bright',
                'description': 'Reach Level 10',
                'achievement_type': 'milestone',
                'rarity': 'epic',
                'icon': 'ri-star-fill',
                'xp_reward': 300,
                'criteria': {'level': 10}
            },
            {
                'name': '⭐ Legendary Scholar',
                'description': 'Reach Level 25',
                'achievement_type': 'milestone',
                'rarity': 'legendary',
                'icon': 'ri-vip-crown-fill',
                'xp_reward': 1000,
                'criteria': {'level': 25}
            },
        ]

        created_count = 0
        for achievement_data in achievements:
            achievement, created = Achievement.objects.get_or_create(
                name=achievement_data['name'],
                defaults=achievement_data
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created: {achievement.name}'))
            else:
                self.stdout.write(f'Already exists: {achievement.name}')

        self.stdout.write(self.style.SUCCESS(f'\n✅ Created {created_count} new achievements!'))

