from django import forms
from .models import Course, Prodi, CoursePeriod, CourseParticipant, CourseAgenda, CourseAnnouncement, CourseAttendance, CourseMaterial, CourseAssignment
from .models import UserDosen, UserMhs


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
    # GANTI NAMA FIELD: Jangan pakai 'mahasiswa', tapi pakai 'list_mahasiswa'
    # Ini memutus hubungan otomatis yang menyebabkan error.
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
            'credit_t', 'credit_p', 'duration_weeks', 'is_active', 'coaches', 'group'
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
            'duration_weeks': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '16',
                'value': 16
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
        }
 

class AddAgendaForm(forms.ModelForm):
    class Meta:
        model = CourseAgenda
        fields = [
            'title', 
            'agenda_type',
            'description', 
            'learning_outcome', 
            'teaching_method',  
            'agenda_date', 
            'location', 
            'is_online', 
            'meeting_url'      
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contoh: Prilaku Konsumen / UAS'}),
            'agenda_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contoh: Bab 1/ Pertemuan 1/ Bagian 1'}),
            'agenda_date': forms.DateTimeInput(attrs={'class': 'form-control flatpickr-datetime', 'placeholder': 'Pilih Tanggal & Jam'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'style': 'height: 80px;', 'placeholder': 'Deskripsi singkat...'}),
            'learning_outcome': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'style': 'height: 80px;', 'placeholder': 'Capaian pembelajaran mata kuliah...'}),
            'teaching_method': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contoh: Ceramah, Diskusi, Project Based'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Gedung/Ruangan'}),
            'meeting_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://zoom.us/...'}),
            'is_online': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }



class AddAnnouncementForm(forms.ModelForm):
    class Meta:
        model = CourseAnnouncement
        fields = ['title', 'content', 'priority', 'is_pinned']
        widgets = {
            'priority': forms.Select(attrs={
                'class': 'select2 form-select', 
                'data-placeholder': 'Pilih Prioritas'
            }),
            'content': forms.Textarea(attrs={'rows': 4, 'style': 'height: 120px;'}),
            'is_pinned': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
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
    class Meta:
        model = CourseMaterial
        fields = ['agenda', 'title', 'material_type', 'video_url', 'file_attachment', 'text_content', 'duration_seconds', 'is_preview', 'order']
        widgets = {
            'agenda': forms.Select(attrs={'class': 'select2 form-select'}), # Pastikan template punya select2
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Judul Materi'}),
            'material_type': forms.Select(attrs={'class': 'select2 form-select'}),
            'video_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://youtube.com/...'}),
            'file_attachment': forms.FileInput(attrs={'class': 'form-control'}),
            'text_content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'duration_seconds': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Detik'}),
            'is_preview': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Urutan'}),
        }

    # PENTING: Filter Dropdown Section agar sesuai Course
    def __init__(self, *args, **kwargs):
        course_id = kwargs.pop('course_id', None) # Terima parameter course_id
        super().__init__(*args, **kwargs)
        
        if course_id:
            # PERBAIKAN DISINI: Ganti 'section' menjadi 'agenda'
            # Karena field di model dan di Meta bernama 'agenda'
            self.fields['agenda'].queryset = CourseAgenda.objects.filter(
                course_id=course_id
            ).order_by('agenda_date')
            
            # Opsional: Ubah label agar lebih jelas bagi user
            self.fields['agenda'].label = "Pilih Pertemuan / Agenda"


class CourseAssignmentForm(forms.ModelForm):
    class Meta:
        model = CourseAssignment
        fields = ['agenda', 'title', 'description', 'file_instruction', 'due_date', 'max_score', 'allow_late_submission']
        widgets = {
            'agenda': forms.Select(attrs={'class': 'select2 form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Judul Tugas'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Instruksi pengerjaan...'}),
            'file_instruction': forms.FileInput(attrs={'class': 'form-control'}),
            
            # Widget Datepicker Cantik
            'due_date': forms.DateTimeInput(attrs={
                'class': 'form-control flatpickr-datetime', 
                'placeholder': 'Pilih Batas Waktu'
            }),
            
            'max_score': forms.NumberInput(attrs={'class': 'form-control', 'value': 100}),
            'allow_late_submission': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        course_id = kwargs.pop('course_id', None)
        super().__init__(*args, **kwargs)
        # Filter Dropdown Agenda hanya milik Course ini
        if course_id:
            self.fields['agenda'].queryset = CourseAgenda.objects.filter(course_id=course_id).order_by('agenda_date')