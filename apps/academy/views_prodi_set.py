from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Avg
from django.views.generic import TemplateView
from django.urls import reverse
from .decorators_prodi import ProdiOrAdminMixin


from web_project import TemplateLayout

from .models import (
    UserMhs, UserProdi, UserDosen, Prodi,
    Course, CourseAgenda, CourseMaterial, CourseAssignment, CoursePeriod,
    StudentAssignmentSubmission, CourseParticipant, CourseQuiz, CourseDiscussion,
    CourseAnnouncement,
)
from django.contrib.auth.models import User
from .forms_prodi import formProfile




########### SET PROFILE #####################################################

@login_required
def profile_prodi(request):
    userprodi = UserProdi.objects.get(username=request.user)
    if request.method == 'POST':
        form = formProfile(request.POST, request.FILES, instance=userprodi)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil Anda berhasil diperbarui!')
            return redirect('/acd/profile_prodi')
    else:
        form = formProfile(instance=userprodi)

    context = {
        'title':     'Profile',
        'heading':   'Edit Profile',
        'userprodi': userprodi,
        'photo':     userprodi.photo,
        'form':      form,
    }
    return render(request, 'prodi/set/profile.html', context)


########### DAFTAR PENGGUNA #################################################

class UserListView(ProdiOrAdminMixin, TemplateView):
    template_name = "app_user_list.html"

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))

        role   = self.request.GET.get("role", "Mahasiswa")
        search = self.request.GET.get("q", "").strip()
        prodi  = self.request.GET.get("prodi", "")
        status = self.request.GET.get("status", "")

        if role == "Dosen":
            qs = UserDosen.objects.select_related("nip", "prodi").order_by("nip__first_name")
            if search:
                qs = qs.filter(
                    Q(nip__first_name__icontains=search) |
                    Q(nip__last_name__icontains=search)  |
                    Q(nip__username__icontains=search)
                )
            if prodi:
                qs = qs.filter(prodi__id=prodi)
            if status == "aktif":
                qs = qs.filter(nip__is_active=True)
            elif status == "nonaktif":
                qs = qs.filter(nip__is_active=False)
            total       = UserDosen.objects.count()
            total_aktif = UserDosen.objects.filter(nip__is_active=True).count()
        else:
            role = "Mahasiswa"
            qs = UserMhs.objects.select_related("nim", "prodi").order_by("nim__first_name")
            if search:
                qs = qs.filter(
                    Q(nim__first_name__icontains=search) |
                    Q(nim__last_name__icontains=search)  |
                    Q(nim__username__icontains=search)
                )
            if prodi:
                qs = qs.filter(prodi__id=prodi)
            if status == "aktif":
                qs = qs.filter(nim__is_active=True)
            elif status == "nonaktif":
                qs = qs.filter(nim__is_active=False)
            total       = UserMhs.objects.count()
            total_aktif = UserMhs.objects.filter(nim__is_active=True).count()

        context.update({
            "title":       "Daftar Pengguna",
            "role":        role,
            "users":       qs,
            "prodis":      Prodi.objects.filter(status='Aktif').order_by('nama_prodi'),
            "total":       total,
            "total_aktif": total_aktif,
            "search":      search,
            "sel_prodi":   prodi,
            "sel_status":  status,
            "count_mhs":   UserMhs.objects.count(),
            "count_dosen": UserDosen.objects.count(),
        })
        return context


########### RESET PASSWORD ###################################################

@login_required
def reset_password(request, id):
    """Reset password user ke nilai baru yang dikirim via POST (modal konfirmasi)."""
    if not (request.user.is_staff or request.user.is_superuser or
            UserProdi.objects.filter(username=request.user).exists()):
        messages.error(request, 'Akses ditolak.')
        return redirect('app-academy-dashboard')

    target_user = get_object_or_404(User, username=id)

    if request.method == 'POST':
        new_password     = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()

        if not new_password:
            messages.error(request, 'Password baru tidak boleh kosong.')
        elif new_password != confirm_password:
            messages.error(request, 'Konfirmasi password tidak cocok.')
        elif len(new_password) < 6:
            messages.error(request, 'Password minimal 6 karakter.')
        else:
            target_user.set_password(new_password)
            target_user.save()
            messages.success(request, f'Password {target_user.get_full_name() or target_user.username} berhasil direset.')

    role = 'Mahasiswa'
    if hasattr(target_user, 'userdosen'):
        role = 'Dosen'
    return redirect(reverse('app-user-lists') + f'?role={role}')


