from django.views.generic import TemplateView
from django.shortcuts import redirect, get_object_or_404, render
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from web_project import TemplateLayout
from .models import UserMhs, UserDosen, Course, CourseParticipant, CourseAgenda, CourseMaterial, CourseAssignment, CourseAnnouncement, StudentMaterialProgress, StudentAssignmentSubmission, CourseAttendance, CourseQuiz, StudentQuizAttempt, StudentQuizAnswer, QuizQuestion, QuizOption, CourseParticipant, CourseGroupMember
from .forms_mhs import MhsProfileForm  # Pastikan import form Anda
from django.contrib.auth.mixins import LoginRequiredMixin
from .decorators_students import StudentsRequiredMixin
from django.utils import timezone
from django.db.models import Sum

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
    template_name = "students/app_academy_course.html"
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

        # === 1. LOGIK ACTIVE ITEM (BAWAAN ANDA) ===
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

        # === 2. AMBIL DATA PENDUKUNG LAINNYA ===
        announcements = CourseAnnouncement.objects.filter(course=course).order_by('-is_pinned', '-created_at')
        
        # [BARU] Ambil Data Kuis
        quizzes = CourseQuiz.objects.filter(course=course, is_published=True).order_by('start_time')

        completed_material_ids = []
        completed_assignment_ids = []
        attendance_report = [] 
        total_hadir = 0
        user_attendance_map = {} 
        my_group = None
        group_members = []

        # === 3. CEK PROGRESS USER (JIKA LOGIN) ===
        if request.user.is_authenticated:
            mhs_profile = UserMhs.objects.filter(nim=request.user).first()
            if mhs_profile:
                participant = CourseParticipant.objects.filter(course=course, mahasiswa=mhs_profile).first()
                if participant:
                    # Cek Materi Selesai
                    completed_material_ids = StudentMaterialProgress.objects.filter(
                        participant=participant, is_completed=True
                    ).values_list('material_id', flat=True)

                    # Cek Tugas Selesai
                    completed_assignment_ids = StudentAssignmentSubmission.objects.filter(
                        student=mhs_profile, assignment__agenda__course=course
                    ).values_list('assignment_id', flat=True)

                    if active_type == 'assignment':
                        submission = StudentAssignmentSubmission.objects.filter(
                            student=mhs_profile, assignment=active_item
                        ).first()
                    
                    # Cek Absensi
                    records = CourseAttendance.objects.filter(participant=participant)
                    for rec in records:
                        user_attendance_map[rec.agenda.id] = rec
                        if rec.status == 'present':
                            total_hadir += 1
                    
                    my_group_rel = CourseGroupMember.objects.filter(
                        participant=participant
                    ).select_related('group').first()
                    

                    if my_group_rel:
                        my_group = my_group_rel.group
                        group_members = my_group.members.select_related('participant__mahasiswa__nim').order_by('role', 'participant__mahasiswa__nim__first_name')
                        
                    for quiz in quizzes:
                        # Cek apakah sudah ada attempt yang FINISHED (selesai)
                        is_done = StudentQuizAttempt.objects.filter(
                            quiz=quiz, 
                            participant=participant, 
                            finished_at__isnull=False
                        ).exists()
                        # Tempel atribut sementara ke object quiz
                        quiz.user_is_done = is_done

        # === 4. SUSUN LAPORAN ABSENSI ===
        for agenda in sections:
            att_record = user_attendance_map.get(agenda.id)
            attendance_report.append({
                'agenda_title': agenda.title,
                'agenda_type': agenda.agenda_type,
                'agenda_date': agenda.agenda_date,
                'status': att_record.status if att_record else 'none',
                'check_in_time': att_record.check_in_time if att_record else None
            })

        is_overdue = False
        if active_type == 'assignment':
             if timezone.now() > active_item.due_date:
                 is_overdue = True

        # === 5. KIRIM KE CONTEXT ===
        context = self.get_context_data(
            is_overdue=is_overdue,
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
            quizzes=quizzes,  # <--- JANGAN LUPA TAMBAHKAN INI
            my_group=my_group,          # Variabel ini sekarang aman karena sudah di-init di atas
            group_members=group_members
        )
        return self.render_to_response(context)

    def post(self, request, course_uuid, material_id=None, assignment_id=None, *args, **kwargs):
        course = get_object_or_404(Course, uuid=course_uuid)
        
        if not request.user.is_authenticated:
            return redirect('login')

        mhs_profile = get_object_or_404(UserMhs, nim=request.user)
        participant = get_object_or_404(CourseParticipant, course=course, mahasiswa=mhs_profile)

        if material_id:
            # ... (Material logic remains the same) ...
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

            # Consolidated Deadline Check
            is_overdue = timezone.now() > assignment.due_date
            if is_overdue and not assignment.allow_late_submission:
                messages.error(request, 'Batas waktu pengumpulan sudah berakhir.')
                return redirect('course-player-assignment', course_uuid=course.uuid, assignment_id=assignment.id)
            
            # Input Retrieval
            link_input = request.POST.get('submitted_link')
            text_input = request.POST.get('submitted_text')

            # Validation for Link Input
            if not link_input:
                messages.error(request, 'Link tugas tidak boleh kosong!')
                return redirect('course-player-assignment', course_uuid=course.uuid, assignment_id=assignment.id)

            # Update or Create Submission
            submission, created = StudentAssignmentSubmission.objects.update_or_create(
                student=mhs_profile,
                assignment=assignment,
                defaults={
                    'submitted_link': link_input,
                    'submitted_text': text_input,
                    'updated_at': timezone.now()
                }
            )
        
            messages.success(request, 'Tugas berhasil dikumpulkan!')
            return redirect('course-player-assignment', course_uuid=course.uuid, assignment_id=assignment.id)

        return redirect('course-player', course_uuid=course.uuid)



