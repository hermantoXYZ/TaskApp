from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from functools import wraps
from django.contrib import messages

from .models import UserMhs, UserProdi, UserDosen

from django.contrib.auth.models import User

from .forms_prodi import formProfile, formUserEdit
from .decorators_prodi import admin_prodi_required, check_userprodi
from web_project.template_helpers.theme import TemplateHelper


from django.views.generic import TemplateView
from web_project import TemplateLayout
from django.contrib.auth.mixins import PermissionRequiredMixin

from django.http import JsonResponse
from django.views import View
########### SET PROFILE #####################################################

@admin_prodi_required
def profile_prodi(request):
    userprodi = UserProdi.objects.get(username=request.user)      
    if request.method == 'POST':
        form = formProfile(request.POST,  request.FILES, instance=userprodi)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil Anda berhasil diperbarui!')
            return redirect('/acd/profile_prodi')
    else:
        form = formProfile(instance=userprodi)

    context = {
        'title' : 'Profile',
        'heading' : 'Edit Profile',
        'userprodi' : userprodi,
        'photo' : userprodi.photo,
        'form': form,
    }
    return render(request, 'prodi/set/profile.html', context)



########### SETTING USER LAIN #####################################################

class UsersView(PermissionRequiredMixin, TemplateView):
    permission_required = ("user.view_user", "user.delete_user", "user.change_user", "user.add_user")


    # Predefined function
    def get_context_data(self, **kwargs):
        # A function to init the global layout. It is defined in web_project/__init__.py file
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))

        return context


class UserListView(UsersView):
    template_name = "app_user_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        role = self.request.GET.get("role", "Mahasiswa")

        if role == "Mahasiswa":
            users = UserMhs.objects.select_related("prodi")
        elif role == "Dosen":
            users = UserDosen.objects.select_related("prodi")
        else:
            users = []

        context.update({
            "title": "User List",
            "heading": f"Daftar {role}",
            "role": role,
            "users": users,
        })

        return context

class UserListJsonView(View):
    def get(self, request):
        role = request.GET.get("role", "Mahasiswa")

        if role == "Mahasiswa":
            queryset = UserMhs.objects.select_related("nim", "prodi")
        elif role == "Dosen":
            queryset = UserDosen.objects.select_related("nip", "prodi")
        else:
            queryset = []

        data = []

        for user in queryset:
            if role == "Mahasiswa":
                auth_user = user.nim
                avatar = user.photo.url if user.photo else None

            elif role == "Dosen":
                auth_user = user.nip
                avatar = user.photo.url if user.photo else None

            data.append({
                "id": user.pk,  # pk = username
                "full_name": f"{auth_user.first_name} {auth_user.last_name}".strip(),
                "email": auth_user.email,
                "role": role,
                "program_studi": (user.prodi.nama_prodi if user.prodi else "N/A"),
                "status": 2 if auth_user.is_active else 3,
                "avatar": avatar,
                "action": ""
            })
            

        return JsonResponse({"data": data})


@check_userprodi
@admin_prodi_required
def user_edit(request, id, role):
    userprodi = request.userprodi  
    userMaster = get_object_or_404(User, username=id)
    if role == 'Mahasiswa':
        userSelect = get_object_or_404(UserMhs, nim=id)
    if role == 'Dosen':
        userSelect = get_object_or_404(UserDosen, nip=id)
    if request.method == 'POST':
        form = formUserEdit(request.POST, request.FILES, instance=userSelect)
        if form.is_valid():
            userSelect.save()  
            messages.success(request, 'Update User Berhasil')
            if role == 'Mahasiswa':
                return redirect('acd:user_edit', userSelect.nim_id, role)
            else:
                return redirect('acd:user_edit', userSelect.nip_id, role)
        else:
            messages.error(request, 'periksa kembali isian data anda!')
            if role == 'Mahasiswa':
                return redirect('acd:user_edit', userSelect.nim_id, role)
            else:
                return redirect('acd:user_edit', userSelect.nip_id, role)

    else:
        form = formUserEdit(instance=userSelect)

    context = {
        'title' : 'Edit User',
        'heading' : 'Edit User',
        'userprodi' : userprodi,
        'photo' : userprodi.photo,
        'userselect' : userSelect,
        'usermaster' : userMaster,
        'form': form,
    }
    return render(request, 'prodi/set/user_edit.html', context)