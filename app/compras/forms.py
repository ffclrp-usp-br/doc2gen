from django import forms
from .models import Organizacao, PessoaFisica, Contrato, VinculoOrganizacao, Compra, Item, Empenho

class OrganizacaoForm(forms.ModelForm):
    class Meta:
        model = Organizacao
        fields = ['nome', 'nome_fantasia', 'cnpj', 'endereco', 'cidade', 'estado', 'is_propria_instituicao']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'nome_fantasia': forms.TextInput(attrs={'class': 'form-control'}),
            'cnpj': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00.000.000/0000-00'}),
            'endereco': forms.TextInput(attrs={'class': 'form-control'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control'}),
            'estado': forms.TextInput(attrs={'class': 'form-control'}),
            'is_propria_instituicao': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class PessoaFisicaForm(forms.ModelForm):
    class Meta:
        model = PessoaFisica
        fields = ['nome', 'cpf']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'cpf': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '000.000.000-00'}),
        }

class VinculoOrganizacaoForm(forms.ModelForm):
    class Meta:
        model = VinculoOrganizacao
        fields = ['pessoa', 'cargo', 'responsavel_assinatura', 'ativo']
        widgets = {
            'pessoa': forms.Select(attrs={'class': 'form-select'}),
            'cargo': forms.TextInput(attrs={'class': 'form-control'}),
            'responsavel_assinatura': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ContratoForm(forms.ModelForm):
    valor_efetivo = forms.DecimalField(
        label='Valor efetivo',
        max_digits=14,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    data_estimativa_orcamento = forms.DateField(
        label='Data da estimativa do orçamento',
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    data_proposta_comercial = forms.DateField(
        label='Data da proposta comercial',
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    empenho_id = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'id_empenho_id'})
    )

    class Meta:
        model = Contrato
        fields = [
            'numero', 'compra', 'contratante', 'contratada',
            'modalidade_garantia', 'porcentual_garantia', 'valor_garantia', 'data'
        ]
        widgets = {
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
            'compra': forms.Select(attrs={'class': 'form-select'}),
            'contratante': forms.Select(attrs={'class': 'form-select'}),
            'contratada': forms.Select(attrs={'class': 'form-select'}),
            'modalidade_garantia': forms.Select(attrs={'class': 'form-select'}),
            'porcentual_garantia': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'valor_garantia': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'data': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtra contratante para exibir apenas as próprias instituições
        proprias = Organizacao.objects.filter(is_propria_instituicao=True)
        self.fields['contratante'].queryset = proprias
        
        # Se houver apenas uma própria instituição, já deixa selecionada por padrão
        if proprias.count() == 1:
            self.fields['contratante'].initial = proprias.first()

        # Preenche os valores iniciais da Compra relacionada se existir
        if self.instance and self.instance.pk and self.instance.compra:
            compra = self.instance.compra
            self.fields['valor_efetivo'].initial = compra.valor_efetivo
            self.fields['data_estimativa_orcamento'].initial = compra.data_estimativa_orcamento
            self.fields['data_proposta_comercial'].initial = compra.data_proposta_comercial
        elif self.initial.get('compra'):
            try:
                compra = Compra.objects.get(pk=self.initial['compra'])
                self.fields['valor_efetivo'].initial = compra.valor_efetivo
                self.fields['data_estimativa_orcamento'].initial = compra.data_estimativa_orcamento
                self.fields['data_proposta_comercial'].initial = compra.data_proposta_comercial
            except Compra.DoesNotExist:
                pass

    def save(self, commit=True):
        contrato = super().save(commit=False)
        if contrato.compra:
            compra = contrato.compra
            compra.valor_efetivo = self.cleaned_data.get('valor_efetivo')
            compra.data_estimativa_orcamento = self.cleaned_data.get('data_estimativa_orcamento')
            compra.data_proposta_comercial = self.cleaned_data.get('data_proposta_comercial')
            if commit:
                compra.save()

        # Recalcula valor_garantia com base no valor_efetivo atualizado
        if contrato.porcentual_garantia is not None:
            val_efetivo = self.cleaned_data.get('valor_efetivo')
            if val_efetivo is not None:
                from decimal import Decimal
                contrato.valor_garantia = val_efetivo * (contrato.porcentual_garantia / Decimal('100.00'))

        if commit:
            contrato.save()
            empenho_id = self.cleaned_data.get('empenho_id')
            if empenho_id:
                Empenho.objects.filter(id=empenho_id, contrato__isnull=True).update(contrato=contrato)
        return contrato


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = [
            'demanda', 'codigo_material', 'codigo_comprasgov', 'codigo_contabiliza',
            'codigo_bem', 'descricao', 'item_despesa', 'unidade_medida', 'quantidade', 'valor_medio'
        ]
        widgets = {
            'demanda': forms.Select(attrs={'class': 'form-select'}),
            'codigo_material': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo_comprasgov': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo_contabiliza': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo_bem': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
            'item_despesa': forms.TextInput(attrs={'class': 'form-control'}),
            'unidade_medida': forms.TextInput(attrs={'class': 'form-control'}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control'}),
            'valor_medio': forms.NumberInput(attrs={'class': 'form-control'}),
        }

