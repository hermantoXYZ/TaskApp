from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import AppDocumentation
from web_project import TemplateLayout
from django.views.generic import TemplateView

class DocumentationListView(LoginRequiredMixin, TemplateView):
    template_name = "documentation/list.html"

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        user = self.request.user
        
        # Determine user role
        target = 'all'
        if hasattr(user, 'userdosen'):
            target = 'dosen'
        elif hasattr(user, 'usermhs'):
            target = 'mahasiswa'
        elif hasattr(user, 'userprodi') or user.is_superuser:
            target = 'admin'
        
        # Filter documentation based on role and 'all'
        docs = AppDocumentation.objects.filter(target_audience__in=[target, 'all']).order_by('-created_at')
        
        context.update({
            "title": "Panduan Penggunaan",
            "heading": "Dokumentasi & Panduan",
            "docs": docs,
            "user_role": target,
        })
        return context

class DocumentationDetailView(LoginRequiredMixin, TemplateView):
    template_name = "documentation/detail.html"

    def get_context_data(self, slug, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        doc = get_object_or_404(AppDocumentation, slug=slug)

        doc.view_count += 1
        doc.save(update_fields=['view_count'])
        
        embed_video_url = doc.video_url
        if embed_video_url:
            if 'youtube.com/watch?v=' in embed_video_url:
                video_id = embed_video_url.split('v=')[1].split('&')[0]
                embed_video_url = f"https://www.youtube.com/embed/{video_id}"
            elif 'youtu.be/' in embed_video_url:
                video_id = embed_video_url.split('youtu.be/')[1].split('?')[0]
                embed_video_url = f"https://www.youtube.com/embed/{video_id}"

        context.update({
            "title": doc.title,
            "heading": "Detail Panduan",
            "doc": doc,
            "embed_video_url": embed_video_url,
        })
        return context
