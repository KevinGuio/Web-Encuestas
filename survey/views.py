from django.views.generic import CreateView
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Survey, Answer, UserVote, Rating, Comment
from .forms import SurveyCreateForm, RatingForm, CommentForm
from django.shortcuts import redirect
from django.views.generic import DetailView
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
from django.views.generic import DetailView
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from .models import Survey, UserVote, Rating
from .forms import RatingForm
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.template.loader import render_to_string

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
        user = self.request.user  # Usamos el usuario del request

        # Lógica de expiración
        context['is_expired'] = timezone.now() > survey.deadline
        
        # Verificar si el usuario ha votado
        if user.is_authenticated:
            context['user_has_voted'] = UserVote.objects.filter(
                user=user, 
                survey=survey
            ).exists()
            
            # Lógica de valoraciones
            context['user_rating'] = Rating.objects.filter(
                user=user,
                survey=survey
            ).first()
        
        # Datos de valoraciones para todos los usuarios
        context['rating_form'] = RatingForm()
        context['average_rating'] = survey.get_average_rating()
        
        return context

    def post(self, request, *args, **kwargs):
        survey = self.get_object()
        user = request.user
        
        if not user.is_authenticated:
            messages.warning(request, 'Debes iniciar sesión para valorar encuestas')
            return redirect('login')
            
        form = RatingForm(request.POST)
        
        if form.is_valid():
            Rating.objects.update_or_create(
                user=user,
                survey=survey,
                defaults={'stars': form.cleaned_data['stars']}
            )
            messages.success(request, '¡Gracias por valorar la encuesta!')
            return redirect('survey_detail', pk=survey.pk)
        
        # Si el formulario no es válido, recargamos la página con errores
        return self.render_to_response(self.get_context_data(form=form))

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


from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json

@require_POST
def rate_survey(request, pk):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Debes iniciar sesión'}, status=403)
    
    try:
        stars = int(request.POST.get('stars') or json.loads(request.body).get('stars'))
        survey = Survey.objects.get(pk=pk)
        
        if timezone.now() > survey.deadline:
            return JsonResponse({'error': 'Esta encuesta ha finalizado'}, status=403)
        
        rating, created = Rating.objects.update_or_create(
            user=request.user,
            survey=survey,
            defaults={'stars': stars}
        )
        
        # Calcular nuevo promedio
        average = survey.get_average_rating()
        full = int(average)
        half = 1 if (average - full) >= 0.5 else 0
        
        return JsonResponse({
            'success': True,
            'average': round(average, 1),
            'full': full,
            'half': half
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_POST
def post_comment(request, survey_id):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Debes iniciar sesión'}, status=403)
    
    survey = get_object_or_404(Survey, id=survey_id)
    
    if timezone.now() > survey.deadline:
        return JsonResponse({'error': 'La encuesta ha finalizado'}, status=403)
    
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.survey = survey
        comment.user = request.user
        comment.save()
        return JsonResponse({
            'success': True,
            'comment': render_to_string('surveys/comment.html', {'comment': comment})
        })
    
    return JsonResponse({'error': 'Comentario inválido'}, status=400)

@require_POST
def like_comment(request, comment_id):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Debes iniciar sesión'}, status=403)
    
    comment = get_object_or_404(Comment, id=comment_id)
    
    if comment.likes.filter(id=request.user.id).exists():
        comment.likes.remove(request.user)
        liked = False
    else:
        comment.likes.add(request.user)
        liked = True
    
    return JsonResponse({
        'liked': liked,
        'total_likes': comment.total_likes()
    })

@require_POST
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    
    if not comment.can_delete(request.user):
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    comment.delete()
    return JsonResponse({'success': True})