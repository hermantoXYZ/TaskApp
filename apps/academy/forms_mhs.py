from django import forms
from .models import UserMhs


class MhsProfileForm(forms.ModelForm):
    class Meta:
        model = UserMhs
        # Field yang boleh diedit oleh mahasiswa
        fields = ['telp', 'gender', 'tempat_lahir', 'tgl_lahir', 'alamat', 'photo']
        
        widgets = {
            'telp': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '08xxxxxxxx'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'tempat_lahir': forms.TextInput(attrs={'class': 'form-control'}),
            'tgl_lahir': forms.DateInput(attrs={'class': 'form-control flatpickr-date', 'type': 'date'}),
            'alamat': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'telp': 'Nomor Telepon/WA',
            'tgl_lahir': 'Tanggal Lahir',
        }