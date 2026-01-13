"""
URL configuration for web_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path
from web_project.views import SystemView
from django.conf import settings             # <--- Tambahkan ini
from django.conf.urls.static import static   # <--- Tambahkan ini

urlpatterns = [
    path("admin/", admin.site.urls),

    # layouts urls
    path("", include("apps.layouts.urls")),

    # Chat urls
    path("", include("apps.chat.urls")),

    # Calendar urls
    path("", include("apps.my_calendar.urls")),

    # kanban urls
    path("", include("apps.kanban.urls")),

    # Academy urls
    path("", include("apps.academy.urls")),

    # auth urls
    path("", include("auth.urls")),

]

handler404 = SystemView.as_view(template_name="pages_misc_error.html", status=404)
handler403 = SystemView.as_view(template_name="pages_misc_not_authorized.html", status=403)
handler400 = SystemView.as_view(template_name="pages_misc_error.html", status=400)
handler500 = SystemView.as_view(template_name="pages_misc_error.html", status=500)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)