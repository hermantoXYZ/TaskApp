
# Create your models here.
from django.db import models
from django.contrib.auth.models import User
import uuid
from django.utils import timezone as tz
from django.utils import timezone
import os
from django.conf import settings
from django.utils.text import slugify
########################### TABEL USER MASTER #####################################
User.add_to_class("__str__", lambda self: f"{self.username} - {self.first_name}")

########################### JURUSAN PRODI #####################################
    
class Prodi(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    strata = models.CharField(max_length=5, blank=False, null=False)
    nama_prodi = models.CharField(max_length=255, blank=False, null=False)
    gelar = models.CharField(max_length=10, blank=False, null=False)
    status = models.CharField(max_length=10, default='Aktif', choices=[
        ('Aktif', 'Aktif'),
        ('NonAktif', 'NonAktif'), 
        ])
    
    def __str__(self):
        return f"{self.nama_prodi} - {self.strata}"



def rename_photo_dsn(instance, filename):
    ext = filename.split('.')[-1]
    nip = instance.nip
    timestamp = timezone.now().strftime('%Y%m%d%H%M%S')  # format waktu: 20250427153520
    new_filename = f"{nip}_{timestamp}.{ext}"
    return os.path.join('img_profile/dsn/', new_filename)


########################### MANAGE USERS #####################################

class UserDosen(models.Model):
    nip = models.OneToOneField(User, on_delete=models.CASCADE, to_field="username", primary_key=True)
    prodi = models.ForeignKey(Prodi, on_delete=models.SET_NULL, null=True, blank=True)
    status_kepegawaian = models.CharField(max_length=15, choices=[
                    ('PNS', 'PNS'),
                    ('CPNS', 'CPNS'),
                    ('PPPK', 'PPPK'),
                    ('NON-ASN', 'NON-ASN'),
                ],null=True, blank=True)
    telp = models.CharField(max_length=15)
    gender = models.CharField(max_length=15, choices=[
        ('Laki-laki', 'Laki-laki'),
        ('Perempuan', 'Perempuan'),
    ])
    tempat_lahir = models.CharField(max_length=50, null=True, blank=True)
    tgl_lahir = models.DateField(null=True, blank=True)
    nidn = models.CharField(max_length=20, null=True, blank=True)
    pangkat = models.CharField(max_length=30, choices=[
                    ('Penata Muda Tingkat I', 'Penata Muda Tingkat I'),
                    ('Penata', 'Penata'),
                    ('Penata Tingkat I', 'Penata Tingkat I'),
                    ('Pembina', 'Pembina'),
                    ('Pembina Utama Muda', 'Pembina Utama Muda'),
                    ('Pembina Utama Madya', 'Pembina Utama Madya'),
                    ('Pembina Utama', 'Pembina Utama'),
                ],null=True, blank=True)
    golongan = models.CharField(max_length=10, choices=[
                    ('III/b', 'III/b'),
                    ('III/c', 'III/c'),
                    ('III/d', 'III/d'),
                    ('IV/a', 'IV/a'),
                    ('IV/b', 'IV/b'),
                    ('IV/c', 'IV/c'),
                    ('IV/d', 'IV/d'),
                    ('IV/e', 'IV/e'),
                ],null=True, blank=True)
    jafung = models.CharField(max_length=15, choices=[
                    ('Asisten Ahli', 'Asisten Ahli'),
                    ('Lektor', 'Lektor'),
                    ('Lektor Kepala', 'Lektor Kepala'),
                    ('Guru Besar', 'Guru Besar'),
                ],null=True, blank=True)
    bidang_keahlian = models.CharField(max_length=100, null=True, blank=True)
    photo = models.ImageField(upload_to=rename_photo_dsn)

    def save(self, *args, **kwargs):
        try:
            old_instance = UserDosen.objects.get(pk=self.pk)
            if old_instance.photo and old_instance.photo != self.photo:
                old_photo_path = os.path.join(settings.MEDIA_ROOT, old_instance.photo.name)
                if os.path.isfile(old_photo_path):
                    os.remove(old_photo_path)
        except UserDosen.DoesNotExist:
            pass  # ini data baru, jadi tidak perlu hapus apa-apa

        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.nip}"
    
