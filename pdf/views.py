from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Document, StudyPlan, StudyWeek, StudyActivity, LearningResource, UserProfile, Achievement, UserAchievement, Quiz, Question, Answer, QuizAttempt
import os
import json
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from gemini import process_document_with_gemini
from study_plan_prompts import get_basic_prompt, get_enhanced_prompt
from youtube_helper import search_youtube_videos
from gamification_helper import (
    get_or_create_profile,
    handle_activity_completion,
    handle_week_completion,
    handle_video_watched,
    get_user_stats
)

# Create your views here.
def landing(request):
    return render(request,'landing.html')

@login_required
def upload(request):
    if request.method == 'POST':
        # Check if this is a JSON request (for multiple files) or form data
        if request.content_type == 'application/json':
            # Handle JSON request for enhanced mode
            data = json.loads(request.body)
            return JsonResponse({'error': 'Use form data for file uploads'}, status=400)

        # Handle form data upload
        uploaded_file = request.FILES.get('file')
        syllabus_file = request.FILES.get('syllabus')  # Optional syllabus
        document_type = request.POST.get('document_type', 'handout')

        if uploaded_file:
            # Validate file type (only PDF)
            if uploaded_file.content_type != 'application/pdf':
                return JsonResponse({'error': 'Invalid file type. Please upload a PDF file.'}, status=400)

            # Validate file size (50MB limit)
            if uploaded_file.size > 50 * 1024 * 1024:
                return JsonResponse({'error': 'File size exceeds 50MB limit.'}, status=400)

            # Ensure media directory exists
            media_dir = settings.MEDIA_ROOT
            if not os.path.exists(media_dir):
                os.makedirs(media_dir)

            # Create main document instance
            document = Document(
                file=uploaded_file,
                file_name=uploaded_file.name,
                file_size=uploaded_file.size,
                file_type='pdf',
                document_type=document_type
            )
            document.save()

            # Build absolute URLs for the files
            file_absolute_url = request.build_absolute_uri(document.file.url)

            response_data = {
                'success': True,
                'message': 'File uploaded successfully',
                'file_name': document.file_name,
                'file_url': file_absolute_url,
                'document_id': document.id
            }

            # Handle optional syllabus upload
            if syllabus_file:
                if syllabus_file.content_type != 'application/pdf':
                    return JsonResponse({'error': 'Syllabus must be a PDF file.'}, status=400)

                if syllabus_file.size > 50 * 1024 * 1024:
                    return JsonResponse({'error': 'Syllabus file size exceeds 50MB limit.'}, status=400)

                syllabus_doc = Document(
                    file=syllabus_file,
                    file_name=syllabus_file.name,
                    file_size=syllabus_file.size,
                    file_type='pdf',
                    document_type='syllabus'
                )
                syllabus_doc.save()

                syllabus_absolute_url = request.build_absolute_uri(syllabus_doc.file.url)
                response_data['syllabus_uploaded'] = True
                response_data['syllabus_url'] = syllabus_absolute_url
                response_data['syllabus_id'] = syllabus_doc.id

            return JsonResponse(response_data)

        return JsonResponse({'error': 'No file uploaded'}, status=400)

    return render(request, 'upload_simple.html')

