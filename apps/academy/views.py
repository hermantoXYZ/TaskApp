from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView
from web_project import TemplateLayout
from .forms import CourseForm, AddParticipantForm, AddAgendaForm, AddAnnouncementForm, AttendanceForm, CourseMaterialForm, AddProgramStudiCourseForm, CoursePeriodForm, CourseAssignmentForm
from django.contrib import messages
from .models import Course, CourseParticipant, CourseAgenda, CourseAnnouncement, CourseAttendance, CourseMaterial, StudentMaterialProgress, Prodi, CoursePeriod, StudentAssignmentSubmission, CourseAssignment
from .models import UserMhs
from django.utils import timezone
from web_project.template_helpers.theme import TemplateHelper
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from .decorators_students import check_userstudents
from .decorators_dosen import DosenRequiredMixin

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
    def get(self, request, course_id, *args, **kwargs):
        course = get_object_or_404(Course, id=course_id)
        form = CourseForm(instance=course)

        return self.render_to_response(self.get_context_data(
            form=form, 
            course=course,
            is_edit=True  
        ))

    def post(self, request, course_id, *args, **kwargs):
        course = get_object_or_404(Course, id=course_id)
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

class EditAllCourse(DosenRequiredMixin, AcademyView):
    template_name = "academy_course.html"

    def get(self, request, course_id, *args, **kwargs):
        course = get_object_or_404(Course, id=course_id)
        return self.render_to_response(self.get_context_data(form=CourseForm(instance=course), course=course))

class ListCourse(AcademyView):
    template_name = "list_academy_course.html"
    def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            courses = Course.objects.all()
            context['courses'] = courses
            return context
    
class DeleteCourse(AcademyView):
    def get(self, request, *args, **kwargs):
        course_id = kwargs.get('course_id')
        course = get_object_or_404(Course, id=course_id)
        course.delete()
        messages.success(request, f'Course {course.code} berhasil dihapus.')
        return redirect('list-academy-course') # Pastikan 'list_course' sesuai nama url di urls.py
    
class AddCourseParticipant(AcademyView):
    template_name = "add_course_participant.html"

    def get(self, request, course_id, *args, **kwargs):
        course = get_object_or_404(Course, id=course_id)
        participants = CourseParticipant.objects.filter(course=course).select_related('mahasiswa')
        
        context = self.get_context_data(
            form=AddParticipantForm(),
            course=course,
            participants=participants
        )
        return self.render_to_response(context)

    def post(self, request, course_id, *args, **kwargs):
        course = get_object_or_404(Course, id=course_id)
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
            return redirect('add-course-participant', course_id=course.id)
                
        participants = CourseParticipant.objects.filter(course=course).select_related('mahasiswa')
        return self.render_to_response(self.get_context_data(form=form, course=course, participants=participants))
    
# 1. VIEW UNTUK TAMBAH (ADD)
class AddCourseAgenda(AcademyView):
    template_name = "add_course_agenda.html"

    def get(self, request, course_id, *args, **kwargs):
        course = get_object_or_404(Course, id=course_id)
        agendas = CourseAgenda.objects.filter(course=course).order_by('agenda_date')
        
        # Logic hitung kehadiran untuk tabel
        self._calculate_attendance(course, agendas)

        return render(request, self.template_name, self.get_context_data(
            form=AddAgendaForm(),
            course=course,
            agendas=agendas,
            is_edit=False
        ))

    def post(self, request, course_id, *args, **kwargs):
        course = get_object_or_404(Course, id=course_id)
        form = AddAgendaForm(request.POST)

        if form.is_valid():
            agenda = form.save(commit=False)
            agenda.course = course
            agenda.save()
            messages.success(request, f'Agenda "{agenda.title}" berhasil ditambahkan.')
            return redirect('add-course-agenda', course_id=course.id)
        
        # Jika error
        agendas = CourseAgenda.objects.filter(course=course).order_by('agenda_date')
        self._calculate_attendance(course, agendas)
        
        return render(request, self.template_name, self.get_context_data(
            form=form,
            course=course,
            agendas=agendas,
            is_edit=False
        ))
    
    # Helper untuk menghitung presensi (agar tidak duplikasi code)
    def _calculate_attendance(self, course, agendas):
        total_participants = CourseParticipant.objects.filter(course=course).count()
        for ag in agendas:
            hadir_count = CourseAttendance.objects.filter(agenda=ag, status__in=['present', 'late']).count()
            ag.hadir_count = hadir_count
            ag.total_students = total_participants
            ag.percent = int((hadir_count / total_participants) * 100) if total_participants > 0 else 0