def rename_photo_mhs(instance, filename):
    ext = filename.split('.')[-1]
    nim = instance.nim
    timestamp = timezone.now().strftime('%Y%m%d%H%M%S')  # format waktu: 20250427153520
    new_filename = f"{nim}_{timestamp}.{ext}"
    return os.path.join('img_profile/mhs/', new_filename)  

class UserMhs(models.Model):
    nim = models.OneToOneField(User, on_delete=models.CASCADE, to_field="username", primary_key=True)
    prodi = models.ForeignKey(Prodi, on_delete=models.SET_NULL, null=True, blank=True, related_name="usermhs_prodi")
    telp = models.CharField(max_length=15)
    gender = models.CharField(max_length=15, choices=[
        ('Laki-laki', 'Laki-laki'),
        ('Perempuan', 'Perempuan'),
    ])
    tempat_lahir = models.CharField(max_length=50, null=True, blank=True)
    tgl_lahir = models.DateField(null=True, blank=True)
    tgl_masuk = models.DateField(null=True, blank=True)
    alamat = models.CharField(max_length=255, null=True, blank=True)
    penasehat_akademik = models.ForeignKey(UserDosen, on_delete=models.SET_NULL, null=True, blank=True, related_name="usermhs_pa") 
    photo = models.ImageField(upload_to=rename_photo_mhs)

    def save(self, *args, **kwargs):
        try:
            old_instance = UserMhs.objects.get(pk=self.pk)
            if old_instance.photo and old_instance.photo != self.photo:
                old_photo_path = os.path.join(settings.MEDIA_ROOT, old_instance.photo.name)
                if os.path.isfile(old_photo_path):
                    os.remove(old_photo_path)
        except UserMhs.DoesNotExist:
            pass  # ini data baru, jadi tidak perlu hapus apa-apa

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nim}"
    

def rename_photo_admin(instance, filename):
    ext = filename.split('.')[-1]
    username = instance.username
    timestamp = timezone.now().strftime('%Y%m%d%H%M%S')  # format waktu: 20250427153520
    new_filename = f"{username}_{timestamp}.{ext}"
    return os.path.join('img_profile/admin/', new_filename)  


class UserProdi(models.Model):
    username = models.OneToOneField(User, on_delete=models.CASCADE, to_field="username", primary_key=True)
    prodi = models.ForeignKey('academy.Prodi', on_delete=models.SET_NULL, null=True, blank=True)
    telp = models.CharField(max_length=15)
    gender = models.CharField(max_length=15, choices=[
        ('Laki-laki', 'Laki-laki'),
        ('Perempuan', 'Perempuan'),
    ])
    photo = models.ImageField(upload_to=rename_photo_admin)

    def save(self, *args, **kwargs):
        try:
            old_instance = UserProdi.objects.get(pk=self.pk)
            if old_instance.photo and old_instance.photo != self.photo:
                old_photo_path = os.path.join(settings.MEDIA_ROOT, old_instance.photo.name)
                if os.path.isfile(old_photo_path):
                    os.remove(old_photo_path)
        except UserProdi.DoesNotExist:
            pass  # ini data baru, jadi tidak perlu hapus apa-apa

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username}"


