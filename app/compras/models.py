from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.db.models import Avg
from compras.utils.date_utils import DateUtils
from compras.utils.moeda_utils import MoedaUtils

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
        r"\ADM\PROJETOS ORÇAMENTO": "59.___",        
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
        
        # Normalizar para comparação (sem espaços, tudo maiúsculo, sem \ no início)
        centro_gerencial_norm = centro_gerencial.replace(" ", "").upper().lstrip('\\')
        
        # Buscar correspondência
        for chave, valor in cls.MAPEAMENTO.items():
            chave_norm = chave.replace(" ", "").upper().lstrip('\\')
            if chave_norm == centro_gerencial_norm:
                return valor
        
        # Se não encontrar, retornar padrão
        return cls.PADRAO


def demanda_validator(value):
    if not value:
        return
    RegexValidator(r'^\d+/\d{4}$', 'Formato deve ser n/yyyy')(value)


class Compra(models.Model):
    MODALIDADE_CHOICES = [
        ('Audiência Pública', 'Audiência Pública'),
        ('Concorrência', 'Concorrência'),
        ('Concurso', 'Concurso'),
        ('Credenciamento', 'Credenciamento'),
        ('Dispensa', 'Dispensa'),
        ('Inexigibilidade', 'Inexigibilidade'),
        ('Leilão', 'Leilão'),
        ('Manifestação de interesse', 'Manifestação de interesse'),
        ('Pré-Qualificação', 'Pré-Qualificação'),
        ('Pregão', 'Pregão'),
        ('Registro de Preços', 'Registro de Preços'),
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
        max_length=20,
        validators=[RegexValidator(r'^(\d{12}|\d+/\d{4})$', 'Formato deve ser 12 dígitos ou n/yyyy')],
        unique=True,
    )
    
    numero_comprasgov = models.CharField(
        'Número comprasgov',
        max_length=20,
        validators=[
            RegexValidator(
                r'^(\d{12}|\d+/\d{4})$',
                'Formato deve ser 12 dígitos ou n/yyyy'
            )
        ],
        unique=True,
        null=True,
        blank=True,
    )

    data_proposta_comercial = models.DateField(
        'Data da proposta comercial',
        null=True,
        blank=True
    )

    numero_sei = models.CharField(
        'Número SEI',
        max_length=20,
        validators=[RegexValidator(r'^\d{3}\.\d{8}/\d{4}-\d{2}$', 'Formato deve ser 154.00009999/2026-99')],
        unique=True,
        blank=True,
    )
    objeto = models.CharField('Objeto', max_length=255, blank=True)
    modalidade = models.CharField('Modalidade', max_length=255, choices=MODALIDADE_CHOICES, blank=True)
    tipo = models.CharField('Tipo', max_length=20, choices=TIPO_CHOICES, blank=True)
    valor_total_previsto = models.DecimalField('Valor total previsto', max_digits=14, decimal_places=2, validators=[MinValueValidator(0)], blank=True, null=True)
    valor_efetivo = models.DecimalField('Valor efetivo', max_digits=14, decimal_places=2, validators=[MinValueValidator(0)], blank=True, null=True)
    nome_agente_contratacao = models.CharField('Agente de contratação', max_length=255, choices=AGENTE_CHOICES, blank=True)
    data_estimativa_orcamento = models.DateField(
        'Data da proposta comercial',
        null=True,
        blank=True
    )
    disputa = models.BooleanField('Disputa', default=True)
    pdf_file = models.FileField('Arquivo PDF', upload_to='compras/', blank=True, null=True)

    @property
    def valor_total_previsto_brl(self):
        return MoedaUtils.to_brl(self.valor_total_previsto)
    
    @property
    def valor_efetivo_brl(self):
        return MoedaUtils.to_brl(self.valor_efetivo)

    @property
    def data_estimativa_orcamento_dmy(self):
        return DateUtils.to_dmy(self.data_estimativa_orcamento)

    @property
    def data_proposta_comercial_dmy(self):
        return DateUtils.to_dmy(self.data_proposta_comercial)

    
    @property
    def valor_garantia_brl(self):
        return MoedaUtils.to_brl(self.valor_garantia)
    
    @property
    def valor_efetivo_brl_extenso(self):
        return MoedaUtils.valor_por_extenso(self.valor_efetivo)


    def __str__(self):
        return f'{self.numero_compra} - {self.objeto[:50]}'


