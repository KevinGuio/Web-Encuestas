from django import forms
from .models import Survey, Rating, Comment

class SurveyCreateForm(forms.ModelForm):
    # Campo para seleccionar el número de respuestas (1-5)
    num_answers = forms.ChoiceField(
        label="Número de respuestas",
        choices=[(i, str(i)) for i in range(1, 6)],
        widget=forms.Select(attrs={'id': 'num_answers'})
    )
    
    # Campos dinámicos para las respuestas (se manejarán con JavaScript)
    answer_1 = forms.CharField(label="Respuesta 1", max_length=200)
    answer_2 = forms.CharField(label="Respuesta 2", max_length=200, required=False)
    answer_3 = forms.CharField(label="Respuesta 3", max_length=200, required=False)
    answer_4 = forms.CharField(label="Respuesta 4", max_length=200, required=False)
    answer_5 = forms.CharField(label="Respuesta 5", max_length=200, required=False)

    class Meta:
        model = Survey
        fields = ['title', 'description', 'category', 'deadline']
        widgets = {
            'deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        num_answers = int(cleaned_data.get('num_answers', 0))
        
        # Validar que las respuestas requeridas no estén vacías
        for i in range(1, num_answers + 1):
            if not cleaned_data.get(f'answer_{i}'):
                self.add_error(f'answer_{i}', 'Este campo es obligatorio.')

class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['stars']
        widgets = {
            'stars': forms.RadioSelect(choices=[
                (1, '★'), 
                (2, '★★'), 
                (3, '★★★'), 
                (4, '★★★★'), 
                (5, '★★★★★')
            ])
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'Escribe tu comentario...'
            })
        }

class ReplyForm(CommentForm):
    class Meta(CommentForm.Meta):
        widgets = {
            'text': forms.Textarea(attrs={
                'rows': 1,
                'placeholder': 'Escribe una respuesta...'
            })
        }