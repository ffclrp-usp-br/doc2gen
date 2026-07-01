from django.db import migrations


def migrar_tipo_servico(apps, schema_editor):
    Compra = apps.get_model('compras', 'Compra')
    ModeloDocumento = apps.get_model('compras', 'ModeloDocumento')

    Compra.objects.filter(tipo='SERVIÇO_SEM_DEDICACAO_MAO_OBRA').update(tipo='SERVICO_SEM_DEDICACAO_MAO_OBRA')
    Compra.objects.filter(tipo='SERVIÇO_COM_DEDICACAO_MAO_OBRA').update(tipo='SERVICO_COM_DEDICACAO_MAO_OBRA')

    ModeloDocumento.objects.filter(tipo='SERVIÇO_SEM_DEDICACAO_MAO_OBRA').update(tipo='SERVICO_SEM_DEDICACAO_MAO_OBRA')
    ModeloDocumento.objects.filter(tipo='SERVIÇO_COM_DEDICACAO_MAO_OBRA').update(tipo='SERVICO_COM_DEDICACAO_MAO_OBRA')


def reverso(apps, schema_editor):
    Compra = apps.get_model('compras', 'Compra')
    ModeloDocumento = apps.get_model('compras', 'ModeloDocumento')

    Compra.objects.filter(tipo='SERVICO_SEM_DEDICACAO_MAO_OBRA').update(tipo='SERVIÇO_SEM_DEDICACAO_MAO_OBRA')
    Compra.objects.filter(tipo='SERVICO_COM_DEDICACAO_MAO_OBRA').update(tipo='SERVIÇO_COM_DEDICACAO_MAO_OBRA')

    ModeloDocumento.objects.filter(tipo='SERVICO_SEM_DEDICACAO_MAO_OBRA').update(tipo='SERVIÇO_SEM_DEDICACAO_MAO_OBRA')
    ModeloDocumento.objects.filter(tipo='SERVICO_COM_DEDICACAO_MAO_OBRA').update(tipo='SERVIÇO_COM_DEDICACAO_MAO_OBRA')


class Migration(migrations.Migration):

    dependencies = [
        ('compras', '0019_alter_modelodocumento_categoria'),
    ]

    operations = [
        migrations.RunPython(migrar_tipo_servico, reverso),
    ]
