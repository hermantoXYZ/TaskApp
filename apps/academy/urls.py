from django.urls import path
from .views import AcademyView, AcademyDashboardView, AddCourse, EditCourse, ListCourse, AddCourseParticipant, AddCourseAgenda, CourseAnnouncementView, CourseAttendanceView, ManageCurriculumView, AddCourseMaterialView, DeleteCourseMaterialView, EditCourseMaterialView, ViewsAllCourse, AddProgramStudiCourse, EditProgramStudiCourse, AddCoursePeriod, EditCoursePeriod, AddCourseAssignmentView, DeleteCourseAgenda, AppPasswordChangeView, CoursePreviewPublicView, MediaLibraryListView, MediaLibraryUploadView, MediaLibraryDeleteView, MediaLibraryAttachView, DeleteAgendaMediaItemView, ListDosenCourse
from .views_students import UserProfileView
from django.contrib.auth.decorators import login_required
from . import views
from .views_prodi_set import UserListView, reset_password, LecturerPerformanceView, LecturerPerformanceDetailView, ClassReportView
from .views_students import StudentCourseListView, CoursePlayerView, StudentQuizStartView, StudentQuizTakeView, StudentQuizSubmitView, StudentQuizResultView, StudentLibraryListView, StudentBookDetailView, CourseLeaderboardView, StudentCourseGradesView
from .views_export_data import CourseRecapitulationView
from .views_apps import KanbanAcademyView, ChatAcademyViews, StartChatView, CalendarEventListCreateView, CalendarEventDetailView, StudentPortfolioListView, StudentPortfolioAddView, StudentPortfolioEditView, StudentPortfolioDeleteView, AdminPortfolioListView, PortfolioVerifyView, PublicPortfolioView, DosenPortfolioListView, PublicPortfolioDetailView, AdminPortfolioDeleteView, KanbanBoardListCreateView, KanbanBoardDetailView, KanbanTaskListCreateView, KanbanTaskDetailView, KanbanReorderView, KanbanUserSearchView
from .views_dosen import DosenProfileView, AddBookView, ManageCategoryView, DeleteBookView, DeleteCategoryView, ListBookView, EditBookView
from .views_discussion import (
    CourseDiscussionListView, CourseDiscussionDetailView, CourseDiscussionTogglePinView, CourseDiscussionToggleCloseView,
    CourseDiscussionDeleteView,
    DiscussionLikeToggleView, ReplyLikeToggleView, DiscussionReplyDeleteView,
)
from .views_documentation import DocumentationListView, DocumentationDetailView
from django.contrib.auth.views import LogoutView
from .views_import import (
    SetupSemesterView,
    ImportCoursesView,
    ImportCoachesView,
    ImportParticipantsView,
    DownloadTemplateView,
)

