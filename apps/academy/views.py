from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView
from web_project import TemplateLayout
from .forms import CourseForm, AddParticipantForm, AddAgendaForm, AddAnnouncementForm, AttendanceForm, CourseMaterialForm, AddProgramStudiCourseForm, CoursePeriodForm, CourseAssignmentForm, CourseQuizForm, QuizQuestionForm
from django.contrib import messages
from .models import ChatRoom, Course, CourseParticipant, CourseAgenda, CourseAnnouncement, CourseAttendance, CourseMaterial, StudentMaterialProgress, Prodi, CoursePeriod, StudentAssignmentSubmission, CourseAssignment, CourseQuiz, QuizQuestion, QuizOption, StudentQuizAttempt, StudentQuizAnswer
from .models import UserMhs, CourseGroup, CourseGroupMember
from django.utils import timezone
from web_project.template_helpers.theme import TemplateHelper
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from .decorators_students import check_userstudents
from .decorators_dosen import DosenRequiredMixin

from django.db import transaction

from django.db.models import Sum
import random

from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin


class AcademyView(TemplateView):
    # Predefined function
    def get_context_data(self, **kwargs):
        # A function to init the global layout. It is defined in web_project/__init__.py file
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))

        return context
    


def loginView(request):
    context = {
        'layout_path': TemplateHelper.set_layout("layout_blank.html"),
        'title': 'Login',
        'heading': 'Login',
        'style': 'light',
    }
    if request.method == "POST":
        print (request.POST)
        username_in = request.POST['username']
        password_in = request.POST['password']
        user = authenticate(request, username=username_in, password=password_in)        
        if user is not None:
            login(request, user)
            print(user)
            messages.success(request, 'Selamat Datang!')
            if user.is_superuser:
                request.session['su'] = '557799'
            else:
                request.session['su'] = '0'
            return redirect('/app/academy/dashboard/')
        else:
            messages.warning(request, 'Periksa Kembali Username dan Password Anda!')
            return redirect('login')
    
    if request.method == "GET":
        if request.user.is_authenticated:
            return redirect('/app/academy/dashboard/')
        else:
            return render(request,'auth_login_basic.html', context) 

def LogoutView(request):
    logout(request)
    return redirect('login')


class AppPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = 'auth/reset_password.html'
    success_url = reverse_lazy('login') 

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context.update({
            "title": "Ganti Password",
        })
        return context

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Password berhasil diubah. Silakan login kembali.")
        logout(self.request)
        
        # 5. Redirect ke halaman Login
        return redirect(self.success_url)
class AddCourse(DosenRequiredMixin, AcademyView):
    template_name = "add_academy_course.html"
    def get(self, request, *args, **kwargs):
        return self.render_to_response(self.get_context_data(form=CourseForm()))
    def post(self, request, *args, **kwargs):
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save()
            messages.success(request, f'Course {course.code} berhasil dibuat.')
            return redirect('list-academy-course')
        return self.render_to_response(self.get_context_data(form=form))
    
class AddProgramStudiCourse(DosenRequiredMixin, AcademyView):
    template_name = "add_program_studi_course.html"

    def get(self, request, *args, **kwargs):
        # 1. Ambil semua data (misal diurutkan dari yang terbaru)
        data_prodi = Prodi.objects.all().order_by('-id')
        
        # 2. Masukkan ke context
        context = self.get_context_data(form=AddProgramStudiCourseForm())
        context['data_list'] = data_prodi 
        
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        form = AddProgramStudiCourseForm(request.POST)
        if form.is_valid():
            course = form.save()
            messages.success(request, f'Course berhasil dibuat.')
            # Jika ingin tetap di halaman ini untuk melihat tabel, redirect ke diri sendiri
            # Ganti 'add-program-studi-course' dengan nama URL pattern halaman ini
            return redirect('program-studi-course') 
            
        # Jika form error, data list tetap harus muncul
        data_prodi = Prodi.objects.all().order_by('-id')
        context = self.get_context_data(form=form)
        context['data_list'] = data_prodi
        
        return self.render_to_response(context)
    
class EditProgramStudiCourse(DosenRequiredMixin, AcademyView):
    template_name = "add_program_studi_course.html" # Kita gunakan template yang sama

    def get(self, request, pk, *args, **kwargs):
        # 1. Ambil data yang mau diedit berdasarkan ID (pk)
        course_obj = get_object_or_404(Prodi, id=pk)
        
        # 2. Masukkan data tersebut ke dalam Form
        form = AddProgramStudiCourseForm(instance=course_obj)
        
        # 3. Ambil list data untuk tetap ditampilkan di tabel bawah
        data_prodi = Prodi.objects.all().order_by('-id')

        context = self.get_context_data(form=form)
        context['data_list'] = data_prodi
        context['is_edit'] = True # Penanda untuk merubah judul di HTML (opsional)
        
        return self.render_to_response(context)

    def post(self, request, pk, *args, **kwargs):
        course_obj = get_object_or_404(Prodi, id=pk)
        form = AddProgramStudiCourseForm(request.POST, instance=course_obj)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Course berhasil diperbarui.')
            return redirect('program-studi-course')
        data_prodi = Prodi.objects.all().order_by('-id')
        context = self.get_context_data(form=form)
        context['data_list'] = data_prodi
        
        return self.render_to_response(context)


class DeleteProgramStudiCourse(DosenRequiredMixin, AcademyView):
    def get(self, request, pk, *args, **kwargs):
        course_obj = get_object_or_404(Prodi, id=pk)
        course_obj.delete()
        messages.success(request, 'Course berhasil dihapus.')
        return redirect('program-studi-course')
    

class AddCoursePeriod(DosenRequiredMixin, AcademyView):
    template_name = "add_course_period.html" # Kita buat file html baru nanti

    def get(self, request, *args, **kwargs):
        # Ambil data period
        data_period = CoursePeriod.objects.all().order_by('-id')
        
        context = self.get_context_data(form=CoursePeriodForm())
        context['data_list'] = data_period
        
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        form = CoursePeriodForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Periode Course berhasil dibuat.')
            return redirect('course-period') # Nama URL yang akan kita buat
            
        # Jika error
        data_period = CoursePeriod.objects.all().order_by('-id')
        context = self.get_context_data(form=form)
        context['data_list'] = data_period
        return self.render_to_response(context)

