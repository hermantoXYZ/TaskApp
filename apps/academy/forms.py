from django import forms
from .models import Course, Prodi, CoursePeriod, CourseParticipant, CourseAgenda, CourseAnnouncement, CourseAttendance, CourseMaterial, CourseAssignment, StudentPortfolio
from .models import UserDosen, UserMhs, CourseQuiz, QuizQuestion, QuizOption
from django_summernote.widgets import SummernoteWidget

class CourseQuizForm(forms.ModelForm):
    class Meta:
        model = CourseQuiz
        fields = ['title', 'quiz_type', 'description', 'start_time', 'end_time', 'duration_minutes', 'passing_score', 'max_attempts', 'max_security_violations', 'is_published']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Deskripsi singkat...'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Misalnya: Quiz Harian/Ujian Semester'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'passing_score': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_attempts': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_security_violations': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 20}),
            'quiz_type': forms.Select(attrs={'class': 'form-select'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class QuizQuestionForm(forms.ModelForm):
    class Meta:
        model = QuizQuestion
        fields = ['text', 'image', 'score_weight']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Tulis soal atau kode LaTeX disini...'}),
            'score_weight': forms.NumberInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }


class CoursePeriodForm(forms.ModelForm):
    class Meta:
        model = CoursePeriod
        fields = ['name', 'start_date', 'end_date', 'is_active']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class AddParticipantForm(forms.ModelForm):
    list_mahasiswa = forms.ModelMultipleChoiceField(
        queryset=UserMhs.objects.all(),
        widget=forms.SelectMultiple(attrs={
            'class': 'select2 form-select', 
            'data-placeholder': 'Pilih Mahasiswa'
        }),
        label="Tambahkan Mahasiswa"
    )

    class Meta:
        model = CourseParticipant
        # EXCLUDE field 'mahasiswa' asli agar tidak error saat validasi
        exclude = ['mahasiswa', 'course', 'joined_at', 'final_score']
        # Atau jika ingin spesifik yang ditampilkan:
        # fields = ['list_mahasiswa', 'is_active']

class AddProgramStudiCourseForm(forms.ModelForm):
    
    class Meta:
        model = Prodi
        fields = ['strata', 'nama_prodi', 'gelar', 'status']
        widgets = {
            'strata': forms.Select(attrs={'class': 'form-select'}),
            'nama_prodi': forms.TextInput(attrs={'class': 'form-control'}),
            'gelar': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class CourseForm(forms.ModelForm):
    prodi = forms.ModelChoiceField(
        queryset=Prodi.objects.all(),
        empty_label="Pilih Program Studi", 
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    period = forms.ModelChoiceField(
        queryset=CoursePeriod.objects.all(),
        empty_label="Pilih Period", 
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    coaches = forms.ModelMultipleChoiceField(
        queryset=UserDosen.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={ 
            'class': 'select2 form-select',
            'multiple': 'multiple' 
        })
    )

    class Meta:
        model = Course
        fields = [
            'code', 'name', 'description', 'period', 'prodi',
            'credit_t', 'credit_p', 'is_active', 'coaches', 'group', 'link_rps'
        ]
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contoh: CS101'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contoh: Pengantar Ilmu Komputer'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Deskripsi mata kuliah',
            }),
            'period': forms.Select(attrs={
                'class': 'form-select'
            }),
            'prodi': forms.Select(attrs={
                'class': 'form-select',
            }),
            'credit_t': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'SKS Teori'
            }),
            'credit_p': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'SKS Praktik'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'coaches': forms.Select(attrs={
                'class': 'select2 form-select',
                'multiple': 'multiple',
            }),
            'group': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contoh: A, B, C'
            }),
            'link_rps': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://drive.google.com/...'
            })
        }
 

class AddAgendaForm(forms.ModelForm):
    class Meta:
        model = CourseAgenda
        fields = [
            'title',
            'agenda_type',
            'learning_outcome',
            'teaching_method',
            'agenda_date',
            'location',
            'is_online',
            'meeting_url',
            'lecturer',
            'allow_discussion',
            'is_active',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contoh: Pengantar Manajemen / UAS'}),
            'agenda_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contoh: Perkuliahan / UTS / UAS'}),
            'agenda_date': forms.DateTimeInput(
                attrs={'class': 'form-control flatpickr-datetime', 'placeholder': 'Pilih Tanggal & Jam'}
            ),
            'learning_outcome': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'style': 'height: 80px;', 'placeholder': 'Capaian pembelajaran mata kuliah...'}),
            'teaching_method': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contoh: Ceramah, Diskusi, Project Based'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Gedung/Ruangan'}),
            'meeting_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://zoom.us/...'}),
            'lecturer': forms.Select(attrs={'class': 'select2 form-select'}),
            'is_online': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_discussion': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        course = kwargs.pop('course', None)
        super().__init__(*args, **kwargs)
        self.fields['agenda_date'].required = False
        self.fields['lecturer'].required = False
        self.fields['lecturer'].empty_label = '— Pilih Dosen Pengampu —'
        # Filter hanya coach yang terdaftar di course ini
        if course is not None:
            self.fields['lecturer'].queryset = course.coaches.all()
        else:
            self.fields['lecturer'].queryset = UserDosen.objects.all()



