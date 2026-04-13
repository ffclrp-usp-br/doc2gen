from decimal import Decimal, InvalidOperation

from django import forms
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView, DeleteView, FormView

from .models import Compra, Demanda, Item, Pesquisa

from services.parser_service import ParserService


class MultipleFileInput(forms.FileInput):
    """Custom widget that supports multiple file uploads."""
    def __init__(self, attrs=None):
        super().__init__(attrs)
    
    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['attrs']['multiple'] = True
        return context


class CompraListView(ListView):
    model = Compra
    template_name = 'compras/compra_list.html'
    context_object_name = 'compras'

    def get_queryset(self):
        return Compra.objects.prefetch_related('demandas__itens__pesquisas')


class UploadPDFForm(forms.Form):
    arquivo = forms.FileField(label='Arquivo PDF')


class UploadDemandaPDFForm(forms.Form):
    arquivos = forms.FileField(
        label='Arquivos PDF',
        widget=MultipleFileInput(),
        help_text='Você pode selecionar múltiplos arquivos de demanda de uma vez.'
    )


class CompraImportPDFView(FormView):
    template_name = 'compras/compra_pdf_upload.html'
    form_class = UploadPDFForm
    success_url = reverse_lazy('compra_list')

    def form_valid(self, form):
        arquivo = form.cleaned_data['arquivo']
        try:
            dados = ParserService.processar_pdf(arquivo, tipo='compra')
        except Exception as exc:
            form.add_error('arquivo', str(exc))
            return self.form_invalid(form)

        if dados.get('tipo') != 'compra' or not dados.get('numero_compra'):
            form.add_error('arquivo', 'O PDF não corresponde a um documento de compra válido.')
            return self.form_invalid(form)

        compra, created = Compra.objects.get_or_create(
            numero_compra=dados['numero_compra'],
            defaults={
                'numero_sei': dados.get('numero_sei') or '',
                'objeto': dados.get('objeto') or '',
                'modalidade': dados.get('modalidade') or '',
                'tipo': dados.get('tipo_compra') or '',
                'valor_estimado': None,
                'nome_agente_contratacao': '',
            }
        )

        if not created:
            updated = False
            for field, value in {
                'numero_sei': dados.get('numero_sei', ''),
                'objeto': dados.get('objeto', ''),
                'modalidade': dados.get('modalidade', ''),
                'tipo': dados.get('tipo_compra', ''),
            }.items():
                if value and not getattr(compra, field):
                    setattr(compra, field, value)
                    updated = True
            if updated:
                compra.save()

        self._processar_compra(compra, dados)

        return super().form_valid(form)

    def _parse_decimal(self, valor):
        if valor is None:
            return None

        if isinstance(valor, Decimal):
            return valor

        valor_str = str(valor).strip()
        if not valor_str:
            return None

        valor_str = valor_str.replace('.', '').replace(',', '.')
        try:
            return Decimal(valor_str)
        except (InvalidOperation, TypeError):
            return None

    def _get_demanda_padrao(self, compra):
        demanda, _ = Demanda.objects.get_or_create(
            numero_demanda=compra.numero_compra,
            compra=compra,
            defaults={
                'centro_despesa': '',
                'grupo_orcamentario': '',
            }
        )
        return demanda

    def _get_or_create_item(self, demanda, item_data):
        bem = item_data.get('bem', '') or ''
        bec = item_data.get('bec', '') or ''
        descricao = item_data.get('descricao', '') or ''
        valor_previsto = self._parse_decimal(item_data.get('valor_previsto'))

        queryset = Item.objects.filter(demanda=demanda)
        if bem:
            queryset = queryset.filter(codigo_bem=bem)
        if bec:
            queryset = queryset.filter(codigo_compras_gov=bec)

        item = queryset.first()
        if item:
            updated = False
            if descricao and not item.descricao:
                item.descricao = descricao
                updated = True
            if valor_previsto is not None and item.valor_medio is None:
                item.valor_medio = valor_previsto
                updated = True
            if updated:
                item.save()
            return item

        return Item.objects.create(
            demanda=demanda,
            codigo_compras_gov=bec,
            codigo_contabiliza='',
            codigo_bem=bem,
            descricao=descricao,
            item_despesa='',
            valor_medio=valor_previsto,
        )

    def _processar_compra(self, compra, dados):
        # Sempre criar uma demanda padrão para a compra
        demanda = self._get_demanda_padrao(compra)

        itens = dados.get('itens', [])
        if not itens:
            return

        for item_data in itens:
            item = self._get_or_create_item(demanda, item_data)
            for cotacao in item_data.get('cotacoes', []):
                fornecedor = cotacao.get('empresa')
                if not fornecedor:
                    continue

                valor_unitario = self._parse_decimal(cotacao.get('valor_unitario'))
                pesquisa, created = Pesquisa.objects.get_or_create(
                    item=item,
                    nome_fornecedor=fornecedor.strip(),
                    defaults={
                        'valor_unitario': valor_unitario,
                        'compra': compra,
                    },
                )
                if not created and valor_unitario is not None and pesquisa.valor_unitario is None:
                    pesquisa.valor_unitario = valor_unitario
                    pesquisa.save()


