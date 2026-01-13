from import_export import resources, fields
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from .models import UserMhs, UserDosen
from apps.academy.models import Prodi

class UserDsnResource(resources.ModelResource):
    password = fields.Field(column_name='password', attribute='password')
    prodi = fields.Field(column_name='prodi', attribute='userdsn.prodi', saves_null_values=False)

    class Meta:
        model = User
        import_id_fields = ('username',)
        fields = ('username', 'email', 'first_name', 'last_name', 'is_active', 'password', 'prodi', 'telp', 'status_kepegawaian', 'tempat_lahir', 'tgl_lahir', 'nidn', 'pangkat', 'golongan', 'jafung', 'bidang_keahlian')

    def before_import_row(self, row, **kwargs):
        if 'password' in row and row['password']:
            row['password'] = make_password(row['password'])

    def after_import_row(self, row, row_result, **kwargs):
        if row_result.import_type in ('new', 'update'):
            user = User.objects.get(username=row['username'])
            userdsn, created = UserDosen.objects.get_or_create(nip=user)
            
            # Mengonversi string prodi menjadi instance Prodi
            prodi_name = row.get('prodi')
            if prodi_name:
                nama_prodi, strata = prodi_name.rsplit(" - ", 1)

                try:
                    # Mencari prodi berdasarkan nama_prodi dan strata
                    prodi_instance = Prodi.objects.get(nama_prodi=nama_prodi, strata=strata)
                    userdsn.prodi = prodi_instance
                except ObjectDoesNotExist:
                    # Jika tidak ditemukan, raise error agar impor gagal
                    raise ValidationError(f"Prodi '{prodi_name}' tidak ditemukan di database. Tambahkan prodi terlebih dahulu.")
                
            userdsn.status_kepegawaian = row.get('status_kepegawaian', '')
            userdsn.telp = row.get('telp', '')
            userdsn.photo = row.get('photo', None)  # Pastikan 'photo' sudah sesuai dengan field di model Anda
            userdsn.gender = row.get('gender', '')  # Sama seperti 'photo', pastikan field ini ada dan valid
            userdsn.tempat_lahir = row.get('tempat_lahir', '')
            userdsn.tgl_lahir = row.get('tgl_lahir', '')
            userdsn.nidn = row.get('nidn', '')
            userdsn.pangkat = row.get('pangkat', '')
            userdsn.golongan = row.get('golongan', '')
            userdsn.jafung = row.get('jafung', '')
            userdsn.bidang_keahlian = row.get('bidang_keahlian', '')
            userdsn.save()


class UserMhsResource(resources.ModelResource):
    password = fields.Field(column_name='password', attribute='password')
    prodi = fields.Field(column_name='prodi', attribute='usermhs.prodi', saves_null_values=False)

    class Meta:
        model = User
        import_id_fields = ('username',)
        fields = ('username', 'email', 'first_name', 'last_name', 'is_active', 'password', 'prodi', 'telp', 'tgl_masuk')

    def before_import_row(self, row, **kwargs):
        if 'password' in row and row['password']:
            row['password'] = make_password(row['password'])

    def after_import_row(self, row, row_result, **kwargs):
        if row_result.import_type in ('new', 'update'):
            user = User.objects.get(username=row['username'])
            usermhs, created = UserMhs.objects.get_or_create(nim=user)
            
            # Mengonversi string prodi menjadi instance Prodi
            from django.core.exceptions import ObjectDoesNotExist, ValidationError

            prodi_name = row.get('prodi')
            if prodi_name:
                nama_prodi, strata = prodi_name.rsplit(" - ", 1)

                try:
                    # Mencari prodi berdasarkan nama_prodi dan strata
                    prodi_instance = Prodi.objects.get(nama_prodi=nama_prodi, strata=strata)
                    usermhs.prodi = prodi_instance
                except ObjectDoesNotExist:
                    # Jika tidak ditemukan, raise error agar impor gagal
                    raise ValidationError(f"Prodi '{prodi_name}' tidak ditemukan di database. Tambahkan prodi terlebih dahulu.")
                
            
                usermhs.telp = row.get('telp', '')
                usermhs.tgl_masuk = row.get('tgl_masuk', '')
                usermhs.photo = row.get('photo', None)
                usermhs.gender = row.get('gender', '')
                usermhs.tempat_lahir = row.get('tempat_lahir', '')
                usermhs.tgl_lahir = row.get('tgl_lahir', None)
                usermhs.penasehat_akademik = row.get('penasehat_akademik', None)
                usermhs.save()