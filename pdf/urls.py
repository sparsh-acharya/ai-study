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
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.user_register, name='register'),
]