@csrf_exempt
@login_required
def analyze(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            file_url = data.get('file_url')
            syllabus_url = data.get('syllabus_url')  # Optional
            plan_mode = data.get('plan_mode', 'basic')  # 'basic' or 'enhanced'

            # Select appropriate prompt based on mode
            if plan_mode == 'enhanced':
                prompt = get_enhanced_prompt(has_syllabus=bool(syllabus_url))
            else:
                prompt = get_basic_prompt()

            if not file_url:
                return JsonResponse({'error': 'No file URL provided'}, status=400)

            # Process the document with Gemini
            result = process_document_with_gemini(file_url, prompt)

            # Parse the result and save to database
            try:
                study_plan_data = json.loads(result)

                # Find the document by URL (assuming it's in the format /media/filename)
                file_name = file_url.split('/')[-1]
                print(f"DEBUG: Looking for document with file_name: {file_name}")

                # Try to find document by the actual file path first, then by file_name
                document = Document.objects.filter(file=file_name).first()
                if not document:
                    # Fallback: try to match by original filename
                    document = Document.objects.filter(file_name__icontains=file_name.split('_')[0]).first()

                print(f"DEBUG: Found document: {document}")
                if document:
                    print(f"DEBUG: Document file: {document.file}, file_name: {document.file_name}")

                if document:
                    # Find syllabus document if provided
                    syllabus_document = None
                    if syllabus_url:
                        syllabus_file_name = syllabus_url.split('/')[-1]
                        syllabus_document = Document.objects.filter(file=syllabus_file_name).first()

                    # Create or update study plan
                    study_plan, created = StudyPlan.objects.get_or_create(
                        user=request.user,
                        document=document,
                        defaults={
                            'course_name': study_plan_data.get('course_name', 'Untitled Course'),
                            'course_description': study_plan_data.get('course_description', ''),
                            'total_duration_weeks': study_plan_data.get('total_duration_weeks', 12),
                            'recommended_daily_study_time': study_plan_data.get('recommended_schedule', {}).get('daily_study_time', '1-2 hours'),
                            'study_plan_data': study_plan_data,
                            'plan_mode': plan_mode,
                            'syllabus_document': syllabus_document
                        }
                    )

                    if not created:
                        # Update existing study plan
                        study_plan.course_name = study_plan_data.get('course_name', study_plan.course_name)
                        study_plan.course_description = study_plan_data.get('course_description', study_plan.course_description)
                        study_plan.total_duration_weeks = study_plan_data.get('total_duration_weeks', study_plan.total_duration_weeks)
                        study_plan.recommended_daily_study_time = study_plan_data.get('recommended_schedule', {}).get('daily_study_time', study_plan.recommended_daily_study_time)
                        study_plan.study_plan_data = study_plan_data
                        study_plan.plan_mode = plan_mode
                        study_plan.syllabus_document = syllabus_document
                        study_plan.save()

                    # Clear existing weeks and activities if updating
                    if not created:
                        study_plan.weeks.all().delete()

                    # Create study weeks and activities
                    for week_data in study_plan_data.get('study_plan', []):
                        study_week = StudyWeek.objects.create(
                            study_plan=study_plan,
                            week_number=week_data.get('week', 1),
                            topic=week_data.get('topic', 'Untitled Topic'),
                            estimated_hours=f"{week_data.get('estimated_hours', 8)} hours"
                        )

                        # Create activities for this week
                        for activity_data in week_data.get('study_activities', []):
                            activity_type = activity_data.get('type', 'other').lower()
                            if activity_type not in ['reading', 'assignment', 'practical', 'project', 'review', 'quiz', 'video']:
                                activity_type = 'other'

                            activity = StudyActivity.objects.create(
                                study_week=study_week,
                                activity_type=activity_type,
                                description=activity_data.get('description', ''),
                                estimated_time=activity_data.get('estimated_time', '')
                            )

                            # If this is a video activity in enhanced mode, fetch YouTube videos
                            if plan_mode == 'enhanced' and activity_type == 'video':
                                search_query = activity_data.get('search_query', week_data.get('topic', ''))
                                if search_query:
                                    try:
                                        videos = search_youtube_videos(search_query, max_results=3)
                                        for video in videos:
                                            LearningResource.objects.create(
                                                study_week=study_week,
                                                resource_type='youtube',
                                                title=video.get('title', ''),
                                                url=video.get('url', ''),
                                                description=video.get('description', ''),
                                                thumbnail_url=video.get('thumbnail_url', ''),
                                                duration=video.get('duration', ''),
                                                channel_name=video.get('channel_name', ''),
                                                view_count=video.get('view_count', 0)
                                            )
                                    except Exception as e:
                                        print(f"Error fetching YouTube videos: {str(e)}")

                        # Process recommended_resources if in enhanced mode
                        if plan_mode == 'enhanced':
                            for resource_data in week_data.get('recommended_resources', []):
                                resource_type = resource_data.get('type', 'other')
                                search_query = resource_data.get('search_query', '')

                                if resource_type == 'video' and search_query:
                                    try:
                                        videos = search_youtube_videos(search_query, max_results=2)
                                        for video in videos:
                                            LearningResource.objects.create(
                                                study_week=study_week,
                                                resource_type='youtube',
                                                title=video.get('title', ''),
                                                url=video.get('url', ''),
                                                description=resource_data.get('purpose', video.get('description', '')),
                                                thumbnail_url=video.get('thumbnail_url', ''),
                                                duration=video.get('duration', ''),
                                                channel_name=video.get('channel_name', ''),
                                                view_count=video.get('view_count', 0)
                                            )
                                    except Exception as e:
                                        print(f"Error fetching recommended videos: {str(e)}")

                    return JsonResponse({
                        'success': True,
                        'result': result,
                        'study_plan_id': study_plan.id
                    })
                else:
                    # Document not found, still return the result
                    return JsonResponse({
                        'success': True,
                        'result': result,
                        'warning': 'Study plan generated but not saved - document not found'
                    })

            except json.JSONDecodeError:
                # If JSON parsing fails, still return the raw result
                return JsonResponse({
                    'success': True,
                    'result': result,
                    'warning': 'Study plan generated but not saved - invalid JSON format'
                })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=400)


