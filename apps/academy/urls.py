from django.urls import path
from .views import AcademyView, AddCourse, EditCourse, ListCourse, DeleteCourse, AddCourseParticipant, AddCourseAgenda, CourseAnnouncementView, CourseAttendanceView, ManageCurriculumView, AddCourseMaterialView, DeleteCourseMaterialView, EditCourseMaterialView, ViewsAllCourse, AddProgramStudiCourse, EditProgramStudiCourse, DeleteProgramStudiCourse, AddCoursePeriod, EditCoursePeriod, DeleteCoursePeriod, AddCourseAssignmentView, DeleteCourseAgenda
from .views_students import UserProfileView
from django.contrib.auth.decorators import login_required
from . import views
from .views_prodi_set import UserListView, UserListJsonView
from .views_students import StudentCourseListView, CoursePlayerView
from .views_export_data import CourseRecapitulationView

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


    path('course/submission/<int:submission_id>/update-grade/', views.update_grade_submission, name='update-grade-submission'),
    # user
    path('profile/mahasiswa', UserProfileView.as_view(), name='profile'),
    path('login/', views.loginView, name='login'),
    path("app/user/listss/", UserListView.as_view(), name="app-user-lists"),
    path("users/json/", UserListJsonView.as_view(), name="user-list-json"),
    path("", views.loginView, name="login"),

    # students
    path('app/academy/course/', StudentCourseListView.as_view(), name='app-academy-course'),
    path('course/<uuid:course_uuid>/learn/', CoursePlayerView.as_view(), name='course-player'),
    path('course/<uuid:course_uuid>/learn/material/<int:material_id>/', CoursePlayerView.as_view(), name='course-player-material'),
    path('course/<uuid:course_uuid>/learn/assignment/<int:assignment_id>/', CoursePlayerView.as_view(), name='course-player-assignment'),


    # user public
    path('public/share/<uuid:course_uuid>/agenda/<int:agenda_id>/', views.PublicAgendaMaterialView.as_view(), name='public-agenda-material'),

    path(
        "app/academy/dashboard/",
        login_required(AcademyView.as_view(template_name="app_academy_dashboard.html")),
        name="app-academy-dashboard",
    ),
    path(
        "app/academy/course_details/",
        login_required(AcademyView.as_view(template_name="app_academy_course_details.html")),
        name="app-academy-course-details",
    ),
    path(
        "app-perpustakaan/",
        login_required(AcademyView.as_view(template_name="app_perpustakaan.html")),
        name="app-perpustakaan",
    )
]
