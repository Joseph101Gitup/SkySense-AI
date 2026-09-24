from django.urls import path
from . import views

app_name = 'predictions'

urlpatterns = [
    path('demo/', views.demo_view, name='demo'),
    path('demo/analyze/', views.demo_analyze_view, name='demo_analyze'),
    path('demo/image/<path:subpath>', views.demo_image_serve_view, name='demo_image_serve'),
    path('predict/', views.predict_view, name='predict'),
    path('predict/sample/', views.predict_sample_view, name='predict_sample'),
    path('predictions/<uuid:pk>/result/', views.result_view, name='result'),
    path('predictions/<uuid:pk>/', views.detail_view, name='detail'),
    path('predictions/<uuid:pk>/delete/', views.delete_view, name='delete'),
    path('history/', views.history_view, name='history'),
    path('api/predict/', views.api_predict_view, name='api_predict'),
]