@login_required
def study_plans(request):
    """Display all study plans for the current user"""
    user_study_plans = StudyPlan.objects.filter(user=request.user).prefetch_related('weeks')

    # Add progress information to each study plan
    for plan in user_study_plans:
        weeks = plan.weeks.all()
        total_weeks = weeks.count()
        completed_weeks = weeks.filter(is_completed=True).count()

        plan.total_weeks = total_weeks
        plan.completed_weeks = completed_weeks
        plan.progress_percentage = (completed_weeks / total_weeks * 100) if total_weeks > 0 else 0

    return render(request, 'study_plans.html', {'study_plans': user_study_plans})


@login_required
def study_plan_detail(request, plan_id):
    """Display detailed view of a specific study plan with progress tracking"""
    try:
        study_plan = StudyPlan.objects.get(id=plan_id, user=request.user)
        weeks = study_plan.weeks.all().prefetch_related('activities', 'resources')

        # Calculate progress statistics
        total_weeks = weeks.count()
        completed_weeks = weeks.filter(is_completed=True).count()
        total_activities = sum(week.activities.count() for week in weeks)
        completed_activities = sum(week.activities.filter(is_completed=True).count() for week in weeks)

        # Calculate video stats
        total_videos = sum(week.resources.filter(resource_type='youtube').count() for week in weeks)
        watched_videos = sum(week.resources.filter(resource_type='youtube', is_watched=True).count() for week in weeks)

        progress_stats = {
            'weeks_progress': (completed_weeks / total_weeks * 100) if total_weeks > 0 else 0,
            'activities_progress': (completed_activities / total_activities * 100) if total_activities > 0 else 0,
            'videos_progress': (watched_videos / total_videos * 100) if total_videos > 0 else 0,
            'completed_weeks': completed_weeks,
            'total_weeks': total_weeks,
            'completed_activities': completed_activities,
            'total_activities': total_activities,
            'watched_videos': watched_videos,
            'total_videos': total_videos,
        }

        # Get user gamification stats
        user_stats = get_user_stats(request.user)

        return render(request, 'study_plan_detail.html', {
            'study_plan': study_plan,
            'weeks': weeks,
            'progress_stats': progress_stats,
            'user_stats': user_stats,
        })
    except StudyPlan.DoesNotExist:
        messages.error(request, 'Study plan not found.')
        return redirect('study_plans')