# 2. VIEW UNTUK EDIT
class EditCourseAgenda(AcademyView):
    template_name = "add_course_agenda.html"

    def get(self, request, course_id, agenda_id, *args, **kwargs):
        course = get_object_or_404(Course, id=course_id)
        agenda_instance = get_object_or_404(CourseAgenda, id=agenda_id, course=course)
        
        agendas = CourseAgenda.objects.filter(course=course).order_by('agenda_date')
        
        # Panggil helper calculation dari class AddCourseAgenda (atau copy paste methodnya)
        # Disini saya copy logic-nya agar independen
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

    def post(self, request, course_id, agenda_id, *args, **kwargs):
        course = get_object_or_404(Course, id=course_id)
        agenda_instance = get_object_or_404(CourseAgenda, id=agenda_id, course=course)
        
        form = AddAgendaForm(request.POST, instance=agenda_instance)

        if form.is_valid():
            form.save()
            messages.success(request, f'Agenda "{agenda_instance.title}" berhasil diperbarui.')
            return redirect('add-course-agenda', course_id=course.id)
        
        agendas = CourseAgenda.objects.filter(course=course).order_by('agenda_date')
        return render(request, self.template_name, self.get_context_data(
            form=form, 
            course=course, 
            agendas=agendas,
            is_edit=True,
            edit_id=agenda_id
        ))


class DeleteCourseAgenda(DosenRequiredMixin, AcademyView):
    def get(self, request, course_id, agenda_id, *args, **kwargs):
        course = get_object_or_404(Course, id=course_id)
        agenda = get_object_or_404(CourseAgenda, id=agenda_id, course=course)
        title = agenda.title
        agenda.delete()       
        messages.success(request, f'Agenda "{title}" berhasil dihapus.')
        return redirect('add-course-agenda', course_id=course.id)

class CourseAnnouncementView(AcademyView):
    template_name = "add_course_announcement.html"

    def get(self, request, course_id, *args, **kwargs):
        course = get_object_or_404(Course, id=course_id)
        announcements = CourseAnnouncement.objects.filter(course=course).order_by('-is_pinned', '-created_at')

        return self.render_to_response(self.get_context_data(
            form=AddAnnouncementForm(),
            course=course,
            announcements=announcements
        ))

    def post(self, request, course_id, *args, **kwargs):
        course = get_object_or_404(Course, id=course_id)
        form = AddAnnouncementForm(request.POST)

        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.course = course
            announcement.save()
            
            messages.success(request, 'Pengumuman berhasil dipublikasikan.')
            return redirect('course-announcement', course_id=course.id)
        
        announcements = CourseAnnouncement.objects.filter(course=course).order_by('-is_pinned', '-created_at')
        return self.render_to_response(self.get_context_data(
            form=form, 
            course=course, 
            announcements=announcements
        ))
    
