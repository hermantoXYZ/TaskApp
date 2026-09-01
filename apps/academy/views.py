from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.views import View
from web_project import TemplateLayout
from .forms import CourseForm, AddAgendaForm, AddAnnouncementForm, AttendanceForm, CourseMaterialForm, AddProgramStudiCourseForm, CoursePeriodForm, CourseAssignmentForm, CourseQuizForm, QuizQuestionForm, ChangeRoleForm
from django.contrib import messages
from .models import ChatRoom, Course, CourseParticipant, CourseAgenda, CourseAnnouncement, CourseAttendance, CourseMaterial, StudentMaterialProgress, Prodi, CoursePeriod, StudentAssignmentSubmission, CourseAssignment, CourseQuiz, QuizQuestion, QuizOption, StudentQuizAttempt, StudentQuizAnswer, MediaFile, AgendaMediaItem, UserProdi
from .models import UserMhs, CourseGroup, CourseGroupMember, UserDosen, User
from django.utils import timezone
from web_project.template_helpers.theme import TemplateHelper
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .decorators_students import check_userstudents
from .decorators_dosen import DosenRequiredMixin
from .decorators_prodi import ProdiRequiredMixin
from django.utils import timezone as tz
from django.db import transaction
from django.db.models import Q, Sum, Max
import random

from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin

from django.db.models import Case, When, Value, IntegerField


class AcademyView(TemplateView):
    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        return context

class AcademyDashboardView(AcademyView):
    template_name = "app_academy_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        coached_courses = []
        my_courses = []
        active_period = None
        is_dosen = False
        is_student = False
        is_prodi = False

        try:
            from .models import UserProdi
            user_prodi = UserProdi.objects.select_related('prodi').get(username=user)
            is_prodi = True
            self.template_name = "prodi/dashboard_prodi.html"
            active_period = CoursePeriod.objects.filter(is_active=True).first()
            all_periods   = CoursePeriod.objects.all().order_by('-start_date')
            prodi = user_prodi.prodi
            base_qs = Course.objects.filter(is_active=True)
            if prodi:
                base_qs = base_qs.filter(prodi=prodi)

            period_id = self.request.GET.get('period')
            if period_id:
                try:
                    active_period = CoursePeriod.objects.get(id=period_id)
                except CoursePeriod.DoesNotExist:
                    pass
            if active_period:
                base_qs = base_qs.filter(period=active_period)

            total_courses   = base_qs.count()
            total_agendas   = CourseAgenda.objects.filter(course__in=base_qs).count()
            total_dosen     = UserDosen.objects.filter(coached_courses__in=base_qs).distinct().count()
            total_mahasiswa = CourseParticipant.objects.filter(
                course__in=base_qs, mahasiswa__isnull=False
            ).values('mahasiswa').distinct().count()
            total_materials = CourseMaterial.objects.filter(agenda__course__in=base_qs).count()
            total_tasks     = CourseAssignment.objects.filter(agenda__course__in=base_qs).count()
            courses_detail = base_qs.select_related('period', 'prodi').prefetch_related('coaches', 'participants')
            for c in courses_detail:
                c.student_count  = c.participants.filter(mahasiswa__isnull=False).count()
                c.material_count = CourseMaterial.objects.filter(agenda__course=c).count()
                c.task_count     = CourseAssignment.objects.filter(agenda__course=c).count()

            context.update({
                'user_prodi':       user_prodi,
                'prodi':            prodi,
                'active_period':    active_period,
                'all_periods':      all_periods,
                'total_courses':    total_courses,
                'total_agendas':    total_agendas,
                'total_dosen':      total_dosen,
                'total_mahasiswa':  total_mahasiswa,
                'total_materials':  total_materials,
                'total_tasks':      total_tasks,
                'courses_detail':   courses_detail,
                'is_prodi':         True,
            })
            return context
        except Exception:
            pass

        try:
            dosen = UserDosen.objects.get(nip=user)
            is_dosen = True
            active_period = CoursePeriod.objects.filter(is_active=True).first()
            qs = Course.objects.filter(
                coaches=dosen,
                is_active=True
            ).select_related('period', 'prodi').prefetch_related('participants').order_by('period__name', 'code')
            for course in qs:
                course.student_count = course.participants.filter(is_active=True).count()
                course.agenda_count = CourseAgenda.objects.filter(course=course, is_active=True).count()
            coached_courses = qs
        except UserDosen.DoesNotExist:
            pass

        if not is_dosen:
            try:
                from .models import UserMhs, StudentMaterialProgress as SMP
                mhs = UserMhs.objects.get(nim=user)
                is_student = True
                active_period = CoursePeriod.objects.filter(is_active=True).first()
                enrolled_participants = CourseParticipant.objects.filter(
                    mahasiswa=mhs
                ).select_related('course')
                enrolled_course_ids = enrolled_participants.values_list('course_id', flat=True)
                qs_mhs = Course.objects.filter(id__in=enrolled_course_ids)\
                    .select_related('prodi', 'period')\
                    .prefetch_related('coaches')\
                    .order_by('-created_at')
                participant_map = {p.course_id: p for p in enrolled_participants}
                for course in qs_mhs:
                    participant = participant_map.get(course.id)
                    total = CourseMaterial.objects.filter(agenda__course=course).count()
                    if participant and total > 0:
                        completed = SMP.objects.filter(
                            participant=participant, is_completed=True
                        ).count()
                        course.progress = round((completed / total) * 100)
                    else:
                        course.progress = 0
                    course.agenda_count = CourseAgenda.objects.filter(course=course, is_active=True).count()
                my_courses = qs_mhs
            except UserMhs.DoesNotExist:
                pass
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Dashboard mahasiswa error: {e}")

        context['coached_courses'] = coached_courses
        context['my_courses'] = my_courses
        context['active_period'] = active_period
        context['all_periods'] = CoursePeriod.objects.all().order_by('-start_date')
        context['is_dosen'] = is_dosen
        context['is_student'] = is_student
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
class AddCourse(ProdiRequiredMixin, AcademyView):
    template_name = "prodi/add_academy_course.html"
    def get(self, request, *args, **kwargs):
        return self.render_to_response(self.get_context_data(form=CourseForm()))
    def post(self, request, *args, **kwargs):
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save()
            messages.success(request, f'Course {course.code} berhasil dibuat.')
            return redirect('list-academy-course')
        return self.render_to_response(self.get_context_data(form=form))
    