# --- VIEW: HALAMAN COVER / PERSIAPAN UJIAN ---
class StudentQuizStartView(StudentsRequiredMixin, AcademyView):
    template_name = "students/quiz_start.html"

    def get(self, request, quiz_id, *args, **kwargs):
        quiz = get_object_or_404(CourseQuiz, id=quiz_id)
        
        # 1. Identifikasi Mahasiswa & Peserta Course
        mhs_profile = get_object_or_404(UserMhs, nim=request.user)
        participant = get_object_or_404(CourseParticipant, course=quiz.course, mahasiswa=mhs_profile)
        
        # 2. Cek apakah ada ujian yang BELUM disubmit (Status Running)
        active_attempt = StudentQuizAttempt.objects.filter(
            quiz=quiz, 
            participant=participant, 
            finished_at__isnull=True
        ).first()

        # Jika ada yang aktif, paksa redirect ke halaman pengerjaan
        if active_attempt:
            return redirect('student-quiz-take', attempt_id=active_attempt.id)

        # 3. Hitung jumlah percobaan yang sudah selesai
        existing_attempts = StudentQuizAttempt.objects.filter(
            quiz=quiz, 
            participant=participant, 
            finished_at__isnull=False
        ).count()

        can_start = True
        if existing_attempts >= quiz.max_attempts:
            can_start = False
            messages.warning(request, "Anda sudah menghabiskan batas maksimal percobaan untuk ujian ini.")

        return self.render_to_response(self.get_context_data(
            quiz=quiz,
            participant=participant,
            existing_attempts=existing_attempts,
            can_start=can_start
        ))

    def post(self, request, quiz_id, *args, **kwargs):
        quiz = get_object_or_404(CourseQuiz, id=quiz_id)
        mhs_profile = get_object_or_404(UserMhs, nim=request.user)
        participant = get_object_or_404(CourseParticipant, course=quiz.course, mahasiswa=mhs_profile)

        # Cek limit lagi untuk keamanan
        count = StudentQuizAttempt.objects.filter(quiz=quiz, participant=participant).count()
        if count >= quiz.max_attempts:
            return redirect('student-quiz-start', quiz_id=quiz.id)

        # Create Attempt Baru
        attempt = StudentQuizAttempt.objects.create(
            quiz=quiz,
            participant=participant
        )
        return redirect('student-quiz-take', attempt_id=attempt.id)


# --- VIEW: HALAMAN MENGERJAKAN SOAL (TIMER & SOAL) ---
class StudentQuizTakeView(StudentsRequiredMixin, AcademyView):
    template_name = "students/quiz_take.html"

    def get(self, request, attempt_id, *args, **kwargs):
        # 1. Validasi Attempt milik user yang login
        attempt = get_object_or_404(
            StudentQuizAttempt, 
            id=attempt_id, 
            participant__mahasiswa__nim=request.user
        )
        
        # 2. Jika sudah selesai, lempar ke result
        if attempt.finished_at:
            return redirect('student-quiz-result', attempt_id=attempt.id)
            
        quiz = attempt.quiz
        questions = quiz.questions.all().order_by('order')

        # 3. Hitung Sisa Waktu (Server Side Calculation)
        import datetime
        now = timezone.now()
        # Batas waktu = Waktu Mulai + Durasi Menit
        time_limit = attempt.started_at + datetime.timedelta(minutes=quiz.duration_minutes)
        remaining_seconds = (time_limit - now).total_seconds()

        # 4. Jika waktu minus, paksa submit
        if remaining_seconds <= 0:
            messages.warning(request, "Waktu ujian telah habis!")
            # Kita redirect ke view submit untuk memproses penutupan
            return redirect('student-quiz-submit', attempt_id=attempt.id)

        return self.render_to_response(self.get_context_data(
            attempt=attempt,
            quiz=quiz,
            questions=questions,
            remaining_seconds=int(remaining_seconds)
        ))