class CourseAttendanceView(AcademyView):
    template_name = "course_attendance.html"

    def get(self, request, agenda_id, *args, **kwargs):
        agenda = get_object_or_404(CourseAgenda, id=agenda_id)
        course = agenda.course
        
        participants = CourseParticipant.objects.filter(
            course=course
        ).select_related('mahasiswa').order_by('mahasiswa__nim')

        # 3. Siapkan Data Gabungan (Participant + Form Unik)
        student_data = []
        for p in participants:
            # Cek apakah sudah ada data absen sebelumnya?
            existing_obj = CourseAttendance.objects.filter(
                agenda=agenda, 
                participant=p
            ).first()
            
            form = AttendanceForm(instance=existing_obj, prefix=str(p.id))
            
            # Masukkan ke list dictionary
            student_data.append({
                'participant': p, # Untuk ditampilkan Nama/NIM di tabel
                'form': form      # Untuk ditampilkan Radio Button & Input Note
            })

        context = self.get_context_data(
            agenda=agenda,
            course=course,
            student_data=student_data 
        )
        return self.render_to_response(context)

    def post(self, request, agenda_id, *args, **kwargs):
        agenda = get_object_or_404(CourseAgenda, id=agenda_id)
        course = agenda.course
        
        # Ambil ulang participant untuk looping saat simpan
        participants = CourseParticipant.objects.filter(course=course)

        saved_count = 0
        for p in participants:
            # Tangkap data form berdasarkan PREFIX unik tadi
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
        return redirect('course-attendance', agenda_id=agenda.id)
    


class ManageCurriculumView(DosenRequiredMixin, AcademyView):
    template_name = "manage_curriculum.html"

    def get(self, request, course_id, *args, **kwargs):
        course = get_object_or_404(Course, id=course_id)
        sections = CourseAgenda.objects.filter(course=course).prefetch_related('materials')
        
        context = self.get_context_data(
            course=course,
            sections=sections
        )
        return self.render_to_response(context)



class AddCourseMaterialView(DosenRequiredMixin, AcademyView):
    template_name = "add_course_material.html"

    def get(self, request, course_id, *args, **kwargs):
        course = get_object_or_404(Course, id=course_id)
        form = CourseMaterialForm(course_id=course.id)
        
        return self.render_to_response(self.get_context_data(
            form=form, 
            course=course
        ))

    def post(self, request, course_id, *args, **kwargs):
        course = get_object_or_404(Course, id=course_id)
        form = CourseMaterialForm(request.POST, request.FILES, course_id=course.id)

        if form.is_valid():
            material = form.save()
            messages.success(request, f'Materi "{material.title}" berhasil disimpan.')
            return redirect('manage-curriculum', course_id=course.id)
        
        return self.render_to_response(self.get_context_data(form=form, course=course))   
    
class EditCourseMaterialView(DosenRequiredMixin, AcademyView):
    template_name = "add_course_material.html"

    def get(self, request, course_id, material_id, *args, **kwargs):
        course = get_object_or_404(Course, id=course_id)
        material = get_object_or_404(CourseMaterial, id=material_id)
    
        # PERBAIKAN: Ganti 'material.section' menjadi 'material.agenda'
        if material.agenda.course != course:
            messages.error(request, "Materi tidak valid untuk kursus ini.")
            # Redirect kembali ke halaman Agenda, bukan manage-curriculum
            return redirect('add-course-agenda', course_id=course.id)

        form = CourseMaterialForm(instance=material, course_id=course.id)
        
        return self.render_to_response(self.get_context_data(
            form=form, 
            course=course,
            material=material, 
            is_edit=True     
        ))

    def post(self, request, course_id, material_id, *args, **kwargs):
        course = get_object_or_404(Course, id=course_id)
        material = get_object_or_404(CourseMaterial, id=material_id)

        # PERBAIKAN: Ganti 'material.section' menjadi 'material.agenda'
        if material.agenda.course != course:
            return redirect('add-course-agenda', course_id=course.id)

        form = CourseMaterialForm(request.POST, request.FILES, instance=material, course_id=course.id)

        if form.is_valid():
            form.save()
            messages.success(request, f'Materi "{material.title}" berhasil diperbarui.')
            # Redirect kembali ke halaman Agenda
            return redirect('add-course-agenda', course_id=course.id)
        
        return self.render_to_response(self.get_context_data(
            form=form, 
            course=course, 
            material=material,
            is_edit=True
        ))
    