@csrf_exempt
@login_required
def toggle_week_completion(request, week_id):
    """Toggle completion status of a study week"""
    if request.method == 'POST':
        try:
            week = StudyWeek.objects.get(id=week_id, study_plan__user=request.user)
            week.is_completed = not week.is_completed

            gamification_result = None
            if week.is_completed:
                from django.utils import timezone
                week.completed_at = timezone.now()
                # Award XP and check achievements
                gamification_result = handle_week_completion(request.user, week)
            else:
                week.completed_at = None
            week.save()

            response_data = {
                'success': True,
                'is_completed': week.is_completed,
                'completed_at': week.completed_at.isoformat() if week.completed_at else None
            }

            if gamification_result:
                response_data['gamification'] = gamification_result

            return JsonResponse(response_data)
        except StudyWeek.DoesNotExist:
            return JsonResponse({'error': 'Week not found'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)


@csrf_exempt
@login_required
def toggle_activity_completion(request, activity_id):
    """Toggle completion status of a study activity"""
    if request.method == 'POST':
        try:
            activity = StudyActivity.objects.get(id=activity_id, study_week__study_plan__user=request.user)
            activity.is_completed = not activity.is_completed

            gamification_result = None
            if activity.is_completed:
                from django.utils import timezone
                activity.completed_at = timezone.now()
                # Award XP and check achievements
                gamification_result = handle_activity_completion(request.user, activity)
            else:
                activity.completed_at = None
            activity.save()

            response_data = {
                'success': True,
                'is_completed': activity.is_completed,
                'completed_at': activity.completed_at.isoformat() if activity.completed_at else None
            }

            if gamification_result:
                response_data['gamification'] = gamification_result

            return JsonResponse(response_data)
        except StudyActivity.DoesNotExist:
            return JsonResponse({'error': 'Activity not found'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)


@csrf_exempt
@login_required
def toggle_video_watched(request, resource_id):
    """Toggle watched status of a learning resource (video)"""
    if request.method == 'POST':
        try:
            resource = LearningResource.objects.get(
                id=resource_id,
                study_week__study_plan__user=request.user
            )
            resource.is_watched = not resource.is_watched

            gamification_result = None
            if resource.is_watched:
                from django.utils import timezone
                resource.watched_at = timezone.now()
                # Award XP and check achievements
                gamification_result = handle_video_watched(request.user, resource)
            else:
                resource.watched_at = None
            resource.save()

            response_data = {
                'success': True,
                'is_watched': resource.is_watched,
                'watched_at': resource.watched_at.isoformat() if resource.watched_at else None
            }

            if gamification_result:
                response_data['gamification'] = gamification_result

            return JsonResponse(response_data)
        except LearningResource.DoesNotExist:
            return JsonResponse({'error': 'Resource not found'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)


@login_required
def user_dashboard(request):
    """Display user's gamification dashboard with stats and achievements"""
    user_stats = get_user_stats(request.user)

    # Get all achievements with unlock status
    all_achievements = Achievement.objects.all()
    unlocked_ids = UserAchievement.objects.filter(user=request.user).values_list('achievement_id', flat=True)

    achievements_data = []
    for achievement in all_achievements:
        achievements_data.append({
            'achievement': achievement,
            'unlocked': achievement.id in unlocked_ids,
            'user_achievement': UserAchievement.objects.filter(
                user=request.user,
                achievement=achievement
            ).first() if achievement.id in unlocked_ids else None
        })

    return render(request, 'dashboard.html', {
        'user_stats': user_stats,
        'achievements_data': achievements_data,
    })


@csrf_exempt
@login_required
def mark_achievements_seen(request):
    """Mark all new achievements as seen"""
    if request.method == 'POST':
        UserAchievement.objects.filter(user=request.user, is_new=True).update(is_new=False)
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Invalid request method'}, status=400)


# Authentication Views
def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            return redirect('landing')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'auth/login.html')

def user_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('landing')

def user_register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        # Validation
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'auth/register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'auth/register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return render(request, 'auth/register.html')

        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name
        )

        messages.success(request, 'Account created successfully! Please log in.')
        return redirect('login')

    return render(request, 'auth/register.html')


# ============================================================================
# QUIZ VIEWS
# ============================================================================

@csrf_exempt
@login_required
def generate_quiz(request, week_id):
    """Generate a quiz for a specific study week"""
    if request.method == 'POST':
        try:
            from quiz_generator import generate_quiz_for_week

            data = json.loads(request.body)
            difficulty = data.get('difficulty', 'medium')
            num_questions = int(data.get('num_questions', 10))

            study_week = StudyWeek.objects.get(id=week_id, study_plan__user=request.user)

            # Check if quiz already exists
            existing_quiz = Quiz.objects.filter(study_week=study_week).first()
            if existing_quiz:
                return JsonResponse({
                    'success': False,
                    'error': 'Quiz already exists for this week',
                    'quiz_id': existing_quiz.id
                })

            # Generate the quiz
            quiz = generate_quiz_for_week(study_week, difficulty, num_questions)

            return JsonResponse({
                'success': True,
                'quiz_id': quiz.id,
                'message': f'Quiz generated with {quiz.total_questions} questions!'
            })

        except StudyWeek.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Study week not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=400)


