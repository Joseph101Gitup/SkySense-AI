from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.landing_view, name='landing'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('api/dashboard/stats/', views.api_dashboard_stats, name='api_dashboard_stats'),
    path('about/', views.about_view, name='about'),
    path('model/', views.model_info_view, name='model_info'),
    path('performance/', views.model_performance_view, name='model_performance'),
    path('metrics/', views.model_performance_view, name='research_metrics'),
]