########### LECTURER PERFORMANCE SCORE (LPS) #################################

def _calc_lps(dosen, period_id=None):
    courses_qs = dosen.coached_courses.all()
    if period_id:
        courses_qs = courses_qs.filter(period_id=period_id)

    agendas = CourseAgenda.objects.filter(course__in=courses_qs)
    total_agendas = agendas.count()

    if total_agendas > 0:
        filled_outcome = agendas.exclude(learning_outcome__isnull=True).exclude(learning_outcome='').count()
        filled_method  = agendas.exclude(teaching_method__isnull=True).exclude(teaching_method='').count()
        filled_loc     = agendas.filter(
            Q(location__gt='') | Q(is_online=True)
        ).count()
        lp_score = round(
            ((filled_outcome / total_agendas) * 10 +
             (filled_method  / total_agendas) * 10 +
             (filled_loc     / total_agendas) * 10), 1
        )
    else:
        lp_score = 0.0

    if total_agendas > 0:
        agendas_with_material = agendas.filter(materials__isnull=False).distinct().count()
        agendas_with_media    = agendas.filter(media_items__isnull=False).distinct().count()
        proc_score = round(
            ((agendas_with_material / total_agendas) * 30 +
             (agendas_with_media    / total_agendas) * 10), 1
        )
    else:
        proc_score = 0.0

    assignments = CourseAssignment.objects.filter(agenda__course__in=courses_qs)
    total_assignments = assignments.count()
    if total_agendas > 0:
        agendas_with_assignment = agendas.filter(assignments__isnull=False).distinct().count()
        task_score = round((agendas_with_assignment / total_agendas) * 15, 1)
    else:
        task_score = 0.0

    if total_assignments > 0:
        graded_count = StudentAssignmentSubmission.objects.filter(
            assignment__in=assignments, score__isnull=False
        ).count()
        total_subs   = StudentAssignmentSubmission.objects.filter(
            assignment__in=assignments
        ).count()
        grade_score  = round((graded_count / total_subs) * 15, 1) if total_subs > 0 else 0.0
    else:
        grade_score = 0.0

    assess_score = round(task_score + grade_score, 1)
    total_score  = round(lp_score + proc_score + assess_score, 1)

    return {
        'lesson_planning':    lp_score,
        'learning_process':   proc_score,
        'learning_assessment': assess_score,
        'total':              total_score,
        'jumlah_kelas':       courses_qs.count(),
    }


class LecturerPerformanceView(ProdiOrAdminMixin, TemplateView):
    template_name = "prodi/lps_report.html"

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        search    = self.request.GET.get("q", "").strip()
        prodi_id  = self.request.GET.get("prodi", "")
        period_id = self.request.GET.get("period", "")
        active_period = CoursePeriod.objects.filter(is_active=True).first()
        if not period_id and active_period:
            period_id = str(active_period.id)

        dosen_qs = UserDosen.objects.select_related("nip", "prodi").filter(
            nip__is_active=True
        ).order_by("nip__first_name")

        if search:
            dosen_qs = dosen_qs.filter(
                Q(nip__first_name__icontains=search) |
                Q(nip__last_name__icontains=search)  |
                Q(nidn__icontains=search)             |
                Q(nip__username__icontains=search)
            )
        if prodi_id:
            dosen_qs = dosen_qs.filter(prodi__id=prodi_id)

        lps_data = []
        for dosen in dosen_qs:
            scores = _calc_lps(dosen, period_id or None)
            lps_data.append({
                'dosen':  dosen,
                'scores': scores,
            })

        lps_data.sort(key=lambda x: x['scores']['total'], reverse=True)

        context.update({
            "title":         "Lecturer Performance Score",
            "lps_data":      lps_data,
            "prodis":        Prodi.objects.filter(status='Aktif').order_by('nama_prodi'),
            "periods":       CoursePeriod.objects.order_by('-start_date'),
            "sel_prodi":     prodi_id,
            "sel_period":    period_id,
            "active_period": active_period,
            "search":        search,
        })
        return context


