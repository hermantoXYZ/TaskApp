from django.urls import path
from .views import AcademyView, AddCourse, EditCourse, ListCourse, DeleteCourse, AddCourseParticipant, AddCourseAgenda, CourseAnnouncementView, CourseAttendanceView, ManageCurriculumView, AddCourseMaterialView, DeleteCourseMaterialView, EditCourseMaterialView, ViewsAllCourse, AddProgramStudiCourse, EditProgramStudiCourse, DeleteProgramStudiCourse, AddCoursePeriod, EditCoursePeriod, DeleteCoursePeriod, AddCourseAssignmentView, DeleteCourseAgenda, InstructorCoursePreviewView, AppPasswordChangeView
from .views_students import UserProfileView
from django.contrib.auth.decorators import login_required
from . import views
from .views_prodi_set import UserListView, UserListJsonView
from .views_students import StudentCourseListView, CoursePlayerView, StudentQuizStartView, StudentQuizTakeView, StudentQuizSubmitView, StudentQuizResultView
from .views_export_data import CourseRecapitulationView
from .views_apps import KanbanAcademyView, ChatAcademyViews, StartChatView
from .views_dosen import DosenProfileView
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('tambah/academy/course/', AddCourse.as_view(), name='tambah-academy-course'),
    path('views/academy/course/<uuid:course_uuid>/', ViewsAllCourse.as_view(), name='edit-all-academy-course'),
    path('edit/academy/course/<uuid:course_uuid>/', EditCourse.as_view(), name='edit-academy-course'),
    path('list/academy/course/', ListCourse.as_view(), name='list-academy-course'),
    path('course/delete/<uuid:course_uuid>/', DeleteCourse.as_view(), name='delete_course'),
    path('course/<uuid:course_uuid>/participant/', views.AddCourseParticipant.as_view(), name='add-course-participant'),
    path('course/<uuid:course_uuid>/participant/<int:participant_id>/delete/', views.DeleteCourseParticipant.as_view(), name='delete-participant'),
    path('course/<uuid:course_uuid>/agenda/', AddCourseAgenda.as_view(), name='add-course-agenda'),
    path('course/<uuid:course_uuid>/agenda/<int:agenda_id>/edit/', views.EditCourseAgenda.as_view(), name='edit-course-agenda'),
    path('course/<uuid:course_uuid>/agenda/<int:agenda_id>/delete/', DeleteCourseAgenda.as_view(), name='delete-agenda'),
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
    path('course/delete/<uuid:pk>/', DeleteProgramStudiCourse.as_view(), name='delete-program-studi-course'),
    path('list-course-period', AddCoursePeriod.as_view(), name='list-course-period'),
    path('course/period/edit/<uuid:pk>/', EditCoursePeriod.as_view(), name='edit-course-period'),
    path('course/period/delete/<uuid:pk>/', DeleteCoursePeriod.as_view(), name='delete-course-period'),

    path('course/<uuid:course_uuid>/rekapitulasi/', CourseRecapitulationView.as_view(), name='course-rekapitulasi'),

    path('course/<uuid:course_uuid>/preview/', InstructorCoursePreviewView.as_view(), name='course-preview'),
    path('course/<uuid:course_uuid>/preview/material/<int:material_id>/', InstructorCoursePreviewView.as_view(), name='course-preview-material'),
    path('course/<uuid:course_uuid>/preview/assignment/<int:assignment_id>/', InstructorCoursePreviewView.as_view(), name='course-preview-assignment'),

    # path('course/submission/<int:submission_id>/update-grade/', views.update_grade_submission, name='update-grade-submission'),
    # # user
    path('profile/mahasiswa', UserProfileView.as_view(), name='profile'),
    path('dosen/profile/', DosenProfileView.as_view(), name='dosen-profile'),
    path('login/', views.loginView, name='login'),
    path("logout/",LogoutView.as_view(),name="logout",),
    path("app/user/listss/", UserListView.as_view(), name="app-user-lists"),
    path("users/json/", UserListJsonView.as_view(), name="user-list-json"),
    path("", views.loginView, name="login"),

    # === PUBLIC URLS ===
    path('public/share/<uuid:course_uuid>/agenda/<int:agenda_id>/', views.PublicAgendaMaterialView.as_view(), name='public-agenda-material'),

    path('account/password/change/', AppPasswordChangeView.as_view(), name='password_change'),


    # QUIZ URLS
    path('course/<uuid:course_uuid>/quizzes/', views.CourseQuizListView.as_view(), name='course-quiz-list'),
    path('course/<uuid:course_uuid>/quizzes/create/', views.QuizCreateView.as_view(), name='course-quiz-create'),
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
    path('course/<uuid:course_uuid>/learn/material/<int:material_id>/', CoursePlayerView.as_view(), name='course-player-material'),
    path('course/<uuid:course_uuid>/learn/assignment/<int:assignment_id>/', CoursePlayerView.as_view(), name='course-player-assignment'),

    path('quiz/<uuid:quiz_id>/start/', StudentQuizStartView.as_view(), name='student-quiz-start'),
    path('quiz/attempt/<uuid:attempt_id>/take/', StudentQuizTakeView.as_view(), name='student-quiz-take'),
    path('quiz/attempt/<uuid:attempt_id>/submit/', StudentQuizSubmitView.as_view(), name='student-quiz-submit'), 
    path('quiz/attempt/<uuid:attempt_id>/result/', StudentQuizResultView.as_view(), name='student-quiz-result'),

    # === GROUP URLS === #
    path('course/<uuid:course_uuid>/groups/', views.CourseGroupListView.as_view(), name='course-groups'),
    path('groups/<uuid:group_id>/', views.CourseGroupDetailView.as_view(), name='group-detail'),

    # === KANBAN & CHAT URLS === #
    path('app/kanban/', KanbanAcademyView.as_view(), name="app-kanban"),
    path('chat/', ChatAcademyViews.as_view(), name='chat-index'),
    path('chat/<uuid:room_uuid>/', ChatAcademyViews.as_view(), name='chat-detail'),
    path('chat/start/<int:target_user_id>/', StartChatView.as_view(), name='chat-start'),
    path("app/academy/dashboard/",login_required(AcademyView.as_view(template_name="app_academy_dashboard.html")),name="app-academy-dashboard",),
]
