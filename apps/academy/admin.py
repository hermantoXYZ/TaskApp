
# Register your models here.
from .models import ChatMessage, ChatRoom, UserDosen, UserMhs, UserProdi, Prodi, CoursePeriod, Course, CourseParticipant, CourseAgenda, CourseAnnouncement, CourseAttendance, CourseMaterial, StudentMaterialProgress, CourseAssignment, StudentAssignmentSubmission, StudentQuizAnswer, StudentQuizAttempt, QuizOption, BookCategory, Book, CalendarEvent, CourseDiscussion, CourseDiscussionReply, CourseDiscussionLike, CourseGroup, MediaFile, AgendaMediaItem, CategoryPortfolio, StudentPortfolio, KanbanBoard, KanbanTask, AppDocumentation
from django.contrib import admin

admin.site.register(AppDocumentation)




from import_export.admin import ImportExportModelAdmin
from .admin_resources import UserMhsResource, UserDsnResource

class UserMhsImport(ImportExportModelAdmin):
    resource_class = UserMhsResource  # Import User Mahasiswa

class UserDsnImport(ImportExportModelAdmin):
    resource_class = UserDsnResource  # Import User DOSEN


admin.site.register(UserMhs, UserMhsImport)
admin.site.register(UserDosen, UserDsnImport)
admin.site.register(UserProdi)



admin.site.register(Prodi)
admin.site.register(CoursePeriod)
admin.site.register(Course)
admin.site.register(CourseParticipant)
admin.site.register(CourseAgenda)
admin.site.register(CourseAnnouncement)
admin.site.register(CourseAttendance)
admin.site.register(CourseMaterial)
admin.site.register(StudentMaterialProgress)
admin.site.register(CourseAssignment)
admin.site.register(StudentAssignmentSubmission)
admin.site.register(StudentQuizAnswer)
admin.site.register(StudentQuizAttempt)
admin.site.register(QuizOption)
admin.site.register(ChatMessage)
admin.site.register(ChatRoom)
admin.site.register(BookCategory)
admin.site.register(Book)
admin.site.register(CalendarEvent)
admin.site.register(CourseDiscussion)
admin.site.register(CourseDiscussionReply)
admin.site.register(CourseDiscussionLike)
admin.site.register(CourseGroup)
admin.site.register(MediaFile)
admin.site.register(AgendaMediaItem)
admin.site.register(CategoryPortfolio)
admin.site.register(StudentPortfolio)
admin.site.register(KanbanBoard)
admin.site.register(KanbanTask)
