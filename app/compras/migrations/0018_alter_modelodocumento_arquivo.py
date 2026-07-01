from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compras', '0017_alter_compra_tipo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='modelodocumento',
            name='arquivo',
            field=models.FileField(max_length=255, upload_to='modelos_oficiais/', verbose_name='Arquivo'),
        ),
    ]
