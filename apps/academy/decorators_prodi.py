from django.shortcuts import redirect
from django.contrib import messages
from .models import UserProdi 
from functools import wraps

def check_userprodi(function):
    def wrapper(request, *args, **kwargs):
        userprodi = UserProdi.objects.get(username=request.user)
        request.userprodi = userprodi
        if userprodi.photo == None :
            messages.error(request, "Lengkapi data anda terlebih dahulu!")
            return redirect('/acd/profile_prodi')               
        return function(request, *args, **kwargs)
    
    return wrapper


def admin_prodi_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.last_name != "Admin Prodi":
            return redirect('/acd/dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view