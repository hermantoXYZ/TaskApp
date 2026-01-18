
# Create your models here.
from django.db import models
from django.contrib.auth.models import User
import uuid
from django.utils import timezone
import os
from django.conf import settings

########################### TABEL USER MASTER #####################################
User.add_to_class("__str__", lambda self: f"{self.username} - {self.first_name}")

########################### MANAGE USERS #####################################

########################### JURUSAN #####################################
    
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
    duration_weeks = models.PositiveIntegerField()
    prodi = models.ForeignKey( Prodi, on_delete=models.CASCADE, related_name='courses' )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
    title = models.CharField(max_length=255)
    agenda_type = models.CharField(max_length=20)
    description = models.TextField(blank=True)
    agenda_date = models.DateTimeField()
    location = models.CharField(max_length=255, blank=True)
    is_online = models.BooleanField(default=False)
    meeting_url = models.URLField(blank=True, help_text='Link Zoom/GMeet')
    learning_outcome = models.TextField(blank=True, null=True, help_text="Capaian Pembelajaran")
    teaching_method = models.CharField(max_length=100, blank=True, null=True, help_text="Metode Pengajaran")
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['agenda_date'] 

    def __str__(self):
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
    course = models.ForeignKey( Course, related_name='announcements', on_delete=models.SET_NULL, null=True )
    title = models.CharField(max_length=255)
    content = models.TextField()
    priority = models.CharField( max_length=20, choices=PRIORITY_CHOICES, default='normal' )
    is_pinned = models.BooleanField(default=False)
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
        return f"{self.participant.mahasiswa.nim.first_name} - {self.agenda.title}"


class CourseMaterial(models.Model):
    MATERIAL_TYPES = [
        ('video', 'Video'),
        ('reading', 'Reading/Article'),
        ('assignment', 'Assignment'),
    ]
    agenda = models.ForeignKey(CourseAgenda, on_delete=models.CASCADE, related_name='materials')
    title = models.CharField(max_length=255)
    material_type = models.CharField(max_length=20, choices=MATERIAL_TYPES, default='video')
    video_url = models.URLField(blank=True)
    file_attachment = models.FileField(upload_to='course/materials/', blank=True)
    text_content = models.TextField(blank=True)
    duration_seconds = models.PositiveIntegerField(default=0)
    is_preview = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0) 
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


ASSIGNMENT_TYPES = [
        ('individual', 'Individu'),
        ('group', 'Kelompok'),
    ]

class CourseAssignment(models.Model):
    assignment_type = models.CharField(max_length=20, choices=ASSIGNMENT_TYPES, default='individual',)
    agenda = models.ForeignKey(CourseAgenda, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=255)
    description = models.TextField(help_text="Instruksi pengerjaan tugas")
    file_instruction = models.FileField(upload_to='course/assignments/instructions/', blank=True, null=True)
    due_date = models.DateTimeField() # Batas waktu pengumpulan
    max_score = models.IntegerField(default=100) # Nilai maksimal (biasanya 100)
    allow_late_submission = models.BooleanField(default=False, help_text="Izinkan pengumpulan telat?")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['due_date']
        verbose_name = "Course Assignment"

    def __str__(self):
        return f"TUGAS: {self.title} ({self.agenda.course.code})"
    
class StudentAssignmentSubmission(models.Model):
    assignment = models.ForeignKey(CourseAssignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(UserMhs, on_delete=models.CASCADE, related_name='submissions')
    submitted_link = models.URLField(max_length=500, blank=False, null=False)
    submitted_text = models.TextField(blank=True, null=True, help_text="Jawaban teks/link GDrive")   
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    group = models.ForeignKey( CourseGroup, on_delete=models.CASCADE, null=True, blank=True, help_text="Menyimpan ID kelompok agar nilai & file terikat ke kelompok, bukan cuma individu" )
    feedback = models.TextField(blank=True, null=True) # Catatan dari dosen
    
    def __str__(self):
        return f"{self.student.nim} - {self.assignment.title}"

class CourseQuiz(models.Model):
    EXAM_TYPES = [
        ('quiz', 'Kuis Harian'),
        ('exam', 'Ujian Semester'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='quizzes')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    quiz_type = models.CharField(max_length=20, choices=EXAM_TYPES, default='quiz')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=90)
    passing_score = models.IntegerField(default=60)
    max_attempts = models.PositiveIntegerField(default=1)
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
    quiz = models.ForeignKey(CourseQuiz, on_delete=models.CASCADE, related_name='attempts')
    participant = models.ForeignKey(CourseParticipant, on_delete=models.CASCADE, related_name='quiz_attempts')
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    total_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    def __str__(self):
        return f"{self.participant.mahasiswa.nim} - {self.quiz.title}"


class StudentQuizAnswer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt = models.ForeignKey(StudentQuizAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(QuizOption, on_delete=models.SET_NULL, null=True, blank=True)
    text_answer = models.TextField(blank=True, null=True)
    score_obtained = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    class Meta:
        unique_together = ['attempt', 'question']

    def __str__(self):
        return f"Ans: {self.question.id}"
    

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

    def __str__(self):
        return f"Chat Room {self.id}"

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