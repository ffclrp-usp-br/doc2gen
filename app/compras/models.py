from django.core.validators import DecimalValidator, MinValueValidator, RegexValidator
from django.db import models
from django.db.models import Avg


class CentroGerencialGrupoOrcamentario:
    """Mapeamento de Centro Gerencial para Grupo Orçamentário."""
    
    MAPEAMENTO = {
        r"\ADM\INF": "59.003",
        r"\ADM\MANUT": "59.001",
        r"\ADM\RECEITA\PROJETOS RECEITA": "59.007",
        r"\ADM-SEG": "59.002",
        r"\ADM-TREINA": "59.004",
        r"\ADM\BIB": "59.131",
        r"\ADM\PROJETOS COP": "59.174",
    }
    
    PADRAO = "59.000"
    
    @classmethod
    def obter_grupo_orcamentario(cls, centro_gerencial: str) -> str:
        """
        Retorna o grupo orçamentário baseado no centro gerencial.
        Se não encontrar, retorna o padrão (59.000).
        """
        if not centro_gerencial:
            return cls.PADRAO
        
        centro_gerencial = centro_gerencial.strip()
        
        # Buscar correspondência exata
        for chave, valor in cls.MAPEAMENTO.items():
            if chave.lstrip('\\').lstrip('r') == centro_gerencial.lstrip('\\'):
                return valor
        
        # Se não encontrar, retornar padrão
        return cls.PADRAO


def demanda_validator(value):
    if not value or not RegexValidator(r'^\d+/\d{4}$')(value):
        return


class Compra(models.Model):
    MODALIDADE_CHOICES = [
        ('COMPRA DIRETA COM DISPUTA', 'COMPRA DIRETA COM DISPUTA'),
        ('COMPRA DIRETA SEM DISPUTA', 'COMPRA DIRETA SEM DISPUTA'),
        ('PREGÃO', 'PREGÃO'),
        ('INEXIGIBILIADE', 'INEXIGIBILIADE'),
        ('CONCURSO', 'CONCURSO'),
    ]

    TIPO_CHOICES = [
        ('FORNECIMENTO', 'FORNECIMENTO'),
        ('SERVIÇO', 'SERVIÇO'),
    ]

    AGENTE_CHOICES = [
        ('Lucas', 'Lucas'),
        ('Marcos', 'Marcos'),
        ('Melina', 'Melina'),
        ('Regina', 'Regina'),
    ]

    numero_compra = models.CharField(
        'Número de compra',
        max_length=14,
        validators=[RegexValidator(r'^\d+/\d{4}$', 'Formato deve ser n/yyyy')],
        unique=True,
    )
    numero_sei = models.CharField(
        'Número SEI',
        max_length=20,
        validators=[RegexValidator(r'^\d{3}\.\d{8}/\d{4}-\d{2}$', 'Formato deve ser 154.00009999/2026-99')],
        unique=True,
        blank=True,
    )
    objeto = models.CharField('Objeto', max_length=255, blank=True)
    modalidade = models.CharField('Modalidade', max_length=30, choices=MODALIDADE_CHOICES, blank=True)
    tipo = models.CharField('Tipo', max_length=20, choices=TIPO_CHOICES, blank=True)
    valor_estimado = models.DecimalField('Valor estimado', max_digits=14, decimal_places=2, validators=[MinValueValidator(0)], blank=True, null=True)
    nome_agente_contratacao = models.CharField('Agente de contratação', max_length=255, choices=AGENTE_CHOICES, blank=True)
    pdf_file = models.FileField('Arquivo PDF', upload_to='compras/', blank=True, null=True)

    def __str__(self):
        return f'{self.numero_compra} - {self.objeto[:50]}'


class Demanda(models.Model):
    numero_demanda = models.CharField(
        'Número da demanda',
        max_length=14,
        validators=[RegexValidator(r'^\d+/\d{4}$', 'Formato deve ser n/yyyy')],
        unique=True,
    )

    centro_gerencial = models.CharField('Centro Gerencial', max_length=50, blank=True)

    grupo_orcamentario = models.CharField(
        'Grupo orçamentário',
        max_length=8,
        validators=[RegexValidator(r'^\d{2}\.\d{3}$', 'Formato deve ser 59.001')],
        blank=True,
    )

    compra = models.ForeignKey(Compra, related_name='demandas', on_delete=models.CASCADE)

    def __str__(self):
        return self.numero



class Item(models.Model):

    numero_ordem = models.PositiveIntegerField('Ordem', editable=False, db_index=True)

    codigo_material = models.CharField(
        'Código material',
        max_length=14,
        blank=True,
    )

    codigo_compras_gov = models.CharField(
        'Código compras gov',
        max_length=14,
        blank=True,
    )

    codigo_contabiliza = models.CharField(
        'Código contabiliza',
        max_length=14,
        blank=True,
    )

    codigo_bem = models.CharField(
        'Código bem compras gov',
        max_length=14,
        blank=True,
    )


    descricao = models.CharField('Descrição', max_length=255, blank=True)
    
    item_despesa = models.CharField(
        'Item de despesa',
        max_length=255,
        validators=[RegexValidator(r'^\d+$', 'Deve ser apenas números')],
        blank=True,
    )
    
    valor_medio = models.DecimalField('Valor médio', max_digits=14, decimal_places=2, validators=[MinValueValidator(0)], blank=True, null=True)
    
    quantidade = models.PositiveIntegerField('Quantidade', blank=True, null=True)
    
    demanda = models.ForeignKey(Demanda, related_name='itens', on_delete=models.CASCADE)
    
    
    class Meta:
        unique_together = ('demanda', 'numero_ordem')
        ordering = ['demanda', 'numero_ordem']

    def save(self, *args, **kwargs):
        if not self.pk:
            last = Item.objects.filter(demanda=self.demanda).order_by('-numero_ordem').first()
            self.numero_ordem = 1 if last is None else last.numero_ordem + 1
        super().save(*args, **kwargs)

    def calcular_valor_medio(self):
        """Calcula e atualiza o valor médio baseado nas pesquisas associadas."""
        media = self.pesquisas.aggregate(avg_valor=Avg('valor_unitario'))['avg_valor']
        if media is not None:
            self.valor_medio = media
            self.save(update_fields=['valor_medio'])
        return media

    def __str__(self):
        return f'{self.demanda.compra.numero_compra} - Item {self.numero_ordem}'


class Pesquisa(models.Model):
    nome_fornecedor = models.CharField('Nome do fornecedor', max_length=255)
    valor_unitario = models.DecimalField('Valor unitário', max_digits=14, decimal_places=2, blank=True, null=True)

    codigo_contabiliza = models.CharField('Código contabiliza', max_length=14, blank=True)

    codigo_bem = models.CharField('Código bem compras gov', max_length=14, blank=True)

    descricao = models.CharField('Descrição', max_length=255, blank=True)
    item = models.ForeignKey(Item, related_name='pesquisas', on_delete=models.CASCADE, blank=True, null=True)
    compra = models.ForeignKey(Compra, related_name='pesquisas', on_delete=models.CASCADE)

    def __str__(self):
        if self.item:
            return f'{self.item.compra.numero_compra} - {self.nome_fornecedor}'
        else:
            return f'{self.compra.numero_compra} - {self.nome_fornecedor}'