class EditCoursePeriod(DosenRequiredMixin, AcademyView):
    template_name = "add_course_period.html"

    def get(self, request, pk, *args, **kwargs):
        obj = get_object_or_404(CoursePeriod, id=pk)
        form = CoursePeriodForm(instance=obj)
        
        data_period = CoursePeriod.objects.all().order_by('-id')
        
        context = self.get_context_data(form=form)
        context['data_list'] = data_period
        context['is_edit'] = True
        
        return self.render_to_response(context)

    def post(self, request, pk, *args, **kwargs):
        obj = get_object_or_404(CoursePeriod, id=pk)
        form = CoursePeriodForm(request.POST, instance=obj)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Periode Course berhasil diperbarui.')
            return redirect('list-course-period')
            
        data_period = CoursePeriod.objects.all().order_by('-id')
        context = self.get_context_data(form=form)
        context['data_list'] = data_period
        return self.render_to_response(context)

class DeleteCoursePeriod(DosenRequiredMixin, AcademyView):
    def get(self, request, pk, *args, **kwargs):
        obj = get_object_or_404(CoursePeriod, id=pk)
        obj.delete()
        messages.success(request, 'Periode berhasil dihapus.')
        return redirect('list-course-period')


class EditCourse(DosenRequiredMixin, AcademyView):
    template_name = "add_academy_course.html" 
    def get(self, request, course_uuid, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)
        form = CourseForm(instance=course)

        return self.render_to_response(self.get_context_data(
            form=form, 
            course=course,
            is_edit=True  
        ))

    def post(self, request, course_uuid, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)
        form = CourseForm(request.POST, instance=course)

        if form.is_valid():
            course = form.save()
            messages.success(request, f'Course {course.code} berhasil diperbarui.')
            return redirect('list-academy-course')
        return self.render_to_response(self.get_context_data(
            form=form, 
            course=course,
            is_edit=True
        ))

class ViewsAllCourse(DosenRequiredMixin, AcademyView):
    template_name = "view_all_academy_course.html"
    def get(self, request, course_uuid, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)
        
        return self.render_to_response(self.get_context_data(
            form=CourseForm(instance=course), 
            course=course
        ))
    
class ListCourse(DosenRequiredMixin, AcademyView):
    template_name = "list_academy_course.html"
    def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            courses = Course.objects.all()
            context['courses'] = courses
            return context
    
class DeleteCourse(DosenRequiredMixin, AcademyView):
    def get(self, request, *args, **kwargs):
        course_uuid = kwargs.get('course_uuid')
        course = get_object_or_404(Course, uuid=course_uuid)
        course.delete()
        messages.success(request, f'Course {course.code} berhasil dihapus.')
        return redirect('list-academy-course')
    
class AddCourseParticipant(DosenRequiredMixin, AcademyView):
    template_name = "add_participant.html"

    def get(self, request, course_uuid, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)
        participants = CourseParticipant.objects.filter(course=course).select_related('mahasiswa')
        
        context = self.get_context_data(
            form=AddParticipantForm(),
            course=course,
            participants=participants
        )
        return self.render_to_response(context)

    def post(self, request, course_uuid, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)
        form = AddParticipantForm(request.POST)

        if form.is_valid():
            mahasiswa_terpilih = form.cleaned_data['list_mahasiswa'] 
            is_active = form.cleaned_data.get('is_active', True)
            jumlah_sukses = 0

            for mhs in mahasiswa_terpilih:
                obj, created = CourseParticipant.objects.get_or_create(
                    course=course,
                    mahasiswa=mhs,
                    defaults={'is_active': is_active}
                )
                if created:
                    jumlah_sukses += 1
            
            messages.success(request, f'Berhasil menambahkan {jumlah_sukses} mahasiswa.')
            return redirect('add-course-participant', course_uuid=course.uuid)
                
        participants = CourseParticipant.objects.filter(course=course).select_related('mahasiswa')
        return self.render_to_response(self.get_context_data(form=form, course=course, participants=participants))
    
class DeleteCourseParticipant(DosenRequiredMixin, AcademyView):
    def get(self, request, *args, **kwargs):
        course_uuid = self.kwargs.get('course_uuid')
        participant_id = self.kwargs.get('participant_id')
        course = get_object_or_404(Course, uuid=course_uuid)
        participant = get_object_or_404(CourseParticipant, id=participant_id, course=course)
        mhs_name = str(participant.mahasiswa) 
        participant.delete()
        messages.success(request, f'Mahasiswa "{mhs_name}" berhasil dihapus dari kelas.')
        return redirect('add-course-participant', course_uuid=course.uuid)

class AddCourseAgenda(DosenRequiredMixin, AcademyView):
    template_name = "add_agenda.html"

    def get(self, request, course_uuid, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)
        agendas = CourseAgenda.objects.filter(course=course).order_by('agenda_date')

        self._calculate_attendance(course, agendas)

        return render(request, self.template_name, self.get_context_data(
            form=AddAgendaForm(),
            course=course,
            agendas=agendas,
            is_edit=False
        ))

    def post(self, request, course_uuid, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)
        form = AddAgendaForm(request.POST)

        if form.is_valid():
            agenda = form.save(commit=False)
            agenda.course = course
            agenda.save()
            messages.success(request, f'Agenda "{agenda.title}" berhasil ditambahkan.')
            return redirect('add-course-agenda', course_uuid=course.uuid)
        
        agendas = CourseAgenda.objects.filter(course=course).order_by('agenda_date')
        self._calculate_attendance(course, agendas)
        
        return render(request, self.template_name, self.get_context_data(
            form=form,
            course=course,
            agendas=agendas,
            is_edit=False
        ))
    
    def _calculate_attendance(self, course, agendas):
        total_participants = CourseParticipant.objects.filter(course=course).count()
        for ag in agendas:
            hadir_count = CourseAttendance.objects.filter(agenda=ag, status__in=['present', 'late']).count()
            ag.hadir_count = hadir_count
            ag.total_students = total_participants
            ag.percent = int((hadir_count / total_participants) * 100) if total_participants > 0 else 0