class Demanda(models.Model):
    numero_demanda = models.CharField(
        'Número da demanda',
        max_length=20,
        validators=[RegexValidator(r'^(\d{12}|\d+/\d{4})$', 'Formato deve ser 12 dígitos ou n/yyyy')],
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
        null=True,
    )

    codigo_comprasgov = models.CharField(
        'Código compras gov',
        max_length=14,
        blank=True,
        null=True,
    )

    codigo_contabiliza = models.CharField(
        'Código contabiliza',
        max_length=14,
        blank=True,
        null=True,
    )

    codigo_bem = models.CharField(
        'Código bem compras gov',
        max_length=14,
        blank=True,
        null=True,
    )


    descricao = models.CharField('Descrição', max_length=255, blank=True, null=True)
    
    item_despesa = models.CharField(
        'Item de despesa',
        max_length=255,
        validators=[RegexValidator(r'^\d+$', 'Deve ser apenas números')],
        blank=True,
        null=True,
    )
    
    valor_medio = models.DecimalField('Valor médio', max_digits=14, decimal_places=2, validators=[MinValueValidator(0)], blank=True, null=True)
    
    quantidade = models.PositiveIntegerField('Quantidade', blank=True, null=True)

    unidade_medida = models.CharField('Unidade de medida', max_length=255, blank=True, null=True)
    
    demanda = models.ForeignKey(Demanda, related_name='itens', on_delete=models.CASCADE)
    
    
    class Meta:
        unique_together = ('demanda', 'numero_ordem')
        ordering = ['demanda', 'numero_ordem']

    def save(self, *args, **kwargs):
        if not self.pk and not self.numero_ordem:
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

    @property
    def valor_medio_brl(self):
        return MoedaUtils.to_brl(self.valor_medio)


    def __str__(self):
        return f'{self.demanda.compra.numero_compra} - Item {self.numero_ordem}'


class Pesquisa(models.Model):
    nome_fornecedor = models.CharField('Nome do fornecedor', max_length=255)
    valor_unitario = models.DecimalField('Valor unitário', max_digits=14, decimal_places=2, blank=True, null=True) 

    codigo_contabiliza = models.CharField('Código contabiliza', max_length=14, blank=True, null=True)

    codigo_bem = models.CharField('Código bem compras gov', max_length=14, blank=True, null=True)

    descricao = models.CharField('Descrição', max_length=255, blank=True, null=True)
    item = models.ForeignKey(Item, related_name='pesquisas', on_delete=models.CASCADE, blank=True, null=True)
    compra = models.ForeignKey(Compra, related_name='pesquisas', on_delete=models.CASCADE)

    @property
    def valor_unitario_brl(self):
        return MoedaUtils.to_brl(self.valor_unitario)


    def __str__(self):
        if self.item:
            return f'{self.item.compra.numero_compra} - {self.nome_fornecedor}'
        else:
            return f'{self.compra.numero_compra} - {self.nome_fornecedor}'
        


class PessoaFisica(models.Model):

    nome = models.CharField(max_length=255)

    cpf = models.CharField(
        max_length=14,
        unique=True
    )

    def __str__(self):
        return self.nome


class Organizacao(models.Model):

    nome = models.CharField(
        'Nome/Razão Social',
        max_length=255
    )

    nome_fantasia = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    cnpj = models.CharField(
        max_length=18,
        unique=True
    )

    endereco = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    cidade = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    estado = models.CharField(
        max_length=2,
        blank=True,
        null=True
    )

    is_propria_instituicao = models.BooleanField(
        default=False
    )

    def __str__(self):
        return self.nome