class DemandaImportPDFView(FormView):
    template_name = 'compras/demanda_pdf_upload.html'
    form_class = UploadDemandaPDFForm

    def _extrair_grupo_orcamentario(self, valor: str) -> str:
        """Extrai apenas os primeiros 8 caracteres do grupo orçamentário."""
        if not valor:
            return ''
        # Remove espaços e limita a 8 caracteres
        return valor.strip()[:8]

    def _processar_demanda(self, compra, dados):
        """Processa uma demanda individual."""
        if dados.get('tipo') != 'demanda' or not dados.get('numero_demanda'):
            return None, 'O PDF não corresponde a um documento de demanda válido.'

        demanda, created = Demanda.objects.get_or_create(
            numero_demanda=dados['numero_demanda'],
            compra=compra,
            defaults={
                'centro_despesa': dados.get('unidade_despesa', ''),
                'grupo_orcamentario': self._extrair_grupo_orcamentario(dados.get('centro_gerencial', '')),
            }
        )

        if not created:
            updated = False
            if not demanda.centro_despesa and dados.get('unidade_despesa'):
                demanda.centro_despesa = dados.get('unidade_despesa')
                updated = True
            if not demanda.grupo_orcamentario and dados.get('centro_gerencial'):
                demanda.grupo_orcamentario = self._extrair_grupo_orcamentario(dados.get('centro_gerencial'))
                updated = True
            if updated:
                demanda.save()

        for item_data in dados.get('itens', []):
            if not Item.objects.filter(
                demanda=demanda,
                codigo_contabiliza=item_data.get('contabiliza', ''),
                codigo_bem=item_data.get('cod_bem', ''),
            ).exists():
                Item.objects.create(
                    demanda=demanda,
                    codigo_compras_gov=item_data.get('cod_mat', ''),
                    codigo_contabiliza=item_data.get('contabiliza', ''),
                    codigo_bem=item_data.get('cod_bem', ''),
                    descricao='',
                    item_despesa='',
                    valor_medio=None,
                )

        return demanda, None

    def form_valid(self, form):
        compra = Compra.objects.get(pk=self.kwargs.get('pk'))
        arquivos = self.request.FILES.getlist('arquivos')
        
        if not arquivos:
            form.add_error('arquivos', 'Selecione pelo menos um arquivo.')
            return self.form_invalid(form)

        demandas_processadas = []
        erros = []

        for arquivo in arquivos:
            try:
                dados = ParserService.processar_pdf(arquivo, tipo='demanda')
                demanda, erro = self._processar_demanda(compra, dados)
                if erro:
                    erros.append(f'{arquivo.name}: {erro}')
                else:
                    demandas_processadas.append(demanda.numero_demanda)
            except Exception as exc:
                erros.append(f'{arquivo.name}: {str(exc)}')

        if erros:
            form.add_error('arquivos', 'Erros ao processar: ' + '; '.join(erros))
            if not demandas_processadas:
                return self.form_invalid(form)

        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('compra_update', kwargs={'pk': self.kwargs.get('pk')})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['compra'] = Compra.objects.get(pk=self.kwargs.get('pk'))
        ctx['demandas_existentes'] = Demanda.objects.filter(compra_id=self.kwargs.get('pk'))
        return ctx