# --- VIEW: PROSES SUBMIT JAWABAN (Logic Penilaian) ---
class StudentQuizSubmitView(StudentsRequiredMixin, AcademyView):
    def get(self, request, attempt_id, *args, **kwargs):
        # Jika user akses GET (misal via URL langsung), tutup ujian jika waktu habis,
        # atau redirect ke result jika sudah selesai.
        attempt = get_object_or_404(
            StudentQuizAttempt, 
            id=attempt_id, 
            participant__mahasiswa__nim=request.user
        )
        if not attempt.finished_at:
             # Auto close mechanism (misal waktu habis)
             attempt.finished_at = timezone.now()
             attempt.save()
        return redirect('student-quiz-result', attempt_id=attempt.id)

    def post(self, request, attempt_id, *args, **kwargs):
        attempt = get_object_or_404(
            StudentQuizAttempt, 
            id=attempt_id, 
            participant__mahasiswa__nim=request.user
        )
        
        # Cegah submit ulang
        if attempt.finished_at:
            return redirect('student-quiz-result', attempt_id=attempt.id)

        quiz = attempt.quiz
        questions = quiz.questions.all()
        
        # --- 1. Simpan Jawaban ---
        for q in questions:
            input_name = f"question_{q.id}"
            
            # Case A: Pilihan Ganda
            if q.question_type == 'multiple_choice':
                selected_option_id = request.POST.get(input_name)
                if selected_option_id:
                    # Validasi opsi milik soal tersebut
                    option = QuizOption.objects.filter(id=selected_option_id, question=q).first()
                    if option:
                        StudentQuizAnswer.objects.update_or_create(
                            attempt=attempt,
                            question=q,
                            defaults={'selected_option': option, 'text_answer': None}
                        )
            
            # Case B: Essay
            elif q.question_type == 'essay':
                text_ans = request.POST.get(input_name)
                if text_ans:
                    StudentQuizAnswer.objects.update_or_create(
                        attempt=attempt,
                        question=q,
                        defaults={'text_answer': text_ans, 'selected_option': None}
                    )

        # --- 2. Auto Grading (Khusus PG) & Finalisasi ---
        attempt.finished_at = timezone.now()
        
        total_score = 0
        # Ambil semua jawaban di attempt ini
        answers = StudentQuizAnswer.objects.filter(attempt=attempt).select_related('question', 'selected_option')
        
        for ans in answers:
            # Logic Nilai: Jika PG dan Benar, ambil bobot soal
            if ans.question.question_type == 'multiple_choice':
                if ans.selected_option and ans.selected_option.is_correct:
                    ans.score_obtained = ans.question.score_weight
                else:
                    ans.score_obtained = 0
                ans.save() # Simpan nilai per soal
                total_score += ans.score_obtained
            
            # Essay score_obtained default 0, menunggu penilaian dosen
        
        attempt.total_score = total_score
        attempt.save()

        messages.success(request, "Jawaban berhasil dikirim. Terima kasih!")
        return redirect('student-quiz-result', attempt_id=attempt.id)


# --- VIEW: HALAMAN HASIL / RESULT ---
class StudentQuizResultView(StudentsRequiredMixin, AcademyView):
    template_name = "students/quiz_result.html"

    def get(self, request, attempt_id, *args, **kwargs):
        attempt = get_object_or_404(
            StudentQuizAttempt, 
            id=attempt_id, 
            participant__mahasiswa__nim=request.user
        )
        
        # Hitung jumlah soal benar/salah (Statistik sederhana)
        total_questions = attempt.quiz.questions.count()
        correct_answers = StudentQuizAnswer.objects.filter(
            attempt=attempt, 
            score_obtained__gt=0
        ).count()

        return self.render_to_response(self.get_context_data(
            attempt=attempt,
            quiz=attempt.quiz,
            course_uuid=attempt.quiz.course.uuid,
            stats={
                'total': total_questions,
                'correct': correct_answers
            }
        ))