from django.shortcuts import redirect
from django.contrib import messages
from .models import UserDosen
from functools import wraps
from django.utils import timezone
from django.contrib.auth.mixins import AccessMixin

now = timezone.now()

class DosenRequiredMixin(AccessMixin):
    """Verify that the current user is authenticated and is a Dosen."""
    def dispatch(self, request, *args, **kwargs):
        # 1. Cek Login
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # 2. Cek Role Dosen (Sesuai logika Anda)
        if request.user.last_name != "Dosen":
            # Redirect ke dashboard jika bukan dosen
            return redirect('/app/academy/dashboard/')
            
        return super().dispatch(request, *args, **kwargs)