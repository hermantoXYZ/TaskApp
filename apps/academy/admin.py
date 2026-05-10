
# Register your models here.
from .models import ChatMessage, ChatRoom, UserDosen, UserMhs, UserProdi, Prodi, CoursePeriod, Course, CourseParticipant, CourseAgenda, CourseAnnouncement, CourseAttendance, CourseMaterial, StudentMaterialProgress, CourseAssignment, StudentAssignmentSubmission, StudentQuizAnswer, StudentQuizAttempt, QuizOption, BookCategory, Book, CalendarEvent, CourseDiscussion, CourseDiscussionReply, CourseDiscussionLike, CourseGroup, MediaFile, AgendaMediaItem, CategoryPortfolio, StudentPortfolio, KanbanBoard, KanbanTask, AppDocumentation
from django.contrib import admin

admin.site.register(AppDocumentation)

from import_export.admin import ImportExportModelAdmin
from .admin_resources import UserMhsResource, UserDsnResource

class UserMhsImport(ImportExportModelAdmin):
    resource_class = UserMhsResource  

class UserDsnImport(ImportExportModelAdmin):
    resource_class = UserDsnResource  
admin.site.register(UserMhs, UserMhsImport)
admin.site.register(UserDosen, UserDsnImport)
admin.site.register(UserProdi)

@admin.register(Prodi)
class ProdiAdmin(admin.ModelAdmin):
    list_display = ('nama_prodi', 'strata', 'gelar', 'status')
    list_filter = ('status', 'strata') 
    search_fields = ('nama_prodi', 'gelar')

@admin.register(CoursePeriod)
class CoursePeriodAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at') 
    search_fields = ('name',)

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'group', 'created_at', 'updated_at' ,'code')
    list_filter = ('period', 'group', 'created_at')
    search_fields = ('name',)

@admin.register(CourseParticipant)
class CourseParticipantAdmin(admin.ModelAdmin):
    list_display = ('course', 'mahasiswa', 'joined_at')


@admin.register(CourseAgenda)
class CourseAgendaAdmin(admin.ModelAdmin):
    list_display = ('course', 'created_at', 'created_by')
    search_fields = ('course__name', 'agenda_type')

@admin.register(CourseAnnouncement)
class CourseAnnouncementAdmin(admin.ModelAdmin):
    list_display = ('course', 'title', 'created_at', 'created_by')
    search_fields = ('course__name', 'title')


@admin.register(CourseAttendance)
class CourseAttendanceAdmin(admin.ModelAdmin):
    list_display = ('participant', 'agenda', 'status', 'created_at')
    search_fields = ('agenda__name', 'participant__username')

@admin.register(CourseMaterial)
class CourseMaterialAdmin(admin.ModelAdmin):
    list_display = ('title', 'agenda', 'created_at')

@admin.register(KanbanTask)
class KanbanTaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'updated_at')

@admin.register(KanbanBoard)
class KanbanBoardAdmin(admin.ModelAdmin):
    list_display = ('title','created_at' )
    search_fields = ('title',)
    list_filter = ('created_at',)

@admin.register(StudentMaterialProgress)
class StudentMaterialProgressAdmin(admin.ModelAdmin):
    list_display = ('participant', 'material', 'completed_at')

@admin.register(CourseAssignment)
class CourseAssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'assignment_type', 'created_at')

@admin.register(StudentAssignmentSubmission)
class StudentAssignmentSubmissionAdmin(admin.ModelAdmin):
    list_display = ('student', 'updated_at')

@admin.register(MediaFile)
class MediaFileAdmin(admin.ModelAdmin):
    list_display = ('name', 'file_type', 'created_at', 'file_size')

@admin.register(AgendaMediaItem)
class AgendaMediaItemAdmin(admin.ModelAdmin):
    list_display = ('agenda', 'media_file', 'created_at')
    list_filter = ('created_at',)

@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'room_type', 'updated_at', 'created_at')
    search_fields = ('name',)
    list_filter = ('created_at',)

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('content', 'is_read', 'created_at', 'room')
    list_filter = ('created_at',)

    

admin.site.register(StudentQuizAnswer)
admin.site.register(StudentQuizAttempt)
admin.site.register(QuizOption)


admin.site.register(BookCategory)
admin.site.register(Book)
admin.site.register(CalendarEvent)
admin.site.register(CourseDiscussion)
admin.site.register(CourseDiscussionReply)
admin.site.register(CourseDiscussionLike)
admin.site.register(CourseGroup)
admin.site.register(CategoryPortfolio)
admin.site.register(StudentPortfolio)
