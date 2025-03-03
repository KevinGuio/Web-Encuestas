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
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from .models import Survey, UserVote, Rating
from .forms import RatingForm
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from .models import Survey
from django.db.models import Q

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
    if survey.is_blocked:
        return redirect('survey_detail', pk=survey.id)
    
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
    survey = get_object_or_404(Survey, pk=pk)
    
    if survey.is_blocked:
        return redirect('survey_detail', pk=survey.id)
    
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
def post_comment(request, pk):
    survey = get_object_or_404(Survey, pk=pk)
    if survey.is_blocked:
        return redirect('survey_detail', pk=survey.id)
    try:
        comment = Comment.objects.create(
            user=request.user,
            survey=survey,
            text=request.POST.get('text'),
            parent_id=request.POST.get('parent_id')
        )
        
        return JsonResponse({
            'success': True,
            'comment_id': comment.id,
            'username': request.user.username,
            'is_owner_or_admin': request.user == comment.user or request.user.is_staff,
            'text': comment.text
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@require_POST
@login_required
def like_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    user = request.user
    
    try:
        # Verificar si el usuario ya dio like
        liked = user in comment.likes.all()
        if liked:
            comment.likes.remove(user)
        else:
            comment.likes.add(user)
        
        # Devolver datos actualizados
        return JsonResponse({
            'success': True,
            'liked': not liked,  # Estado invertido
            'total_likes': comment.likes.count()
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_POST
def delete_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    if not (request.user == comment.user or request.user.is_staff):
        return JsonResponse({'success': False, 'error': 'No tienes permiso'}, status=403)
    
    try:
        comment.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


from django.contrib.contenttypes.models import ContentType
from .models import Report
from django.http import HttpResponseForbidden
from django.shortcuts import render

@require_POST
@login_required
def create_report(request):
    content_type = request.POST.get('content_type')
    object_id = request.POST.get('object_id')
    reason = request.POST.get('reason', '')
    
    try:
        model_class = ContentType.objects.get(model=content_type).model_class()
        content_object = model_class.objects.get(pk=object_id)
        
        Report.objects.create(
            content_object=content_object,
            reporter=request.user,
            reason=reason
        )
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

from django.contrib.contenttypes.models import ContentType

@staff_member_required
def survey_management(request):
    surveys = Survey.objects.all().order_by('-created_at')
    return render(request, 'surveys/survey_management.html', {
        'surveys': surveys
    })

def report_list(request):
    reports = Report.objects.filter(resolved=False).prefetch_related('content_type')
    
    # Obtener todos los objetos reportados en una sola consulta
    content_types = ContentType.objects.filter(
        pk__in=reports.values_list('content_type', flat=True).distinct()
    )
    
    # Mapear content_types a sus modelos
    model_classes = {ct.id: ct.model_class() for ct in content_types}
    
    # Obtener todos los IDs de los objetos reportados
    object_ids = {
        ct.id: list(reports.filter(content_type=ct).values_list('object_id', flat=True))
        for ct in content_types
    }
    
    # Obtener todos los objetos en una consulta por modelo
    fetched_objects = {}
    for ct_id, model_class in model_classes.items():
        if model_class:
            fetched_objects[ct_id] = model_class.objects.filter(
                pk__in=object_ids[ct_id]
            ).in_bulk()
    
    # Adjuntar los objetos a los reportes
    for report in reports:
        model_class = model_classes.get(report.content_type_id)
        if model_class:
            report.content_object = fetched_objects.get(
                report.content_type_id, {}
            ).get(report.object_id)
    
    return render(request, 'surveys/report_list.html', {'reports': reports})

@require_POST
@staff_member_required
def resolve_report(request, pk):
    report = get_object_or_404(Report, pk=pk)
    report.resolved = True
    report.save()
    return JsonResponse({'success': True})

@csrf_exempt
def toggle_survey_block(request, survey_id):
    if request.method == 'POST':
        survey = get_object_or_404(Survey, id=survey_id)
        data = json.loads(request.body)
        reason = data.get('reason', None)

        if reason:
            survey.is_blocked = True
            survey.block_reason = reason
            survey.blocked_at = timezone.now()
        else:
            survey.is_blocked = False
            survey.block_reason = ''
            survey.blocked_at = None

        survey.save()
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Invalid request method'}, status=400)


def survey_list(request):
    query = request.GET.get('q', '').strip()  # Limpiar espacios en blanco
    current_time = timezone.now()
    
    # Filtrar solo por título y encuestas no expiradas
    surveys = Survey.objects.filter(
        Q(title__icontains=query)
    ).order_by('-created_at')
    
    context = {
        'surveys': surveys,
        'search_query': query,
        'current_time': current_time
    }
    return render(request, 'surveys/survey_list.html', context)