########################### ACADEMY MODELS #####################################
class CoursePeriod(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)  
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Course(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    code = models.CharField(max_length=20, db_index=True)  
    name = models.CharField(max_length=255)
    description = models.TextField(max_length=500)
    period = models.ForeignKey( CoursePeriod, on_delete=models.SET_NULL, null=True, blank=True, related_name='courses' )
    credit_t = models.PositiveIntegerField()
    coaches = models.ManyToManyField(UserDosen, blank=True, related_name='coached_courses' )
    group = models.CharField(max_length=50)
    credit_p = models.PositiveIntegerField()
    prodi = models.ForeignKey( Prodi, on_delete=models.SET_NULL, null=True, blank=True, related_name='courses' )
    link_rps = models.URLField(max_length=200, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    TOTAL_SESSIONS = 16  

    def save(self, *args, **kwargs):
        is_new = self.pk is None  
        super().save(*args, **kwargs)
        if is_new:
            self._create_default_sessions()

    def _create_default_sessions(self):
        default_date = tz.now() 
        sessions = [
            CourseAgenda(
                course=self,
                session_number=i,
                title=f"Pertemuan {i}",
                agenda_type="Perkuliahan",
                agenda_date=default_date,
            )
            for i in range(1, self.TOTAL_SESSIONS + 1)
        ]
        CourseAgenda.objects.bulk_create(sessions)

    def __str__(self):
        return f"{self.code} - {self.name} ({self.period})"

class CourseGroup(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='groups')
    name = models.CharField(max_length=100)  
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.course.code}"

    def member_count(self):
        return self.members.count()


class CourseAgenda(models.Model):
    course = models.ForeignKey(Course, related_name='agendas', on_delete=models.CASCADE)
    session_number = models.PositiveSmallIntegerField(null=True, blank=True) 
    title = models.CharField(max_length=255)
    agenda_type = models.CharField(max_length=20, default="Perkuliahan")
    agenda_date = models.DateTimeField(null=True, blank=True, help_text="Tanggal & jam pelaksanaan")
    location = models.CharField(max_length=255, blank=True)
    is_online = models.BooleanField(default=False)
    meeting_url = models.URLField(blank=True, help_text='Link Zoom/GMeet')
    learning_outcome = models.TextField(blank=True, null=True, help_text="Capaian Pembelajaran")
    teaching_method = models.CharField(max_length=100, blank=True, null=True, help_text="Metode Pengajaran")
    created_by = models.ForeignKey(UserDosen, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_agendas', help_text="Dosen yang membuat agenda")
    lecturer = models.ForeignKey(UserDosen, on_delete=models.SET_NULL, null=True, blank=True, related_name='teaching_agendas', help_text="Dosen pengampu sesi ini (bisa berbeda dari pembuat)")
    allow_discussion = models.BooleanField(default=False, help_text="Centang untuk menampilkan ke beranda diskusi.",)
    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['session_number', 'agenda_date']
        unique_together = [('course', 'session_number')]  # Satu nomor sesi per course

    def __str__(self):
        if self.session_number:
            return f"{self.course.code} - Sesi {self.session_number}: {self.title}"
        return f"{self.course.code} - {self.title}"



class CourseParticipant(models.Model):
    course = models.ForeignKey( Course, related_name='participants', on_delete=models.CASCADE )
    mahasiswa = models.ForeignKey(UserMhs, on_delete=models.SET_NULL, null=True, blank=True, related_name='enrolled_courses' )
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    final_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    def __str__(self):
        return f"{self.course.code}"




class CourseAnnouncement(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    course = models.ForeignKey( Course, related_name='announcements', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    content = models.TextField()
    priority = models.CharField( max_length=20, choices=PRIORITY_CHOICES, default='normal' )
    is_pinned = models.BooleanField(default=False)
    allow_discussion = models.BooleanField(default=False, help_text="Centang untuk membuka thread diskusi di beranda kelas.")
    created_by = models.ForeignKey(UserDosen, on_delete=models.SET_NULL, null=True, related_name='created_announcements' )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class CourseAttendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused'),
        ('sick', 'Sick'),
    ]
    
    participant = models.ForeignKey( CourseParticipant, on_delete=models.CASCADE, related_name='attendances' ) 
    agenda = models.ForeignKey( CourseAgenda, on_delete=models.CASCADE, related_name='attendances' )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='present')
    notes = models.TextField(blank=True)
    check_in_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        mahasiswa = self.participant.mahasiswa if self.participant else None
        nama = mahasiswa.nim.first_name if mahasiswa else "Mahasiswa Dihapus"
        agenda = self.agenda.title if self.agenda else "Agenda Dihapus"

        return f"{nama} - {agenda}"


def media_library_upload_path(instance, filename):
    return f"media_library/{instance.uploaded_by.username}/{filename}"


class MediaFile(models.Model):
    FILE_TYPE_CHOICES = [
        ('video_url', 'Video (URL YouTube/Vimeo)'),
        ('pdf',       'Dokumen PDF'),
        ('docx',      'Dokumen Word'),
        ('pptx',      'Presentasi PowerPoint'),
        ('image',     'Gambar'),
        ('other',     'Berkas Lainnya'),
    ]

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name        = models.CharField(max_length=255, verbose_name="Nama Berkas")
    file_type   = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES, default='other')
    file        = models.FileField(upload_to=media_library_upload_path, blank=True, null=True)
    video_url   = models.URLField(blank=True, null=True, help_text="Isi jika tipe adalah Video URL (YouTube/Vimeo)")
    file_size   = models.PositiveBigIntegerField(default=0, help_text="Ukuran file dalam bytes (diisi otomatis)")
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='media_files')
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Media Library File"
        verbose_name_plural = "Media Library Files"

    def __str__(self):
        return self.name

    @property
    def file_size_display(self):
        size = self.file_size
        if size >= 1_000_000:
            return f"{size / 1_000_000:.2f} MB"
        elif size >= 1_000:
            return f"{size / 1_000:.2f} KB"
        return f"{size} B" if size else "—"

    def save(self, *args, **kwargs):
        if self.file and hasattr(self.file, 'size'):
            self.file_size = self.file.size
        super().save(*args, **kwargs)