def _calc_lps_per_course(dosen, course, period_id=None):
    """Hitung skor LPS breakdown per satu mata kuliah."""
    from .models import CourseParticipant, CourseAttendance

    agendas      = CourseAgenda.objects.filter(course=course)
    total_agendas = agendas.count()
    jumlah_peserta = CourseParticipant.objects.filter(
        course=course, mahasiswa__isnull=False
    ).count()

    # ── Lesson Planning (30%): materi diunggah ──
    if total_agendas > 0:
        agendas_with_material = agendas.filter(materials__isnull=False).distinct().count()
        lp = round((agendas_with_material / total_agendas) * 30, 1)
    else:
        lp = 0.0

    # ── Learning Process – Aktif Berdiskusi (20%) ──
    if total_agendas > 0:
        agendas_discussion = agendas.filter(allow_discussion=True).count()
        lp_diskusi = round((agendas_discussion / total_agendas) * 20, 1)
    else:
        lp_diskusi = 0.0

    # ── Learning Process – Feedback/Nilai Tugas (10%) ──
    assignments = CourseAssignment.objects.filter(agenda__course=course)
    total_subs  = StudentAssignmentSubmission.objects.filter(assignment__in=assignments).count()
    graded_subs = StudentAssignmentSubmission.objects.filter(
        assignment__in=assignments, score__isnull=False
    ).count()
    lp_feedback = round((graded_subs / total_subs) * 10, 1) if total_subs > 0 else 0.0

    # ── Learning Process – Kehadiran (10%) ──
    from .models import CourseAttendance
    total_att = CourseAttendance.objects.filter(agenda__course=course).count()
    if total_agendas > 0 and jumlah_peserta > 0:
        max_att = total_agendas * jumlah_peserta
        lp_kehadiran = round((total_att / max_att) * 10, 1) if max_att > 0 else 0.0
    else:
        lp_kehadiran = 0.0

    proc_score = round(lp_diskusi + lp_feedback + lp_kehadiran, 1)

    # ── Learning Assessment – Tugas/Kuis/Ujian (30%) ──
    if total_agendas > 0:
        agendas_with_task = agendas.filter(assignments__isnull=False).distinct().count()
        assess = round((agendas_with_task / total_agendas) * 30, 1)
    else:
        assess = 0.0

    total = round(lp + proc_score + assess, 1)

    return {
        'course':           course,
        'jumlah_peserta':   jumlah_peserta,
        'lesson_planning':  lp,          # 0–30
        'lp_diskusi':       lp_diskusi,  # 0–20
        'lp_feedback':      lp_feedback, # 0–10
        'lp_kehadiran':     lp_kehadiran,# 0–10
        'learning_process': proc_score,  # 0–40
        'learning_assessment': assess,   # 0–30
        'total':            total,
    }


class LecturerPerformanceDetailView(ProdiOrAdminMixin, TemplateView):
    template_name = "prodi/lps_detail.html"

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))

        nip      = self.kwargs['nip']
        period_id = self.request.GET.get("period", "")

        active_period = CoursePeriod.objects.filter(is_active=True).first()
        if not period_id and active_period:
            period_id = str(active_period.id)

        dosen = get_object_or_404(UserDosen, nip__username=nip)

        # Kumpulkan kelas yang diajar
        courses_qs = dosen.coached_courses.select_related('period', 'prodi')
        if period_id:
            courses_qs = courses_qs.filter(period_id=period_id)
        courses_qs = courses_qs.order_by('name')

        # Skor keseluruhan
        overall = _calc_lps(dosen, period_id or None)

        # Breakdown per kelas
        courses_detail = []
        for course in courses_qs:
            row = _calc_lps_per_course(dosen, course, period_id)
            courses_detail.append(row)

        # Search kelas
        search_course = self.request.GET.get("q", "").strip()
        if search_course:
            courses_detail = [
                r for r in courses_detail
                if search_course.lower() in r['course'].name.lower() or
                   search_course.lower() in r['course'].code.lower()
            ]

        context.update({
            "title":          f"LPS – {dosen.nip.first_name}",
            "dosen":          dosen,
            "overall":        overall,
            "courses_detail": courses_detail,
            "periods":        CoursePeriod.objects.order_by('-start_date'),
            "sel_period":     period_id,
            "active_period":  active_period,
            "search_course":  search_course,
        })
        return context


