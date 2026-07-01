import os
import shutil
from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


def migrar_templates_existentes(apps, schema_editor):
    ModeloDocumento = apps.get_model('compras', 'ModeloDocumento')

    templates_dir = os.path.join(settings.BASE_DIR, 'compras', 'templates_docs')
    destino_dir = os.path.join(settings.MEDIA_ROOT, 'modelos_oficiais')
    os.makedirs(destino_dir, exist_ok=True)

    modelos = [
        {
            'modalidade': 'Pregão',
            'categoria': 'PRINCIPAL',
            'tipo': None,
            'arquivo_nome': 'CONFERENCIA_PREGAO.docx',
        },
        {
            'modalidade': 'Dispensa',
            'categoria': 'PRINCIPAL',
            'tipo': None,
            'arquivo_nome': 'CONFERENCIA_CD_COM_DISPUTA.docx',
        },
        {
            'modalidade': 'Dispensa',
            'categoria': 'PRINCIPAL',
            'tipo': None,
            'arquivo_nome': 'CONFERENCIA_CD_SEM_DISPUTA.docx',
        },
    ]

    for m in modelos:
        origem = os.path.join(templates_dir, m['arquivo_nome'])
        if not os.path.exists(origem):
            continue

        destino = os.path.join(destino_dir, m['arquivo_nome'])
        shutil.copy2(origem, destino)

        ModeloDocumento.objects.create(
            modalidade=m['modalidade'],
            categoria=m['categoria'],
            tipo=m['tipo'],
            arquivo=os.path.join('modelos_oficiais', m['arquivo_nome']),
        )


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('compras', '0015_remove_vinculoorganizacao_ativo_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ModeloDocumento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('modalidade', models.CharField(choices=[('Audiência Pública', 'Audiência Pública'), ('Concorrência', 'Concorrência'), ('Concurso', 'Concurso'), ('Credenciamento', 'Credenciamento'), ('Dispensa', 'Dispensa'), ('Inexigibilidade', 'Inexigibilidade'), ('Leilão', 'Leilão'), ('Manifestação de interesse', 'Manifestação de interesse'), ('Pré-Qualificação', 'Pré-Qualificação'), ('Pregão', 'Pregão'), ('Registro de Preços', 'Registro de Preços')], max_length=100, verbose_name='Modalidade')),
                ('categoria', models.CharField(choices=[('PRINCIPAL', 'Documento Principal'), ('TR', 'Termo de Referência'), ('CONTRATO', 'Contrato')], max_length=10, verbose_name='Categoria')),
                ('tipo', models.CharField(blank=True, choices=[('FORNECIMENTO', 'FORNECIMENTO'), ('SERVIÇO_SEM_DEDICACAO_MAO_OBRA', 'SERVIÇO SEM DEDICAÇÃO DE MÃO DE OBRA'), ('SERVIÇO_COM_DEDICACAO_MAO_OBRA', 'SERVIÇO COM DEDICAÇÃO DE MÃO DE OBRA')], max_length=50, null=True, verbose_name='Tipo')),
                ('arquivo', models.FileField(upload_to='modelos_oficiais/', verbose_name='Arquivo')),
                ('data_atualizacao', models.DateTimeField(auto_now=True, verbose_name='Data da última atualização')),
            ],
            options={
                'db_table': 'modelo_documento',
                'unique_together': {('modalidade', 'categoria', 'tipo')},
            },
        ),
        migrations.RunPython(migrar_templates_existentes, migrations.RunPython.noop),
    ]