class CourseMaterial(models.Model):
    agenda = models.ForeignKey(CourseAgenda, on_delete=models.CASCADE, related_name='materials')
    title = models.CharField(max_length=255)
    text_content = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=False)
    allow_discussion = models.BooleanField(default=False, help_text="Centang untuk menampilkan ke beranda diskusi.")
    created_by = models.ForeignKey(UserDosen, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_materials', verbose_name="Dibuat oleh")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']
        verbose_name = "Course Material"

    def __str__(self):
        return f"{self.agenda.title} - {self.title}"


class StudentMaterialProgress(models.Model):
    participant = models.ForeignKey(CourseParticipant, on_delete=models.CASCADE, related_name='material_progress')
    material = models.ForeignKey(CourseMaterial, on_delete=models.CASCADE, related_name='student_progress')
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)


class AgendaMediaItem(models.Model):
    agenda = models.ForeignKey(CourseAgenda, on_delete=models.CASCADE, related_name='media_items')
    media_file = models.ForeignKey(MediaFile, on_delete=models.SET_NULL, null=True, blank=True, related_name='agenda_items')
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = "Agenda Media Item"
        unique_together = [('agenda', 'media_file')]  

    def __str__(self):
        media_name = self.media_file.name if self.media_file else "Media Dihapus"
        return f"{self.agenda} - {media_name}"


ASSIGNMENT_TYPES = [
        ('individual', 'Individu'),
        ('group', 'Kelompok'),
    ]

class CourseAssignment(models.Model):
    assignment_type = models.CharField(max_length=20, choices=ASSIGNMENT_TYPES, default='individual',)
    agenda = models.ForeignKey(CourseAgenda, on_delete=models.SET_NULL, null=True, blank=True, related_name='assignments')
    title = models.CharField(max_length=255)
    description = models.TextField(help_text="Instruksi pengerjaan tugas")
    file_instruction = models.FileField(upload_to='course/assignments/instructions/', blank=True, null=True)
    due_date = models.DateTimeField() 
    max_score = models.IntegerField(default=100) 
    allow_late_submission = models.BooleanField(default=False, help_text="Izinkan pengumpulan telat?")
    is_published = models.BooleanField(default=False)
    allow_discussion = models.BooleanField(default=False, help_text="Centang untuk menampilkan ke beranda diskusi.",)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['due_date']
        verbose_name = "Course Assignment"

    def __str__(self):
        if self.agenda and self.agenda.course:
            return f"TUGAS: {self.title} ({self.agenda.course.code})"
        return f"TUGAS: {self.title}"
    
class StudentAssignmentSubmission(models.Model):
    assignment = models.ForeignKey(CourseAssignment, on_delete=models.SET_NULL, null=True, blank=True, related_name='submissions')
    student = models.ForeignKey(UserMhs, on_delete=models.SET_NULL, null=True, blank=True, related_name='submissions')
    submitted_link = models.URLField(max_length=500, blank=False, null=False)
    submitted_text = models.TextField(blank=True, null=True, help_text="Jawaban teks/link GDrive")   
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    group = models.ForeignKey( CourseGroup, on_delete=models.SET_NULL, null=True, blank=True, help_text="Menyimpan ID kelompok agar nilai & file terikat ke kelompok, bukan cuma individu" )
    feedback = models.TextField(blank=True, null=True) 
    
    def __str__(self):
        student = self.student.nim if self.student else "Mahasiswa Dihapus"
        assignment = self.assignment.title if self.assignment else "Tugas Dihapus"
        return f"{student} - {assignment}"