class EditCourseAgenda(DosenRequiredMixin, AcademyView):
    template_name = "add_agenda.html"

    def get(self, request, course_uuid, agenda_id, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)
        agenda_instance = get_object_or_404(CourseAgenda, id=agenda_id, course=course)
        
        agendas = CourseAgenda.objects.filter(course=course).order_by('agenda_date')
    
        total_participants = CourseParticipant.objects.filter(course=course).count()
        for ag in agendas:
            hadir_count = CourseAttendance.objects.filter(agenda=ag, status__in=['present', 'late']).count()
            ag.hadir_count = hadir_count
            ag.total_students = total_participants
            ag.percent = int((hadir_count / total_participants) * 100) if total_participants > 0 else 0

        form = AddAgendaForm(instance=agenda_instance)

        return render(request, self.template_name, self.get_context_data(
            form=form,
            course=course,
            agendas=agendas,
            is_edit=True,
            edit_id=agenda_id
        ))

    def post(self, request, course_uuid, agenda_id, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)
        agenda_instance = get_object_or_404(CourseAgenda, id=agenda_id, course=course)
        
        form = AddAgendaForm(request.POST, instance=agenda_instance)

        if form.is_valid():
            form.save()
            messages.success(request, f'Agenda "{agenda_instance.title}" berhasil diperbarui.')
            return redirect('add-course-agenda', course_uuid=course.uuid )
        
        agendas = CourseAgenda.objects.filter(course=course).order_by('agenda_date')
        return render(request, self.template_name, self.get_context_data(
            form=form, 
            course=course, 
            agendas=agendas,
            is_edit=True,
            edit_id=agenda_id
        ))



class DeleteCourseAgenda(DosenRequiredMixin, AcademyView):
    def get(self, request, *args, **kwargs):
        course_uuid = self.kwargs.get('course_uuid') or self.kwargs.get('course_id')
        agenda_id = self.kwargs.get('agenda_id') or self.kwargs.get('pk')
        course = get_object_or_404(Course, uuid=course_uuid)
        agenda = get_object_or_404(CourseAgenda, id=agenda_id, course=course)
        agenda_title = agenda.title
        agenda.delete()
        messages.success(request, f'Agenda "{agenda_title}" dan data presensinya berhasil dihapus.')
        return redirect('add-course-agenda', course_uuid=course.uuid)
    

class CourseAnnouncementView(DosenRequiredMixin, AcademyView):
    template_name = "add_announcement.html"
    def get(self, request, course_uuid, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)
        announcements = CourseAnnouncement.objects.filter(course=course).order_by('-is_pinned', '-created_at')

        return self.render_to_response(self.get_context_data(
            form=AddAnnouncementForm(),
            course=course,
            announcements=announcements
        ))

    def post(self, request, course_uuid, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)
        form = AddAnnouncementForm(request.POST)

        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.course = course
            announcement.save()
            
            messages.success(request, 'Pengumuman berhasil dipublikasikan.')
            return redirect('add-course-announcement', course_uuid=course.uuid)
        
        announcements = CourseAnnouncement.objects.filter(course=course).order_by('-is_pinned', '-created_at')
        return self.render_to_response(self.get_context_data(
            form=form, 
            course=course, 
            announcements=announcements
        ))
    
class DeleteCourseAnnouncementView(DosenRequiredMixin, AcademyView):
    def get(self, request, announcement_id, *args, **kwargs):
        course_uuid = self.kwargs.get('course_uuid')
        course = get_object_or_404(Course, uuid=course_uuid)
        announcement = get_object_or_404(CourseAnnouncement, id=announcement_id, course=course)
        announcement.delete()
        messages.success(request, 'Pengumuman berhasil dihapus.')
        return redirect('add-course-announcement', course_uuid=course.uuid)
    

class CourseAttendanceView(DosenRequiredMixin, AcademyView):
    template_name = "course_attendance.html"

    def get(self, request, course_uuid, agenda_id, *args, **kwargs):
        # 1. Ambil Course pakai UUID (Validasi keamanan)
        course = get_object_or_404(Course, uuid=course_uuid)
        
        # 2. Ambil Agenda & Pastikan agenda ini milik course tersebut
        agenda = get_object_or_404(CourseAgenda, id=agenda_id, course=course)
        
        participants = CourseParticipant.objects.filter(
            course=course
        ).select_related('mahasiswa').order_by('mahasiswa__nim')

        student_data = []
        for p in participants:
            existing_obj = CourseAttendance.objects.filter(
                agenda=agenda, 
                participant=p
            ).first()
            
            form = AttendanceForm(instance=existing_obj, prefix=str(p.id))
            
            student_data.append({
                'participant': p, 
                'form': form      
            })

        context = self.get_context_data(
            agenda=agenda,
            course=course,
            student_data=student_data 
        )
        return self.render_to_response(context)

    # TAMBAHKAN parameter course_uuid
    def post(self, request, course_uuid, agenda_id, *args, **kwargs):
        # 1. Validasi Course & Agenda
        course = get_object_or_404(Course, uuid=course_uuid)
        agenda = get_object_or_404(CourseAgenda, id=agenda_id, course=course)
        
        participants = CourseParticipant.objects.filter(course=course)

        saved_count = 0
        for p in participants:
            form = AttendanceForm(request.POST, prefix=str(p.id))
            
            if form.is_valid():
                status = form.cleaned_data['status']
                notes = form.cleaned_data['notes']
                
                CourseAttendance.objects.update_or_create(
                    agenda=agenda,     
                    participant=p,    
                    defaults={
                        'status': status,
                        'notes': notes
                    }
                )
                saved_count += 1
        
        messages.success(request, f'Presensi berhasil disimpan untuk {saved_count} mahasiswa.')
        return redirect('course-attendance', course_uuid=course.uuid, agenda_id=agenda.id)
    


