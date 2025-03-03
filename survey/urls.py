from django.urls import path
from .views import SurveyCreateView
from .views import SurveyDetailView
from .views import SurveyListView
from .views import vote
from .views import SurveyUpdateView
from .views import SurveyDeleteView
from .views import ExportSurveyView
from .views import rate_survey
from . import views
from .views import survey_management, toggle_survey_block
urlpatterns = [
    path('create/', SurveyCreateView.as_view(), name='survey_create'),
    path('<int:pk>/', SurveyDetailView.as_view(), name='survey_detail'),
    path('<int:survey_id>/vote/<int:answer_id>/', vote, name='vote'),
    path('', SurveyListView.as_view(), name='survey_list'),
    path('<int:pk>/edit/', SurveyUpdateView.as_view(), name='survey_edit'),
    path('<int:pk>/delete/', SurveyDeleteView.as_view(), name='survey_delete'),
    path('<int:pk>/export/', ExportSurveyView.as_view(), name='survey_export'),
    path('<int:pk>/rate/', rate_survey, name='rate_survey'),
    path('survey/<int:pk>/comment/', views.post_comment, name='post_comment'),
    path('comments/<int:pk>/like/', views.like_comment, name='like_comment'),
    path('comments/<int:pk>/delete/', views.delete_comment, name='delete_comment'),
    path('report/', views.create_report, name='create_report'),
    path('reports/', views.report_list, name='report_list'),
    path('reports/<int:pk>/resolve/', views.resolve_report, name='resolve_report'),
    path('surveys_management/', survey_management, name='survey_management'),
    path('surveys_management/toggle-block/<int:survey_id>/', toggle_survey_block, name='toggle_survey_block'),
    path('surveys/', views.survey_list, name='survey_list'),
]