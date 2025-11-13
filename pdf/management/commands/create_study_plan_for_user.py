from django.core.management.base import BaseCommand
from pdf.models import Document, StudyPlan, StudyWeek, StudyActivity
from django.contrib.auth.models import User
import json

class Command(BaseCommand):
    help = 'Create a study plan for a specific user'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username to create study plan for')

    def handle(self, *args, **options):
        username = options['username']
        
        try:
            user = User.objects.get(username=username)
            self.stdout.write(f'Creating study plan for user: {user.username}')
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User "{username}" not found'))
            return
        
        # Get the latest document
        document = Document.objects.last()
        if not document:
            self.stdout.write(self.style.ERROR('No documents found'))
            return
            
        self.stdout.write(f'Using document: {document.file_name}')
        
        # Sample study plan data
        sample_study_plan_data = {
            "course_name": "Machine Learning Fundamentals",
            "total_duration_weeks": 8,
            "course_description": "A comprehensive introduction to machine learning concepts and techniques based on the uploaded document.",
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
                            "description": "Read Chapter 1: ML Fundamentals from the uploaded document",
                            "estimated_time": "2 hours"
                        },
                        {
                            "type": "Practice",
                            "description": "Complete basic ML exercises and examples",
                            "estimated_time": "3 hours"
                        },
                        {
                            "type": "Review",
                            "description": "Review key concepts and terminology",
                            "estimated_time": "1 hour"
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
                            "description": "Study regression and classification algorithms",
                            "estimated_time": "3 hours"
                        },
                        {
                            "type": "Project",
                            "description": "Build a simple classifier using provided examples",
                            "estimated_time": "4 hours"
                        },
                        {
                            "type": "Assignment",
                            "description": "Complete supervised learning exercises",
                            "estimated_time": "2 hours"
                        }
                    ]
                },
                {
                    "week": 3,
                    "topic": "Unsupervised Learning",
                    "difficulty_level": "Intermediate",
                    "estimated_hours": 9,
                    "study_activities": [
                        {
                            "type": "Reading",
                            "description": "Study clustering and dimensionality reduction",
                            "estimated_time": "3 hours"
                        },
                        {
                            "type": "Practical",
                            "description": "Implement clustering algorithms",
                            "estimated_time": "4 hours"
                        },
                        {
                            "type": "Quiz",
                            "description": "Self-assessment on unsupervised learning",
                            "estimated_time": "1 hour"
                        }
                    ]
                }
            ],
            "recommended_schedule": {
                "daily_study_time": "1-2 hours"
            }
        }
        
        try:
            # Delete existing study plan for this user and document if it exists
            existing_plan = StudyPlan.objects.filter(user=user, document=document).first()
            if existing_plan:
                existing_plan.delete()
                self.stdout.write('Deleted existing study plan')
            
            # Create new study plan
            study_plan = StudyPlan.objects.create(
                user=user,
                document=document,
                course_name=sample_study_plan_data.get('course_name', 'Untitled Course'),
                course_description=sample_study_plan_data.get('course_description', ''),
                total_duration_weeks=sample_study_plan_data.get('total_duration_weeks', 12),
                recommended_daily_study_time=sample_study_plan_data.get('recommended_schedule', {}).get('daily_study_time', '1-2 hours'),
                study_plan_data=sample_study_plan_data
            )
            
            self.stdout.write(self.style.SUCCESS(f'Created new study plan: {study_plan.course_name}'))
            
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
            self.stdout.write(f'You can view it at: http://127.0.0.1:8000/study-plan/{study_plan.id}/')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating study plan: {str(e)}'))
            import traceback
            traceback.print_exc()