class ManageCurriculumView(DosenRequiredMixin, AcademyView):
    template_name = "manage_curriculum.html"

    def get(self, request, course_uuid, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)
        sections = CourseAgenda.objects.filter(course=course).prefetch_related('materials')
        
        context = self.get_context_data(
            course=course,
            sections=sections
        )
        return self.render_to_response(context)



class AddCourseMaterialView(DosenRequiredMixin, AcademyView):
    template_name = "add_material.html"

    def get(self, request, course_uuid, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)
        form = CourseMaterialForm(course_uuid=course.uuid)
        
        return self.render_to_response(self.get_context_data(
            form=form, 
            course=course
        ))

    def post(self, request, course_uuid, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)
        form = CourseMaterialForm(request.POST, request.FILES, course_uuid=course.uuid)

        if form.is_valid():
            material = form.save()
            messages.success(request, f'Materi "{material.title}" berhasil disimpan.')
            return redirect('manage-curriculum', course_uuid=course.uuid)
        
        return self.render_to_response(self.get_context_data(form=form, course=course))   
    
class EditCourseMaterialView(DosenRequiredMixin, AcademyView):
    template_name = "add_material.html"

    def get(self, request, course_uuid, material_id, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)
        material = get_object_or_404(CourseMaterial, id=material_id)
        if material.agenda.course != course:
            messages.error(request, "Materi tidak valid untuk kursus ini.")
            return redirect('manage-curriculum', course_uuid=course.uuid)

        form = CourseMaterialForm(instance=material, course_uuid=course.uuid)
        
        return self.render_to_response(self.get_context_data(
            form=form, 
            course=course,
            material=material, 
            is_edit=True     
        ))

    def post(self, request, course_uuid, material_id, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)
        material = get_object_or_404(CourseMaterial, id=material_id)

        # PERBAIKAN: Ganti 'material.section' menjadi 'material.agenda'
        if material.agenda.course != course:
            return redirect('manage-curriculum', course_uuid=course.uuid)

        form = CourseMaterialForm(request.POST, request.FILES, instance=material, course_uuid=course.uuid)

        if form.is_valid():
            form.save()
            messages.success(request, f'Materi "{material.title}" berhasil diperbarui.')
            # Redirect kembali ke halaman Agenda
            return redirect('manage-curriculum', course_uuid=course.uuid)
        
        return self.render_to_response(self.get_context_data(
            form=form, 
            course=course, 
            material=material,
            is_edit=True
        ))
    
class DeleteCourseMaterialView(DosenRequiredMixin, AcademyView):
    def get(self, request, material_id, *args, **kwargs):
        material = get_object_or_404(CourseMaterial, id=material_id)
        course_uuid = material.agenda.course.uuid
        material.delete()
        messages.success(request, f'Materi "{material.title}" berhasil dihapus.')
        return redirect('manage-curriculum', course_uuid=course_uuid)
    
class AddCourseAssignmentView(DosenRequiredMixin, AcademyView):
    template_name = "add_assignment.html" 

    def get(self, request, course_uuid, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)
        form = CourseAssignmentForm(course_uuid=course.uuid)
        
        return self.render_to_response(self.get_context_data(
            form=form, 
            course=course
        ))

    def post(self, request, course_uuid, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)
        form = CourseAssignmentForm(request.POST, request.FILES, course_uuid=course.uuid)

        if form.is_valid():
            assignment = form.save(commit=False)
            if assignment.agenda.course != course:
                messages.error(request, "Agenda tidak valid.")
                return redirect('manage-curriculum', course_uuid=course.uuid)
            
            assignment.save()
            messages.success(request, f'Tugas "{assignment.title}" berhasil ditambahkan.')
            return redirect('manage-curriculum', course_uuid=course.uuid)
        
        return self.render_to_response(self.get_context_data(
            form=form, 
            course=course
        ))
    
class EditCourseAssignmentView(DosenRequiredMixin, AcademyView):
    template_name = "add_assignment.html"

    def get(self, request, course_uuid, assignment_id, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)
        assignment = get_object_or_404(CourseAssignment, id=assignment_id)
        if assignment.agenda.course != course:
            messages.error(request, "Data tugas tidak valid untuk mata kuliah ini.")
            return redirect('manage-curriculum', course_uuid=course.uuid)

        form = CourseAssignmentForm(instance=assignment, course_uuid=course.uuid)
        
        return self.render_to_response(self.get_context_data(
            form=form, 
            course=course,
            assignment=assignment,
            is_edit=True 
        ))

    def post(self, request, course_uuid, assignment_id, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)
        assignment = get_object_or_404(CourseAssignment, id=assignment_id)

        if assignment.agenda.course != course:
            return redirect('manage-curriculum', course_uuid=course.uuid)

        form = CourseAssignmentForm(request.POST, request.FILES, instance=assignment, course_uuid=course.uuid)

        if form.is_valid():
            form.save()
            messages.success(request, f'Tugas "{assignment.title}" berhasil diperbarui.')
            return redirect('manage-curriculum', course_uuid=course.uuid)
        
        return self.render_to_response(self.get_context_data(
            form=form, 
            course=course,
            assignment=assignment,
            is_edit=True
        ))
    

class DeleteCourseAssignmentView(DosenRequiredMixin, AcademyView):
    def get(self, request, assignment_id, *args, **kwargs):
        course_uuid = self.kwargs.get('course_uuid')
        course = get_object_or_404(Course, uuid=course_uuid)
        assignment = get_object_or_404(CourseAssignment, id=assignment_id)
        if assignment.agenda.course != course:
            messages.error(request, "Tugas tidak ditemukan di kelas ini.")
            return redirect('manage-curriculum', course_uuid=course.uuid)
        title = assignment.title
        assignment.delete()
        messages.success(request, f'Tugas "{title}" berhasil dihapus.')
        return redirect('manage-curriculum', course_uuid=course.uuid)
    
# apps/academy/views.py