class CourseQuiz(models.Model):
    EXAM_TYPES = [
        ('quiz', 'Kuis Harian'),
        ('exam', 'Ujian Semester'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name='quizzes')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    quiz_type = models.CharField(max_length=20, choices=EXAM_TYPES, default='quiz')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=90)
    passing_score = models.IntegerField(default=60)
    max_attempts = models.PositiveIntegerField(default=1)
    max_security_violations = models.PositiveSmallIntegerField(default=3)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start_time']

    def __str__(self):
        return f"{self.title} ({self.course.code})"



class QuizQuestion(models.Model):
    QUESTION_TYPES = [
        ('multiple_choice', 'Pilihan Ganda'),
        ('essay', 'Esai'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(CourseQuiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField(verbose_name="Soal") 
    image = models.ImageField(upload_to='quiz/questions/', blank=True, null=True)
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='multiple_choice')
    score_weight = models.PositiveIntegerField(default=10)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Soal No {self.order} ({self.quiz.title})"


class QuizOption(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name='options')
    text = models.TextField() # Support LaTeX
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.text[:20]} ({'Benar' if self.is_correct else 'Salah'})"


class StudentQuizAttempt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(CourseQuiz, on_delete=models.SET_NULL, null=True, blank=True, related_name='attempts')
    participant = models.ForeignKey(CourseParticipant, on_delete=models.SET_NULL, null=True, blank=True, related_name='quiz_attempts')
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    total_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_graded = models.BooleanField(default=False, help_text="Tandai jika sudah diperiksa oleh dosen")
    security_violation_count = models.PositiveSmallIntegerField(default=0)
    security_events = models.JSONField(default=list, blank=True)
    
    def __str__(self):
        student = self.participant.mahasiswa.nim if self.participant and self.participant.mahasiswa else "Mahasiswa Dihapus"
        quiz_title = self.quiz.title if self.quiz else "Kuis Dihapus"
        return f"{student} - {quiz_title}"


class StudentQuizAnswer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt = models.ForeignKey(StudentQuizAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(QuizQuestion, on_delete=models.SET_NULL, null=True, blank=True)
    selected_option = models.ForeignKey(QuizOption, on_delete=models.SET_NULL, null=True, blank=True)
    text_answer = models.TextField(blank=True, null=True)
    score_obtained = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    class Meta:
        unique_together = ['attempt', 'question']

    def __str__(self):
        return f"Ans: {self.question.id if self.question else 'Question Deleted'}"
    

class CourseGroupMember(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(CourseGroup, on_delete=models.CASCADE, related_name='members')
    participant = models.ForeignKey(CourseParticipant, on_delete=models.CASCADE, related_name='group_memberships')
    role = models.CharField(max_length=20, default='member', choices=[
        ('leader', 'Ketua'),
        ('member', 'Anggota'),
    ])
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['group', 'participant'] 

    def __str__(self):
        return f"{self.participant.mahasiswa.nim} -> {self.group.name}"

ROOM_TYPES = [
        ('private', 'Private'),
        ('group', 'Group'),
    ]

class ChatRoom(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, null=True, blank=True)
    participants = models.ManyToManyField(User, related_name='chat_rooms')
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES, default='private')
    group = models.OneToOneField(CourseGroup, on_delete=models.CASCADE, null=True, blank=True) # Perlu ditambah
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Chat Room"
        verbose_name_plural = "Chat Rooms"
        ordering = ['-updated_at'] 

    def __str__(self):
        if self.name:
            return self.name
        return f"Private Chat ({str(self.id)[:8]})" if self.room_type == 'private' else f"Group Chat ({str(self.id)[:8]})"


    def get_partner(self, user):
        return self.participants.exclude(id=user.id).first()

class ChatMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()  
    is_read = models.BooleanField(default=False) 
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at'] 

    def __str__(self):
        return f"{self.sender.username}: {self.content[:20]}..."
    
class BookCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True) 

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
def rename_books_cover(instance, filename):
    ext = filename.split('.')[-1]
    title = instance.title.replace(" ", "_")
    timestamp = timezone.now().strftime('%Y%m%d%H%M%S')  
    new_filename = f"{title}_{timestamp}.{ext}"
    return os.path.join('books/covers/', new_filename)
    
class Book(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255, blank=True, null=True)
    category = models.ForeignKey(BookCategory, on_delete=models.SET_NULL, null=True, related_name='books')
    description = models.TextField(blank=True, null=True)
    cover = models.ImageField(upload_to=rename_books_cover)
    embed_url = models.URLField(max_length=500)
    source_url = models.URLField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return self.title

########################### CALENDAR EVENT #####################################

CALENDAR_LABEL_CHOICES = [
    ('Campus', 'Campus'),
    ('Business', 'Business'),
    ('Personal', 'Personal'),
    ('Family', 'Family'),
    ('Holiday', 'Holiday'),
    ('Finance', 'Finance'),
    ('Self-Dev', 'Self-Dev'),
    ('Health & Fitness', 'Health & Fitness'),
    ('Lainnya', 'Lainnya'),
]

class CalendarEvent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='calendar_events')
    title = models.CharField(max_length=255)
    label = models.CharField(max_length=20, choices=CALENDAR_LABEL_CHOICES, default='Campus')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    all_day = models.BooleanField(default=False)
    url = models.URLField(max_length=500, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start_date']

    def __str__(self):
        return f"{self.title} ({self.user.username})"


########################### DISCUSSION / FORUM MODELS #####################################

class CourseDiscussion(models.Model):
    DISCUSSION_TYPES = [
        ('general',    'Diskusi Umum'),
        ('material',   'Terkait Materi'),
        ('assignment', 'Terkait Tugas'),
        ('question',   'Pertanyaan'),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='discussions')
    agenda = models.ForeignKey(CourseAgenda, on_delete=models.SET_NULL, null=True, blank=True, related_name='discussions')
    material = models.ForeignKey(CourseMaterial, on_delete=models.SET_NULL, null=True, blank=True, related_name='discussions')
    assignment = models.ForeignKey(CourseAssignment, on_delete=models.SET_NULL, null=True, blank=True, related_name='discussions')
    announcement = models.ForeignKey(CourseAnnouncement, on_delete=models.SET_NULL, null=True, blank=True, related_name='discussions')
    discussion_type = models.CharField(max_length=20, choices=DISCUSSION_TYPES, default='general')
    title = models.CharField(max_length=255)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_discussions')
    is_pinned = models.BooleanField(default=False, help_text="Hanya dosen yang bisa pin")
    is_closed = models.BooleanField(default=False, help_text="Tidak bisa dibalas jika ditutup")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_pinned', '-created_at']

    def __str__(self):
        return f"[{self.course.code}] {self.title}"

    def reply_count(self):
        return self.replies.filter(parent__isnull=True).count()

    def like_count(self):
        return self.likes.count()


class CourseDiscussionReply(models.Model):
    discussion = models.ForeignKey(CourseDiscussion, on_delete=models.CASCADE, related_name='replies')
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    body = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='discussion_replies')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        user = self.created_by.username if self.created_by else "User Deleted"
        return f"Reply by {user} on '{self.discussion.title}'"

    def like_count(self):
        return self.likes.count()


