from django.contrib import admin
from django.urls import path,include
from pdf import views

urlpatterns = [
    path('',views.landing,name='landing'),
    path('upload/',views.upload,name='upload'),
    path('analyze/', views.analyze, name='analyze'),
    path('study-plans/', views.study_plans, name='study_plans'),
    path('study-plan/<int:plan_id>/', views.study_plan_detail, name='study_plan_detail'),
    path('toggle-week/<int:week_id>/', views.toggle_week_completion, name='toggle_week_completion'),
    path('toggle-activity/<int:activity_id>/', views.toggle_activity_completion, name='toggle_activity_completion'),
    path('toggle-video/<int:resource_id>/', views.toggle_video_watched, name='toggle_video_watched'),
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('mark-achievements-seen/', views.mark_achievements_seen, name='mark_achievements_seen'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.user_register, name='register'),

    # Quiz URLs
    path('generate-quiz/<int:week_id>/', views.generate_quiz, name='generate_quiz'),
    path('quiz/<int:quiz_id>/', views.quiz_detail, name='quiz_detail'),
    path('quiz/<int:quiz_id>/start/', views.start_quiz, name='start_quiz'),
    path('quiz-attempt/<int:attempt_id>/submit/', views.submit_quiz, name='submit_quiz'),
    path('quiz-attempt/<int:attempt_id>/results/', views.quiz_results, name='quiz_results'),
]