class AssignmentGradingView(DosenRequiredMixin, AcademyView):
    template_name = "grading_assignment.html"

    # Method GET (Menampilkan Daftar - TIDAK BERUBAH)
    def get(self, request, course_uuid, assignment_id, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)
        assignment = get_object_or_404(CourseAssignment, id=assignment_id)
        
        if assignment.agenda.course != course:
            messages.error(request, "Tugas tidak ditemukan di kelas ini.")
            return redirect('manage-curriculum', course_uuid=course.uuid)
        
        grading_list = []
        stats = {'total': 0, 'submitted': 0, 'graded': 0}

        # === LOGIKA TUGAS KELOMPOK ===
        if assignment.assignment_type == 'group':
            groups = CourseGroup.objects.filter(course=course).prefetch_related('members__participant__mahasiswa')
            stats['total'] = CourseParticipant.objects.filter(course=course).count()

            for group in groups:
                members_data = []
                for member in group.members.all():
                    mhs = member.participant.mahasiswa
                    sub = StudentAssignmentSubmission.objects.filter(assignment=assignment, student=mhs).first()
                    status, is_late = self._get_status(sub, assignment)
                    
                    if sub: 
                        stats['submitted'] += 1
                        if sub.score is not None: stats['graded'] += 1

                    members_data.append({
                        'student': mhs, 'participant': member.participant, 'role': member.role,
                        'submission': sub, 'status': status, 'is_late': is_late
                    })
                
                grading_list.append({'type': 'group', 'group_obj': group, 'members': members_data})

            # Handle Mahasiswa Tanpa Kelompok (Orphans)
            grouped_ids = CourseGroupMember.objects.filter(group__course=course).values_list('participant_id', flat=True)
            orphans = CourseParticipant.objects.filter(course=course).exclude(id__in=grouped_ids)
            if orphans.exists():
                orphan_data = []
                for p in orphans:
                    sub = StudentAssignmentSubmission.objects.filter(assignment=assignment, student=p.mahasiswa).first()
                    status, is_late = self._get_status(sub, assignment)
                    if sub: 
                        stats['submitted'] += 1
                        if sub.score is not None: stats['graded'] += 1
                    orphan_data.append({'student': p.mahasiswa, 'submission': sub, 'status': status, 'is_late': is_late})
                grading_list.append({'type': 'no_group', 'group_obj': None, 'members': orphan_data})

        # === LOGIKA TUGAS INDIVIDU ===
        else:
            participants = CourseParticipant.objects.filter(course=course).select_related('mahasiswa')
            stats['total'] = participants.count()
            for p in participants:
                sub = StudentAssignmentSubmission.objects.filter(assignment=assignment, student=p.mahasiswa).first()
                status, is_late = self._get_status(sub, assignment)
                if sub: 
                    stats['submitted'] += 1
                    if sub.score is not None: stats['graded'] += 1
                grading_list.append({'type': 'individual', 'student': p.mahasiswa, 'submission': sub, 'status': status, 'is_late': is_late})

        return self.render_to_response(self.get_context_data(
            assignment=assignment, course=course, grading_list=grading_list, stats=stats
        ))

    # === [BARU] Method POST (Menyimpan Nilai) ===
    def post(self, request, course_uuid, assignment_id, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)
        assignment = get_object_or_404(CourseAssignment, id=assignment_id)

        # 1. Ambil Data dari Form
        submission_id = request.POST.get('submission_id') # ID diambil dari hidden input
        score = request.POST.get('score')
        feedback = request.POST.get('feedback')

        # 2. Validasi Submission
        submission = get_object_or_404(StudentAssignmentSubmission, id=submission_id)

        # Security Check: Pastikan submission ini memang milik assignment yang sedang dibuka
        if submission.assignment.id != assignment.id:
            messages.error(request, "Terjadi kesalahan data (Assignment Mismatch).")
            return redirect('assignment-grading', course_uuid=course.uuid, assignment_id=assignment.id)

        # 3. Simpan Nilai
        if score:
            submission.score = score
            submission.feedback = feedback
            submission.save()
            
            # Buat nama target untuk pesan sukses
            target_name = submission.student.nim.first_name
            messages.success(request, f"Nilai untuk {target_name} berhasil disimpan.")

        # 4. Refresh Halaman (Redirect ke URL yang sama)
        return redirect('assignment-grading', course_uuid=course.uuid, assignment_id=assignment.id)

    def _get_status(self, sub, assignment):
        status = 'missing'
        is_late = False
        if sub:
            status = 'submitted'
            if sub.score is not None: status = 'graded'
            if sub.submitted_at > assignment.due_date: is_late = True
        return status, is_late

class PublicAgendaMaterialView(TemplateView):
    template_name = "public_agenda_materials.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course_uuid = self.kwargs.get('course_uuid')
        agenda_id = self.kwargs.get('agenda_id')

        agenda = get_object_or_404(CourseAgenda, id=agenda_id, course__uuid=course_uuid)
        
        materials = CourseMaterial.objects.filter(agenda=agenda).order_by('order')

        context['agenda'] = agenda
        context['course'] = agenda.course
        context['materials'] = materials
        return context
    

class CourseQuizListView(DosenRequiredMixin, AcademyView):
    template_name = "quiz/quiz_list.html"

    def get(self, request, course_uuid, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)
        quizzes = CourseQuiz.objects.filter(course=course).order_by('start_time')
        
        return self.render_to_response(self.get_context_data(
            course=course,
            quizzes=quizzes
        ))


class QuizCreateView(DosenRequiredMixin, AcademyView):
    template_name = "quiz/quiz_form.html"

    def get(self, request, course_uuid, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)
        form = CourseQuizForm()
        
        return self.render_to_response(self.get_context_data(
            form=form,
            course=course
        ))

    def post(self, request, course_uuid, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)
        form = CourseQuizForm(request.POST)
        
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.course = course
            quiz.save()
            
            messages.success(request, "Kuis berhasil dibuat! Silakan tambah soal.")
            # Redirect ke halaman Manage Soal
            return redirect('quiz-manage', quiz_id=quiz.id)
        
        return self.render_to_response(self.get_context_data(
            form=form,
            course=course
        ))