class CourseDiscussionLike(models.Model):
    discussion = models.ForeignKey(CourseDiscussion, on_delete=models.CASCADE, null=True, blank=True, related_name='likes')
    reply = models.ForeignKey(CourseDiscussionReply, on_delete=models.CASCADE, null=True, blank=True, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='discussion_likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['discussion', 'user'],
                condition=models.Q(discussion__isnull=False),
                name='unique_discussion_like'
            ),
            models.UniqueConstraint(
                fields=['reply', 'user'],
                condition=models.Q(reply__isnull=False),
                name='unique_reply_like'
            ),
        ]

    def __str__(self):
        if self.discussion:
            return f"{self.user.username} ♥ diskusi: {self.discussion.title}"
        return f"{self.user.username} ♥ reply #{self.reply_id}"

def portfolio_thumbnail_upload(instance, filename):
    return f"portfolio/{instance.user.username}/thumbnail/{filename}"


class CategoryPortfolio(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug: self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self): return self.name


class StudentPortfolio(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived')
        ]
    ACTIVITY_TYPE_CHOICES = [
        ('project', 'Project'),
        ('presentation', 'Presentation'),
        ('competition', 'Competition'),
        ('internship', 'Internship'),
        ('research', 'Research'),
        ('publication', 'Publication'),
        ('certificate', 'Certificate'),
        ('other', 'Other'),
    ]
    VERIFICATION_CHOICES = [
        ('pending',  'Menunggu Verifikasi'),
        ('verified', 'Terverifikasi'),
        ('rejected', 'Ditolak'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='student_portfolio')
    category_portfolio = models.ForeignKey(CategoryPortfolio, on_delete=models.SET_NULL, null=True, blank=True, related_name='portfolios')
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name='portfolio_projects')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPE_CHOICES, default='project')
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True, blank=True)
    description = models.TextField(blank=True, help_text="Deskripsi singkat project")
    body = models.TextField(blank=True, help_text="Penjelasan lengkap project")
    thumbnail = models.ImageField(upload_to=portfolio_thumbnail_upload, blank=True, null=True)
    project_url = models.URLField(max_length=500, blank=True, null=True, help_text="Link project / presentasi / github / gdrive / youtube")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    is_featured = models.BooleanField(default=False)
    view_count = models.PositiveIntegerField(default=0)
    verification_status = models.CharField(max_length=10, choices=VERIFICATION_CHOICES, default='pending', verbose_name='Status Verifikasi')
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_portfolios', verbose_name='Diverifikasi oleh')
    verified_at = models.DateTimeField(null=True, blank=True, verbose_name='Waktu Verifikasi')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Student Portfolio"
        verbose_name_plural = "Student Portfolios"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            while StudentPortfolio.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{uuid.uuid4().hex[:6]}"
            self.slug = slug
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.thumbnail:
            self.thumbnail.delete(save=False)
        super().delete(*args, **kwargs)

    def __str__(self): return f"{self.user.username} - {self.title}"