class AddProgramStudiCourse(ProdiRequiredMixin, AcademyView):
    template_name = "prodi/add_program_studi_course.html"

    def get(self, request, *args, **kwargs):
        data_prodi = Prodi.objects.all().order_by('-id')
        context = self.get_context_data(form=AddProgramStudiCourseForm())
        context['data_list'] = data_prodi 
        
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        form = AddProgramStudiCourseForm(request.POST)
        if form.is_valid():
            course = form.save()
            messages.success(request, f'Course Prodi berhasil dibuat.')
            return redirect('program-studi-course') 
            
        data_prodi = Prodi.objects.all().order_by('-id')
        context = self.get_context_data(form=form)
        context['data_list'] = data_prodi
        
        return self.render_to_response(context)
    
class EditProgramStudiCourse(ProdiRequiredMixin, AcademyView):
    template_name = "prodi/add_program_studi_course.html" 

    def get(self, request, pk, *args, **kwargs):
        course_obj = get_object_or_404(Prodi, id=pk)
        form = AddProgramStudiCourseForm(instance=course_obj)
        data_prodi = Prodi.objects.all().order_by('-id')

        context = self.get_context_data(form=form)
        context['data_list'] = data_prodi
        context['is_edit'] = True 
        
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

class AddCoursePeriod(ProdiRequiredMixin, AcademyView):
    template_name = "prodi/add_course_period.html" 

    def get(self, request, *args, **kwargs):
        data_period = CoursePeriod.objects.all().order_by('-created_at')
        context = self.get_context_data(form=CoursePeriodForm())
        context['data_list'] = data_period
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        form = CoursePeriodForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Periode Course berhasil dibuat.')
            return redirect('course-period') 
            
        data_period = CoursePeriod.objects.all().order_by('-id')
        context = self.get_context_data(form=form)
        context['data_list'] = data_period
        return self.render_to_response(context)

class EditCoursePeriod(ProdiRequiredMixin, AcademyView):
    template_name = "prodi/add_course_period.html"

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

class EditCourse(ProdiRequiredMixin, AcademyView):
    template_name = "prodi/add_academy_course.html" 
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
    
class ListCourse(ProdiRequiredMixin, AcademyView):
    template_name = "prodi/list_academy_course.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request = self.request

        q_search  = request.GET.get('q', '').strip()
        q_period  = request.GET.get('period', '').strip()
        q_group   = request.GET.get('group', '').strip()

        all_periods = CoursePeriod.objects.all().order_by('-start_date')
        all_groups  = Course.objects.values_list('group', flat=True).distinct().order_by('group')

        if not q_period:
            latest_period = all_periods.first()
            if latest_period:
                q_period = str(latest_period.id)

        courses = Course.objects.filter()

        if q_search:
            courses = courses.filter(
                Q(name__icontains=q_search) | Q(code__icontains=q_search)
            )
        if q_period:
            courses = courses.filter(period__id=q_period)
        if q_group:
            courses = courses.filter(group__icontains=q_group)

        context.update({
            'courses':     courses,
            'all_periods': all_periods,
            'all_groups':  all_groups,
            'q_search':    q_search,
            'q_period':    q_period,
            'q_group':     q_group,
        })
        return context
    
class ListDosenCourse(DosenRequiredMixin, AcademyView):
    template_name = "dosen/list_dosen_course.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request = self.request

        q_search  = request.GET.get('q', '').strip()
        q_period  = request.GET.get('period', '').strip()
        q_group   = request.GET.get('group', '').strip()

        all_periods = CoursePeriod.objects.filter(courses__coaches__nip=request.user).distinct().order_by('-start_date')
        all_groups  = Course.objects.filter(coaches__nip=request.user).values_list('group', flat=True).distinct().order_by('group')

        if not q_period:
            latest_period = all_periods.first()
            if latest_period:
                q_period = str(latest_period.id)

        courses = Course.objects.filter(coaches__nip=request.user)

        if q_search:
            courses = courses.filter(
                Q(name__icontains=q_search) | Q(code__icontains=q_search)
            )
        if q_period:
            courses = courses.filter(period__id=q_period)
        if q_group:
            courses = courses.filter(group__icontains=q_group)

        context.update({
            'courses':     courses,
            'all_periods': all_periods,
            'all_groups':  all_groups,
            'q_search':    q_search,
            'q_period':    q_period,
            'q_group':     q_group,
        })
        return context
    
class AddCourseParticipant(DosenRequiredMixin, AcademyView):
    template_name = "add_participant.html"

    def get(self, request, course_uuid, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)
        participants = CourseParticipant.objects.filter(course=course).select_related('mahasiswa')
        
        context = self.get_context_data(
            course=course,
            participants=participants
        )
        return self.render_to_response(context)
    
class AddCourseAgenda(DosenRequiredMixin, AcademyView):
    template_name = "add_agenda.html"

    def _get_agendas(self, course):
        return (
            CourseAgenda.objects
            .filter(course=course)
            .select_related('created_by__nip')
            .prefetch_related('materials', 'assignments')
            .order_by('session_number', 'agenda_date')
        )

    def get(self, request, course_uuid, *args, **kwargs):
        course = get_object_or_404(
            Course.objects.prefetch_related('coaches', 'participants'),
            uuid=course_uuid
        )
        agendas = self._get_agendas(course)
        self._calculate_attendance(course, agendas)

        try:
            dosen = UserDosen.objects.get(nip=request.user)
            importable_materials = CourseMaterial.objects.filter(
                agenda__course__coaches=dosen
            ).select_related('agenda', 'agenda__course').order_by('-created_at')
        except UserDosen.DoesNotExist:
            importable_materials = CourseMaterial.objects.all().select_related('agenda', 'agenda__course').order_by('-created_at')

        return render(request, self.template_name, self.get_context_data(
            course=course,
            agendas=agendas,
            importable_materials=importable_materials,
        ))

    def _calculate_attendance(self, course, agendas):
        now = tz.now()
        total_participants = CourseParticipant.objects.filter(course=course).count()
        for ag in agendas:
            hadir_count = CourseAttendance.objects.filter(
                agenda=ag, status__in=['present', 'late']
            ).count()
            ag.hadir_count = hadir_count
            ag.total_students = total_participants
            ag.percent = int((hadir_count / total_participants) * 100) if total_participants > 0 else 0
            ag.is_done = ag.agenda_date < now if ag.agenda_date else False
            ag.has_konten_materi = ag.materials.exists()