class QuizManageView(DosenRequiredMixin, AcademyView):
    template_name = "quiz/quiz_manage.html"

    def get(self, request, quiz_id, *args, **kwargs):
        quiz = get_object_or_404(CourseQuiz, id=quiz_id)
        # Ambil soal urut berdasarkan field 'order'
        questions = quiz.questions.all().order_by('order')
        
        return self.render_to_response(self.get_context_data(
            quiz=quiz,
            questions=questions,
            course=quiz.course
        ))


class AddQuizQuestionView(DosenRequiredMixin, AcademyView):
    template_name = "quiz/question_form.html"

    def get(self, request, quiz_id, q_type, *args, **kwargs):
        quiz = get_object_or_404(CourseQuiz, id=quiz_id)
        form = QuizQuestionForm()
        
        return self.render_to_response(self.get_context_data(
            quiz=quiz,
            form=form,
            q_type=q_type,
            q_type_label='Pilihan Ganda' if q_type == 'multiple_choice' else 'Esai'
        ))

    def post(self, request, quiz_id, q_type, *args, **kwargs):
        quiz = get_object_or_404(CourseQuiz, id=quiz_id)
        form = QuizQuestionForm(request.POST, request.FILES)

        if form.is_valid():
            with transaction.atomic():
                # 1. Simpan Soal Utama
                question = form.save(commit=False)
                question.quiz = quiz
                question.question_type = q_type
                
                # Auto Order: Taruh di urutan terakhir
                last_order = QuizQuestion.objects.filter(quiz=quiz).count()
                question.order = last_order + 1
                question.save()

                # 2. Logic Khusus Pilihan Ganda (Simpan Opsi)
                if q_type == 'multiple_choice':
                    options = request.POST.getlist('option_text') # Ambil array input HTML
                    correct_index = request.POST.get('correct_option') # Index radio button yg dipilih

                    for idx, opt_text in enumerate(options):
                        # Hanya simpan jika teks opsi tidak kosong
                        if opt_text.strip():
                            is_correct = (str(idx) == correct_index)
                            QuizOption.objects.create(
                                question=question,
                                text=opt_text,
                                is_correct=is_correct,
                                order=idx+1
                            )
                
            messages.success(request, "Soal berhasil ditambahkan.")
            return redirect('quiz-manage', quiz_id=quiz.id)

        # Jika form error
        return self.render_to_response(self.get_context_data(
            quiz=quiz,
            form=form,
            q_type=q_type,
            q_type_label='Pilihan Ganda' if q_type == 'multiple_choice' else 'Esai'
        ))


class DeleteQuizView(DosenRequiredMixin, AcademyView):
    def get(self, request, quiz_id, *args, **kwargs):
        quiz = get_object_or_404(CourseQuiz, id=quiz_id)
        course_uuid = quiz.course.uuid
        title = quiz.title
        
        quiz.delete()
        messages.success(request, f'Kuis "{title}" berhasil dihapus.')
        return redirect('course-quiz-list', course_uuid=course_uuid)
    
class EditQuizQuestionView(DosenRequiredMixin, AcademyView):
    template_name = "quiz/question_form.html"

    def get(self, request, question_id, *args, **kwargs):
        question = get_object_or_404(QuizQuestion, id=question_id)
        quiz = question.quiz
        form = QuizQuestionForm(instance=question)
        
        # Ambil opsi jika tipe soal Pilihan Ganda
        existing_options = None
        if question.question_type == 'multiple_choice':
            existing_options = question.options.all().order_by('order')

        return self.render_to_response(self.get_context_data(
            quiz=quiz,
            form=form,
            q_type=question.question_type,
            q_type_label='Pilihan Ganda' if question.question_type == 'multiple_choice' else 'Esai',
            is_edit=True,            # Penanda mode Edit
            existing_options=existing_options
        ))

    def post(self, request, question_id, *args, **kwargs):
        question = get_object_or_404(QuizQuestion, id=question_id)
        quiz = question.quiz
        
        form = QuizQuestionForm(request.POST, request.FILES, instance=question)

        if form.is_valid():
            with transaction.atomic():
                # 1. Update Data Soal Utama
                q = form.save(commit=False)
                q.save()

                # 2. Logic Reset Opsi (Khusus Pilihan Ganda)
                if question.question_type == 'multiple_choice':
                    # Hapus semua opsi lama
                    question.options.all().delete()
                    
                    # Buat ulang opsi baru dari input form
                    options = request.POST.getlist('option_text')
                    correct_index = request.POST.get('correct_option')

                    for idx, opt_text in enumerate(options):
                        if opt_text.strip():
                            is_correct = (str(idx) == correct_index)
                            QuizOption.objects.create(
                                question=question,
                                text=opt_text,
                                is_correct=is_correct,
                                order=idx+1
                            )
            
            messages.success(request, "Soal berhasil diperbarui.")
            return redirect('quiz-manage', quiz_id=quiz.id)
        
        # Jika form error, kembalikan ke halaman dengan data yang ada
        existing_options = question.options.all().order_by('order') if question.question_type == 'multiple_choice' else None
        
        return self.render_to_response(self.get_context_data(
            quiz=quiz,
            form=form,
            q_type=question.question_type,
            q_type_label='Pilihan Ganda' if question.question_type == 'multiple_choice' else 'Esai',
            is_edit=True,
            existing_options=existing_options
        ))


class DeleteQuizQuestionView(DosenRequiredMixin, AcademyView):
    def get(self, request, question_id, *args, **kwargs):
        question = get_object_or_404(QuizQuestion, id=question_id)
        quiz_id = question.quiz.id
        
        question.delete()
        messages.success(request, "Soal berhasil dihapus.")
        return redirect('quiz-manage', quiz_id=quiz_id)
    
