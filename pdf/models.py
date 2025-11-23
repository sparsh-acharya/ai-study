from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json

# Create your models here.

class Document(models.Model):
    DOCUMENT_TYPES = [
        ('handout', 'Handout/Notes'),
        ('syllabus', 'Syllabus'),
        ('textbook', 'Textbook'),
        ('other', 'Other'),
    ]

    file = models.FileField(upload_to='')
    uploaded_at = models.DateTimeField(default=timezone.now)
    file_name = models.CharField(max_length=255)
    file_size = models.IntegerField()  # Size in bytes
    file_type = models.CharField(max_length=10)  # pdf, ppt, pptx
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES, default='handout')

    def __str__(self):
        return self.file_name

    class Meta:
        ordering = ['-uploaded_at']


class StudyPlan(models.Model):
    PLAN_MODES = [
        ('basic', 'Basic Study Plan'),
        ('enhanced', 'Enhanced with Resources'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='main_study_plans')
    syllabus_document = models.ForeignKey(Document, on_delete=models.SET_NULL, null=True, blank=True, related_name='syllabus_study_plans')

    # Plan configuration
    plan_mode = models.CharField(max_length=20, choices=PLAN_MODES, default='basic')

    # Course information
    course_name = models.CharField(max_length=255)
    course_description = models.TextField(blank=True)
    total_duration_weeks = models.IntegerField()
    recommended_daily_study_time = models.CharField(max_length=50, default='1-2 hours')

    # Study plan data
    study_plan_data = models.JSONField()  # Store the full study plan JSON

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.course_name} - {self.user.username}"

    class Meta:
        ordering = ['-created_at']


class StudyWeek(models.Model):
    study_plan = models.ForeignKey(StudyPlan, on_delete=models.CASCADE, related_name='weeks')
    week_number = models.IntegerField()
    topic = models.CharField(max_length=255)
    estimated_hours = models.CharField(max_length=50, blank=True)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Week {self.week_number}: {self.topic}"

    @property
    def quiz(self):
        """Get the quiz for this week if it exists"""
        return self.quizzes.first()

    class Meta:
        ordering = ['week_number']
        unique_together = ['study_plan', 'week_number']


class StudyActivity(models.Model):
    ACTIVITY_TYPES = [
        ('reading', 'Reading'),
        ('assignment', 'Assignment'),
        ('practical', 'Practical Task'),
        ('project', 'Project'),
        ('review', 'Review'),
        ('quiz', 'Quiz'),
        ('video', 'Video Tutorial'),
        ('other', 'Other'),
    ]

    study_week = models.ForeignKey(StudyWeek, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    description = models.TextField()
    estimated_time = models.CharField(max_length=50, blank=True)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)  # User can add personal notes

    def __str__(self):
        return f"{self.get_activity_type_display()}: {self.description[:50]}"

    class Meta:
        ordering = ['id']


class LearningResource(models.Model):
    RESOURCE_TYPES = [
        ('youtube', 'YouTube Video'),
        ('article', 'Article'),
        ('documentation', 'Documentation'),
        ('tutorial', 'Tutorial'),
        ('course', 'Online Course'),
        ('other', 'Other'),
    ]

    study_week = models.ForeignKey(StudyWeek, on_delete=models.CASCADE, related_name='resources')
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES)
    title = models.CharField(max_length=500)
    url = models.URLField(max_length=1000)
    description = models.TextField(blank=True)
    thumbnail_url = models.URLField(max_length=1000, blank=True)
    duration = models.CharField(max_length=50, blank=True)  # For videos
    channel_name = models.CharField(max_length=255, blank=True)  # For YouTube videos
    view_count = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    is_watched = models.BooleanField(default=False)
    watched_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.get_resource_type_display()}: {self.title[:50]}"

    class Meta:
        ordering = ['id']


# ============= GAMIFICATION MODELS =============

class UserProfile(models.Model):
    """Extended user profile with gamification stats"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='study_profile')

    # XP and Leveling
    total_xp = models.IntegerField(default=0)
    level = models.IntegerField(default=1)

    # Streaks
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)

    # Statistics
    total_study_time_minutes = models.IntegerField(default=0)
    total_activities_completed = models.IntegerField(default=0)
    total_weeks_completed = models.IntegerField(default=0)
    total_videos_watched = models.IntegerField(default=0)

    # Quiz Statistics
    total_quizzes_completed = models.IntegerField(default=0)
    total_quizzes_passed = models.IntegerField(default=0)
    total_perfect_scores = models.IntegerField(default=0)
    current_quiz_streak = models.IntegerField(default=0)
    longest_quiz_streak = models.IntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile - Level {self.level}"

    @property
    def xp_for_next_level(self):
        """Calculate XP needed for next level (exponential growth)"""
        return self.level * 100

    @property
    def xp_progress_percentage(self):
        """Calculate progress to next level"""
        xp_in_current_level = self.total_xp % self.xp_for_next_level
        return (xp_in_current_level / self.xp_for_next_level) * 100 if self.xp_for_next_level > 0 else 0

    def add_xp(self, amount):
        """Add XP and check for level up"""
        self.total_xp += amount
        old_level = self.level

        # Calculate new level
        while self.total_xp >= self.xp_for_next_level:
            self.level += 1

        self.save()

        # Return True if leveled up
        return self.level > old_level

    def update_streak(self):
        """Update study streak based on activity"""
        from datetime import date, timedelta

        today = date.today()

        if self.last_activity_date is None:
            # First activity ever
            self.current_streak = 1
            self.longest_streak = 1
            self.last_activity_date = today
        elif self.last_activity_date == today:
            # Already studied today, no change
            pass
        elif self.last_activity_date == today - timedelta(days=1):
            # Studied yesterday, increment streak
            self.current_streak += 1
            if self.current_streak > self.longest_streak:
                self.longest_streak = self.current_streak
            self.last_activity_date = today
        else:
            # Streak broken
            self.current_streak = 1
            self.last_activity_date = today

        self.save()

    class Meta:
        ordering = ['-total_xp']


class Achievement(models.Model):
    """Achievement definitions"""
    ACHIEVEMENT_TYPES = [
        ('streak', 'Streak Achievement'),
        ('completion', 'Completion Achievement'),
        ('speed', 'Speed Achievement'),
        ('dedication', 'Dedication Achievement'),
        ('milestone', 'Milestone Achievement'),
    ]

    RARITY_LEVELS = [
        ('common', 'Common'),
        ('rare', 'Rare'),
        ('epic', 'Epic'),
        ('legendary', 'Legendary'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField()
    achievement_type = models.CharField(max_length=20, choices=ACHIEVEMENT_TYPES)
    rarity = models.CharField(max_length=20, choices=RARITY_LEVELS, default='common')
    icon = models.CharField(max_length=50, default='ri-trophy-line')  # RemixIcon class
    xp_reward = models.IntegerField(default=50)

    # Unlock criteria (stored as JSON)
    criteria = models.JSONField(default=dict)

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.name} ({self.get_rarity_display()})"

    class Meta:
        ordering = ['rarity', 'name']


class UserAchievement(models.Model):
    """Track which achievements users have unlocked"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    unlocked_at = models.DateTimeField(default=timezone.now)
    is_new = models.BooleanField(default=True)  # For showing "NEW!" badge

    def __str__(self):
        return f"{self.user.username} - {self.achievement.name}"

    class Meta:
        unique_together = ['user', 'achievement']
        ordering = ['-unlocked_at']


