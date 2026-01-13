from django.shortcuts import redirect
from django.contrib import messages
from .models import UserMhs, User 
from functools import wraps
from django.contrib.auth.mixins import AccessMixin

def check_userstudents(function):
    def wrapper(request, *args, **kwargs):
        usermhs = UserMhs.objects.get(nim=request.user) 
        request.usermhs = usermhs
        if usermhs.photo == None or usermhs.tempat_lahir == None or usermhs.tgl_lahir == None or usermhs.gender == None or usermhs.penasehat_akademik == None:
            messages.error(request, "Lengkapi data anda terlebih dahulu!")
            return redirect('/acd/profile_mhs')               
        return function(request, *args, **kwargs)
    return wrapper


class StudentsRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        # 1. Cek Login
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.last_name != "Mahasiswa":
            return redirect('/app/academy/dashboard/')
            
        return super().dispatch(request, *args, **kwargs)
