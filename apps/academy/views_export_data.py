import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView
from web_project import TemplateLayout
from .forms import CourseForm, AddParticipantForm, AddAgendaForm, AddAnnouncementForm, AttendanceForm, CourseMaterialForm, AddProgramStudiCourseForm, CoursePeriodForm, CourseAssignmentForm
from django.contrib import messages
from .models import Course, CourseParticipant, CourseAgenda, CourseAnnouncement, CourseAttendance, CourseMaterial, StudentMaterialProgress, Prodi, CoursePeriod, StudentAssignmentSubmission, CourseAssignment, CourseQuiz, StudentQuizAttempt
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

import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.urls import reverse # Wajib import ini untuk Link

class CourseRecapitulationView(DosenRequiredMixin, AcademyView):
    template_name = "course_rekapitulasi.html" 

    def get(self, request, course_uuid, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)
    
        # 1. Ambil Data Dasar
        participants = CourseParticipant.objects.filter(course=course).select_related('mahasiswa', 'mahasiswa__prodi').order_by('mahasiswa__nim')
        agendas = CourseAgenda.objects.filter(course=course).order_by('agenda_date')
        assignments = CourseAssignment.objects.filter(agenda__course=course).order_by('due_date')
        quizzes = CourseQuiz.objects.filter(course=course).order_by('created_at') 
        total_agendas = agendas.count()
        
        # --- KONFIGURASI BOBOT POIN ABSENSI ---
        POINTS_MAP = {
            'present': 100,
            'late': 75,
            'sick': 60,
            'excused': 50,
            'absent': 0,
            '-': 0
        }

        # 2. Optimasi Query Absensi
        all_attendances = CourseAttendance.objects.filter(agenda__course=course)
        attendance_map = {(att.participant_id, att.agenda_id): att.status for att in all_attendances}

        rekap_data = [] 

        for p in participants:
            # --- A. DETAIL ABSENSI & HITUNG SKOR ---
            student_agenda_statuses = []
            current_total_points = 0 
            
            for ag in agendas:
                status = attendance_map.get((p.id, ag.id), '-') 
                student_agenda_statuses.append({'agenda_id': ag.id, 'status': status})
                current_total_points += POINTS_MAP.get(status, 0)
            
            # Hitung Skor Akhir Absensi (Skala 0-100)
            attendance_score = 0
            if total_agendas > 0:
                max_possible_points = total_agendas * 100
                attendance_score = round((current_total_points / max_possible_points) * 100, 1)

            # --- B. DETAIL NILAI TUGAS ---
            student_grades = []
            total_score_collected = 0
            
            for task in assignments:
                sub = StudentAssignmentSubmission.objects.filter(
                    assignment=task, 
                    student=p.mahasiswa
                ).first()
                
                score = 0
                status = 'missing'
                sub_link = "-"
                sub_time = "-"
                
                if sub:
                    sub_link = sub.submitted_link if sub.submitted_link else "-"
                    if sub.submitted_at:
                        local_time = timezone.localtime(sub.submitted_at)
                        sub_time = local_time.strftime("%d/%m %H:%M")

                    if sub.score is not None:
                        score = sub.score
                        status = 'graded'
                    else:
                        status = 'submitted'
                
                student_grades.append({
                    'task_id': task.id,
                    'score': score,
                    'status': status,
                    'link': sub_link,
                    'time': sub_time
                })
                total_score_collected += score
            
            avg_score = 0
            if assignments.count() > 0:
                avg_score = round(total_score_collected / assignments.count(), 1)

            student_quiz_grades = []
            
            for quiz in quizzes:
                # Ambil attempt terbaik atau terakhir yang sudah selesai
                attempt = StudentQuizAttempt.objects.filter(
                    quiz=quiz, 
                    participant=p, 
                    finished_at__isnull=False
                ).order_by('-total_score').first() # Ambil nilai tertinggi jika ada multiple attempt
                
                quiz_data = {
                    'id': quiz.id,
                    'score': attempt.total_score if attempt else None,
                    'is_finished': True if attempt else False
                }
                student_quiz_grades.append(quiz_data)

            rekap_data.append({
                'participant': p,
                'agenda_statuses': student_agenda_statuses,
                'attendance_score': attendance_score, 
                'grades': student_grades,
                'final_avg': avg_score,
                'quiz_grades': student_quiz_grades,
            })

        # Cek Export Excel (Pass 'request' untuk generate full URL)
        if request.GET.get('export') == 'excel':
            return self.export_to_excel(request, course, agendas, assignments, quizzes, rekap_data)

        return self.render_to_response(self.get_context_data(
            course=course,
            agendas=agendas,
            assignments=assignments,
            quizzes=quizzes,
            rekap_data=rekap_data, 
            total_agendas=total_agendas
        ))
    def export_to_excel(self, request, course, agendas, assignments, quizzes, data):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Rekapitulasi Kelas"

        # --- STYLING ---
        bold_font = Font(bold=True)
        center_align = Alignment(horizontal='center', vertical='center')
        border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
        
        # Warna Header
        header_fill = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")
        quiz_fill = PatternFill(start_color="FFE0DB", end_color="FFE0DB", fill_type="solid")

        # Style Khusus Link (Biru + Underline)
        link_font = Font(color="0000FF", underline="single", bold=True)
        link_fill = PatternFill(start_color="E6F7FF", end_color="E6F7FF", fill_type="solid")

        # --- HEADER ROW 1 ---
        # [UPDATE] Menambahkan "Kelompok"
        headers = ["No", "Nama Mahasiswa", "NIM", "Prodi", "Kelas", "Kelompok", "Kode MK"] 
        
        # Hitung kolom awal agenda (otomatis menyesuaikan panjang headers)
        agenda_start_col = len(headers) + 1
        
        # Header Absensi
        for i, ag in enumerate(agendas):
            headers.append(f"P-{i+1}")
        
        headers.extend(["Skor Absen"])

        # Header Tugas
        for i, task in enumerate(assignments):
            prefix = f"Tgs-{i+1}"
            headers.append(f"{prefix} Link")
            headers.append(f"{prefix} Waktu")
            headers.append(f"{prefix} Nilai")
        
        # [UPDATE] Hitung kolom awal Tugas (Berubah karena ada tambahan kolom Kelompok)
        # Rumus: 7 (Identitas + Kelompok) + Agendas + 1 (Skor Absen) + 1 (Start Excel Index)
        assignment_start_col = 7 + len(agendas) + 1 + 1

        # Header Kuis
        quiz_start_col = len(headers) + len(agendas) + 1 + (len(assignments) * 3) + 1
        
        # ATAU gunakan logika dinamis append headers
        for i, quiz in enumerate(quizzes):
            # Ambil tipe quiz, default ke 'Quiz' jika kosong
            q_type = getattr(quiz, 'quiz_type', 'Quiz')
            label = str(q_type).upper() 
            
            headers.append(label)
        headers.append("Rata-rata Nilai")

        ws.append(headers)

        # --- APPLY STYLE HEADER ---
        for cell in ws[1]:
            cell.font = bold_font
            cell.alignment = center_align
            cell.border = border
            # Cek range kolom quiz untuk warna berbeda
            # Kita hitung ulang index kolom quiz start secara dinamis agar aman
            current_col_idx = cell.col_idx
            total_cols_before_quiz = 7 + len(agendas) + 1 + (len(assignments) * 3) 
            
            if total_cols_before_quiz < current_col_idx <= (total_cols_before_quiz + len(quizzes)):
                cell.fill = quiz_fill
            else:
                cell.fill = header_fill

        # --- HEADER AGENDA LINKS ---
        scheme = request.scheme
        host = request.get_host()
        base_url = f"{scheme}://{host}"

        for i, ag in enumerate(agendas):
            col_idx = agenda_start_col + i
            cell = ws.cell(row=1, column=col_idx)
            try:
                relative_path = reverse('public-agenda-material', kwargs={'course_uuid': course.uuid, 'agenda_id': ag.id})
                full_link = f"{base_url}{relative_path}"
                cell.hyperlink = full_link
                cell.font = link_font
                cell.fill = link_fill
                cell.value = f"P-{i+1}" 
            except:
                pass 

        # --- DATA ROWS ---
        for idx, item in enumerate(data):
            mhs = item['participant'].mahasiswa
            nim_str = "-"
            nama_str = "Tanpa Nama"
            prodi_str = "-"

            if mhs:
                if mhs.nim:
                    user_obj = mhs.nim 
                    nim_str = str(user_obj.username) 
                    nama_str = f"{user_obj.first_name} {user_obj.last_name}".strip()
                if mhs.prodi:
                    prodi_str = mhs.prodi.nama_prodi

            # [LOGIC BARU] Ambil Nama Kelompok
            group_name = "-"
            # Asumsi: participant punya related_name 'group_memberships'
            group_member = item['participant'].group_memberships.first()
            if group_member:
                group_name = group_member.group.name

            # [UPDATE] Masukkan group_name ke dalam list row
            row = [idx + 1, nama_str, nim_str, prodi_str, course.group, group_name, course.code]

            # Absensi
            for stat in item['agenda_statuses']:
                code_map = {'present': 'H', 'late': 'T', 'absent': 'A', 'sick': 'S', 'excused': 'I', '-': '-'}
                row.append(code_map.get(stat['status'], '-'))
            row.append(item['attendance_score'])

            # Tugas
            for grade in item['grades']:
                row.append(grade['link']) 
                row.append(grade['time'])
                val = grade['score'] if grade['score'] is not None else 0 
                row.append(val)
            
            # Kuis
            for q_grade in item['quiz_grades']:
                val = q_grade['score'] if q_grade['score'] is not None else 0
                row.append(val)

            # Rata-rata
            row.append(item['final_avg'])

            # Tulis baris ke Excel
            ws.append(row)
            
            # --- LOGIC HYPERLINK "Link" ---
            current_row = ws.max_row
            
            for k, grade in enumerate(item['grades']):
                url = grade['link']
                
                if url and url != "-" and str(url).startswith('http'):
                    # Hitung posisi kolom Excel:
                    # Start Kolom Tugas + (Indeks Tugas ke-k * 3 kolom per tugas)
                    col_idx = assignment_start_col + (k * 3)
                    
                    cell = ws.cell(row=current_row, column=col_idx)
                    cell.value = "Link"       
                    cell.hyperlink = url       
                    cell.font = link_font     
                    cell.alignment = center_align

        # Auto Adjust Column Width
        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            header_val = str(col[0].value)

            for cell in col:
                try:
                    val_len = len(str(cell.value))
                    if val_len > max_length:
                        max_length = val_len
                except:
                    pass
            
            if "Link" in header_val:
                final_width = 12 
            else:
                final_width = (max_length + 2)
            
            ws.column_dimensions[column].width = final_width

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename=Rekap_Lengkap_{course.code}.xlsx'
        wb.save(response)
        return response