from django.urls import path
from .views import AcademyView, AddCourse, EditCourse, ListCourse, DeleteCourse, AddCourseParticipant, AddCourseAgenda, CourseAnnouncementView, CourseAttendanceView, ManageCurriculumView, AddCourseMaterialView, DeleteCourseMaterialView, EditCourseMaterialView, EditAllCourse, AddProgramStudiCourse, EditProgramStudiCourse, DeleteProgramStudiCourse, AddCoursePeriod, EditCoursePeriod, DeleteCoursePeriod, AddCourseAssignmentView
from .views_students import UserProfileView
from django.contrib.auth.decorators import login_required
from . import views
from .views_prodi_set import UserListView, UserListJsonView
from .views_students import StudentCourseListView, CoursePlayerView


urlpatterns = [
    path('tambah/academy/course/', AddCourse.as_view(), name='tambah-academy-course'),
    path('edit/academy/course/<int:course_id>/', EditAllCourse.as_view(), name='edit-all-academy-course'),
    path('course/<int:course_id>/edit/', EditCourse.as_view(), name='edit-academy-course'),
    path('list/academy/course/', ListCourse.as_view(), name='list-academy-course'),
    path('course/delete/<int:course_id>/', DeleteCourse.as_view(), name='delete_course'),
    path('course/<int:course_id>/add-participant/', AddCourseParticipant.as_view(), name='add-course-participant'),
    path('course/<int:course_id>/add-agenda/', AddCourseAgenda.as_view(), name='add-course-agenda'),
    path('course/<int:course_id>/agenda/<int:agenda_id>/edit/', views.EditCourseAgenda.as_view(), name='edit-course-agenda'),
    path('course/<int:course_id>/agenda/<int:agenda_id>/delete/', views.DeleteCourseAgenda.as_view(), name='delete-course-agenda'),
    
    path('course/<int:course_id>/announcement/', CourseAnnouncementView.as_view(), name='add-course-announcement'),
    path('agenda/<int:agenda_id>/attendance/', CourseAttendanceView.as_view(), name='course-attendance'),

    
    path('course/<int:course_id>/curriculum/', ManageCurriculumView.as_view(), name='manage-curriculum'),
    path('course/<int:course_id>/curriculum/add-material/', AddCourseMaterialView.as_view(), name='add-course-material'),
    path('course/<int:course_id>/curriculum/material/<int:material_id>/edit/', EditCourseMaterialView.as_view(), name='edit-course-material'),
    path('course/<int:course_id>/learn/<int:material_id>/', CoursePlayerView.as_view(), name='course-player-detail'),
    path('course/<int:course_id>/curriculum/material/<int:material_id>/delete/', DeleteCourseMaterialView.as_view(), name='delete-course-material'),
    path('course/program-studi', AddProgramStudiCourse.as_view(), name='program-studi-course'),
    path('course/edit/progam-studi/<uuid:pk>/', EditProgramStudiCourse.as_view(), name='edit-program-studi-course'),
    path('course/delete/<uuid:pk>/', DeleteProgramStudiCourse.as_view(), name='delete-program-studi-course'),
    path('list-course-period', AddCoursePeriod.as_view(), name='list-course-period'),
    path('course/period/edit/<uuid:pk>/', EditCoursePeriod.as_view(), name='edit-course-period'),
    path('course/period/delete/<uuid:pk>/', DeleteCoursePeriod.as_view(), name='delete-course-period'),
    path('course/<int:course_id>/curriculum/add-assignment/', views.AddCourseAssignmentView.as_view(), name='add-course-assignment'),
    path('course/assignment/<int:assignment_id>/grading/', views.AssignmentGradingView.as_view(), name='assignment-grading'),
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
