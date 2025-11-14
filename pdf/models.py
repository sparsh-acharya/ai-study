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

    def __str__(self):
        return f"{self.get_resource_type_display()}: {self.title[:50]}"

    class Meta:
        ordering = ['id']
