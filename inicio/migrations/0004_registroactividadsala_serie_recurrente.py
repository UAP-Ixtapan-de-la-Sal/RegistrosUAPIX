from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inicio', '0003_registroactividadsala_numero_cuenta_docente'),
    ]

    operations = [
        migrations.AddField(
            model_name='registroactividadsala',
            name='serie_recurrente',
            field=models.UUIDField(blank=True, db_index=True, null=True),
        ),
    ]