class DeleteCourseMaterialView(DosenRequiredMixin, AcademyView):
    def get(self, request, material_id, *args, **kwargs):
        material = get_object_or_404(CourseMaterial, id=material_id)
        course_id = material.agenda.course.id
        material.delete()
        messages.success(request, f'Materi "{material.title}" berhasil dihapus.')
        return redirect('manage-curriculum', course_id=course_id)
    
class AddCourseAssignmentView(DosenRequiredMixin, AcademyView):
    template_name = "add_course_assignment.html" 

    def get(self, request, course_id, *args, **kwargs):
        course = get_object_or_404(Course, id=course_id)
        form = CourseAssignmentForm(course_id=course.id)
        
        return self.render_to_response(self.get_context_data(
            form=form, 
            course=course
        ))

    def post(self, request, course_id, *args, **kwargs):
        course = get_object_or_404(Course, id=course_id)
        form = CourseAssignmentForm(request.POST, request.FILES, course_id=course.id)

        if form.is_valid():
            assignment = form.save(commit=False)
            if assignment.agenda.course != course:
                messages.error(request, "Agenda tidak valid.")
                return redirect('manage-curriculum', course_id=course.id)
            
            assignment.save()
            messages.success(request, f'Tugas "{assignment.title}" berhasil ditambahkan.')
            return redirect('manage-curriculum', course_id=course.id)
        
        return self.render_to_response(self.get_context_data(
            form=form, 
            course=course
        ))
    
class AssignmentGradingView(DosenRequiredMixin, AcademyView):
    template_name = "grading_assignment.html"

    def get(self, request, assignment_id, *args, **kwargs):
        # 1. Ambil Data Assignment & Course
        assignment = get_object_or_404(CourseAssignment, id=assignment_id)
        course = assignment.agenda.course
        
        # 2. Ambil Semua Peserta (Mahasiswa) di Course ini
        participants = CourseParticipant.objects.filter(course=course).select_related('mahasiswa')
        
        # 3. Gabungkan Data Mahasiswa dengan Data Submission
        grading_list = []
        stats = {'total': participants.count(), 'submitted': 0, 'graded': 0}
        
        for p in participants:
            # Cek apakah mahasiswa ini sudah submit?
            sub = StudentAssignmentSubmission.objects.filter(assignment=assignment, student=p.mahasiswa).first()
            
            status = 'missing' # Default: Belum kumpul
            is_late = False

            if sub:
                status = 'submitted'
                stats['submitted'] += 1
                
                # Cek apakah sudah dinilai
                if sub.score is not None:
                    status = 'graded'
                    stats['graded'] += 1
                
                # Cek apakah terlambat
                if sub.submitted_at > assignment.due_date:
                    is_late = True

            grading_list.append({
                'participant': p,
                'student': p.mahasiswa,
                'submission': sub, 
                'status': status,
                'is_late': is_late
            })

        # 4. Kirim ke Template
        context = self.get_context_data(
            assignment=assignment,
            course=course,
            grading_list=grading_list,
            stats=stats
        )
        return self.render_to_response(context)


# ---------------------------------------------------------
# FUNGSI UNTUK SIMPAN NILAI (Dipanggil tombol Save)
# ---------------------------------------------------------
@login_required
def update_grade_submission(request, submission_id):
    if request.method == "POST":
        submission = get_object_or_404(StudentAssignmentSubmission, id=submission_id)
        
        # Security Check: Pastikan user adalah Dosen/Staff
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, "Anda tidak memiliki izin.")
            return redirect('app-academy-dashboard')

        # Ambil data dari Form
        score = request.POST.get('score')
        feedback = request.POST.get('feedback')

        # Simpan
        if score:
            submission.score = score
            submission.feedback = feedback
            submission.save()
            messages.success(request, f"Nilai untuk {submission.student.nim.first_name} berhasil disimpan.")
        
        # Redirect kembali ke halaman grading
        return redirect('assignment-grading', assignment_id=submission.assignment.id)
    
    return redirect('app-academy-dashboard')