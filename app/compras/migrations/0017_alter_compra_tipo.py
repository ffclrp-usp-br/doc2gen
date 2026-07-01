from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compras', '0016_modelodocumento'),
    ]

    operations = [
        migrations.AlterField(
            model_name='compra',
            name='tipo',
            field=models.CharField(blank=True, choices=[('FORNECIMENTO', 'FORNECIMENTO'), ('SERVIÇO_SEM_DEDICACAO_MAO_OBRA', 'SERVIÇO SEM DEDICAÇÃO DE MÃO DE OBRA'), ('SERVIÇO_COM_DEDICACAO_MAO_OBRA', 'SERVIÇO COM DEDICAÇÃO DE MÃO DE OBRA')], max_length=50, verbose_name='Tipo'),
        ),
    ]
