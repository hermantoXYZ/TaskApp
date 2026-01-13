from django import forms
from django.utils import timezone

tgl_now = timezone.now()

from .models import (User, UserProdi, UserDosen)
from apps.academy.models import Prodi

class formProfile(forms.ModelForm):
    class Meta:
        model = UserProdi
        fields = [    
            'telp',
            'gender',
            'photo',
        ]
        widgets = {
            'gender': forms.Select(
                choices=[
                    ('Laki-laki', 'Laki-laki'),
                    ('Perempuan', 'Perempuan'),
                ],
                attrs={'class': 'form-control'}
            ),
            'telp': forms.NumberInput(attrs={'class': 'form-control'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }

        
class formUserEdit(forms.ModelForm):
    class Meta:
        model = UserProdi
        fields = [
            'prodi',
            'telp',
            'gender',
            'photo',
        ]
        widgets = {
            'gender': forms.Select(
                choices=[
                    ('Laki-laki', 'Laki-laki'),
                    ('Perempuan', 'Perempuan'),
                ],
                attrs={'class': 'form-control'}
            ),
            'telp': forms.NumberInput(attrs={'class': 'form-control'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }

    # Form field for 'prodi' using ModelChoiceField
    prodi = forms.ModelChoiceField(
        queryset=Prodi.objects.all(),  # This gets the available 'Prodi' options
        empty_label="Pilih Prodi",  # This is the placeholder option in the dropdown
        widget=forms.Select(attrs={'class': 'form-control'}),  # Using the same form-control class for consistency
        label="Program Studi"
    )


