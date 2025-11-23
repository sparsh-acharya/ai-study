from django.core.management.base import BaseCommand
from pdf.models import Document, StudyPlan, StudyWeek, StudyActivity
from django.contrib.auth.models import User
import json

class Command(BaseCommand):
    help = 'Test study plan creation with sample data'

    def handle(self, *args, **options):
        # Get or create a test user
        user, created = User.objects.get_or_create(username='testuser', defaults={'email': 'test@example.com'})
        if created:
            user.set_password('testpass')
            user.save()
            self.stdout.write(f'Created test user: {user.username}')
        else:
            self.stdout.write(f'Using existing user: {user.username}')
        
        # Get the latest document
        document = Document.objects.last()
        if not document:
            self.stdout.write(self.style.ERROR('No documents found'))
            return
            
        self.stdout.write(f'Using document: {document.file_name}')
        
        # Sample study plan data (simplified version of what Gemini would return)
        sample_study_plan_data = {
            "course_name": "Machine Learning Fundamentals",
            "total_duration_weeks": 8,
            "course_description": "A comprehensive introduction to machine learning concepts and techniques.",
            "learning_objectives": ["Understand ML basics", "Apply algorithms", "Evaluate models"],
            "study_plan": [
                {
                    "week": 1,
                    "topic": "Introduction to Machine Learning",
                    "difficulty_level": "Beginner",
                    "estimated_hours": 8,
                    "study_activities": [
                        {
                            "type": "Reading",
                            "description": "Read Chapter 1: ML Fundamentals",
                            "estimated_time": "2 hours"
                        },
                        {
                            "type": "Practice",
                            "description": "Complete basic exercises",
                            "estimated_time": "3 hours"
                        }
                    ]
                },
                {
                    "week": 2,
                    "topic": "Supervised Learning",
                    "difficulty_level": "Intermediate",
                    "estimated_hours": 10,
                    "study_activities": [
                        {
                            "type": "Reading",
                            "description": "Study regression and classification",
                            "estimated_time": "3 hours"
                        },
                        {
                            "type": "Project",
                            "description": "Build a simple classifier",
                            "estimated_time": "4 hours"
                        }
                    ]
                }
            ],
            "recommended_schedule": {
                "daily_study_time": "1-2 hours"
            }
        }
        
        try:
            # Create or update study plan
            study_plan, created = StudyPlan.objects.get_or_create(
                user=user,
                document=document,
                defaults={
                    'course_name': sample_study_plan_data.get('course_name', 'Untitled Course'),
                    'course_description': sample_study_plan_data.get('course_description', ''),
                    'total_duration_weeks': sample_study_plan_data.get('total_duration_weeks', 12),
                    'recommended_daily_study_time': sample_study_plan_data.get('recommended_schedule', {}).get('daily_study_time', '1-2 hours'),
                    'study_plan_data': sample_study_plan_data
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created new study plan: {study_plan.course_name}'))
            else:
                self.stdout.write(f'Study plan already exists: {study_plan.course_name}')
                # Update existing study plan
                study_plan.course_name = sample_study_plan_data.get('course_name', study_plan.course_name)
                study_plan.course_description = sample_study_plan_data.get('course_description', study_plan.course_description)
                study_plan.total_duration_weeks = sample_study_plan_data.get('total_duration_weeks', study_plan.total_duration_weeks)
                study_plan.recommended_daily_study_time = sample_study_plan_data.get('recommended_schedule', {}).get('daily_study_time', study_plan.recommended_daily_study_time)
                study_plan.study_plan_data = sample_study_plan_data
                study_plan.save()
                self.stdout.write(self.style.SUCCESS('Updated existing study plan'))
            
            # Clear existing weeks and activities if updating
            if not created:
                study_plan.weeks.all().delete()
                self.stdout.write('Cleared existing weeks and activities')
            
            # Create study weeks and activities
            for week_data in sample_study_plan_data.get('study_plan', []):
                study_week = StudyWeek.objects.create(
                    study_plan=study_plan,
                    week_number=week_data.get('week', 1),
                    topic=week_data.get('topic', 'Untitled Topic'),
                    estimated_hours=f"{week_data.get('estimated_hours', 8)} hours"
                )
                self.stdout.write(f'Created week {study_week.week_number}: {study_week.topic}')
                
                # Create activities for this week
                for activity_data in week_data.get('study_activities', []):
                    activity_type = activity_data.get('type', 'other').lower()
                    if activity_type not in ['reading', 'assignment', 'practical', 'project', 'review', 'quiz']:
                        activity_type = 'other'
                        
                    activity = StudyActivity.objects.create(
                        study_week=study_week,
                        activity_type=activity_type,
                        description=activity_data.get('description', ''),
                        estimated_time=activity_data.get('estimated_time', '')
                    )
                    self.stdout.write(f'  - Created activity: {activity.get_activity_type_display()} - {activity.description}')
            
            self.stdout.write(self.style.SUCCESS(f'Study plan creation completed! ID: {study_plan.id}'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating study plan: {str(e)}'))
            import traceback
            traceback.print_exc()
