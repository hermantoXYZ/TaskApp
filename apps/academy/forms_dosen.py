


from django import forms
from apps.academy.models import UserDosen, Book, BookCategory


class DosenProfileForm(forms.ModelForm):
    class Meta:
        model = UserDosen
        # Field yang bisa diedit dosen. 
        # NIP (Username) dan Prodi biasanya tidak boleh diedit sendiri.
        fields = [
            'nidn', 'status_kepegawaian', 'telp', 'gender',
            'tempat_lahir', 'tgl_lahir', 
            'pangkat', 'golongan', 'jafung', 
            'bidang_keahlian', 'photo'
        ]
        
        widgets = {
            'nidn': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nomor Induk Dosen Nasional'}),
            'status_kepegawaian': forms.Select(attrs={'class': 'form-select'}),
            'telp': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '08...'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'tempat_lahir': forms.TextInput(attrs={'class': 'form-control'}),
            'tgl_lahir': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}), # Type date agar muncul kalender
            'pangkat': forms.Select(attrs={'class': 'form-select'}),
            'golongan': forms.Select(attrs={'class': 'form-select'}),
            'jafung': forms.Select(attrs={'class': 'form-select'}),
            'bidang_keahlian': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contoh: Ekonomi Makro, AI, dll'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'author', 'category', 'description', 'cover', 'embed_url', 'source_url']
        widgets = {
            # Gunakan class 'form-control' agar sinkron dengan template layout Anda
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'author': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'cover': forms.FileInput(attrs={'class': 'form-control'}),
            'embed_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Link preview (G-Drive)'}),
            'source_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Link download/original'}),
        }

class BookCategoryForm(forms.ModelForm):
    class Meta:
        model = BookCategory
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama Kategori'}),
        }