urlpatterns = [
    # === SETUP AWAL SEMESTER (Import Excel) ===
    path('setup/semester/', SetupSemesterView.as_view(), name='setup-semester'),
    path('import/courses/', ImportCoursesView.as_view(), name='import-courses'),
    path('import/coaches/', ImportCoachesView.as_view(), name='import-coaches'),
    path('import/participants/', ImportParticipantsView.as_view(), name='import-participants'),
    path('import/template/<str:tipe>/', DownloadTemplateView.as_view(),   name='download-template'),

    path('tambah/academy/course/', AddCourse.as_view(), name='tambah-academy-course'),
    path('views/academy/course/<uuid:course_uuid>/', ViewsAllCourse.as_view(), name='edit-all-academy-course'),
    path('edit/academy/course/<uuid:course_uuid>/', EditCourse.as_view(), name='edit-academy-course'),
    path('list/academy/course/', ListCourse.as_view(), name='list-academy-course'),
    path('course/<uuid:course_uuid>/participant/', views.AddCourseParticipant.as_view(), name='add-course-participant'),
    path('course/<uuid:course_uuid>/agenda/', AddCourseAgenda.as_view(), name='add-course-agenda'),
    path('course/<uuid:course_uuid>/agenda/<int:agenda_id>/edit/', views.EditCourseAgenda.as_view(), name='edit-course-agenda'),
    # path('course/<uuid:course_uuid>/agenda/<int:agenda_id>/delete/', DeleteCourseAgenda.as_view(), name='delete-agenda'),
    path('course/<uuid:course_uuid>/agenda/<int:agenda_id>/attendance/', views.CourseAttendanceView.as_view(), name='course-attendance'),
    path('course/<uuid:course_uuid>/curriculum/', ManageCurriculumView.as_view(), name='manage-curriculum'),
    path('course/<uuid:course_uuid>/curriculum/material/', AddCourseMaterialView.as_view(), name='add-course-material'),
    path('course/<uuid:course_uuid>/curriculum/material/<int:material_id>/delete/', DeleteCourseMaterialView.as_view(), name='delete-course-material'),
    path('course/<uuid:course_uuid>/curriculum/material/<int:material_id>/edit/', EditCourseMaterialView.as_view(), name='edit-course-material'),
    path('course/<uuid:course_uuid>/learn/<int:material_id>/', CoursePlayerView.as_view(), name='course-player-detail'),
    path('course/<uuid:course_uuid>/curriculum/assignment/', views.AddCourseAssignmentView.as_view(), name='add-course-assignment'),
    path('course/<uuid:course_uuid>/curriculum/assignment/<int:assignment_id>/edit/', views.EditCourseAssignmentView.as_view(), name='edit-course-assignment'),
    path('course/<uuid:course_uuid>/assignment/<int:assignment_id>/delete/', views.DeleteCourseAssignmentView.as_view(), name='delete-course-assignment'),
    path('course/<uuid:course_uuid>/assignment/<int:assignment_id>/grading/', views.AssignmentGradingView.as_view(), name='assignment-grading'),
    path('course/<uuid:course_uuid>/announcement/', CourseAnnouncementView.as_view(), name='add-course-announcement'),
    path('course/<uuid:course_uuid>/announcement/<int:announcement_id>/delete/', views.DeleteCourseAnnouncementView.as_view(), name='delete-course-announcement'),
    path('course/program-studi', AddProgramStudiCourse.as_view(), name='program-studi-course'),
    path('course/edit/progam-studi/<uuid:pk>/', EditProgramStudiCourse.as_view(), name='edit-program-studi-course'),
    # path('course/delete/<uuid:pk>/', DeleteProgramStudiCourse.as_view(), name='delete-program-studi-course'),
    path('list-course-period', AddCoursePeriod.as_view(), name='list-course-period'),
    path('course/period/edit/<uuid:pk>/', EditCoursePeriod.as_view(), name='edit-course-period'),
    path('course/<uuid:course_uuid>/rekapitulasi/', CourseRecapitulationView.as_view(), name='course-rekapitulasi'),
    
    # === PRODI COURSE AGENDA URLS ===
    path('prodi/course/<uuid:course_uuid>/agenda/', views.AdminCourseAgendaListView.as_view(), name='admin-course-agenda'),
    path('prodi/course/<uuid:course_uuid>/agenda/create/', views.AdminCourseAgendaCreateView.as_view(), name='admin-course-agenda-create'),
    path('prodi/course/<uuid:course_uuid>/agenda/<int:agenda_id>/edit/', views.AdminCourseAgendaEditView.as_view(), name='admin-course-agenda-edit'),

    # === DOSEN URL ===
    path('list/dosen/course/', ListDosenCourse.as_view(), name='list-dosen-course'),

    # === PUBLIC COURSE PREVIEW URLS ===
    path('course/<uuid:course_uuid>/preview/public/', CoursePreviewPublicView.as_view(), name='course-preview-public'),   
    path('course/<uuid:course_uuid>/preview/public/material/<int:material_id>/', CoursePreviewPublicView.as_view(), name='course-preview-public-material'),
    path('course/<uuid:course_uuid>/preview/public/assignment/<int:assignment_id>/', CoursePreviewPublicView.as_view(), name='course-preview-public-assignment'), 

    # path('course/submission/<int:submission_id>/update-grade/', views.update_grade_submission, name='update-grade-submission'),
    # # user
    path('profile/mahasiswa', UserProfileView.as_view(), name='profile'),
    path('dosen/profile/', DosenProfileView.as_view(), name='dosen-profile'),
    path('login/', views.loginView, name='login'),
    path("logout/",LogoutView.as_view(),name="logout",),
    path("app/user/listss/", UserListView.as_view(), name="app-user-lists"),
    path("app/user/<str:id>/reset-password/", reset_password, name="app-user-reset-password"),
    path("reports/lps/",LecturerPerformanceView.as_view(),name="lps-report"),
    path("reports/lps/<str:nip>/",LecturerPerformanceDetailView.as_view(), name="lps-detail"),
    path("reports/class-report/", ClassReportView.as_view(), name="lecturer-class-report"),
    path("", views.loginView, name="login"),
    
    # === PUBLIC URLS ===
    path('account/password/change/', AppPasswordChangeView.as_view(), name='password_change'),

    # QUIZ URLS
    path('course/<uuid:course_uuid>/assessment/', views.CourseAssessmentView.as_view(), name='course-assessment'),
    path('course/<uuid:course_uuid>/quizzes/', views.CourseQuizListView.as_view(), name='course-quiz-list'),
    path('course/<uuid:course_uuid>/quizzes/create/', views.QuizCreateView.as_view(), name='course-quiz-create'),
    path('course/<uuid:course_uuid>/quiz/<uuid:quiz_id>/edit/', views.CourseQuizUpdateView.as_view(), name='course-quiz-edit'),
    path('quiz/<uuid:quiz_id>/manage/', views.QuizManageView.as_view(), name='quiz-manage'),
    path('quiz/<uuid:quiz_id>/add-question/<str:q_type>/', views.AddQuizQuestionView.as_view(), name='quiz-add-question'),
    path('quiz/<uuid:quiz_id>/delete/', views.DeleteQuizView.as_view(), name='quiz-delete'),
    path('quiz/question/<uuid:question_id>/edit/', views.EditQuizQuestionView.as_view(), name='quiz-edit-question'),
    path('quiz/question/<uuid:question_id>/delete/', views.DeleteQuizQuestionView.as_view(), name='quiz-delete-question'),
    path('quiz/<uuid:quiz_id>/submissions/', views.QuizSubmissionListView.as_view(), name='quiz-submissions'),
    path('quiz/attempt/<uuid:attempt_id>/grade/', views.QuizSubmissionGradeView.as_view(), name='quiz-grade-submission'),

    # === MAHASISWA QUIZ ACCESS ===
    path('app/academy/course/', StudentCourseListView.as_view(), name='app-academy-course'),
    path('course/<uuid:course_uuid>/learn/', CoursePlayerView.as_view(), name='course-player'),
    path('course/<uuid:course_uuid>/leaderboard/', CourseLeaderboardView.as_view(), name='course-leaderboard'),
    path('course/<uuid:course_uuid>/grades/', StudentCourseGradesView.as_view(), name='student-course-grades'),
    path('course/<uuid:course_uuid>/learn/material/<int:material_id>/', CoursePlayerView.as_view(), name='course-player-material'),
    path('course/<uuid:course_uuid>/learn/assignment/<int:assignment_id>/', CoursePlayerView.as_view(), name='course-player-assignment'),

    path('quiz/<uuid:quiz_id>/start/', StudentQuizStartView.as_view(), name='student-quiz-start'),
    path('quiz/attempt/<uuid:attempt_id>/take/', StudentQuizTakeView.as_view(), name='student-quiz-take'),
    path('quiz/attempt/<uuid:attempt_id>/submit/', StudentQuizSubmitView.as_view(), name='student-quiz-submit'), 
    path('quiz/attempt/<uuid:attempt_id>/result/', StudentQuizResultView.as_view(), name='student-quiz-result'),

    path('app/library/', StudentLibraryListView.as_view(), name='student-library-list'),
    path('app/library/read/<uuid:pk>/', StudentBookDetailView.as_view(), name='student-book-read'),

    # === GROUP URLS === #
    path('course/<uuid:course_uuid>/groups/', views.CourseGroupListView.as_view(), name='course-groups'),
    path('groups/<uuid:group_id>/', views.CourseGroupDetailView.as_view(), name='group-detail'),

    # === BOOK URLS === #
    path('app/books/add/', AddBookView.as_view(), name='add-book'),
    path('app/books/edit/<uuid:pk>/', EditBookView.as_view(), name='edit-book'),
    path('app/list/books/', ListBookView.as_view(), name='list-books'),
    path('app/books/categories/', ManageCategoryView.as_view(), name='manage-category'),
    path('app/library/books/delete/<uuid:pk>/', DeleteBookView.as_view(), name='delete-book'),
    path('app/library/categories/delete/<int:pk>/', DeleteCategoryView.as_view(), name='delete-category'),

    # === KANBAN & CHAT URLS === #
    path('app/kanban/', KanbanAcademyView.as_view(), name="app-kanban"),

    # === KANBAN API ===
    path('api/kanban/boards/',                                   login_required(KanbanBoardListCreateView.as_view()), name='api-kanban-boards'),
    path('api/kanban/boards/<uuid:board_id>/',                   login_required(KanbanBoardDetailView.as_view()),     name='api-kanban-board-detail'),
    path('api/kanban/boards/<uuid:board_id>/tasks/',             login_required(KanbanTaskListCreateView.as_view()),  name='api-kanban-tasks'),
    path('api/kanban/tasks/<uuid:task_id>/',                     login_required(KanbanTaskDetailView.as_view()),      name='api-kanban-task-detail'),
    path('api/kanban/reorder/',                                  login_required(KanbanReorderView.as_view()),         name='api-kanban-reorder'),
    path('api/kanban/users/',                                    login_required(KanbanUserSearchView.as_view()),      name='api-kanban-users'),

    path('chat/', ChatAcademyViews.as_view(), name='chat-index'),
    path('chat/<uuid:room_uuid>/', ChatAcademyViews.as_view(), name='chat-detail'),
    path('chat/start/<int:target_user_id>/', StartChatView.as_view(), name='chat-start'),
    path("app/academy/dashboard/",login_required(AcademyDashboardView.as_view()),name="app-academy-dashboard",),
    path("app/academy/calender",login_required(AcademyView.as_view(template_name="app_academy_calender.html")),name="app-academy-calender",),

    # === CALENDAR API URLS ===
    path('api/calendar/events/', login_required(CalendarEventListCreateView.as_view()), name='api-calendar-events'),
    path('api/calendar/events/<int:pk>/', login_required(CalendarEventDetailView.as_view()), name='api-calendar-event-detail'),

    # === MEDIA LIBRARY API URLS ===
    path('api/media-library/',                   MediaLibraryListView.as_view(),   name='media-library-list'),
    path('api/media-library/upload/',             MediaLibraryUploadView.as_view(), name='media-library-upload'),
    path('api/media-library/attach/',             MediaLibraryAttachView.as_view(), name='media-library-attach'),
    path('api/media-library/<uuid:pk>/delete/',   MediaLibraryDeleteView.as_view(), name='media-library-delete'),

    path('course/<uuid:course_uuid>/media-item/<int:item_id>/delete/',
        DeleteAgendaMediaItemView.as_view(),
        name='delete-agenda-media-item'),

    # === DISCUSSION / FORUM URLS ===
    path('course/<uuid:course_uuid>/discussions/', CourseDiscussionListView.as_view(), name='course-discussion-list'),
    path('course/<uuid:course_uuid>/discussions/delete/<int:disc_id>/', CourseDiscussionDeleteView.as_view(), name='course-discussion-delete'),
    path('course/<uuid:course_uuid>/discussions/<int:disc_id>/', CourseDiscussionDetailView.as_view(), name='course-discussion-detail'),
    path('course/<uuid:course_uuid>/discussions/<int:disc_id>/pin/', CourseDiscussionTogglePinView.as_view(), name='course-discussion-pin'),
    path('course/<uuid:course_uuid>/discussions/<int:disc_id>/close/', CourseDiscussionToggleCloseView.as_view(), name='course-discussion-close'),
    path('course/<uuid:course_uuid>/discussions/<int:disc_id>/like/', DiscussionLikeToggleView.as_view(), name='discussion-like'),
    path('course/<uuid:course_uuid>/discussions/reply/<int:reply_id>/like/', ReplyLikeToggleView.as_view(), name='discussion-reply-like'),
    path('course/<uuid:course_uuid>/discussions/reply/<int:reply_id>/delete/', DiscussionReplyDeleteView.as_view(), name='discussion-reply-delete'),

    # === PORTFOLIO MAHASISWA ===
    path('app/portfolio/', StudentPortfolioListView.as_view(), name='portfolio-list'),
    path('app/portfolio/add/', StudentPortfolioAddView.as_view(), name='portfolio-add'),
    path('app/portfolio/<uuid:pk>/edit/', StudentPortfolioEditView.as_view(), name='portfolio-edit'),
    path('app/portfolio/<uuid:pk>/delete/', StudentPortfolioDeleteView.as_view(), name='portfolio-delete'),

    # === ADMIN PORTFOLIO ===
    path('prodi/portfolio/', AdminPortfolioListView.as_view(), name='admin-portfolio-list'),
    path('prodi/portfolio/<uuid:pk>/verify/', PortfolioVerifyView.as_view(), name='portfolio-verify'),
    path('prodi/portfolio/<uuid:pk>/delete/', AdminPortfolioDeleteView.as_view(), name='admin-portfolio-delete'),

    # === DOSEN PORTOFOLIO ===
    path('portfolio/mahasiswa', DosenPortfolioListView.as_view(), name='dosen-portfolio-list'),

    # === PUBLIC PORTFOLIO  /@username ===
    path('@<str:username>/',                             PublicPortfolioView.as_view(),       name='public-portfolio'),
    path('@<str:username>/<slug:slug>/',                 PublicPortfolioDetailView.as_view(), name='public-portfolio-detail'),

    # === DOCUMENTATION URLS ===
    path('app/documentation/', DocumentationListView.as_view(), name='documentation-list'),
    path('app/documentation/<slug:slug>/', DocumentationDetailView.as_view(), name='documentation-detail'),
]
