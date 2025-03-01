from django.views.generic import CreateView
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Survey, Answer
from .forms import SurveyCreateForm
from django.shortcuts import redirect
from django.views.generic import DetailView
from .models import Survey
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from .models import Survey, Answer, UserVote
from django.views.generic import UpdateView, DeleteView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse_lazy
from django.utils import timezone
import csv
from django.http import HttpResponse

class SurveyCreateView(LoginRequiredMixin, CreateView):
    model = Survey
    form_class = SurveyCreateForm
    template_name = 'surveys/survey_create.html'
    
    def form_valid(self, form):
        # Asignar el usuario actual como creador
        survey = form.save(commit=False)
        survey.creator = self.request.user
        survey.save()
        
        # Crear las respuestas
        num_answers = int(form.cleaned_data['num_answers'])
        for i in range(1, num_answers + 1):
            Answer.objects.create(
                survey=survey,
                text=form.cleaned_data[f'answer_{i}']
            )
        
        return redirect('survey_detail', pk=survey.pk)  # Redirige al detalle

class SurveyDetailView(DetailView):
    model = Survey
    template_name = 'surveys/survey_detail.html'
    context_object_name = 'survey'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        survey = self.object
        
        # Verificar si la encuesta ha expirado
        context['is_expired'] = timezone.now() > survey.deadline
        
        # Resto de lógica existente
        if self.request.user.is_authenticated:
            context['user_has_voted'] = UserVote.objects.filter(
                user=self.request.user, 
                survey=survey
            ).exists()
            
        return context

from django.views.generic import ListView

class SurveyListView(ListView):
    model = Survey
    template_name = 'surveys/survey_list.html'
    context_object_name = 'surveys'
    ordering = ['-created_at']
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_time'] = timezone.now()
        return context

@login_required
@require_POST
def vote(request, survey_id, answer_id):
    survey = get_object_or_404(Survey, id=survey_id)
    answer = get_object_or_404(Answer, id=answer_id, survey=survey)
    
    # Verificar si el usuario ya votó
    if UserVote.objects.filter(user=request.user, survey=survey).exists():
        return redirect('survey_detail', pk=survey.id)
    
    # Registrar el voto
    answer.votes += 1
    answer.save()
    UserVote.objects.create(user=request.user, survey=survey)
    
    return redirect('survey_detail', pk=survey.id)

# Editar Encuesta
class SurveyUpdateView(UserPassesTestMixin, UpdateView):
    model = Survey
    form_class = SurveyCreateForm  # Reutilizamos el formulario de creación
    template_name = 'surveys/survey_edit.html'
    
    def test_func(self):
        """Solo el creador o un admin puede editar"""
        survey = self.get_object()
        return self.request.user == survey.creator or self.request.user.is_staff
    
    def form_valid(self, form):
        survey = form.save()
        
        # Actualizar respuestas existentes o crear nuevas
        num_answers = int(form.cleaned_data['num_answers'])
        existing_answers = survey.answers.all().order_by('id')
        
        for i in range(1, num_answers + 1):
            answer_text = form.cleaned_data[f'answer_{i}']
            if i <= len(existing_answers):
                answer = existing_answers[i-1]
                answer.text = answer_text
                answer.save()
            else:
                Answer.objects.create(survey=survey, text=answer_text)
        
        # Eliminar respuestas sobrantes si se redujo el número
        if len(existing_answers) > num_answers:
            for answer in existing_answers[num_answers:]:
                answer.delete()
                
        return redirect('survey_detail', pk=survey.pk)

# Eliminar Encuesta
class SurveyDeleteView(UserPassesTestMixin, DeleteView):
    model = Survey
    template_name = 'surveys/survey_delete.html'
    success_url = reverse_lazy('survey_list')  # Redirige al listado
    
    def test_func(self):
        """Solo el creador o un admin puede eliminar"""
        survey = self.get_object()
        return self.request.user == survey.creator or self.request.user.is_staff


class HomeView(SurveyListView):
    template_name = 'global/home.html'
    paginate_by = None  # No paginar en la página principal

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_time'] = timezone.now()
        return context


import csv
from django.http import HttpResponse

class ExportSurveyView(UserPassesTestMixin, View):
    def test_func(self):
        survey = get_object_or_404(Survey, pk=self.kwargs['pk'])
        return (self.request.user == survey.creator or self.request.user.is_staff) and timezone.now() > survey.deadline

    def get(self, request, pk):
        survey = get_object_or_404(Survey, pk=pk)
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{survey.title}_resultados.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Respuesta', 'Votos', 'Porcentaje'])
        
        total_votes = sum(answer.votes for answer in survey.answers.all())
        
        for answer in survey.answers.all():
            percentage = (answer.votes / total_votes * 100) if total_votes > 0 else 0
            writer.writerow([
                answer.text,
                answer.votes,
                f"{percentage:.2f}%"
            ])
            
        return response