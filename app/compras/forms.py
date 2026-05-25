from django import forms
from .models import Organizacao, PessoaFisica, Contrato, VinculoOrganizacao, Compra, Item

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
        fields = ['nome', 'cpf', 'email']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'cpf': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '000.000.000-00'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
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
    class Meta:
        model = Contrato
        fields = ['numero', 'compra', 'contratante', 'contratada', 'modalidade_garantia', 'valor_garantia', 'data']
        widgets = {
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
            'compra': forms.Select(attrs={'class': 'form-select'}),
            'contratante': forms.Select(attrs={'class': 'form-select'}),
            'contratada': forms.Select(attrs={'class': 'form-select'}),
            'modalidade_garantia': forms.Select(attrs={'class': 'form-select'}),
            'valor_garantia': forms.NumberInput(attrs={'class': 'form-control'}),
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

