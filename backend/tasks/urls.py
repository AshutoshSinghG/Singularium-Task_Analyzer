"""
URL routing for tasks app API endpoints.
"""
from django.urls import path
from .views import AnalyzeTasksView, SuggestTasksView

urlpatterns = [
    path('tasks/analyze/', AnalyzeTasksView.as_view(), name='analyze-tasks'),
    path('tasks/suggest/', SuggestTasksView.as_view(), name='suggest-tasks'),
]