class AddAnnouncementForm(forms.ModelForm):
    class Meta:
        model = CourseAnnouncement
        fields = ['title', 'content', 'priority', 'is_pinned', 'allow_discussion']
        widgets = {
            'priority': forms.Select(attrs={
                'class': 'select2 form-select', 
                'data-placeholder': 'Pilih Prioritas'
            }),
            'content': forms.Textarea(attrs={'rows': 4, 'style': 'height: 120px;'}),
            'is_pinned': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_discussion': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = CourseAttendance
        fields = ['status', 'notes']
        widgets = {
            # RadioSelect akan kita loop di template agar jadi tombol warna-warni
            'status': forms.RadioSelect(attrs={'class': 'btn-check'}), 
            'notes': forms.TextInput(attrs={
                'class': 'form-control form-control-sm', 
                'placeholder': 'Keterangan (Opsional)...'
            })
        }
class CourseMaterialForm(forms.ModelForm):
    text_content = forms.CharField(widget=SummernoteWidget(), required=False)

    class Meta:
        model = CourseMaterial
        fields = [
            'agenda', 'title',
            'text_content',
            'order', 'is_published', 'allow_discussion'
        ]
        widgets = {
            'agenda': forms.Select(attrs={'class': 'select2 form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Judul Materi'}),
            'text_content': SummernoteWidget(attrs={'summernote': {'width': '100%', 'height': '400px'}}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_discussion': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Urutan'}),
        }

    def __init__(self, *args, **kwargs):
        course_uuid = kwargs.pop('course_uuid', None)
        super().__init__(*args, **kwargs)
        
        if course_uuid:
            self.fields['agenda'].queryset = CourseAgenda.objects.filter(
                course__uuid=course_uuid
            ).order_by('agenda_date')
            
            self.fields['agenda'].label = "Pilih Pertemuan / Agenda"

class CourseAssignmentForm(forms.ModelForm):
    class Meta:
        model = CourseAssignment
        fields = ['agenda', 'title', 'description', 'file_instruction', 'due_date', 'max_score', 'allow_late_submission', 'assignment_type', 'is_published', 'allow_discussion']
        widgets = {
            'assignment_type': forms.Select(attrs={'class': 'form-select'}),
            'agenda': forms.Select(attrs={'class': 'select2 form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Judul Tugas'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Instruksi pengerjaan...'}),
            'file_instruction': forms.FileInput(attrs={'class': 'form-control'}),
            'due_date': forms.DateTimeInput(attrs={
                'class': 'form-control flatpickr-datetime', 
                'placeholder': 'Pilih Batas Waktu'
            }),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'max_score': forms.NumberInput(attrs={'class': 'form-control', 'value': 100}),
            'allow_late_submission': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_discussion': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
            course_uuid = kwargs.pop('course_uuid', None)
            super().__init__(*args, **kwargs)

            if course_uuid:
                self.fields['agenda'].queryset = CourseAgenda.objects.filter(
                    course__uuid=course_uuid
                ).order_by('agenda_date')

class StudentPortfolioForm(forms.ModelForm):
    body = forms.CharField(
        widget=SummernoteWidget(attrs={'summernote': {'width': '100%', 'height': '350px'}}),
        required=False,
        label='Penjelasan Lengkap',
    )

    class Meta:
        model = StudentPortfolio
        fields = [
            'title', 'description', 'body',
            'project_url', 'activity_type',
            'status', 'is_featured',
            'category_portfolio', 'course', 'thumbnail',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contoh: Aplikasi Web E-Commerce dengan Django',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Deskripsi singkat tentang portofolio ini...',
            }),
            'project_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://github.com/username/repo',
            }),
            'activity_type': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'category_portfolio': forms.Select(attrs={'class': 'form-select'}),
            'course': forms.Select(attrs={'class': 'form-select'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'thumbnail': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class ChangeRoleForm(forms.Form):
    ROLE_CHOICES = [
        ('all', 'Semua Role'),
        ('dosen', 'Dosen'),
        ('mahasiswa', 'Mahasiswa'),
        ('prodi', 'Admin Prodi'),
    ]
    role_type = forms.ChoiceField(
        choices=ROLE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_role_type'}),
        label='Filter Role'
    )
    user_target = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={'class': 'form-select select2', 'id': 'id_user_target'}),
        label='Pilih Target User'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import UserProdi
        flat_choices = [('', '-- Pilih User Tujuan --')]

        # Dosen
        dosen_users = UserDosen.objects.select_related('nip', 'prodi').all().order_by('nip__first_name')
        dosen_choices = [
            (d.nip.username, f"{d.nip.first_name or d.nip.username} ({d.nip.username}) - Dosen {f'[{d.prodi.nama_prodi}]' if d.prodi else ''}")
            for d in dosen_users if d.nip
        ]
        if dosen_choices:
            flat_choices.append(('Dosen', tuple(dosen_choices)))

        # Mahasiswa
        mhs_users = UserMhs.objects.select_related('nim', 'prodi').all().order_by('nim__first_name')
        mhs_choices = [
            (m.nim.username, f"{m.nim.first_name or m.nim.username} ({m.nim.username}) - Mahasiswa {f'[{m.prodi.nama_prodi}]' if m.prodi else ''}")
            for m in mhs_users if m.nim
        ]
        if mhs_choices:
            flat_choices.append(('Mahasiswa', tuple(mhs_choices)))

        # Admin Prodi
        prodi_users = UserProdi.objects.select_related('username', 'prodi').all().order_by('username__first_name')
        prodi_choices = [
            (p.username.username, f"{p.username.first_name or p.username.username} ({p.username.username}) - Admin Prodi {f'[{p.prodi.nama_prodi}]' if p.prodi else ''}")
            for p in prodi_users if p.username
        ]
        if prodi_choices:
            flat_choices.append(('Admin Prodi', tuple(prodi_choices)))

        self.fields['user_target'].choices = flat_choices