class CompraCreateView(CreateView):
    model = Compra
    fields = ['numero_compra', 'numero_sei', 'objeto', 'modalidade', 'tipo', 'valor_estimado', 'nome_agente_contratacao']
    template_name = 'compras/compra_form.html'
    success_url = reverse_lazy('compra_list')


class CompraUpdateView(UpdateView):
    model = Compra
    fields = ['numero_compra', 'numero_sei', 'objeto', 'modalidade', 'tipo', 'valor_estimado', 'nome_agente_contratacao']
    template_name = 'compras/compra_form.html'
    success_url = reverse_lazy('compra_list')


class CompraDeleteView(DeleteView):
    model = Compra
    success_url = reverse_lazy('compra_list')
    template_name = 'compras/compra_confirm_delete.html'


class ItemListView(ListView):
    model = Item
    template_name = 'compras/item_list.html'
    context_object_name = 'itens'

    def get_queryset(self):
        compra_id = self.kwargs.get('compra_id')
        return Item.objects.filter(demanda__compra_id=compra_id).order_by('numero_ordem')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['compra'] = Compra.objects.get(pk=self.kwargs.get('compra_id'))
        return ctx

class PesquisaListView(ListView):
    model = Pesquisa
    template_name = 'compras/pesquisa_list.html'
    context_object_name = 'pesquisas'

    def get_queryset(self):
        compra_id = self.kwargs.get('compra_id')
        return Pesquisa.objects.filter(item__demanda__compra_id=compra_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['compra'] = Compra.objects.get(id=self.kwargs.get('compra_id'))
        return context

class ItemCreateView(CreateView):
    model = Item
    fields = ['demanda', 'codigo_compras_gov', 'codigo_contabiliza', 'codigo_bem', 'descricao', 'item_despesa', 'valor_medio']
    template_name = 'compras/item_form.html'

    def form_valid(self, form):
        compra_id = self.kwargs.get('compra_id')
        # Ensure the demanda belongs to the compra
        if form.instance.demanda.compra_id != compra_id:
            form.add_error('demanda', 'Demanda deve pertencer à compra selecionada.')
            return self.form_invalid(form)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('item_list', kwargs={'compra_id': self.kwargs.get('compra_id')})

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        compra_id = self.kwargs.get('compra_id')
        form.fields['demanda'].queryset = Demanda.objects.filter(compra_id=compra_id)
        return form


class ItemUpdateView(UpdateView):
    model = Item
    fields = ['demanda', 'codigo_compras_gov', 'codigo_contabiliza', 'codigo_bem', 'descricao', 'item_despesa', 'valor_medio']
    template_name = 'compras/item_form.html'

    def form_valid(self, form):
        # Ensure the demanda belongs to the compra
        if form.instance.demanda.compra_id != self.object.demanda.compra_id:
            form.add_error('demanda', 'Demanda deve pertencer à compra selecionada.')
            return self.form_invalid(form)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('item_list', kwargs={'compra_id': self.object.demanda.compra_id})

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['demanda'].queryset = Demanda.objects.filter(compra=self.object.demanda.compra)
        return form


class ItemDeleteView(DeleteView):
    model = Item
    template_name = 'compras/item_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('item_list', kwargs={'compra_id': self.object.demanda.compra_id})


class PesquisaUpdateView(UpdateView):
    model = Pesquisa
    fields = ['nome_fornecedor', 'valor_unitario']
    template_name = 'compras/pesquisa_form.html'

    def get_success_url(self):
        return reverse_lazy('pesquisa_list', kwargs={'compra_id': self.object.item.demanda.compra_id})


class PesquisaDeleteView(DeleteView):
    model = Pesquisa
    template_name = 'compras/pesquisa_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('pesquisa_list', kwargs={'compra_id': self.object.item.demanda.compra_id})



