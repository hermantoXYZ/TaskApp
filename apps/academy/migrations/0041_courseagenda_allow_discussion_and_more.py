# Generated manually for allow_discussion flags

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academy', '0040_add_discussion_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='courseagenda',
            name='allow_discussion',
            field=models.BooleanField(
                default=True,
                help_text='Jika nonaktif, tidak ada thread diskusi otomatis untuk sesi ini di feed akademik.',
            ),
        ),
        migrations.AddField(
            model_name='coursematerial',
            name='allow_discussion',
            field=models.BooleanField(
                default=True,
                help_text='Jika nonaktif, tidak ada thread diskusi terkait materi ini.',
            ),
        ),
        migrations.AddField(
            model_name='courseassignment',
            name='allow_discussion',
            field=models.BooleanField(
                default=True,
                help_text='Jika nonaktif, tidak ada thread diskusi terkait tugas ini.',
            ),
        ),
    ]
