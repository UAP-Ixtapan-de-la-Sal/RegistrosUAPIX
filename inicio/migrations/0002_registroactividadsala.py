import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inicio', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='RegistroActividadSala',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('categoria', models.CharField(choices=[('clase', 'Clase'), ('evento', 'Evento')], max_length=10)),
                ('tipo_actividad', models.CharField(choices=[('regular', 'Clase regular'), ('taller', 'Taller'), ('conferencia', 'Conferencia'), ('clase', 'Clase')], max_length=20)),
                ('pertenece_al_plantel', models.BooleanField(blank=True, null=True)),
                ('nombre_actividad', models.CharField(max_length=150)),
                ('responsable', models.CharField(max_length=150)),
                ('grupo', models.CharField(blank=True, max_length=30)),
                ('materia', models.CharField(blank=True, max_length=150)),
                ('fecha', models.DateField()),
                ('hora_inicio', models.TimeField()),
                ('hora_fin', models.TimeField()),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('creado_por', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='actividades_sala', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'registro de actividad de sala',
                'verbose_name_plural': 'registros de actividades de sala',
                'ordering': ('fecha', 'hora_inicio'),
            },
        ),
    ]
