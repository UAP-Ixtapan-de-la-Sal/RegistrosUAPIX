from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inicio', '0002_registroactividadsala'),
    ]

    operations = [
        migrations.AddField(
            model_name='registroactividadsala',
            name='numero_cuenta_docente',
            field=models.CharField(blank=True, max_length=20),
        ),
    ]
