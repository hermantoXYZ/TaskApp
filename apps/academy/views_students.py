from django.views.generic import TemplateView
from django.shortcuts import redirect, get_object_or_404, render
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from web_project import TemplateLayout
from .models import UserMhs, UserDosen, Course, CourseParticipant, CourseAgenda, CourseMaterial, CourseAssignment, CourseAnnouncement, StudentMaterialProgress, StudentAssignmentSubmission, CourseAttendance
from .forms_mhs import MhsProfileForm  # Pastikan import form Anda
from django.contrib.auth.mixins import LoginRequiredMixin
from .decorators_students import StudentsRequiredMixin
from django.utils import timezone

class AcademyView(TemplateView):
    # Predefined function
    def get_context_data(self, **kwargs):
        # A function to init the global layout. It is defined in web_project/__init__.py file
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))

        return context
    
class UsersView(PermissionRequiredMixin, TemplateView):
    permission_required = ("user.view_user", "user.delete_user", "user.change_user", "user.add_user")

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        return context

# --- View Edit Profile Mahasiswa (BARU) ---
class UserProfileView(UsersView):
    template_name = "students/profile.html"
    permission_required = [] 

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        usermhs = get_object_or_404(UserMhs, nim=self.request.user)

        if 'form' not in kwargs:
            kwargs['form'] = MhsProfileForm(instance=usermhs)
        
        # 4. Update context
        context.update({
            "title": "Profile",
            "heading": "Edit Profile",
            "usermhs": usermhs,
            "photo": usermhs.photo,
            "form": kwargs['form'], # Masukkan form ke context
        })
        
        return context

    def post(self, request, *args, **kwargs):
        usermhs = get_object_or_404(UserMhs, nim=request.user)
        form = MhsProfileForm(request.POST, request.FILES, instance=usermhs)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil Anda berhasil diperbarui!')
            return redirect('profile') # Sesuaikan dengan nama URL Anda
        else:
            messages.error(request, 'Gagal Memproses, pastikan semua isian sesuai format')
            return self.render_to_response(self.get_context_data(form=form))
        

class StudentCourseListView(StudentsRequiredMixin, UsersView):
    template_name = "app_academy_course.html"
    permission_required = [] 

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        try:
            mhs = UserMhs.objects.get(nim=user)
            is_student = True
        except UserMhs.DoesNotExist:
            mhs = None
            is_student = False

        if is_student:
            enrolled_course_ids = CourseParticipant.objects.filter(
                mahasiswa=mhs
            ).values_list('course_id', flat=True)
            my_courses = Course.objects.filter(id__in=enrolled_course_ids)\
                .select_related('prodi', 'period')\
                .prefetch_related('coaches')\
                .order_by('-created_at')
            
            context['my_courses'] = my_courses
        else:
            context['my_courses'] = []
        context.update({
            "title": "Academy - Kursus Saya",
            "heading": "Daftar Mata Kuliah",
        })
        
        return context
    