class DeleteAgendaMediaItemView(DosenRequiredMixin, AcademyView):
    def get(self, request, course_uuid, item_id, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)
        item = get_object_or_404(AgendaMediaItem, id=item_id, agenda__course=course)
        course_uuid_val = course.uuid
        item.delete()
        messages.success(request, 'Berkas berhasil dilepas dari sesi.')
        return redirect('add-course-agenda', course_uuid=course_uuid_val)

class EditCourseAgenda(DosenRequiredMixin, AcademyView):
    template_name = "edit_agenda.html"
    def _get_agendas(self, course):
        return list(
            CourseAgenda.objects
            .filter(course=course)
            .select_related('created_by__nip')
            .prefetch_related('materials', 'assignments')
            .order_by('session_number', 'agenda_date')
        )

    def _get_prev_next(self, agendas, agenda_id):
        """Cari prev dan next agenda berdasarkan posisi di list."""
        ids = [ag.id for ag in agendas]
        try:
            idx = ids.index(agenda_id)
        except ValueError:
            return None, None
        prev_ag = agendas[idx - 1] if idx > 0 else None
        next_ag = agendas[idx + 1] if idx < len(agendas) - 1 else None
        return prev_ag, next_ag

    def _annotate_attendance(self, course, agendas):
        from django.utils import timezone as tz
        now = tz.now()
        total_participants = CourseParticipant.objects.filter(course=course).count()
        for ag in agendas:
            hadir_count = CourseAttendance.objects.filter(agenda=ag, status__in=['present', 'late']).count()
            ag.hadir_count = hadir_count
            ag.total_students = total_participants
            ag.percent = int((hadir_count / total_participants) * 100) if total_participants > 0 else 0
            ag.is_done = ag.agenda_date < now if ag.agenda_date else False

    def get(self, request, course_uuid, agenda_id, *args, **kwargs):
        course = get_object_or_404(
            Course.objects.prefetch_related('coaches'),
            uuid=course_uuid
        )
        agenda_instance = get_object_or_404(CourseAgenda, id=agenda_id, course=course)
        agendas = self._get_agendas(course)
        self._annotate_attendance(course, agendas)
        prev_ag, next_ag = self._get_prev_next(agendas, agenda_id)

        form = AddAgendaForm(instance=agenda_instance, course=course)
        return render(request, self.template_name, self.get_context_data(
            form=form,
            course=course,
            agendas=agendas,
            edit_agenda=agenda_instance,
            prev_agenda=prev_ag,
            next_agenda=next_ag,
            is_edit=True,
        ))

    def post(self, request, course_uuid, agenda_id, *args, **kwargs):
        course = get_object_or_404(
            Course.objects.prefetch_related('coaches'),
            uuid=course_uuid
        )
        agenda_instance = get_object_or_404(CourseAgenda, id=agenda_id, course=course)
        form = AddAgendaForm(request.POST, instance=agenda_instance, course=course)

        if form.is_valid():
            updated = form.save(commit=False)
            try:
                updated.created_by = UserDosen.objects.get(nip=request.user)
            except Exception:
                pass
            updated.save()
            messages.success(request, f'Sesi "{updated.title}" berhasil diperbarui.')

            # Cek apakah user klik "Simpan & Sesi Berikutnya"
            if request.POST.get('redirect_to_next'):
                agendas = self._get_agendas(course)
                _, next_ag = self._get_prev_next(agendas, agenda_id)
                if next_ag:
                    return redirect('edit-course-agenda', course_uuid=course.uuid, agenda_id=next_ag.id)

            return redirect('add-course-agenda', course_uuid=course.uuid)

        agendas = self._get_agendas(course)
        self._annotate_attendance(course, agendas)
        prev_ag, next_ag = self._get_prev_next(agendas, agenda_id)
        return render(request, self.template_name, self.get_context_data(
            form=form,
            course=course,
            agendas=agendas,
            edit_agenda=agenda_instance,
            prev_agenda=prev_ag,
            next_agenda=next_ag,
            is_edit=True,
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
    
class AdminCourseAgendaListView(ProdiRequiredMixin, AcademyView):
    template_name = "prodi/admin_agenda_list.html"

    def get(self, request, course_uuid, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)
        agendas = CourseAgenda.objects.filter(course=course).select_related('lecturer__nip').order_by('session_number', 'agenda_date')
        
        return self.render_to_response(self.get_context_data(
            course=course,
            agendas=agendas,
        ))

class AdminCourseAgendaCreateView(ProdiRequiredMixin, AcademyView):
    template_name = "prodi/admin_agenda_form.html"

    def get(self, request, course_uuid, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)
        form = AddAgendaForm(course=course)
        return self.render_to_response(self.get_context_data(
            form=form,
            course=course,
            is_edit=False
        ))

    def post(self, request, course_uuid, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)
        form = AddAgendaForm(request.POST, course=course)

        if form.is_valid():
            agenda = form.save(commit=False)
            agenda.course = course
            agenda.save()
            messages.success(request, f'Sesi "{agenda.title}" berhasil dibuat.')
            return redirect('admin-course-agenda', course_uuid=course.uuid)

        return self.render_to_response(self.get_context_data(
            form=form,
            course=course,
            is_edit=False
        ))

class AdminCourseAgendaEditView(ProdiRequiredMixin, AcademyView):
    template_name = "prodi/admin_agenda_form.html"

    def get(self, request, course_uuid, agenda_id, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)
        agenda = get_object_or_404(CourseAgenda, id=agenda_id, course=course)
        form = AddAgendaForm(instance=agenda, course=course)
        return self.render_to_response(self.get_context_data(
            form=form,
            course=course,
            agenda=agenda,
            is_edit=True
        ))

    def post(self, request, course_uuid, agenda_id, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)
        agenda = get_object_or_404(CourseAgenda, id=agenda_id, course=course)
        form = AddAgendaForm(request.POST, instance=agenda, course=course)

        if form.is_valid():
            form.save()
            messages.success(request, f'Sesi "{agenda.title}" berhasil diperbarui.')
            return redirect('admin-course-agenda', course_uuid=course.uuid)

        return self.render_to_response(self.get_context_data(
            form=form,
            course=course,
            agenda=agenda,
            is_edit=True
        ))


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
            try:
                announcement.created_by = UserDosen.objects.get(nip=request.user)
            except Exception:
                pass
            announcement.save()

            # Sinkronisasi thread diskusi otomatis
            from .views_discussion import _sync_linked_discussion_on_content_save
            fallback_user = request.user
            _sync_linked_discussion_on_content_save(
                course, 'announcement', announcement, fallback_user
            )

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
        course = get_object_or_404(Course, uuid=course_uuid)
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
    

class AddCourseMaterialView(DosenRequiredMixin, AcademyView):
    template_name = "add_material.html"

    def get(self, request, course_uuid, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)
        form = CourseMaterialForm(course_uuid=course.uuid)
        agenda_id = request.GET.get('agenda')
        if agenda_id:
            try:
                form.fields['agenda'].initial = int(agenda_id)
            except (ValueError, TypeError):
                pass

        try:
            dosen = UserDosen.objects.get(nip=request.user)
            importable_materials = CourseMaterial.objects.filter(
                agenda__course__coaches=dosen
            ).select_related('agenda', 'agenda__course').order_by('-created_at')
        except UserDosen.DoesNotExist:
            importable_materials = CourseMaterial.objects.all().select_related('agenda', 'agenda__course').order_by('-created_at')

        agendas = course.agendas.all().order_by('session_number')

        return self.render_to_response(self.get_context_data(
            form=form,
            course=course,
            agendas=agendas,
            preselected_agenda_id=agenda_id,
            importable_materials=importable_materials,
        ))

    def post(self, request, course_uuid, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)
        form = CourseMaterialForm(request.POST, request.FILES, course_uuid=course.uuid)

        if form.is_valid():
            material = form.save(commit=False)
            try:
                material.created_by = UserDosen.objects.get(nip=request.user)
            except UserDosen.DoesNotExist:
                pass
            material.save()
            messages.success(request, f'Materi "{material.title}" berhasil disimpan.')
            return redirect('add-course-agenda', course_uuid=course.uuid)
        
        return self.render_to_response(self.get_context_data(form=form, course=course))

class ImportCourseMaterialView(DosenRequiredMixin, AcademyView):
    def post(self, request, course_uuid, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)
        target_agenda_id = request.POST.get('target_agenda_id')
        source_material_id = request.POST.get('source_material_id')

        if not target_agenda_id or not source_material_id:
            messages.error(request, "Silakan pilih pertemuan tujuan dan materi yang ingin diimpor.")
            return redirect('add-course-agenda', course_uuid=course.uuid)

        target_agenda = get_object_or_404(CourseAgenda, id=target_agenda_id, course=course)
        source_material = get_object_or_404(CourseMaterial, id=source_material_id)

        last_order = CourseMaterial.objects.filter(agenda=target_agenda).aggregate(Max('order'))['order__max'] or 0

        try:
            dosen = UserDosen.objects.get(nip=request.user)
        except UserDosen.DoesNotExist:
            dosen = None

        new_material = CourseMaterial.objects.create(
            agenda=target_agenda,
            title=f"{source_material.title} (Salinan)",
            text_content=source_material.text_content,
            order=last_order + 1,
            is_published=False,
            allow_discussion=source_material.allow_discussion,
            created_by=dosen
        )

        messages.success(request, f'Berhasil mengimpor materi "{source_material.title}" ke {target_agenda.title}.')
        return redirect('edit-course-material', course_uuid=course.uuid, material_id=new_material.id)   
    
class EditCourseMaterialView(DosenRequiredMixin, AcademyView):
    template_name = "add_material.html"

    def get(self, request, course_uuid, material_id, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)
        material = get_object_or_404(CourseMaterial, id=material_id)
        if material.agenda.course != course:
            messages.error(request, "Materi tidak valid untuk kursus ini.")
            return redirect('edit-course-material', course_uuid=course.uuid, material_id=material.id)

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
        if material.agenda.course != course:
            return redirect('edit-course-material', course_uuid=course.uuid, material_id=material.id)

        form = CourseMaterialForm(request.POST, request.FILES, instance=material, course_uuid=course.uuid)

        if form.is_valid():
            updated = form.save(commit=False)
            if not updated.created_by:
                try:
                    updated.created_by = UserDosen.objects.get(nip=request.user)
                except UserDosen.DoesNotExist:
                    pass
            updated.save()
            messages.success(request, f'Materi "{updated.title}" berhasil diperbarui.')
            return redirect('edit-course-material', course_uuid=course.uuid, material_id=material.id)
        
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
        return redirect('add-course-agenda', course_uuid=course_uuid)

class MediaLibraryListView(DosenRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        q = request.GET.get('q', '').strip()
        files = MediaFile.objects.filter(uploaded_by=request.user)
        if q:
            files = files.filter(name__icontains=q)

        data = []
        for f in files:
            data.append({
                'id':         str(f.id),
                'name':       f.name,
                'file_type':  f.file_type,
                'file_url':   request.build_absolute_uri(f.file.url) if f.file else None,
                'video_url':  f.video_url,
                'size':       f.file_size_display,
                'updated_at': f.updated_at.strftime('%d %b %Y, %H:%M'),
            })

        return JsonResponse({'files': data})


class MediaLibraryUploadView(DosenRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        upload_type = request.POST.get('upload_type', 'file')   # 'file' | 'video_url'
        name = request.POST.get('name', '').strip()

        if upload_type == 'video_url':
            video_url = request.POST.get('video_url', '').strip()
            if not video_url:
                return JsonResponse({'success': False, 'error': 'URL video tidak boleh kosong.'}, status=400)
            if not name:
                name = video_url
            media = MediaFile.objects.create(
                name=name,
                file_type='video_url',
                video_url=video_url,
                uploaded_by=request.user,
            )
        else:
            file_obj = request.FILES.get('file')
            if not file_obj:
                return JsonResponse({'success': False, 'error': 'Tidak ada file yang dikirim.'}, status=400)
            if not name:
                name = file_obj.name
            ext = file_obj.name.rsplit('.', 1)[-1].lower()
            type_map = {'pdf': 'pdf', 'docx': 'docx', 'pptx': 'pptx',
                        'jpg': 'image', 'jpeg': 'image', 'png': 'image', 'gif': 'image'}
            file_type = type_map.get(ext, 'other')
            media = MediaFile(
                name=name,
                file_type=file_type,
                uploaded_by=request.user,
            )
            media.file = file_obj
            media.save()   # save() akan hitung file_size otomatis

        return JsonResponse({
            'success':    True,
            'id':         str(media.id),
            'name':       media.name,
            'file_type':  media.file_type,
            'file_url':   request.build_absolute_uri(media.file.url) if media.file else None,
            'video_url':  media.video_url,
            'size':       media.file_size_display,
            'updated_at': media.updated_at.strftime('%d %b %Y, %H:%M'),
        })

class MediaLibraryDeleteView(DosenRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        media = get_object_or_404(MediaFile, id=pk, uploaded_by=request.user)
        if media.file:
            import os
            from django.conf import settings
            file_path = os.path.join(settings.MEDIA_ROOT, media.file.name)
            if os.path.isfile(file_path):
                os.remove(file_path)
        media.delete()
        return JsonResponse({'success': True})

    def get(self, request, pk, *args, **kwargs):
        return self.post(request, pk, *args, **kwargs)

class MediaLibraryAttachView(DosenRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        media_file_id = request.POST.get('media_file_id')
        agenda_id     = request.POST.get('agenda_id')
        course_uuid   = request.POST.get('course_uuid')

        if not all([media_file_id, agenda_id, course_uuid]):
            return JsonResponse({'success': False, 'error': 'Parameter tidak lengkap.'}, status=400)

        media_file = get_object_or_404(MediaFile, id=media_file_id)
        agenda     = get_object_or_404(CourseAgenda, id=agenda_id)
        course     = get_object_or_404(Course, uuid=course_uuid)

        if agenda.course != course:
            return JsonResponse({'success': False, 'error': 'Agenda tidak valid.'}, status=403)
        last_order = AgendaMediaItem.objects.filter(agenda=agenda).count()
        item, created = AgendaMediaItem.objects.get_or_create(
            agenda=agenda,
            media_file=media_file,
            defaults={'order': last_order + 1}
        )

        if not created:
            return JsonResponse({
                'success': False,
                'error': f'Berkas "{media_file.name}" sudah ada di sesi ini.'
            }, status=400)

        return JsonResponse({
            'success':  True,
            'item_id':  item.id,
            'name':     media_file.name,
        })
    
class AddCourseAssignmentView(DosenRequiredMixin, AcademyView):
    template_name = "add_assignment.html"

    def get(self, request, course_uuid, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)
        form = CourseAssignmentForm(course_uuid=course.uuid)
        agenda_id = request.GET.get('agenda')
        if agenda_id:
            try:
                form.fields['agenda'].initial = int(agenda_id)
            except (ValueError, TypeError):
                pass

        return self.render_to_response(self.get_context_data(
            form=form,
            course=course,
            preselected_agenda_id=agenda_id
        ))

    def post(self, request, course_uuid, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)
        form = CourseAssignmentForm(request.POST, request.FILES, course_uuid=course.uuid)

        if form.is_valid():
            assignment = form.save(commit=False)
            if assignment.agenda.course != course:
                messages.error(request, "Agenda tidak valid.")
                return redirect('add-course-agenda', course_uuid=course.uuid)
            
            assignment.save()
            messages.success(request, f'Tugas "{assignment.title}" berhasil ditambahkan.')
            return redirect('add-course-agenda', course_uuid=course.uuid)
        
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
            return redirect('add-course-agenda', course_uuid=course.uuid)

        form = CourseAssignmentForm(request.POST, request.FILES, instance=assignment, course_uuid=course.uuid)

        if form.is_valid():
            form.save()
            messages.success(request, f'Tugas "{assignment.title}" berhasil diperbarui.')
            return redirect('add-course-agenda', course_uuid=course.uuid)
        
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
            return redirect('add-agenda-course', course_uuid=course.uuid)
        title = assignment.title
        assignment.delete()
        messages.success(request, f'Tugas "{title}" berhasil dihapus.')
        return redirect('add-agenda-course', course_uuid=course.uuid)
    
# apps/academy/views.py

class AssignmentGradingView(DosenRequiredMixin, AcademyView):
    template_name = "grading_assignment.html"

    # Method GET (Menampilkan Daftar - TIDAK BERUBAH)
    def get(self, request, course_uuid, assignment_id, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)
        assignment = get_object_or_404(CourseAssignment, id=assignment_id)
        
        if assignment.agenda.course != course:
            messages.error(request, "Tugas tidak ditemukan di kelas ini.")
            return redirect('add-agenda-course', course_uuid=course.uuid)
        
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

    def post(self, request, course_uuid, assignment_id, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)
        assignment = get_object_or_404(CourseAssignment, id=assignment_id)
        submission_id = request.POST.get('submission_id')
        score = request.POST.get('score')
        feedback = request.POST.get('feedback')
        submission = get_object_or_404(StudentAssignmentSubmission, id=submission_id)

        if submission.assignment.id != assignment.id:
            messages.error(request, "Terjadi kesalahan data (Assignment Mismatch).")
            return redirect('assignment-grading', course_uuid=course.uuid, assignment_id=assignment.id)

        if score:
            submission.score = score
            submission.feedback = feedback
            submission.save()
            target_name = submission.student.nim.first_name
            messages.success(request, f"Nilai untuk {target_name} berhasil disimpan.")

        return redirect('assignment-grading', course_uuid=course.uuid, assignment_id=assignment.id)

    def _get_status(self, sub, assignment):
        status = 'missing'
        is_late = False
        if sub:
            status = 'submitted'
            if sub.score is not None: status = 'graded'
            if sub.submitted_at > assignment.due_date: is_late = True
        return status, is_late
    


class CourseAssessmentView(DosenRequiredMixin, AcademyView):
    """Halaman Asesmen — menampilkan semua Tugas & Quiz dalam satu tabel."""
    template_name = "course_assessment.html"

    def get(self, request, course_uuid, *args, **kwargs):
        course = get_object_or_404(
            Course.objects.prefetch_related('coaches', 'participants'),
            uuid=course_uuid
        )

        assignments = (
            CourseAssignment.objects
            .filter(agenda__course=course)
            .select_related('agenda')
            .prefetch_related('submissions')
            .order_by('due_date')
        )

        total_participants = course.participants.count()

        assessment_list = []
        for asgn in assignments:
            graded_count = asgn.submissions.exclude(score__isnull=True).count()
            submission_count = asgn.submissions.count()
            assessment_list.append({
                'id': asgn.id,
                'title': asgn.title,
                'kategori': 'Tugas',
                'assignment_type': asgn.get_assignment_type_display(),
                'agenda': asgn.agenda,
                'due_date': asgn.due_date,
                'updated_at': asgn.updated_at,
                'is_published': asgn.is_published,
                'submission_count': submission_count,
                'graded_count': graded_count,
                'total_participants': total_participants,
                'grading_url': 'assignment-grading',
                'edit_url': 'edit-course-assignment',
                'delete_url': 'delete-course-assignment',
                'obj_id': asgn.id,
                'type': 'assignment',
            })

        # Kumpulkan semua quiz course ini
        quizzes = (
            CourseQuiz.objects
            .filter(course=course)
            .prefetch_related('attempts')
            .order_by('start_time')
        )

        for quiz in quizzes:
            attempt_count = quiz.attempts.count()
            assessment_list.append({
                'id': quiz.id,
                'title': quiz.title,
                'kategori': quiz.get_quiz_type_display(),
                'assignment_type': None,
                'agenda': None,
                'due_date': quiz.end_time,
                'updated_at': quiz.start_time,
                'is_published': quiz.is_published,
                'submission_count': attempt_count,
                'graded_count': attempt_count,
                'total_participants': total_participants,
                'grading_url': 'quiz-submissions',
                'edit_url': 'course-quiz-edit',
                'delete_url': 'quiz-delete',
                'obj_id': quiz.id,
                'type': 'quiz',
            })

        # Urutkan: published dulu, lalu by due_date
        assessment_list.sort(key=lambda x: (not x['is_published'], x['due_date'] or ''))

        return render(request, self.template_name, self.get_context_data(
            course=course,
            assessment_list=assessment_list,
            total_participants=total_participants,
        ))


class CourseQuizListView(DosenRequiredMixin, AcademyView):
    template_name = "quiz/quiz_list.html"

    def get(self, request, course_uuid, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)
        quizzes = CourseQuiz.objects.filter(course=course).order_by('start_time')
        
        try:
            dosen = UserDosen.objects.get(nip=request.user)
            importable_quizzes = CourseQuiz.objects.filter(
                course__coaches=dosen
            ).exclude(course=course).select_related('course').order_by('-created_at')
        except UserDosen.DoesNotExist:
            importable_quizzes = CourseQuiz.objects.exclude(course=course).select_related('course').order_by('-created_at')

        return self.render_to_response(self.get_context_data(
            course=course,
            quizzes=quizzes,
            importable_quizzes=importable_quizzes
        ))


class ImportCourseQuizView(DosenRequiredMixin, AcademyView):
    def post(self, request, course_uuid, *args, **kwargs):
        target_course = get_object_or_404(Course, uuid=course_uuid)
        source_quiz_id = request.POST.get('source_quiz_id')

        if not source_quiz_id:
            messages.error(request, "Silakan pilih kuis yang ingin diimpor.")
            return redirect('course-quiz-list', course_uuid=target_course.uuid)

        source_quiz = get_object_or_404(CourseQuiz, id=source_quiz_id)

        with transaction.atomic():
            new_quiz = CourseQuiz.objects.create(
                course=target_course,
                title=f"{source_quiz.title} (Salinan)",
                description=source_quiz.description,
                quiz_type=source_quiz.quiz_type,
                start_time=timezone.now(),
                end_time=timezone.now() + timezone.timedelta(days=7),
                duration_minutes=source_quiz.duration_minutes,
                passing_score=source_quiz.passing_score,
                max_attempts=source_quiz.max_attempts,
                is_published=False
            )

            for q in source_quiz.questions.all().prefetch_related('options'):
                new_q = QuizQuestion.objects.create(
                    quiz=new_quiz,
                    text=q.text,
                    image=q.image,
                    question_type=q.question_type,
                    score_weight=q.score_weight,
                    order=q.order
                )
                for opt in q.options.all():
                    QuizOption.objects.create(
                        question=new_q,
                        text=opt.text,
                        is_correct=opt.is_correct,
                        order=opt.order
                    )

        messages.success(request, f'Berhasil mengimpor kuis "{source_quiz.title}". Silakan sesuaikan jadwal pelaksanaan kuis.')
        return redirect('course-quiz-edit', course_uuid=target_course.uuid, quiz_id=new_quiz.id)


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

class CourseQuizUpdateView(DosenRequiredMixin, AcademyView):
    template_name = "quiz/quiz_form.html"

    def get(self, request, course_uuid, quiz_id, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)
        quiz = get_object_or_404(CourseQuiz, id=quiz_id, course=course)
        form = CourseQuizForm(instance=quiz)
        
        return self.render_to_response(self.get_context_data(
            form=form,
            course=course,
            quiz=quiz,
            is_edit=True
        ))

    def post(self, request, course_uuid, quiz_id, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)
        quiz = get_object_or_404(CourseQuiz, id=quiz_id, course=course)
        form = CourseQuizForm(request.POST, instance=quiz)
        
        if form.is_valid():
            form.save()
            messages.success(request, "Informasi kuis berhasil diperbarui.")
            return redirect('course-quiz-list', course_uuid=course.uuid)
        
        return self.render_to_response(self.get_context_data(
            form=form,
            course=course,
            quiz=quiz,
            is_edit=True
        ))
    

class QuizManageView(DosenRequiredMixin, AcademyView):
    template_name = "quiz/quiz_manage.html"

    def get(self, request, quiz_id, *args, **kwargs):
        quiz = get_object_or_404(CourseQuiz, id=quiz_id)
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
                question = form.save(commit=False)
                question.quiz = quiz
                question.question_type = q_type
                
                last_order = QuizQuestion.objects.filter(quiz=quiz).count()
                question.order = last_order + 1
                question.save()

                if q_type == 'multiple_choice':
                    options = request.POST.getlist('option_text')
                    correct_index = request.POST.get('correct_option') 

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
                q = form.save(commit=False)
                q.save()

                if question.question_type == 'multiple_choice':
                    question.options.all().delete()
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
        # --- LOGIC MENAMPILKAN DATA (SAMA SEPERTI SEBELUMNYA) ---
        quiz = get_object_or_404(CourseQuiz, id=quiz_id)
        attempts = StudentQuizAttempt.objects.filter(
            quiz=quiz, 
            finished_at__isnull=False
        ).select_related('participant', 'participant__mahasiswa').order_by('-total_score')

        return self.render_to_response(self.get_context_data(
            quiz=quiz,
            course=quiz.course,
            attempts=attempts
        ))

    def post(self, request, quiz_id, *args, **kwargs):
        # --- LOGIC RESET / HAPUS ATTEMPT ---
        attempt_id = request.POST.get('attempt_id') # Ambil ID dari input hidden di HTML
        
        if attempt_id:
            attempt = get_object_or_404(StudentQuizAttempt, id=attempt_id)
            nama_mhs = attempt.participant.mahasiswa.nim.first_name
            
            # Hapus data
            attempt.delete()
            
            messages.success(request, f"Ujian {nama_mhs} berhasil di-reset. Mahasiswa bisa mengerjakan ulang.")
        
        # Refresh halaman yang sama
        return redirect('quiz-submissions', quiz_id=quiz_id)


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
        
        with transaction.atomic():
            for key, value in request.POST.items():
                if key.startswith('score_'):
                    ans_id = key.split('_')[1]
                    try:
                        score_val = float(value)
                        answer_obj = StudentQuizAnswer.objects.get(id=ans_id)
                        if score_val > answer_obj.question.score_weight:
                            messages.warning(request, f"Nilai untuk soal no {answer_obj.question.order} melebihi bobot maksimal ({answer_obj.question.score_weight}). Diset ke maksimal.")
                            score_val = answer_obj.question.score_weight
                            
                        answer_obj.score_obtained = score_val
                        answer_obj.save()
                        
                    except (ValueError, StudentQuizAnswer.DoesNotExist):
                        continue
            new_total = attempt.answers.aggregate(total=Sum('score_obtained'))['total'] or 0
            attempt.total_score = new_total
            attempt.is_graded = True
            attempt.save()

        messages.success(request, f"Nilai berhasil disimpan. Total Skor Baru: {attempt.total_score}")
        return redirect('quiz-submissions', quiz_id=attempt.quiz.id)
    

class CourseGroupListView(DosenRequiredMixin, AcademyView):
    template_name = "groups/group_list.html"

    def get(self, request, course_uuid, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)
        groups = CourseGroup.objects.filter(course=course).prefetch_related('members__participant__mahasiswa')
        assigned_ids = CourseGroupMember.objects.filter(group__course=course).values_list('participant_id', flat=True)
        unassigned_participants = CourseParticipant.objects.filter(course=course).exclude(id__in=assigned_ids)

        return self.render_to_response(self.get_context_data(
            course=course,
            groups=groups,
            unassigned_participants=unassigned_participants
        ))

    def post(self, request, course_uuid, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)

        if 'create_group' in request.POST:
            name = request.POST.get('group_name')
            if name:
                with transaction.atomic():
                    new_group = CourseGroup.objects.create(course=course, name=name)
                    ChatRoom.objects.create(
                        name=f"Grup: {new_group.name}",
                        room_type='group',
                        group=new_group 
                    )
                messages.success(request, f"Kelompok '{name}' dan Ruang Chat berhasil dibuat.")
            else:
                messages.error(request, "Nama kelompok tidak boleh kosong.")
        
        elif 'auto_generate' in request.POST:
            try:
                total_groups = int(request.POST.get('total_groups', 5))
                
                if request.POST.get('clear_existing'):
                    CourseGroup.objects.filter(course=course).delete()

                # Ambil semua peserta aktif
                participants = list(CourseParticipant.objects.filter(course=course))
                
                if not participants:
                    messages.error(request, "Tidak ada peserta untuk dibagi.")
                    return redirect('course-groups', course_uuid=course.uuid)

                random.shuffle(participants) # Acak urutan
                
                with transaction.atomic():
                    created_groups = []
                    group_chat_map = {} 

                    for i in range(total_groups):
                        g = CourseGroup.objects.create(course=course, name=f"Kelompok {i+1}")
                        created_groups.append(g)

                        chat_room = ChatRoom.objects.create(
                            name=f"Grup: {g.name}",
                            room_type='group',
                            group=g
                        )
                        group_chat_map[g.id] = chat_room 
                    
                    for index, p in enumerate(participants):
                        target_group = created_groups[index % total_groups] 
                        
                        CourseGroupMember.objects.create(group=target_group, participant=p)
                        
                        current_room = group_chat_map[target_group.id]
                        
                        current_room.participants.add(p.mahasiswa.nim)
            
                messages.success(request, f"Berhasil membagi peserta ke dalam {total_groups} kelompok & membuat ruang chat.")

            except ValueError:
                messages.error(request, "Input jumlah kelompok tidak valid.")

        return redirect('course-groups', course_uuid=course.uuid)

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
                    CourseGroupMember.objects.create(group=group, participant=participant, role=role)
                    try:
                        chat_room = ChatRoom.objects.get(group=group)
                        chat_room.participants.add(participant.mahasiswa.nim)
                    except ChatRoom.DoesNotExist:
                        pass 

                messages.success(request, "Anggota berhasil ditambahkan.")

        elif 'remove_member' in request.POST:
            member_id = request.POST.get('member_id')
            member_obj = get_object_or_404(CourseGroupMember, id=member_id, group=group)
            user_to_remove = member_obj.participant.mahasiswa.nim 

            with transaction.atomic():
                member_obj.delete()
                try:
                    chat_room = ChatRoom.objects.get(group=group)
                    chat_room.participants.remove(user_to_remove)
                except ChatRoom.DoesNotExist:
                    pass

            messages.success(request, "Anggota dihapus dari kelompok.")
        
        elif 'edit_group' in request.POST:
            new_name = request.POST.get('group_name')
            group.name = new_name
            group.save()
            ChatRoom.objects.filter(group=group).update(name=f"Grup: {new_name}")
            messages.success(request, "Nama kelompok diperbarui.")
        elif 'delete_group' in request.POST:
            course_uuid = group.course.uuid 
            group.delete() 
            messages.success(request, "Kelompok berhasil dihapus.")
            return redirect('course-groups', course_uuid=course_uuid)

        return redirect('group-detail', group_id=group.id)
    
        
class CoursePreviewPublicView(AcademyView):
    template_name = "public_course_player.html" 

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        course_uuid = kwargs.get('course_uuid')
        material_id = kwargs.get('material_id')
        assignment_id = kwargs.get('assignment_id')
        course = get_object_or_404(Course, uuid=course_uuid)
        
        if not course.is_active:
            from django.http import Http404
            raise Http404("Course ini tidak aktif.")

        sections = CourseAgenda.objects.filter(course=course, is_active=True).prefetch_related('materials', 'assignments')

        active_item = None
        active_type = None

        if material_id:
            active_item = get_object_or_404(CourseMaterial, id=material_id, agenda__course=course)
            active_type = 'material'
        elif assignment_id:
            active_item = get_object_or_404(CourseAssignment, id=assignment_id, agenda__course=course)
            active_type = 'assignment'
        else:
            active_item = None
            active_type = None

        announcements = CourseAnnouncement.objects.filter(course=course).order_by('-is_pinned', '-created_at')
        quizzes = CourseQuiz.objects.filter(course=course, is_published=True).order_by('start_time')


        context = self.get_context_data(
            course=course,
            sections=sections,
            active_item=active_item,
            active_type=active_type,
            announcements=announcements,
            quizzes=quizzes,
            

            submission=None,
            completed_material_ids=[], 
            completed_assignment_ids=[],
            attendance_report=[],
            total_hadir=0,
            my_group=None,
            group_members=[],
            is_overdue=False,
            is_public_preview=True
        )

        return self.render_to_response(context)


class ChangeRoleView(AcademyView):
    template_name = "changerole.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        is_su = request.user.is_superuser or request.session.get('su') == '557799' or bool(request.session.get('impersonate_admin_id'))
        if not is_su:
            messages.error(request, 'Hanya Admin Superuser yang memiliki akses ke halaman Change Role.')
            return redirect('app-academy-dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dosen_list = UserDosen.objects.select_related('nip', 'prodi').all().order_by('nip__first_name')
        mhs_list = UserMhs.objects.select_related('nim', 'prodi').all().order_by('nim__first_name')
        prodi_list = UserProdi.objects.select_related('username', 'prodi').all().order_by('username__first_name')

        context.update({
            'title': 'Change Role',
            'form': ChangeRoleForm(),
            'dosen_list': dosen_list,
            'mhs_list': mhs_list,
            'prodi_list': prodi_list,
            'total_dosen': dosen_list.count(),
            'total_mhs': mhs_list.count(),
            'total_prodi': prodi_list.count(),
            'is_impersonating': bool(self.request.session.get('impersonate_admin_id')),
            'original_admin_name': self.request.session.get('original_admin_name'),
            'impersonated_target_role': self.request.session.get('impersonated_target_role'),
            'web_name': 'TaskApp Academy',
        })
        return context

    def post(self, request, *args, **kwargs):
        user_target_username = request.POST.get('user_target', '').strip()
        if not user_target_username:
            messages.error(request, 'Silakan pilih user tujuan.')
            return redirect('change-role')

        try:
            target_user = User.objects.get(username=user_target_username)
        except User.DoesNotExist:
            messages.error(request, 'User target tidak ditemukan.')
            return redirect('change-role')

        original_admin_id = request.session.get('impersonate_admin_id')
        original_admin_name = request.session.get('original_admin_name')
        if not original_admin_id:
            original_admin_id = request.user.id
            original_admin_name = request.user.first_name or request.user.username

        role_label = 'User'
        if hasattr(target_user, 'userdosen'):
            role_label = 'Dosen'
        elif hasattr(target_user, 'usermhs'):
            role_label = 'Mahasiswa'
        elif hasattr(target_user, 'userprodi'):
            role_label = 'Admin Prodi'
        elif target_user.is_superuser:
            role_label = 'Superuser'

        login(request, target_user, backend='django.contrib.auth.backends.ModelBackend')

        request.session['impersonate_admin_id'] = original_admin_id
        request.session['original_admin_name'] = original_admin_name
        request.session['impersonated_target_role'] = role_label
        request.session['su'] = '557799'

        target_display_name = target_user.first_name or target_user.username
        messages.success(request, f'Berhasil beralih role ke {role_label}: {target_display_name} ({target_user.username})')
        return redirect('app-academy-dashboard')


class RevertRoleView(View):
    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        original_admin_id = request.session.get('impersonate_admin_id')
        if not original_admin_id:
            messages.warning(request, 'Anda saat ini tidak sedang dalam mode impersonasi.')
            return redirect('app-academy-dashboard')

        try:
            admin_user = User.objects.get(id=original_admin_id)
            login(request, admin_user, backend='django.contrib.auth.backends.ModelBackend')
            request.session['su'] = '557799'
            request.session.pop('impersonate_admin_id', None)
            request.session.pop('original_admin_name', None)
            request.session.pop('impersonated_target_role', None)
            admin_display_name = admin_user.first_name or admin_user.username
            messages.success(request, f'Selamat datang kembali, Superuser: {admin_display_name}')
        except User.DoesNotExist:
            messages.error(request, 'Akun Superuser asli tidak ditemukan.')

        return redirect('change-role')