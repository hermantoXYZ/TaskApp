from django.shortcuts import redirect
from django.contrib import messages
from .models import UserProdi 
from functools import wraps
from django.utils import timezone
from django.contrib.auth.mixins import AccessMixin
from django.contrib.auth.mixins import LoginRequiredMixin


now = timezone.now()

class ProdiRequiredMixin(AccessMixin):
    """Verify that the current user is authenticated and is a Dosen."""
    def dispatch(self, request, *args, **kwargs):
        # 1. Cek Login
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # 2. Cek Role Dosen (Sesuai logika Anda)
        if request.user.last_name != "Prodi":
            # Redirect ke dashboard jika bukan dosen
            return redirect('/app/academy/dashboard/')
            
        return super().dispatch(request, *args, **kwargs)



class ProdiOrAdminMixin(LoginRequiredMixin):
    """Hanya UserProdi, staff, atau superuser yang boleh akses."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.is_staff or request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)
        if UserProdi.objects.filter(username=request.user).exists():
            return super().dispatch(request, *args, **kwargs)
        messages.error(request, 'Anda tidak memiliki akses ke halaman ini.')
        return redirect('app-academy-dashboard')



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