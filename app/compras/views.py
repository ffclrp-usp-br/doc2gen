from decimal import Decimal, InvalidOperation

from django import forms
from django.urls import reverse_lazy
from django.db.models import Prefetch
from django.views.generic import CreateView, ListView, UpdateView, DeleteView, FormView

from .models import Compra, Demanda, Item, Pesquisa, CentroGerencialGrupoOrcamentario

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
            dados = ParserService.processar_pdf(arquivo, tipo='grade')
        except Exception as exc:
            form.add_error('arquivo', str(exc))
            return self.form_invalid(form)

        if dados.get('tipo') != 'grade' or not dados.get('numero_compra'):
            form.add_error('arquivo', 'O PDF não corresponde a um documento de grade válido.')
            return self.form_invalid(form)

        compra, created = Compra.objects.get_or_create(
            numero_compra=dados['numero_compra'],
            defaults={
                'numero_sei': dados.get('numero_sei') or '',
                'objeto': dados.get('objeto') or '',
                'modalidade': dados.get('modalidade') or '',
                'tipo': dados.get('tipo_compra') or '',
                'valor_estimado': self._parse_decimal(dados.get('valor_total_previsto') or None),
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
        numero_demanda = compra.numero_compra
        print(f"\n[DEBUG] Criando demanda padrão:")
        print(f"  numero_demanda: '{numero_demanda}'")
        print(f"  comprimento: {len(numero_demanda)} caracteres")
        print(f"  bytes: {numero_demanda.encode('utf-8')}")
        
        demanda, created = Demanda.objects.get_or_create(
            numero_demanda=numero_demanda,
            compra=compra,
            defaults={
                'centro_gerencial': '',
                'grupo_orcamentario': '',
            }
        )
        
        if created:
            print(f"  ✓ Demanda criada com sucesso")
        else:
            print(f"  ℹ Demanda já existe")
        
        return demanda

    def _get_or_create_item(self, demanda, item_data):
        bem = item_data.get('codigo_bem', '') or ''
        bec = item_data.get('codigo_bec', '') or ''
        
        descricao = item_data.get('descricao', '') or ''
        valor_previsto = self._parse_decimal(item_data.get('valor_unitario_previsto'))

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
            codigo_contabiliza=item_data.get('codigo_contabiliza', ''),
            codigo_bem=bem,
            descricao=descricao,
            item_despesa=item_data.get('item_despesa', ''),
            valor_medio=valor_previsto,
            quantidade=item_data.get('quantidade'),
        )

    def _processar_compra(self, compra, dados):
        # Para importação de compra, criar Item (que precisa de Demanda) e Pesquisa
        itens = dados.get('itens', [])
        if not itens:
            return

        demanda_padrao = None

        for item_data in itens:
            numero_demanda = item_data.get('numero_demanda')
            centro_gerencial = item_data.get('centro_gerencial')

            if numero_demanda:
                grupo_orcamentario = CentroGerencialGrupoOrcamentario.obter_grupo_orcamentario(centro_gerencial)
                demanda, created = Demanda.objects.get_or_create(
                    numero_demanda=numero_demanda,
                    compra=compra,
                    defaults={
                        'centro_gerencial': centro_gerencial or '',
                        'grupo_orcamentario': grupo_orcamentario or '',
                    }
                )
                if not created:
                    updated = False
                    if not demanda.centro_gerencial and centro_gerencial:
                        demanda.centro_gerencial = centro_gerencial
                        updated = True
                    if not demanda.grupo_orcamentario and demanda.centro_gerencial:
                        demanda.grupo_orcamentario = CentroGerencialGrupoOrcamentario.obter_grupo_orcamentario(demanda.centro_gerencial)
                        updated = True
                    if updated:
                        demanda.save()
            else:
                if not demanda_padrao:
                    demanda_padrao = self._get_demanda_padrao(compra)
                demanda = demanda_padrao

            # Criar Item para cada item_data
            item = self._get_or_create_item(demanda, item_data)

            # Criar Pesquisas para cada cotação do item
            for cotacao in item_data.get('cotacoes', []):
                fornecedor = cotacao.get('empresa')
                if not fornecedor:
                    continue

                valor_unitario = self._parse_decimal(cotacao.get('valor_unitario'))
                pesquisa, created = Pesquisa.objects.get_or_create(
                    compra=compra,
                    item=item,
                    nome_fornecedor=fornecedor.strip(),
                    defaults={
                        'valor_unitario': valor_unitario,
                        'codigo_contabiliza': item_data.get('codigo_contabiliza', ''),
                        'codigo_bem': item_data.get('codigo_bem', ''),
                        'descricao': item_data.get('descricao', ''),
                    },
                )
                if not created and valor_unitario is not None and pesquisa.valor_unitario is None:
                    pesquisa.valor_unitario = valor_unitario
                    pesquisa.save()
                elif not created:
                    # Atualizar campos codigo_contabiliza, codigo_bem e descricao se estiverem vazios
                    updated = False
                    if not pesquisa.codigo_contabiliza and item_data.get('codigo_contabiliza'):
                        pesquisa.codigo_contabiliza = item_data.get('codigo_contabiliza', '')
                        updated = True
                    if not pesquisa.codigo_bem and item_data.get('codigo_bem'):
                        pesquisa.codigo_bem = item_data.get('codigo_bem', '')
                        updated = True
                    if not pesquisa.descricao and item_data.get('descricao'):
                        pesquisa.descricao = item_data.get('descricao', '')
                        updated = True
                    if updated:
                        pesquisa.save()


class DemandaImportPDFView(FormView):
    template_name = 'compras/demanda_pdf_upload.html'
    form_class = UploadDemandaPDFForm

    def _extrair_grupo_orcamentario(self, valor: str) -> str:
        """Extrai a cadeia de caracteres imediatamente anterior ao abre parênteses '('."""
        if not valor:
            return ''
        # Remove espaços e extrai tudo antes do '('
        valor_strip = valor.strip()
        if '(' in valor_strip:
            return valor_strip.split('(')[0].strip()
        return valor_strip

    def _processar_demanda(self, compra, dados):
        """Processa uma demanda individual."""

        if dados.get('tipo') != 'demanda' or not dados.get('numero_demanda'):
            return None, 'O PDF não corresponde a um documento de demanda válido.'

        # Verificar se os itens foram extraídos corretamente
        itens = dados.get('itens', [])
        if not itens:
            return None, 'Não foi possível extrair os itens da demanda. Verifique se o PDF segue o formato esperado: "número número número número número número número descrição".'

        # Verificar se pelo menos um item tem os campos obrigatórios
        itens_validos = [item for item in itens if item.get('codigo_material') or item.get('codigo_compras_gov') or item.get('codigo_contabiliza') or item.get('codigo_bem')]
        if not itens_validos:
            return None, 'Os itens da demanda não possuem os códigos necessários. Verifique se o PDF segue o formato esperado: "número número número número número número número descrição".'

        centro_gerencial_valor = self._extrair_grupo_orcamentario(dados.get('centro_gerencial', ''))
        grupo_orcamentario_valor = CentroGerencialGrupoOrcamentario.obter_grupo_orcamentario(centro_gerencial_valor)
        
        demanda, created = Demanda.objects.get_or_create(
            numero_demanda=dados['numero_demanda'],
            compra=compra,
            defaults={
                'centro_gerencial': centro_gerencial_valor,
                'grupo_orcamentario': grupo_orcamentario_valor,
            }
        )

        if not created:
            updated = False
            if not demanda.centro_gerencial and centro_gerencial_valor:
                demanda.centro_gerencial = centro_gerencial_valor
                updated = True
            if not demanda.grupo_orcamentario:
                demanda.grupo_orcamentario = CentroGerencialGrupoOrcamentario.obter_grupo_orcamentario(demanda.centro_gerencial or centro_gerencial_valor)
                updated = True
            if updated:
                demanda.save()

        for item_data in dados.get('itens', []):
            if not Item.objects.filter(
                demanda=demanda,
                codigo_contabiliza=item_data.get('codigo_contabiliza', ''),
                codigo_bem=item_data.get('codigo_bem', ''),
            ).exists():
                # Converte lista de item_despesa para string separada por vírgula
                item_despesa_list = item_data.get('item_despesa', [])
                item_despesa_str = ' '.join(item_despesa_list) if isinstance(item_despesa_list, list) else ''
                
                
                item = Item.objects.create(
                    demanda=demanda,
                    codigo_material=item_data.get('codigo_material', ''),
                    codigo_compras_gov=item_data.get('codigo_compras_gov', ''),
                    codigo_contabiliza=item_data.get('codigo_contabiliza', ''),
                    codigo_bem=item_data.get('codigo_bem', ''),
                    descricao=item_data.get('descricao', ''),
                    item_despesa=item_despesa_str,
                    valor_medio=None,
                    quantidade=item_data.get('quantidade'),
                )
                
                # Associar pesquisas existentes ao item baseado em codigo_bem e codigo_contabiliza
                self._associar_pesquisas_ao_item(item, compra)

        return demanda, None
    
    def _associar_pesquisas_ao_item(self, item, compra):
        """Associa pesquisas existentes ao item baseado em codigo_bem e codigo_contabiliza."""
        filter_kwargs = {'compra': compra, 'item': None}
        
        if item.codigo_bem and item.codigo_contabiliza:
            # Se ambos os campos existem, buscar por ambos
            pesquisas = Pesquisa.objects.filter(
                compra=compra,
                item__isnull=True,
                codigo_bem=item.codigo_bem,
                codigo_contabiliza=item.codigo_contabiliza,
            )
        elif item.codigo_bem:
            # Se apenas codigo_bem existe, buscar por este
            pesquisas = Pesquisa.objects.filter(
                compra=compra,
                item__isnull=True,
                codigo_bem=item.codigo_bem,
            )
        elif item.codigo_contabiliza:
            # Se apenas codigo_contabiliza existe, buscar por este
            pesquisas = Pesquisa.objects.filter(
                compra=compra,
                item__isnull=True,
                codigo_contabiliza=item.codigo_contabiliza,
            )
        else:
            # Se nenhum dos campos existe, não fazer associação
            return
        
        # Atualizar as pesquisas encontradas para associar ao item
        pesquisas.update(item=item)
        
        # Calcular e atualizar o valor médio do item
        item.calcular_valor_medio()

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

    def form_invalid(self, form):
        # Garantir que o contexto seja passado mesmo com erros de validação
        context = self.get_context_data(form=form)
        return self.render_to_response(context)

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
        return Item.objects.filter(demanda__compra_id=compra_id).prefetch_related('pesquisas').order_by('id', 'numero_ordem')

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
        return Pesquisa.objects.filter(compra_id=compra_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['compra'] = Compra.objects.get(id=self.kwargs.get('compra_id'))
        return context

class ItemCreateView(CreateView):
    model = Item
    fields = ['demanda', 'codigo_material', 'codigo_compras_gov', 'codigo_contabiliza', 'codigo_bem', 'descricao', 'item_despesa', 'quantidade', 'valor_medio']
    template_name = 'compras/item_form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['compra_id'] = self.kwargs.get('compra_id')
        return ctx

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
    fields = ['demanda', 'codigo_material', 'codigo_compras_gov', 'codigo_contabiliza', 'codigo_bem', 'descricao', 'item_despesa', 'quantidade', 'valor_medio']
    template_name = 'compras/item_form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['compra_id'] = self.object.demanda.compra_id
        return ctx

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
    fields = ['nome_fornecedor', 'valor_unitario', 'codigo_contabiliza', 'codigo_bem', 'descricao']
    template_name = 'compras/pesquisa_form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['compra'] = self.object.compra
        return ctx

    def get_success_url(self):
        return reverse_lazy('pesquisa_list', kwargs={'compra_id': self.object.compra_id})


class PesquisaDeleteView(DeleteView):
    model = Pesquisa
    template_name = 'compras/pesquisa_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('pesquisa_list', kwargs={'compra_id': self.object.compra_id})



