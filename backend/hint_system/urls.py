"""
URL configuration for hint_system project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.http import JsonResponse
from hints.views import HintViewSet
from hints.problem_views import ProblemViewSet
from hints.code_views import CodeViewSet
from hints.auth_views import AuthViewSet
from hints.social_views import LeaderboardViewSet, ForumPostViewSet, SolutionShareViewSet

router = DefaultRouter()
router.register(r'hints', HintViewSet, basename='hint')
router.register(r'problems', ProblemViewSet, basename='problem')
router.register(r'code', CodeViewSet, basename='code')
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'leaderboard', LeaderboardViewSet, basename='leaderboard')
router.register(r'forums', ForumPostViewSet, basename='forum')
router.register(r'solutions', SolutionShareViewSet, basename='solution')

from hints.analytics_views import AnalyticsViewSet
router.register(r'analytics', AnalyticsViewSet, basename='analytics')

from hints.sheet_views import ProblemSheetViewSet
router.register(r'sheets', ProblemSheetViewSet, basename='sheet')

from hints.daily_views import DailyProblemViewSet
router.register(r'daily', DailyProblemViewSet, basename='daily')

from struggle_analysis.views import (
    TrajectoryViewSet,
    TrajectoryAnalysisView,
    StruggleAssessmentView,
    StruggleLLMAssessmentView,
    StruggleComparisonView,
    StruggleExperimentView,
    ControlledPatternView,
    StruggleHybridAssessmentView,
    ExportAnnotationBatchView,
    SubmitAnnotationView,
    EvaluateModelsView
)
router.register(r'struggle-analysis/features', TrajectoryViewSet, basename='trajectory-features')

def root_view(request):
    return JsonResponse({
        "name": "Hint Generation API",
        "status": "ok",
        "routes": [
            "/api/hints/", 
            "/api/problems/", 
            "/api/code/", 
            "/api/auth/", 
            "/api/struggle-analysis/trajectory/<problem_id>/",
            "/api/struggle-analysis/assess/<problem_id>/",
            "/api/struggle-analysis/llm-assess/<problem_id>/",
            "/api/struggle-analysis/compare/<problem_id>/",
            "/api/struggle-analysis/hybrid/<problem_id>/",
            "/api/struggle-analysis/experiment/<problem_id>/",
            "/api/struggle-analysis/patterns/",
            "/api/struggle-analysis/annotation/export-batch/",
            "/api/struggle-analysis/annotation/submit/",
            "/api/struggle-analysis/annotation/evaluate/",
            "/admin/"
        ]
    })

urlpatterns = [
    path('', root_view, name='root'),
    path('admin/', admin.site.urls),
    path('api/struggle-analysis/trajectory/<str:problem_id>/', TrajectoryAnalysisView.as_view(), name='trajectory-analysis'),
    path('api/struggle-analysis/assess/<str:problem_id>/', StruggleAssessmentView.as_view(), name='struggle-assessment'),
    path('api/struggle-analysis/llm-assess/<str:problem_id>/', StruggleLLMAssessmentView.as_view(), name='struggle-llm-assess'),
    path('api/struggle-analysis/compare/<str:problem_id>/', StruggleComparisonView.as_view(), name='struggle-compare'),
    path('api/struggle-analysis/hybrid/<str:problem_id>/', StruggleHybridAssessmentView.as_view(), name='struggle-hybrid'),
    path('api/struggle-analysis/experiment/<str:problem_id>/', StruggleExperimentView.as_view(), name='struggle-experiment'),
    path('api/struggle-analysis/patterns/', ControlledPatternView.as_view(), name='struggle-patterns'),
    path('api/struggle-analysis/annotation/export-batch/', ExportAnnotationBatchView.as_view(), name='struggle-export-batch'),
    path('api/struggle-analysis/annotation/submit/', SubmitAnnotationView.as_view(), name='struggle-submit-annotation'),
    path('api/struggle-analysis/annotation/evaluate/', EvaluateModelsView.as_view(), name='struggle-evaluate-models'),
    path('api/', include(router.urls)),
]



