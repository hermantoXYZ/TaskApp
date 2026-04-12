# Diskusi terikat konten = opt-in (default False). Hapus thread otomatis lama
# dan set semua konten ke allow_discussion=False agar tidak ter-generate lagi
# sampai dosen centang saat simpan.

from django.db import migrations, models
from django.db.models import Q


def discussion_opt_in_cleanup(apps, schema_editor):
    CourseDiscussion = apps.get_model('academy', 'CourseDiscussion')
    CourseAgenda = apps.get_model('academy', 'CourseAgenda')
    CourseMaterial = apps.get_model('academy', 'CourseMaterial')
    CourseAssignment = apps.get_model('academy', 'CourseAssignment')

    # Hapus thread yang terikat agenda/materi/tugas (bukan diskusi manual: ketiga FK null).
    CourseDiscussion.objects.filter(
        Q(agenda_id__isnull=False) | Q(material_id__isnull=False) | Q(assignment_id__isnull=False)
    ).delete()

    CourseAgenda.objects.update(allow_discussion=False)
    CourseMaterial.objects.update(allow_discussion=False)
    CourseAssignment.objects.update(allow_discussion=False)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('academy', '0042_alter_courseagenda_allow_discussion_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='courseagenda',
            name='allow_discussion',
            field=models.BooleanField(
                default=False,
                help_text='Centang saat menyimpan jika sesi ini boleh punya thread di beranda diskusi.',
            ),
        ),
        migrations.AlterField(
            model_name='courseassignment',
            name='allow_discussion',
            field=models.BooleanField(
                default=False,
                help_text='Centang saat menyimpan jika tugas ini boleh punya thread di beranda diskusi.',
            ),
        ),
        migrations.AlterField(
            model_name='coursematerial',
            name='allow_discussion',
            field=models.BooleanField(
                default=False,
                help_text='Centang saat menyimpan jika materi ini boleh punya thread di beranda diskusi.',
            ),
        ),
        migrations.RunPython(discussion_opt_in_cleanup, noop_reverse),
    ]
