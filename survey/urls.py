from django.urls import path
from .views import SurveyCreateView
from .views import SurveyDetailView
from .views import SurveyListView
from .views import vote
from .views import SurveyUpdateView
from .views import SurveyDeleteView
from .views import ExportSurveyView

urlpatterns = [
    path('create/', SurveyCreateView.as_view(), name='survey_create'),
    path('<int:pk>/', SurveyDetailView.as_view(), name='survey_detail'),
    path('<int:survey_id>/vote/<int:answer_id>/', vote, name='vote'),
    path('', SurveyListView.as_view(), name='survey_list'),
    path('<int:pk>/edit/', SurveyUpdateView.as_view(), name='survey_edit'),
    path('<int:pk>/delete/', SurveyDeleteView.as_view(), name='survey_delete'),
    path('<int:pk>/export/', ExportSurveyView.as_view(), name='survey_export'),
]