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
    
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

class CourseRecapitulationView(DosenRequiredMixin, AcademyView):
    template_name = "course_rekapitulasi.html" 

    def get(self, request, course_uuid, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)
    
        # 1. Ambil Data Dasar
        participants = CourseParticipant.objects.filter(course=course).select_related('mahasiswa').order_by('mahasiswa__nim')
        agendas = CourseAgenda.objects.filter(course=course).order_by('agenda_date')
        assignments = CourseAssignment.objects.filter(agenda__course=course).order_by('due_date')
        
        total_agendas = agendas.count()

        # 2. Optimasi Query Absensi
        all_attendances = CourseAttendance.objects.filter(agenda__course=course)
        attendance_map = {(att.participant_id, att.agenda_id): att.status for att in all_attendances}

        rekap_data = [] 

        for p in participants:
            # --- A. DETAIL ABSENSI ---
            student_agenda_statuses = []
            hadir_count = 0
            
            for ag in agendas:
                status = attendance_map.get((p.id, ag.id), '-') 
                student_agenda_statuses.append({'agenda_id': ag.id, 'status': status})
                if status in ['present', 'late']:
                    hadir_count += 1
            
            attendance_pct = 0
            if total_agendas > 0:
                attendance_pct = round((hadir_count / total_agendas) * 100, 1)

            # --- B. DETAIL NILAI TUGAS (UPDATED) ---
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
                    # Ambil Link
                    sub_link = sub.submitted_link if sub.submitted_link else "-"
                    
                    # Ambil Waktu & Format jadi String (Tgl/Bln Jam:Menit)
                    if sub.submitted_at:
                        # Convert ke local time dulu jika perlu, lalu format str
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
                    'link': sub_link,  # Data Baru
                    'time': sub_time   # Data Baru
                })
                total_score_collected += score
            
            avg_score = 0
            if assignments.count() > 0:
                avg_score = round(total_score_collected / assignments.count(), 1)

            rekap_data.append({
                'participant': p,
                'agenda_statuses': student_agenda_statuses,
                'attendance_pct': attendance_pct,
                'hadir_count': hadir_count,
                'grades': student_grades,
                'final_avg': avg_score
            })

        # Cek Export Excel
        if request.GET.get('export') == 'excel':
            return self.export_to_excel(course, agendas, assignments, rekap_data)

        return self.render_to_response(self.get_context_data(
            course=course,
            agendas=agendas,
            assignments=assignments,
            rekap_data=rekap_data, 
            total_agendas=total_agendas
        ))

    def export_to_excel(self, course, agendas, assignments, data):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Rekapitulasi Kelas"

        # --- STYLING ---
        bold_font = Font(bold=True)
        center_align = Alignment(horizontal='center', vertical='center')
        border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
        header_fill = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")

        # --- HEADER ROW 1 ---
        headers = ["No", "NIM", "Nama Mahasiswa"] 
        
        # Header Absensi
        for i, ag in enumerate(agendas):
            headers.append(f"P-{i+1}")
        headers.extend(["Total Hadir", "% Absen"])

        # Header Tugas (DIPERLUAS: Link, Waktu, Nilai)
        for i, task in enumerate(assignments):
            prefix = f"Tgs-{i+1}"
            headers.append(f"{prefix} Link")
            headers.append(f"{prefix} Waktu")
            headers.append(f"{prefix} Nilai")
        
        headers.append("Rata-rata Nilai")

        ws.append(headers)

        # Apply Style ke Header
        for cell in ws[1]:
            cell.font = bold_font
            cell.alignment = center_align
            cell.fill = header_fill
            cell.border = border

        # --- DATA ROWS ---
        for idx, item in enumerate(data):
            # Ambil Data Mahasiswa (Safe String)
            mhs = item['participant'].mahasiswa
            nim_str = "-"
            nama_str = "Tanpa Nama"

            if mhs and mhs.nim:
                user_obj = mhs.nim 
                nim_str = str(user_obj.username) 
                nama_str = f"{user_obj.first_name} {user_obj.last_name}".strip()

            row = [
                idx + 1,
                nim_str,
                nama_str,
            ]

            # Loop Status Absensi
            for stat in item['agenda_statuses']:
                code_map = {'present': 'H', 'late': 'T', 'absent': 'A', 'sick': 'S', 'excused': 'I', '-': '-'}
                row.append(code_map.get(stat['status'], '-'))

            # Ringkasan Absen
            row.append(item['hadir_count'])
            row.append(f"{item['attendance_pct']}%")

            # Loop Nilai Tugas (DIPERLUAS 3 Kolom per Tugas)
            for grade in item['grades']:
                # 1. Link Submission
                row.append(grade['link'])
                
                # 2. Waktu Submission
                row.append(grade['time'])
                
                # 3. Nilai (Score)
                val = grade['score'] if grade['score'] is not None else 0 
                row.append(val)

            # Rata-rata Akhir
            row.append(item['final_avg'])

            ws.append(row)

        # Auto Adjust Column Width
        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    val_len = len(str(cell.value))
                    if val_len > max_length:
                        max_length = val_len
                except:
                    pass
            
            # Batasi lebar maksimal kolom Link agar tidak terlalu lebar
            # Jika header mengandung 'Link', max width 30, sisanya auto
            if "Link" in str(col[0].value):
                final_width = min(max_length + 2, 30) 
            else:
                final_width = (max_length + 2)
            
            ws.column_dimensions[column].width = final_width

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename=Rekap_Lengkap_{course.code}.xlsx'
        wb.save(response)
        return response