class StudySession(models.Model):
    """Track individual study sessions for analytics"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='study_sessions')
    study_plan = models.ForeignKey(StudyPlan, on_delete=models.CASCADE, related_name='sessions')
    study_week = models.ForeignKey(StudyWeek, on_delete=models.CASCADE, null=True, blank=True)

    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.IntegerField(default=0)

    activities_completed = models.IntegerField(default=0)
    videos_watched = models.IntegerField(default=0)
    xp_earned = models.IntegerField(default=0)

    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.started_at.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        ordering = ['-started_at']


# ============================================================================
# QUIZ MODELS
# ============================================================================

class Quiz(models.Model):
    """AI-generated quiz for a study plan or week"""
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]

    study_plan = models.ForeignKey(StudyPlan, on_delete=models.CASCADE, related_name='quizzes')
    study_week = models.ForeignKey(StudyWeek, on_delete=models.CASCADE, null=True, blank=True, related_name='quizzes')

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium')

    time_limit_minutes = models.IntegerField(null=True, blank=True, help_text="Time limit in minutes (optional)")
    passing_score = models.IntegerField(default=70, help_text="Minimum percentage to pass")

    xp_reward = models.IntegerField(default=20, help_text="XP awarded for passing the quiz")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.study_plan.subject}"

    @property
    def total_questions(self):
        return self.questions.count()

    @property
    def total_points(self):
        return sum(q.points for q in self.questions.all())

    class Meta:
        ordering = ['-created_at']


class Question(models.Model):
    """Individual question in a quiz"""
    QUESTION_TYPE_CHOICES = [
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
    ]

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')

    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES, default='multiple_choice')

    explanation = models.TextField(blank=True, help_text="Explanation shown after answering")
    points = models.IntegerField(default=1)

    order = models.IntegerField(default=0, help_text="Display order in quiz")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Q{self.order}: {self.question_text[:50]}"

    @property
    def correct_answer(self):
        return self.answers.filter(is_correct=True).first()

    class Meta:
        ordering = ['order']


class Answer(models.Model):
    """Answer option for a question"""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')

    answer_text = models.TextField()
    is_correct = models.BooleanField(default=False)

    order = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.answer_text[:50]} ({'Correct' if self.is_correct else 'Incorrect'})"

    class Meta:
        ordering = ['order']


class QuizAttempt(models.Model):
    """User's attempt at a quiz"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')

    score = models.IntegerField(default=0, help_text="Points earned")
    max_score = models.IntegerField(default=0, help_text="Total possible points")

    time_taken_seconds = models.IntegerField(null=True, blank=True)

    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    is_completed = models.BooleanField(default=False)
    passed = models.BooleanField(default=False)

    # Store user's answers as JSON: {question_id: answer_id}
    answers = models.JSONField(default=dict, blank=True)

    xp_awarded = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} - {self.quiz.title} - {self.score}/{self.max_score}"

    @property
    def percentage(self):
        if self.max_score == 0:
            return 0
        return round((self.score / self.max_score) * 100, 1)

    @property
    def time_taken_formatted(self):
        if not self.time_taken_seconds:
            return "N/A"
        minutes = self.time_taken_seconds // 60
        seconds = self.time_taken_seconds % 60
        return f"{minutes}m {seconds}s"

    def calculate_score(self):
        """Calculate score based on answers"""
        total_score = 0
        max_score = 0

        for question in self.quiz.questions.all():
            max_score += question.points
            answer_id = self.answers.get(str(question.id))

            if answer_id:
                try:
                    answer = Answer.objects.get(id=answer_id, question=question)
                    if answer.is_correct:
                        total_score += question.points
                except Answer.DoesNotExist:
                    pass

        self.score = total_score
        self.max_score = max_score
        self.passed = self.percentage >= self.quiz.passing_score
        self.save()

        return total_score, max_score

    class Meta:
        ordering = ['-started_at']