class Contrato(models.Model):

    MODALIDADE_GARANTIA_CHOICES = (
        ('CAUCAO_DINHEIRO', 'Caução em dinheiro'),
        ('CAUCAO_TITULOS', 'Caução em títulos públicos'),
        ('SEGURO_GARANTIA', 'Seguro-garantia'),
        ('FIANCA_BANCARIA', 'Fiança bancária'),
        ('TITULO_CAPITALIZACAO', 'Título de capitalização'),
    )

    numero = models.CharField(
        max_length=50
    )

    compra = models.ForeignKey(
        'Compra',
        on_delete=models.CASCADE,
        related_name='contratos',
        null=True,
        blank=True
    )

    contratante = models.ForeignKey(
        Organizacao,
        on_delete=models.PROTECT,
        related_name='contratos_como_contratante'
    )

    contratada = models.ForeignKey(
        Organizacao,
        on_delete=models.PROTECT,
        related_name='contratos_como_contratada'
    )

    modalidade_garantia = models.CharField(
        max_length=30,
        choices=MODALIDADE_GARANTIA_CHOICES,
        blank=True,
        null=True
    )

    porcentual_garantia = models.DecimalField(
        'Porcentual de garantia',
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True
    )

    valor_garantia = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True
    )

    data = models.DateField(
        blank=True,
        null=True
    )

    @property
    def valor_garantia_brl(self):
        return MoedaUtils.to_brl(self.valor_garantia)


    @property
    def data_por_extenso(self):
        return DateUtils.data_por_extenso(self.data)

    def clean(self):
        super().clean()
        if self.porcentual_garantia is not None and self.compra and self.compra.valor_efetivo is not None:
            from decimal import Decimal
            self.valor_garantia = self.compra.valor_efetivo * (self.porcentual_garantia / Decimal('100.00'))

    def save(self, *args, **kwargs):
        if self.porcentual_garantia is not None and self.compra and self.compra.valor_efetivo is not None:
            from decimal import Decimal
            self.valor_garantia = self.compra.valor_efetivo * (self.porcentual_garantia / Decimal('100.00'))
        super().save(*args, **kwargs)

    def __str__(self):
        return self.numero


class VinculoOrganizacao(models.Model):

    organizacao = models.ForeignKey(
        Organizacao,
        on_delete=models.CASCADE,
        related_name='vinculos'
    )

    pessoa = models.ForeignKey(
        PessoaFisica,
        on_delete=models.CASCADE,
        related_name='vinculos'
    )

    cargo = models.CharField(
        max_length=255
    )

    responsavel_assinatura = models.BooleanField(
        default=False
    )

    ativo = models.BooleanField(
        default=True
    )

    def __str__(self):
        return f'{self.pessoa} - {self.organizacao}'


class Empenho(models.Model):

    numero = models.CharField(
        'Número da NE',
        max_length=20,
    )

    data_empenho = models.DateField(
        'Data do Empenho',
        null=True,
        blank=True,
    )

    dotacao = models.CharField(
        'Dotação',
        max_length=20,
        blank=True,
        null=True,
    )

    grupo = models.CharField(
        'Grupo',
        max_length=255,
        blank=True,
        null=True,
    )

    unidade = models.CharField(
        'Unidade',
        max_length=255,
        blank=True,
        null=True,
    )

    fonte_recurso = models.CharField(
        'Fonte de Recurso',
        max_length=100,
        blank=True,
        null=True,
    )

    funcional_programatica = models.CharField(
        'Funcional Programática',
        max_length=255,
        blank=True,
        null=True,
    )

    categoria_economica = models.CharField(
        'Categoria Econômica',
        max_length=100,
        blank=True,
        null=True,
    )

    grupo_despesa = models.CharField(
        'Grupo de Despesa',
        max_length=100,
        blank=True,
        null=True,
    )

    modalidade = models.CharField(
        'Modalidade',
        max_length=100,
        blank=True,
        null=True,
    )

    elemento = models.CharField(
        'Elemento',
        max_length=100,
        blank=True,
        null=True,
    )

    item = models.CharField(
        'Item',
        max_length=100,
        blank=True,
        null=True,
    )

    organizacao = models.ForeignKey(
        Organizacao,
        on_delete=models.PROTECT,
        related_name='empenhos',
    )

    contrato = models.OneToOneField(
        Contrato,
        on_delete=models.CASCADE,
        related_name='empenho',
        null=True,
        blank=True,
    )

    def __str__(self):
        return f'{self.numero} - {self.organizacao}'