from django.views.generic import TemplateView
from web_project import TemplateLayout
from django.shortcuts import render, get_object_or_404, redirect

"""
This file is a view controller for multiple pages as a module.
Here you can override the page view layout.
Refer to kanban/urls.py file for more pages.
"""


class AcademyView(TemplateView):
    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))

        return context
    

class KanbanAcademyView(AcademyView):
    template_name = "kanban/app_kanban.html"
    permission_required = [] 

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)


        context.update({
            "title": "Profile",
            "heading": "Edit Profile",
        })
        
        return context
    
class ChatAcademyViews(AcademyView):
    template_name = "chat/app_chat.html"
    permission_required = []