class CoursePlayerView(StudentsRequiredMixin, AcademyView):
    template_name = "course_player.html"

    def get(self, request, course_uuid, material_id=None, assignment_id=None, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)
        sections = CourseAgenda.objects.filter(course=course).prefetch_related('materials', 'assignments')

        active_item = None
        active_type = None
        submission = None

        if material_id:
            active_item = get_object_or_404(CourseMaterial, id=material_id)
            active_type = 'material'
        elif assignment_id:
            active_item = get_object_or_404(CourseAssignment, id=assignment_id)
            active_type = 'assignment'
        else:
            first_material = CourseMaterial.objects.filter(
                agenda__course=course
            ).order_by('agenda__agenda_date', 'order').first()

            first_assignment = CourseAssignment.objects.filter(
                agenda__course=course
            ).order_by('agenda__agenda_date').first()

            if first_material and first_assignment:
                if first_material.agenda.agenda_date <= first_assignment.agenda.agenda_date:
                    active_item = first_material
                    active_type = 'material'
                else:
                    active_item = first_assignment
                    active_type = 'assignment'
            elif first_material:
                active_item = first_material
                active_type = 'material'
            elif first_assignment:
                active_item = first_assignment
                active_type = 'assignment'

        announcements = CourseAnnouncement.objects.filter(course=course).order_by('-is_pinned', '-created_at')
        completed_material_ids = []
        completed_assignment_ids = []
        attendance_report = [] 
        total_hadir = 0
        user_attendance_map = {} 

        if request.user.is_authenticated:
            mhs_profile = UserMhs.objects.filter(nim=request.user).first()
            if mhs_profile:
                participant = CourseParticipant.objects.filter(course=course, mahasiswa=mhs_profile).first()
                if participant:
                    completed_material_ids = StudentMaterialProgress.objects.filter(
                        participant=participant, is_completed=True
                    ).values_list('material_id', flat=True)

                    completed_assignment_ids = StudentAssignmentSubmission.objects.filter(
                        student=mhs_profile, assignment__agenda__course=course
                    ).values_list('assignment_id', flat=True)

                    if active_type == 'assignment':
                        submission = StudentAssignmentSubmission.objects.filter(
                            student=mhs_profile, assignment=active_item
                        ).first()
                    
                    records = CourseAttendance.objects.filter(participant=participant)
                    for rec in records:
                        user_attendance_map[rec.agenda.id] = rec
                        if rec.status == 'present':
                            total_hadir += 1

        for agenda in sections:
            att_record = user_attendance_map.get(agenda.id)
            attendance_report.append({
                'agenda_title': agenda.title,
                'agenda_type': agenda.agenda_type,
                'agenda_date': agenda.agenda_date,
                'status': att_record.status if att_record else 'none', # 'none' artinya belum absen
                'check_in_time': att_record.check_in_time if att_record else None
            })

        context = self.get_context_data(
            course=course,
            sections=sections,
            active_item=active_item,
            active_type=active_type,
            submission=submission,
            completed_material_ids=completed_material_ids,
            completed_assignment_ids=completed_assignment_ids,
            announcements=announcements,     
            attendance_report=attendance_report, 
            total_hadir=total_hadir,        
        )
        return self.render_to_response(context)

    def post(self, request, course_uuid, material_id=None, assignment_id=None, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)
        
        if not request.user.is_authenticated:
            return redirect('login')

        mhs_profile = get_object_or_404(UserMhs, nim=request.user)
        participant = get_object_or_404(CourseParticipant, course=course, mahasiswa=mhs_profile)

        if material_id:
            material = get_object_or_404(CourseMaterial, id=material_id)
            progress, created = StudentMaterialProgress.objects.get_or_create(
                participant=participant, material=material
            )
            progress.is_completed = True
            progress.completed_at = timezone.now()
            progress.save()
            
            messages.success(request, 'Materi selesai!')
            return redirect('course-player-material', course_uuid=course.uuid, material_id=material_id)

        elif assignment_id:
            assignment = get_object_or_404(CourseAssignment, id=assignment_id)
            
            if not assignment.allow_late_submission and timezone.now() > assignment.due_date:
                messages.error(request, 'Batas waktu pengumpulan sudah berakhir.')
                return redirect('course-player-assignment', course_uuid=course.uuid, assignment_id=assignment.id)

            submission, created = StudentAssignmentSubmission.objects.get_or_create(
                student=mhs_profile,
                assignment=assignment
            )
            

            if 'submitted_file' in request.FILES:
                submission.submitted_file = request.FILES['submitted_file']
            
            if 'submitted_text' in request.POST:
                submission.submitted_text = request.POST['submitted_text']

            submission.updated_at = timezone.now()
            submission.save()
            
            messages.success(request, 'Tugas berhasil dikumpulkan!')
            return redirect('course-player-assignment', course_uuid=course.uuid, assignment_id=assignment.id)

        return redirect('course-player', course_uuid=course.uuid)
