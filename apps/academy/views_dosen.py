from django.views.generic import TemplateView
from web_project import TemplateLayout
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import UserDosen
from .forms_dosen import DosenProfileForm
from .decorators_dosen import DosenRequiredMixin # Pastikan Anda punya ini atau gunakan LoginRequiredMixin


class AcademyView(TemplateView):
    # Predefined function
    def get_context_data(self, **kwargs):
        # A function to init the global layout. It is defined in web_project/__init__.py file
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))

        return context
    
class DosenProfileView(DosenRequiredMixin, AcademyView):
    template_name = "dosen/profile.html" 
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 1. Ambil data Dosen berdasarkan user yang login
        # nip adalah OneToOne ke User, jadi kita bisa query pakai request.user
        userdosen = get_object_or_404(UserDosen, nip=self.request.user)

        # 2. Setup Form
        if 'form' not in kwargs:
            kwargs['form'] = DosenProfileForm(instance=userdosen)
        
        # 3. Update Context
        context.update({
            "title": "Profil Dosen",
            "heading": "Edit Profil Dosen",
            "userdosen": userdosen,
            "photo": userdosen.photo,
            "form": kwargs['form'],
        })
        
        return context

    def post(self, request, *args, **kwargs):
        userdosen = get_object_or_404(UserDosen, nip=request.user)
        
        # Jangan lupa request.FILES untuk upload foto
        form = DosenProfileForm(request.POST, request.FILES, instance=userdosen)
        
        if form.is_valid():
            form.save()
            
            # Update juga nama depan/belakang di tabel User utama jika perlu
            user = request.user
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            if first_name or last_name:
                user.first_name = first_name
                user.last_name = last_name
                user.save()

            messages.success(request, 'Data profil berhasil diperbarui!')
            return redirect('dosen-profile') 
        else:
            messages.error(request, 'Gagal menyimpan. Periksa kembali isian Anda.')
            return self.render_to_response(self.get_context_data(form=form))