# ============================================================
# KANBAN PRODUCTIVITY MODELS (Solo)
# ============================================================

class KanbanBoard(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='kanban_boards')
    title = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = "Kanban Board"
        verbose_name_plural = "Kanban Boards"

    def __str__(self):
        return f"{self.user.username} - {self.title}"

def kanban_attachments_upload(instance, filename):
    return f"kanban_attachments/{instance.board.user.username}/{filename}"

class KanbanTask(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    board = models.ForeignKey(KanbanBoard, on_delete=models.CASCADE, related_name='tasks')
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_kanban_tasks')
    title = models.CharField(max_length=255)
    due_date = models.DateField(null=True, blank=True)
    label = models.CharField(max_length=50, blank=True, null=True)
    label_color = models.CharField(max_length=50, blank=True, null=True, default='bg-label-primary')
    comments = models.TextField(blank=True, null=True)
    attachments = models.FileField(upload_to=kanban_attachments_upload, blank=True, null=True)
    assignees = models.ManyToManyField(User, blank=True, related_name='assigned_kanban_tasks', verbose_name="Ditugaskan kepada")
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = "Kanban Task"
        verbose_name_plural = "Kanban Tasks"

    def __str__(self):
        return f"{self.board.title} - {self.title}"

    def delete(self, *args, **kwargs):
        if self.attachments: self.attachments.delete()
        super().delete(*args, **kwargs)

class KanbanActivity(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(KanbanTask, on_delete=models.CASCADE, related_name='activities')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    text = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Kanban Activity"
        verbose_name_plural = "Kanban Activities"

    def __str__(self):
        return self.text


def doc_thumbnail_upload(instance, filename):
    return f"documentation/thumbnail/{filename}"

class AppDocumentation(models.Model):
    TARGET_CHOICES = [
        ('all', 'Semua Pengguna'),
        ('dosen', 'Dosen'),
        ('mahasiswa', 'Mahasiswa'),
        ('admin', 'Admin'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True, blank=True)
    body = models.TextField(blank=True, help_text="Penjelasan lengkap panduan")
    thumbnail = models.ImageField(upload_to=doc_thumbnail_upload, blank=True, null=True)
    video_url = models.URLField(max_length=500, blank=True, null=True, help_text="Link embed video panduan")
    target_audience = models.CharField(max_length=20, choices=TARGET_CHOICES, default='all', help_text="Panduan ditujukan untuk siapa?")
    view_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "App Documentation"
        verbose_name_plural = "App Documentations"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.get_target_audience_display()})"