from datetime import date
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
        fields = ['pessoa', 'cargo']
        widgets = {
            'pessoa': forms.Select(attrs={'class': 'form-select'}),
            'cargo': forms.TextInput(attrs={'class': 'form-control'}),
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
        widget=forms.TextInput(attrs={'class': 'form-control data-brasileira', 'placeholder': 'dd/mm/aaaa', 'autocomplete': 'off'})
    )
    data_proposta_comercial = forms.DateField(
        label='Data da proposta comercial',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control data-brasileira', 'placeholder': 'dd/mm/aaaa', 'autocomplete': 'off'})
    )
    empenho_id = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'id_empenho_id'})
    )

    contratada_endereco = forms.CharField(
        label='Endereço',
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'id_contratada_endereco'})
    )
    contratada_cidade = forms.CharField(
        label='Cidade',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'id_contratada_cidade'})
    )
    contratada_estado = forms.CharField(
        label='Estado',
        max_length=2,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'id_contratada_estado', 'placeholder': 'UF'})
    )

    novo_representante_nome = forms.CharField(
        label='Nome completo',
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'id_novo_representante_nome'})
    )
    novo_representante_cpf = forms.CharField(
        label='CPF',
        max_length=14,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'id_novo_representante_cpf', 'placeholder': '000.000.000-00'})
    )
    novo_representante_cargo = forms.CharField(
        label='Cargo/Função',
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'id_novo_representante_cargo'})
    )

    class Meta:
        model = Contrato
        fields = [
            'numero', 'compra', 'contratada',
            'representante_contratada',
            'modalidade_garantia', 'porcentual_garantia', 'valor_garantia', 'data'
        ]
        widgets = {
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
            'compra': forms.HiddenInput(),
            'contratada': forms.HiddenInput(),
            'representante_contratada': forms.Select(attrs={'class': 'form-select', 'id': 'id_representante_contratada'}),
            'modalidade_garantia': forms.Select(attrs={'class': 'form-select'}),
            'porcentual_garantia': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'valor_garantia': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'data': forms.TextInput(attrs={'class': 'form-control data-brasileira', 'placeholder': 'dd/mm/aaaa', 'autocomplete': 'off'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop('contratante', None)

        if not self.instance.pk:
            self.initial['data'] = date.today().isoformat()

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

        contratada = None
        if self.instance and self.instance.pk:
            contratada = self.instance.contratada
        elif self.initial.get('contratada'):
            try:
                contratada = Organizacao.objects.get(pk=self.initial['contratada'])
            except Organizacao.DoesNotExist:
                pass

        if contratada:
            self.fields['contratada_endereco'].initial = contratada.endereco or ''
            self.fields['contratada_cidade'].initial = contratada.cidade or ''
            self.fields['contratada_estado'].initial = contratada.estado or ''

            vinculos = VinculoOrganizacao.objects.filter(
                organizacao=contratada
            ).select_related('pessoa')
            self.fields['representante_contratada'].queryset = vinculos
        else:
            self.fields['representante_contratada'].queryset = VinculoOrganizacao.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        data_estimativa = cleaned_data.get('data_estimativa_orcamento')
        data_proposta = cleaned_data.get('data_proposta_comercial')

        if data_estimativa and data_proposta and data_proposta < data_estimativa:
            raise forms.ValidationError(
                'A data da proposta comercial deve ser igual ou posterior à data da estimativa do orçamento.'
            )

        return cleaned_data

    def _obter_ou_criar_contratada(self):
        contratada = self.cleaned_data.get('contratada')
        if not contratada:
            return None
        return contratada

    def _salvar_endereco_contratada(self, contratada):
        if not contratada:
            return
        endereco = self.cleaned_data.get('contratada_endereco', '').strip()
        cidade = self.cleaned_data.get('contratada_cidade', '').strip()
        estado = self.cleaned_data.get('contratada_estado', '').strip()
        contratada.endereco = endereco or None
        contratada.cidade = cidade or None
        contratada.estado = estado or None
        contratada.save(update_fields=['endereco', 'cidade', 'estado'])

    def _criar_representante_se_necessario(self, contratada):
        if not contratada:
            return None
        nome = self.cleaned_data.get('novo_representante_nome', '').strip()
        cpf = self.cleaned_data.get('novo_representante_cpf', '').strip()
        cargo = self.cleaned_data.get('novo_representante_cargo', '').strip()

        if not nome or not cpf:
            return None

        vinculo = VinculoOrganizacao.objects.filter(
            organizacao=contratada
        ).select_related('pessoa').first()
        if vinculo:
            return vinculo

        pessoa, _ = PessoaFisica.objects.get_or_create(
            cpf=cpf,
            defaults={'nome': nome}
        )
        if not pessoa.nome:
            pessoa.nome = nome
            pessoa.save(update_fields=['nome'])

        vinculo = VinculoOrganizacao.objects.create(
            organizacao=contratada,
            pessoa=pessoa,
            cargo=cargo or 'Representante Legal',
        )
        return vinculo

    def save(self, commit=True):
        contrato = super().save(commit=False)

        contratante = Organizacao.objects.filter(is_propria_instituicao=True).first()
        if contratante:
            contrato.contratante_id = contratante.pk

        if contrato.compra:
            compra = contrato.compra
            compra.valor_efetivo = self.cleaned_data.get('valor_efetivo')
            compra.data_estimativa_orcamento = self.cleaned_data.get('data_estimativa_orcamento')
            compra.data_proposta_comercial = self.cleaned_data.get('data_proposta_comercial')
            if commit:
                compra.save()

        if contrato.porcentual_garantia is not None:
            val_efetivo = self.cleaned_data.get('valor_efetivo')
            if val_efetivo is not None:
                from decimal import Decimal
                contrato.valor_garantia = val_efetivo * (contrato.porcentual_garantia / Decimal('100.00'))

        if commit:
            contratada = self._obter_ou_criar_contratada()

            if contratada:
                self._salvar_endereco_contratada(contratada)

                if not contrato.representante_contratada_id:
                    vinculo_novo = self._criar_representante_se_necessario(contratada)
                    if vinculo_novo:
                        contrato.representante_contratada_id = vinculo_novo.pk

            if not contrato.contratante_id and contratante:
                contrato.contratante_id = contratante.pk

            contrato.save()

            empenho_id = self.cleaned_data.get('empenho_id')
            if empenho_id:
                Empenho.objects.filter(id=empenho_id).update(contrato=contrato)

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

