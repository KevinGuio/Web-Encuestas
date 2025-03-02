from django.utils import timezone
from django.shortcuts import redirect
from django.contrib import messages

class CheckSuspensionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.user.is_suspended:
            if request.user.suspension_end > timezone.now():
                messages.error(request, f"Tu cuenta está suspendida hasta {request.user.suspension_end.strftime('%d/%m/%Y %H:%M')}. Motivo: {request.user.suspension_reason}")
                return redirect('login')
            else:
                # Auto-remove suspension if time expired
                request.user.is_suspended = False
                request.user.save()
                
        return self.get_response(request)