class QuizSubmissionListView(DosenRequiredMixin, AcademyView):
    template_name = "quiz/submission_list.html"

    def get(self, request, quiz_id, *args, **kwargs):
        quiz = get_object_or_404(CourseQuiz, id=quiz_id)
        
        # Ambil semua percobaan (attempt) yang sudah selesai (finished_at tidak kosong)
        attempts = StudentQuizAttempt.objects.filter(
            quiz=quiz, 
            finished_at__isnull=False
        ).select_related('participant', 'participant__mahasiswa').order_by('-total_score')

        return self.render_to_response(self.get_context_data(
            quiz=quiz,
            course=quiz.course,
            attempts=attempts
        ))


# --- VIEW: FORM PENILAIAN / GRADING (Sisi Dosen) ---
class QuizSubmissionGradeView(DosenRequiredMixin, AcademyView):
    template_name = "quiz/submission_detail.html"

    def get(self, request, attempt_id, *args, **kwargs):
        attempt = get_object_or_404(StudentQuizAttempt, id=attempt_id)
        
        # Ambil jawaban user, urutkan sesuai urutan soal
        answers = StudentQuizAnswer.objects.filter(attempt=attempt).select_related('question', 'selected_option').order_by('question__order')

        return self.render_to_response(self.get_context_data(
            attempt=attempt,
            quiz=attempt.quiz,
            course=attempt.quiz.course,
            answers=answers
        ))

    def post(self, request, attempt_id, *args, **kwargs):
        attempt = get_object_or_404(StudentQuizAttempt, id=attempt_id)
        
        # Kita loop semua inputan dari form
        # Input name format: "score_{answer_id}"
        
        with transaction.atomic():
            for key, value in request.POST.items():
                if key.startswith('score_'):
                    # Ambil ID jawaban dari nama input
                    ans_id = key.split('_')[1]
                    try:
                        score_val = float(value)
                        
                        # Update Score di Tabel Jawaban
                        answer_obj = StudentQuizAnswer.objects.get(id=ans_id)
                        
                        # Validasi sederhana: Nilai tidak boleh melebihi bobot soal
                        if score_val > answer_obj.question.score_weight:
                            messages.warning(request, f"Nilai untuk soal no {answer_obj.question.order} melebihi bobot maksimal ({answer_obj.question.score_weight}). Diset ke maksimal.")
                            score_val = answer_obj.question.score_weight
                            
                        answer_obj.score_obtained = score_val
                        answer_obj.save()
                        
                    except (ValueError, StudentQuizAnswer.DoesNotExist):
                        continue

            # --- HITUNG ULANG TOTAL SKOR ---
            new_total = attempt.answers.aggregate(total=Sum('score_obtained'))['total'] or 0
            attempt.total_score = new_total
            attempt.save()

        messages.success(request, f"Nilai berhasil disimpan. Total Skor Baru: {attempt.total_score}")
        return redirect('quiz-submissions', quiz_id=attempt.quiz.id)
    

class CourseGroupListView(DosenRequiredMixin, AcademyView):
    template_name = "groups/group_list.html"

    def get(self, request, course_uuid, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)
        groups = CourseGroup.objects.filter(course=course).prefetch_related('members__participant__mahasiswa')
        
        # Ambil peserta yang BELUM punya kelompok
        assigned_ids = CourseGroupMember.objects.filter(group__course=course).values_list('participant_id', flat=True)
        unassigned_participants = CourseParticipant.objects.filter(course=course).exclude(id__in=assigned_ids)

        return self.render_to_response(self.get_context_data(
            course=course,
            groups=groups,
            unassigned_participants=unassigned_participants
        ))

    # Fitur: Buat Kelompok Baru
    # Fitur: Buat Kelompok Baru
    def post(self, request, course_uuid, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)

        # === 1. BUAT MANUAL ===
        if 'create_group' in request.POST:
            name = request.POST.get('group_name')
            if name:
                with transaction.atomic():
                    # A. Buat Kelompok Database
                    new_group = CourseGroup.objects.create(course=course, name=name)
                    
                    # B. Buat Chat Room (Manual)
                    ChatRoom.objects.create(
                        name=f"Grup: {new_group.name}",
                        room_type='group',
                        group=new_group 
                    )
                messages.success(request, f"Kelompok '{name}' dan Ruang Chat berhasil dibuat.")
            else:
                messages.error(request, "Nama kelompok tidak boleh kosong.")
        
        # === 2. AUTO GENERATE (YANG PERLU DITAMBAHKAN) ===
        elif 'auto_generate' in request.POST:
            try:
                total_groups = int(request.POST.get('total_groups', 5))
                
                # Logic Hapus Kelompok Lama (Opsional tapi disarankan)
                if request.POST.get('clear_existing'):
                    CourseGroup.objects.filter(course=course).delete()

                # Ambil semua peserta aktif
                participants = list(CourseParticipant.objects.filter(course=course))
                
                if not participants:
                    messages.error(request, "Tidak ada peserta untuk dibagi.")
                    return redirect('course-groups', course_uuid=course.uuid)

                random.shuffle(participants) # Acak urutan
                
                # Gunakan transaction atomic agar data konsisten (Group & Chat terbuat bersamaan)
                with transaction.atomic():
                    created_groups = []
                    group_chat_map = {} # Mapping untuk menyimpan ID Chat Room

                    # A. LOOP BUAT GROUP & CHAT ROOM
                    for i in range(total_groups):
                        # 1. Buat Group
                        g = CourseGroup.objects.create(course=course, name=f"Kelompok {i+1}")
                        created_groups.append(g)

                        # 2. [TAMBAHAN] Buat Chat Room Manual
                        chat_room = ChatRoom.objects.create(
                            name=f"Grup: {g.name}",
                            room_type='group',
                            group=g
                        )
                        # Simpan object chat room ke mapping biar mudah diambil nanti
                        group_chat_map[g.id] = chat_room 
                    
                    # B. LOOP DISTRIBUSI PESERTA
                    for index, p in enumerate(participants):
                        # Algoritma Round Robin (Bagi rata)
                        target_group = created_groups[index % total_groups] 
                        
                        # 3. Masukkan ke Group Member (Database)
                        CourseGroupMember.objects.create(group=target_group, participant=p)
                        
                        # 4. [TAMBAHAN] Masukkan User ke Chat Room Participants
                        # Ambil chat room yang pasangannya 'target_group'
                        current_room = group_chat_map[target_group.id]
                        
                        # p.mahasiswa.nim merujuk ke User object (OneToOne)
                        current_room.participants.add(p.mahasiswa.nim)
            
                messages.success(request, f"Berhasil membagi peserta ke dalam {total_groups} kelompok & membuat ruang chat.")

            except ValueError:
                messages.error(request, "Input jumlah kelompok tidak valid.")

        return redirect('course-groups', course_uuid=course.uuid)