@login_required
def quiz_detail(request, quiz_id):
    """Display quiz taking interface"""
    try:
        quiz = Quiz.objects.prefetch_related('questions__answers').get(
            id=quiz_id,
            study_plan__user=request.user
        )

        # Get user's previous attempts
        attempts = QuizAttempt.objects.filter(
            quiz=quiz,
            user=request.user
        ).order_by('-started_at')

        # Check if there's an incomplete attempt
        incomplete_attempt = attempts.filter(is_completed=False).first()

        context = {
            'quiz': quiz,
            'attempts': attempts.filter(is_completed=True),
            'incomplete_attempt': incomplete_attempt,
            'best_score': attempts.filter(is_completed=True).order_by('-score').first()
        }

        return render(request, 'quiz_detail.html', context)

    except Quiz.DoesNotExist:
        messages.error(request, 'Quiz not found')
        return redirect('study_plans')


@csrf_exempt
@login_required
def start_quiz(request, quiz_id):
    """Start a new quiz attempt"""
    if request.method == 'POST':
        try:
            quiz = Quiz.objects.get(id=quiz_id, study_plan__user=request.user)

            # Create new attempt
            attempt = QuizAttempt.objects.create(
                user=request.user,
                quiz=quiz,
                max_score=quiz.total_points
            )

            return JsonResponse({
                'success': True,
                'attempt_id': attempt.id
            })

        except Quiz.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Quiz not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=400)


@csrf_exempt
@login_required
def submit_quiz(request, attempt_id):
    """Submit quiz answers and calculate score"""
    if request.method == 'POST':
        try:
            from gamification_helper import award_xp, check_and_unlock_achievements
            from django.utils import timezone

            data = json.loads(request.body)
            answers = data.get('answers', {})  # {question_id: answer_id}
            time_taken = data.get('time_taken_seconds', 0)

            attempt = QuizAttempt.objects.get(
                id=attempt_id,
                user=request.user,
                is_completed=False
            )

            # Save answers
            attempt.answers = answers
            attempt.time_taken_seconds = time_taken
            attempt.completed_at = timezone.now()
            attempt.is_completed = True

            # Calculate score
            score, max_score = attempt.calculate_score()

            # Handle gamification for quiz completion
            from gamification_helper import handle_quiz_completion

            gamification_data = None
            if attempt.passed:
                xp_awarded = attempt.quiz.xp_reward
                attempt.xp_awarded = xp_awarded
                attempt.save()

                # Award XP for passing
                profile = award_xp(request.user, xp_awarded, f"Passed quiz: {attempt.quiz.title}")

                # Update quiz stats and check achievements
                quiz_stats = handle_quiz_completion(request.user, attempt)

                gamification_data = {
                    'xp_awarded': xp_awarded,
                    'reason': f"Passed quiz: {attempt.quiz.title}",
                    'leveled_up': profile.get('leveled_up', False),
                    'level': profile.get('level', 1),
                    'quiz_stats': quiz_stats
                }
            else:
                attempt.save()
                # Still update quiz stats even if failed
                quiz_stats = handle_quiz_completion(request.user, attempt)

            return JsonResponse({
                'success': True,
                'score': score,
                'max_score': max_score,
                'percentage': attempt.percentage,
                'passed': attempt.passed,
                'time_taken': attempt.time_taken_formatted,
                'gamification': gamification_data
            })

        except QuizAttempt.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Quiz attempt not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=400)


@login_required
def quiz_results(request, attempt_id):
    """Display quiz results with detailed feedback"""
    try:
        attempt = QuizAttempt.objects.select_related('quiz').prefetch_related(
            'quiz__questions__answers'
        ).get(id=attempt_id, user=request.user, is_completed=True)

        # Build results data
        results = []
        for question in attempt.quiz.questions.all():
            user_answer_id = attempt.answers.get(str(question.id))
            user_answer = None
            if user_answer_id:
                try:
                    user_answer = Answer.objects.get(id=user_answer_id)
                except Answer.DoesNotExist:
                    pass

            correct_answer = question.correct_answer

            results.append({
                'question': question,
                'user_answer': user_answer,
                'correct_answer': correct_answer,
                'is_correct': user_answer == correct_answer if user_answer else False
            })

        context = {
            'attempt': attempt,
            'results': results
        }

        return render(request, 'quiz_results.html', context)

    except QuizAttempt.DoesNotExist:
        messages.error(request, 'Quiz results not found')
        return redirect('study_plans')