########### LAPORAN KELAS ###################################################

class ClassReportView(ProdiOrAdminMixin, TemplateView):
    """Laporan aktivitas per kelas: Materi, Tugas, Quiz, Diskusi, Pengumuman, Peserta."""
    template_name = "prodi/class_report.html"

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))

        search    = self.request.GET.get("q", "").strip()
        prodi_id  = self.request.GET.get("prodi", "")
        period_id = self.request.GET.get("period", "")

        active_period = CoursePeriod.objects.filter(is_active=True).first()
        if not period_id and active_period:
            period_id = str(active_period.id)

        courses_qs = Course.objects.select_related('period', 'prodi').prefetch_related('coaches').order_by('prodi__nama_prodi', 'name')

        if period_id:
            courses_qs = courses_qs.filter(period_id=period_id)
        if prodi_id:
            courses_qs = courses_qs.filter(prodi__id=prodi_id)
        if search:
            courses_qs = courses_qs.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search) |
                Q(coaches__nip__first_name__icontains=search) |
                Q(coaches__nip__last_name__icontains=search)
            ).distinct()

        class_data = []
        total_materials    = 0
        total_assignments  = 0
        total_quizzes      = 0
        total_discussions  = 0
        total_participants = 0

        for course in courses_qs:
            agendas           = CourseAgenda.objects.filter(course=course)
            total_agendas     = agendas.count()  # biasanya 16

            jumlah_materi     = CourseMaterial.objects.filter(agenda__course=course).count()
            jumlah_tugas      = CourseAssignment.objects.filter(agenda__course=course).count()
            jumlah_quiz       = CourseQuiz.objects.filter(course=course).count()
            jumlah_diskusi    = CourseDiscussion.objects.filter(course=course).count()
            jumlah_pengumuman = CourseAnnouncement.objects.filter(course=course).count()
            jumlah_peserta    = CourseParticipant.objects.filter(course=course, is_active=True).count()

            # Sesi yang sudah punya konten (materi ATAU tugas)
            sesi_terisi = agendas.filter(
                Q(materials__isnull=False) | Q(assignments__isnull=False)
            ).distinct().count()
            persen_sesi_terisi = round((sesi_terisi / total_agendas) * 100) if total_agendas > 0 else 0

            total_materials    += jumlah_materi
            total_assignments  += jumlah_tugas
            total_quizzes      += jumlah_quiz
            total_discussions  += jumlah_diskusi
            total_participants += jumlah_peserta

            class_data.append({
                'course':              course,
                'jumlah_materi':       jumlah_materi,
                'jumlah_tugas':        jumlah_tugas,
                'jumlah_quiz':         jumlah_quiz,
                'jumlah_diskusi':      jumlah_diskusi,
                'jumlah_pengumuman':   jumlah_pengumuman,
                'jumlah_peserta':      jumlah_peserta,
                'sesi_terisi':         sesi_terisi,
                'total_agendas':       total_agendas,
                'persen_sesi_terisi':  persen_sesi_terisi,
            })

        context.update({
            "title":      "Laporan Kelas",
            "class_data": class_data,
            "prodis":     Prodi.objects.filter(status='Aktif').order_by('nama_prodi'),
            "periods":    CoursePeriod.objects.order_by('-start_date'),
            "sel_prodi":  prodi_id,
            "sel_period": period_id,
            "active_period": active_period,
            "search":     search,
            "summary": {
                "total_courses":      courses_qs.count(),
                "total_materials":    total_materials,
                "total_assignments":  total_assignments,
                "total_quizzes":      total_quizzes,
                "total_discussions":  total_discussions,
                "total_participants": total_participants,
            },
        })
        return context
