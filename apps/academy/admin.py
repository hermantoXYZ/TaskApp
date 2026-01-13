
# Register your models here.
from .models import UserDosen, UserMhs, Prodi, CoursePeriod, Course, CourseParticipant, CourseAgenda, CourseAnnouncement, CourseAttendance, CourseMaterial, StudentMaterialProgress
from django.contrib import admin




from import_export.admin import ImportExportModelAdmin
from .admin_resources import UserMhsResource, UserDsnResource

class UserMhsImport(ImportExportModelAdmin):
    resource_class = UserMhsResource  # Import User Mahasiswa

class UserDsnImport(ImportExportModelAdmin):
    resource_class = UserDsnResource  # Import User DOSEN


admin.site.register(UserMhs, UserMhsImport)
admin.site.register(UserDosen, UserDsnImport)



admin.site.register(Prodi)
admin.site.register(CoursePeriod)
admin.site.register(Course)
admin.site.register(CourseParticipant)
admin.site.register(CourseAgenda)
admin.site.register(CourseAnnouncement)
admin.site.register(CourseAttendance)
admin.site.register(CourseMaterial)
admin.site.register(StudentMaterialProgress)