# --- VIEW: DETAIL KELOMPOK & MANAGE ANGGOTA ---
class CourseGroupDetailView(DosenRequiredMixin, AcademyView):
    template_name = "groups/group_detail.html"

    def get(self, request, group_id, *args, **kwargs):
        group = get_object_or_404(CourseGroup, id=group_id)
        assigned_ids = CourseGroupMember.objects.filter(group__course=group.course).values_list('participant_id', flat=True)
        available_participants = CourseParticipant.objects.filter(course=group.course).exclude(id__in=assigned_ids)

        return self.render_to_response(self.get_context_data(
            group=group,
            members=group.members.all().select_related('participant__mahasiswa'),
            available_participants=available_participants
        ))

    def post(self, request, group_id, *args, **kwargs):
        group = get_object_or_404(CourseGroup, id=group_id)

        # === TAMBAH ANGGOTA ===
        if 'add_member' in request.POST:
            participant_id = request.POST.get('participant_id')
            role = request.POST.get('role', 'member')
            if participant_id:
                participant = get_object_or_404(CourseParticipant, id=participant_id)
                
                with transaction.atomic():
                    # 1. Tambah ke DB Group
                    CourseGroupMember.objects.create(group=group, participant=participant, role=role)
                    
                    # 2. [LOGIC BARU] Tambah User ke Chat Room
                    try:
                        chat_room = ChatRoom.objects.get(group=group)
                        chat_room.participants.add(participant.mahasiswa.nim)
                    except ChatRoom.DoesNotExist:
                        pass # Atau create baru jika mau defensive coding

                messages.success(request, "Anggota berhasil ditambahkan.")

        # === HAPUS ANGGOTA ===
        elif 'remove_member' in request.POST:
            member_id = request.POST.get('member_id')
            member_obj = get_object_or_404(CourseGroupMember, id=member_id, group=group)
            user_to_remove = member_obj.participant.mahasiswa.nim # Simpan User-nya dulu

            with transaction.atomic():
                # 1. Hapus dari DB Group
                member_obj.delete()

                # 2. [LOGIC BARU] Kick User dari Chat Room
                try:
                    chat_room = ChatRoom.objects.get(group=group)
                    chat_room.participants.remove(user_to_remove)
                except ChatRoom.DoesNotExist:
                    pass

            messages.success(request, "Anggota dihapus dari kelompok.")
        
        # === EDIT NAMA GROUP ===
        elif 'edit_group' in request.POST:
            new_name = request.POST.get('group_name')
            group.name = new_name
            group.save()

            # [LOGIC BARU] Update juga nama Chat Room-nya biar sinkron
            ChatRoom.objects.filter(group=group).update(name=f"Grup: {new_name}")
            
            messages.success(request, "Nama kelompok diperbarui.")

        # === HAPUS GROUP ===
        elif 'delete_group' in request.POST:
            course_uuid = group.course.uuid 
            # ChatRoom otomatis terhapus karena CASCADE di models.py
            group.delete() 
            messages.success(request, "Kelompok berhasil dihapus.")
            return redirect('course-groups', course_uuid=course_uuid)

        return redirect('group-detail', group_id=group.id)
    

class InstructorCoursePreviewView(DosenRequiredMixin, AcademyView):
    template_name = "dosen_course_player.html" # Menggunakan template yang SAMA

    # Security: Hanya Dosen Pembuat atau Admin yang bisa akses
    def test_func(self):
        course = get_object_or_404(Course, uuid=self.kwargs['course_uuid'])
        return self.request.user == course.instructor or self.request.user.is_superuser

    def get(self, request, course_uuid, material_id=None, assignment_id=None, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)
        
        # Ambil semua section/materi (Sama seperti view mahasiswa)
        sections = CourseAgenda.objects.filter(course=course).prefetch_related('materials', 'assignments')

        # === 1. LOGIK ACTIVE ITEM (COPY PASTE DARI VIEW MAHASISWA) ===
        # Dosen tetap perlu logic ini agar saat buka link, langsung muncul materi pertama
        active_item = None
        active_type = None

        if material_id:
            active_item = get_object_or_404(CourseMaterial, id=material_id)
            active_type = 'material'
        elif assignment_id:
            active_item = get_object_or_404(CourseAssignment, id=assignment_id)
            active_type = 'assignment'
        else:
            # Default: Ambil item pertama
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

        # === 2. AMBIL DATA UMUM SAJA ===
        # Kita tampilkan pengumuman agar dosen bisa me-review tampilannya
        announcements = CourseAnnouncement.objects.filter(course=course).order_by('-is_pinned', '-created_at')
        
        # Tampilkan list kuis (tapi tanpa status 'user_is_done')
        quizzes = CourseQuiz.objects.filter(course=course, is_published=True).order_by('start_time')

        # === 3. CONTEXT ===
        # Perhatikan: Kita kirim list kosong [] atau None untuk data-data mahasiswa
        # agar tidak error di template, tapi 'is_instructor' kita set True.
        
        context = self.get_context_data(
            is_instructor=True,          # <--- KUNCI UTAMA
            course=course,
            sections=sections,
            active_item=active_item,
            active_type=active_type,
            announcements=announcements,
            quizzes=quizzes,
            
            # Data Mahasiswa dikosongkan/None
            submission=None,
            completed_material_ids=[], 
            completed_assignment_ids=[],
            attendance_report=[],
            total_hadir=0,
            my_group=None,
            group_members=[],
            is_overdue=False
        )
        return self.render_to_response(context)
        
    # View Dosen TIDAK PERLU method POST karena dosen tidak submit tugas/absen di sini.