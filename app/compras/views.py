from django.contrib.auth.mixins import LoginRequiredMixin
from decimal import Decimal, InvalidOperation
from django import forms
from django.urls import reverse_lazy, reverse
from django.db.models import Prefetch
from django.views.generic import CreateView, ListView, UpdateView, DeleteView, FormView

from .models import Compra, Demanda, Item, Pesquisa, CentroGerencialGrupoOrcamentario, Organizacao, PessoaFisica, Contrato, VinculoOrganizacao, Empenho
from .forms import OrganizacaoForm, PessoaFisicaForm, ContratoForm, VinculoOrganizacaoForm, ItemForm, CompraForm

from services.parser_service import ParserService
from django.http import FileResponse, HttpResponseRedirect
from django.views import View
from django.shortcuts import render, get_object_or_404, redirect
from .services.kit_conferencia import KitConferenciaService
from compras.utils.moeda_utils import MoedaUtils


class MultipleFileInput(forms.FileInput):
    """Custom widget that supports multiple file uploads."""
    def __init__(self, attrs=None):
        super().__init__(attrs)
    
    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['attrs']['multiple'] = True
        return context


class CompraListView(LoginRequiredMixin,ListView):
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

        objeto = dados.get('objeto') or self._inferir_objeto_do_arquivo(arquivo.name)

        compra, created = Compra.objects.get_or_create(
            numero_compra=dados['numero_compra'],
            defaults={
                'numero_sei': dados.get('numero_sei') or '',
                'objeto': objeto,
                'modalidade': dados.get('modalidade') or '',
                'tipo': dados.get('tipo_compra') or '',
                'valor_total_previsto': self._parse_decimal(dados.get('valor_total_previsto') or None),
                'nome_agente_contratacao': '',
            }
        )

        if not created:
            updated = False
            for field, value in {
                'numero_sei': dados.get('numero_sei', ''),
                'objeto': objeto,
                'modalidade': dados.get('modalidade', ''),
                'tipo': dados.get('tipo_compra', ''),
            }.items():
                if value and not getattr(compra, field):
                    setattr(compra, field, value)
                    updated = True
            if updated:
                compra.save()

        self._processar_compra(compra, dados)

        return HttpResponseRedirect(reverse('compra_update', kwargs={'pk': compra.pk}))

    def _inferir_objeto_do_arquivo(self, nome_arquivo):
        """Infere o objeto da compra a partir do nome do arquivo.

        Exemplo: '67335_serviço_manutenção_equipamentos_agrícolas.pdf'
              -> 'Serviço manutenção equipamentos agrícolas'
        """
        import re as _re
        # Remove extensão .pdf
        nome = nome_arquivo.rsplit('.', 1)[0] if '.' in nome_arquivo else nome_arquivo
        # Remove número(s) inicial(is) seguido(s) de underscore
        nome = _re.sub(r'^\d+_', '', nome)
        # Substitui underscores por espaços
        nome = nome.replace('_', ' ')
        # Primeira letra maiúscula, restante preservado
        return nome[0].upper() + nome[1:] if nome else ''

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

    def _get_demanda_padrao(self, compra, centro_gerencial=None):
        numero_demanda = compra.numero_compra
        print(f"\n[DEBUG] Criando demanda padrão:")
        print(f"  numero_demanda: '{numero_demanda}'")
        print(f"  comprimento: {len(numero_demanda)} caracteres")
        print(f"  bytes: {numero_demanda.encode('utf-8')}")
        
        grupo_orcamentario = CentroGerencialGrupoOrcamentario.obter_grupo_orcamentario(centro_gerencial) if centro_gerencial else ''

        demanda, created = Demanda.objects.get_or_create(
            numero_demanda=numero_demanda,
            compra=compra,
            defaults={
                'centro_gerencial': centro_gerencial or '',
                'grupo_orcamentario': grupo_orcamentario,
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
            queryset = queryset.filter(codigo_comprasgov=bec)

        item = queryset.first()
        if item:
            updated = False
            if descricao and not item.descricao:
                item.descricao = descricao
                updated = True
            if valor_previsto is not None and item.valor_medio is None:
                item.valor_medio = valor_previsto
                updated = True
            unidade_medida = item_data.get('unidade_medida', '')
            if unidade_medida and not item.unidade_medida:
                item.unidade_medida = unidade_medida
                updated = True
            if updated:
                item.save()
            return item

        return Item.objects.create(
            demanda=demanda,
            numero_ordem=item_data.get('item'),
            codigo_comprasgov=None, #TODO: aqui seria interessante puxar do compras GOV.BR
            codigo_contabiliza=item_data.get('codigo_contabiliza', ''),
            codigo_bem=bem,
            descricao=descricao,
            item_despesa=item_data.get('item_despesa', ''),
            unidade_medida=item_data.get('unidade_medida', ''),
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
                    demanda_padrao = self._get_demanda_padrao(compra, centro_gerencial)
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

# Determinar tipo da compra com base na unidade de medida dos itens
        self._definir_tipo_compra(compra)

    def _definir_tipo_compra(self, compra):
        """Define o tipo da compra com base na unidade de medida dos itens.
        
        Se algum item tiver unidade de medida contendo 'SERVIÇO',
        o tipo é definido como 'SERVIÇO'. Caso contrário, 'FORNECIMENTO'.
        """
        itens = Item.objects.filter(demanda__compra=compra)
        tem_servico = itens.filter(
            unidade_medida__icontains='SERVIÇO'
        ).exists()

        compra.tipo = 'SERVIÇO' if tem_servico else 'FORNECIMENTO'
        compra.save(update_fields=['tipo'])
class DemandaImportPDFView(LoginRequiredMixin, FormView):
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
        itens_validos = [item for item in itens if item.get('codigo_material') or item.get('codigo_comprasgov') or item.get('codigo_contabiliza') or item.get('codigo_bem')]
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
                    numero_ordem=item_data.get('item'),
                    codigo_material=item_data.get('codigo_material', ''),
                    codigo_comprasgov=item_data.get('codigo_comprasgov', ''),
                    codigo_contabiliza=item_data.get('codigo_contabiliza', ''),
                    codigo_bem=item_data.get('codigo_bem', ''),
                    descricao=item_data.get('descricao', ''),
                    item_despesa=item_despesa_str,
                    unidade_medida=item_data.get('unidade', ''),
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


class CompraCreateView(LoginRequiredMixin, CreateView):
    model = Compra
    fields = ['numero_compra', 'numero_sei', 'objeto', 'modalidade', 'tipo', 'valor_total_previsto', 'nome_agente_contratacao', 'disputa']
    template_name = 'compras/compra_form.html'
    success_url = reverse_lazy('compra_list')


class CompraUpdateView(LoginRequiredMixin, UpdateView):
    model = Compra
    form_class = CompraForm
    template_name = 'compras/compra_form.html'

    def get_success_url(self):
        return reverse('item_list', kwargs={'compra_id': self.object.pk})


class CompraDeleteView(LoginRequiredMixin, DeleteView):
    model = Compra
    success_url = reverse_lazy('compra_list')
    template_name = 'compras/compra_confirm_delete.html'


class ItemListView(LoginRequiredMixin, ListView):
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

class PesquisaListView(LoginRequiredMixin,ListView):
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

class ItemCreateView(LoginRequiredMixin, CreateView):
    model = Item
    form_class = ItemForm
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


class ItemUpdateView(LoginRequiredMixin, UpdateView):
    model = Item
    form_class = ItemForm
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


class ItemDeleteView(LoginRequiredMixin, DeleteView):
    model = Item
    template_name = 'compras/item_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('item_list', kwargs={'compra_id': self.object.demanda.compra_id})


class PesquisaUpdateView(LoginRequiredMixin, UpdateView):
    model = Pesquisa
    fields = ['nome_fornecedor', 'valor_unitario', 'codigo_contabiliza', 'codigo_bem', 'descricao']
    template_name = 'compras/pesquisa_form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['compra'] = self.object.compra
        return ctx

    def get_success_url(self):
        return reverse_lazy('pesquisa_list', kwargs={'compra_id': self.object.compra_id})


class PesquisaDeleteView(LoginRequiredMixin, DeleteView):
    model = Pesquisa
    template_name = 'compras/pesquisa_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('pesquisa_list', kwargs={'compra_id': self.object.compra_id})



class KitConferenciaView(LoginRequiredMixin, View):
    def get(self, request, pk):
        try:
            zip_io, filename = KitConferenciaService.generate_kit(pk)
            response = FileResponse(zip_io, content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        except Exception as e:
            # For now, just return a simple error. In a real app, maybe redirect with message.
            from django.http import HttpResponse
            return HttpResponse(f"Erro ao gerar kit: {str(e)}", status=500)


# --- Views para Organização ---

class OrganizacaoListView(LoginRequiredMixin, ListView):
    model = Organizacao
    template_name = 'compras/organizacao_list.html'
    context_object_name = 'organizacoes'

class OrganizacaoCreateView(LoginRequiredMixin, CreateView):
    model = Organizacao
    form_class = OrganizacaoForm
    template_name = 'compras/organizacao_form.html'
    success_url = reverse_lazy('organizacao_list')

class OrganizacaoUpdateView(LoginRequiredMixin, UpdateView):
    model = Organizacao
    form_class = OrganizacaoForm
    template_name = 'compras/organizacao_form.html'
    success_url = reverse_lazy('organizacao_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['vinculos'] = self.object.vinculos.all()
        ctx['pessoas'] = PessoaFisica.objects.all()
        return ctx

class OrganizacaoDeleteView(LoginRequiredMixin, DeleteView):
    model = Organizacao
    success_url = reverse_lazy('organizacao_list')
    template_name = 'compras/organizacao_confirm_delete.html'


# --- Views para Pessoa Física ---

class PessoaFisicaListView(LoginRequiredMixin, ListView):
    model = PessoaFisica
    template_name = 'compras/pessoa_list.html'
    context_object_name = 'pessoas'

class PessoaFisicaCreateView(LoginRequiredMixin, CreateView):
    model = PessoaFisica
    form_class = PessoaFisicaForm
    template_name = 'compras/pessoa_form.html'
    success_url = reverse_lazy('pessoa_list')

class PessoaFisicaUpdateView(LoginRequiredMixin, UpdateView):
    model = PessoaFisica
    form_class = PessoaFisicaForm
    template_name = 'compras/pessoa_form.html'
    success_url = reverse_lazy('pessoa_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['vinculos'] = self.object.vinculos.all()
        ctx['organizacoes'] = Organizacao.objects.all()
        return ctx


class PessoaFisicaDeleteView(LoginRequiredMixin, DeleteView):
    model = PessoaFisica
    success_url = reverse_lazy('pessoa_list')
    template_name = 'compras/pessoa_confirm_delete.html'


# --- Views para Contrato ---

class ContratoListView(LoginRequiredMixin, ListView):
    model = Contrato
    template_name = 'compras/contrato_list.html'
    context_object_name = 'contratos'

    def get_queryset(self):
        return Contrato.objects.select_related('compra', 'contratante', 'contratada')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['tem_contratante'] = Organizacao.objects.filter(is_propria_instituicao=True).exists()
        return ctx

class ContratoCreateView(LoginRequiredMixin, CreateView):
    model = Contrato
    form_class = ContratoForm
    template_name = 'compras/contrato_form.html'

    def get_success_url(self):
        return reverse_lazy('contrato_update', kwargs={'pk': self.object.pk})

    def get_initial(self):
        initial = super().get_initial()
        compra_id = self.request.GET.get('compra_id')
        if compra_id:
            initial['compra'] = compra_id
        return initial

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['contratada_info'] = None
        ctx['compra_info'] = None
        ctx['tem_contratante'] = Organizacao.objects.filter(is_propria_instituicao=True).exists()
        ctx['vinculos_contratada'] = VinculoOrganizacao.objects.none()
        return ctx

class ContratoUpdateView(LoginRequiredMixin, UpdateView):
    model = Contrato
    form_class = ContratoForm
    template_name = 'compras/contrato_form.html'

    def get_success_url(self):
        return reverse_lazy('contrato_update', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        ctx['tem_contratante'] = Organizacao.objects.filter(is_propria_instituicao=True).exists()

        compra = self.object.compra
        if compra:
            ctx['compra_info'] = {
                'id': compra.id,
                'numero': compra.numero_compra,
                'objeto': compra.objeto or '',
            }
        else:
            ctx['compra_info'] = None

        contratada = self.object.contratada
        if contratada:
            ctx['contratada_info'] = {
                'id': contratada.id,
                'nome': contratada.nome,
                'cnpj': contratada.cnpj,
            }
            vinculos = VinculoOrganizacao.objects.filter(
                organizacao=contratada
            ).select_related('pessoa')
            ctx['vinculos_contratada'] = vinculos
        else:
            ctx['contratada_info'] = None
            ctx['vinculos_contratada'] = VinculoOrganizacao.objects.none()

        return ctx

class ContratoDeleteView(LoginRequiredMixin, DeleteView):
    model = Contrato
    success_url = reverse_lazy('contrato_list')
    template_name = 'compras/contrato_confirm_delete.html'


# Helper for AJAX
from django.http import JsonResponse

def buscar_organizacao_cnpj(request):
    cnpj = request.GET.get('cnpj', '').replace('.', '').replace('/', '').replace('-', '')
    organizacao = Organizacao.objects.filter(cnpj__icontains=cnpj).first()
    if organizacao:
        return JsonResponse({
            'success': True,
            'id': organizacao.id,
            'nome': organizacao.nome,
            'cnpj': organizacao.cnpj,
            'endereco': organizacao.endereco or '',
            'cidade': organizacao.cidade or '',
            'estado': organizacao.estado or '',
            'tem_endereco': bool(organizacao.endereco and organizacao.cidade and organizacao.estado),
        })
    return JsonResponse({'success': False})

def buscar_compra_detalhes_ajax(request):
    compra_id = request.GET.get('compra_id')
    if compra_id:
        compra = Compra.objects.filter(id=compra_id).first()
        if compra:
            return JsonResponse({
                'success': True,
                'valor_efetivo': str(compra.valor_efetivo) if compra.valor_efetivo is not None else '',
                'data_estimativa_orcamento': compra.data_estimativa_orcamento.strftime('%Y-%m-%d') if compra.data_estimativa_orcamento else '',
                'data_proposta_comercial': compra.data_proposta_comercial.strftime('%Y-%m-%d') if compra.data_proposta_comercial else '',
            })
    return JsonResponse({'success': False})

def gerenciar_vinculos_ajax(request, org_id):
    organizacao = get_object_or_404(Organizacao, id=org_id)

    if request.method == 'DELETE':
        vinculo_id = request.GET.get('vinculo_id')
        if not vinculo_id:
            return JsonResponse({'success': False, 'error': 'ID do vínculo não informado.'}, status=400)

        vinculo = get_object_or_404(VinculoOrganizacao, id=vinculo_id, organizacao=organizacao)

        from compras.models import Contrato
        if Contrato.objects.filter(representante_contratada=vinculo).exists():
            return JsonResponse({
                'success': False,
                'error': 'Este vínculo está associado a um contrato e não pode ser excluído.'
            }, status=409)

        vinculo.delete()
        return JsonResponse({'success': True})

    if request.method == 'POST' and request.POST.get('action') == 'criar_pessoa':
        nome = request.POST.get('nome', '').strip()
        cpf = request.POST.get('cpf', '').strip()

        if not nome or not cpf:
            return JsonResponse({'success': False, 'error': 'Nome e CPF são obrigatórios.'}, status=400)

        if PessoaFisica.objects.filter(cpf=cpf).exists():
            return JsonResponse({'success': False, 'error': 'Já existe uma pessoa cadastrada com este CPF.'}, status=409)

        pessoa = PessoaFisica.objects.create(nome=nome, cpf=cpf)
        return JsonResponse({'success': True, 'pessoa_id': pessoa.id, 'pessoa_nome': pessoa.nome})

    vinculos = VinculoOrganizacao.objects.filter(organizacao=organizacao)
    pessoas_vinculadas = VinculoOrganizacao.objects.filter(
        organizacao=organizacao
    ).values_list('pessoa_id', flat=True)
    pessoas = PessoaFisica.objects.exclude(id__in=pessoas_vinculadas)

    if request.method == 'POST':
        pessoa_id = request.POST.get('pessoa')
        cargo = request.POST.get('cargo')

        VinculoOrganizacao.objects.create(
            organizacao=organizacao,
            pessoa_id=pessoa_id,
            cargo=cargo,
        )
        return JsonResponse({'success': True})

    return render(request, 'compras/partials/vinculos_lista.html', {
        'organizacao': organizacao,
        'vinculos': vinculos,
        'pessoas': pessoas,
    })


from django.contrib import messages
from django.http import HttpResponse

class ContratoPreencherView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        contrato = get_object_or_404(Contrato, pk=pk)
        docx_file = request.FILES.get('docx_file')
        if not docx_file:
            messages.error(request, "Nenhum arquivo de modelo DOCX foi enviado.")
            return redirect('contrato_list')

        if not contrato.contratada:
            messages.error(request, "O contrato não possui uma empresa contratada definida.")
            return redirect('contrato_update', pk=contrato.pk)

        tem_representante = VinculoOrganizacao.objects.filter(
            organizacao=contrato.contratada,
        ).exists()

        if not tem_representante:
            messages.error(
                request,
                "A empresa contratada não possui representante legal com autoridade de assinatura. "
                "Preencha os dados do representante no formulário do contrato antes de gerar o documento."
            )
            return redirect('contrato_update', pk=contrato.pk)

        tem_endereco = bool(contrato.contratada.endereco and contrato.contratada.cidade and contrato.contratada.estado)
        if not tem_endereco:
            messages.error(
                request,
                "A empresa contratada não possui endereço completo (endereço, cidade e estado). "
                "Preencha o endereço no formulário do contrato antes de gerar o documento."
            )
            return redirect('contrato_update', pk=contrato.pk)

        try:
            from .services.preenchedor_contrato import PreenchedorContratoService
            filled_io, filename = PreenchedorContratoService.fill_docx(docx_file, contrato)

            response = HttpResponse(
                filled_io.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        except Exception as e:
            messages.error(request, f"Erro ao preencher o contrato: {str(e)}")
            return redirect('contrato_list')


class ContratoPreencherTermoCienciaView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        contrato = get_object_or_404(Contrato, pk=pk)
        docx_file = request.FILES.get('docx_file')
        if not docx_file:
            messages.error(request, "Nenhum arquivo de modelo DOCX foi enviado.")
            return redirect('contrato_list')

        if not contrato.contratada:
            messages.error(request, "O contrato não possui uma empresa contratada definida.")
            return redirect('contrato_update', pk=contrato.pk)

        tem_representante = VinculoOrganizacao.objects.filter(
            organizacao=contrato.contratada,
        ).exists()

        if not tem_representante:
            messages.error(
                request,
                "A empresa contratada não possui representante legal com autoridade de assinatura. "
                "Preencha os dados do representante no formulário do contrato antes de gerar o documento."
            )
            return redirect('contrato_update', pk=contrato.pk)

        tem_endereco = bool(contrato.contratada.endereco and contrato.contratada.cidade and contrato.contratada.estado)
        if not tem_endereco:
            messages.error(
                request,
                "A empresa contratada não possui endereço completo (endereço, cidade e estado). "
                "Preencha o endereço no formulário do contrato antes de gerar o documento."
            )
            return redirect('contrato_update', pk=contrato.pk)

        try:
            from .services.preenchedor_termo_ciencia_notificacao import PreenchedorTermoCienciaNotificacaoService
            filled_io, filename = PreenchedorTermoCienciaNotificacaoService.fill_docx(docx_file, contrato)

            response = HttpResponse(
                filled_io.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        except Exception as e:
            messages.error(request, f"Erro ao preencher o Termo de Ciência: {str(e)}")
            return redirect('contrato_list')


class ContratoEmpenhoUploadView(LoginRequiredMixin, View):

    def post(self, request, pk=None, *args, **kwargs):
        contrato = None
        if pk:
            contrato = get_object_or_404(Contrato, pk=pk)

        pdf_file = request.FILES.get('pdf_file')

        if not pdf_file:
            return JsonResponse({'success': False, 'error': 'Nenhum arquivo PDF enviado.'}, status=400)

        try:
            dados = ParserService.processar_pdf(pdf_file, tipo='empenho')
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Erro ao processar PDF: {str(e)}'}, status=500)

        if not dados.get('numero'):
            return JsonResponse({'success': False, 'error': 'O PDF não corresponde a uma Nota de Empenho válida.'}, status=400)

        cnpj = dados.get('organizacao_cnpj', '')
        organizacao_nome = dados.get('organizacao_nome', '')

        organizacao = None
        if cnpj:
            organizacao = Organizacao.objects.filter(cnpj=cnpj).first()

        if not organizacao and cnpj:
            organizacao = Organizacao.objects.create(
                nome=organizacao_nome,
                cnpj=cnpj,
            )
        elif not organizacao:
            return JsonResponse({'success': False, 'error': 'CNPJ da organização não encontrado no documento.'}, status=400)

        compra_numero = dados.get('compra', '')
        compra_obj = None
        if compra_numero:
            compra_obj = Compra.objects.filter(numero_compra=compra_numero).first()
            if not compra_obj:
                return JsonResponse({
                    'success': False,
                    'error': f'A compra {compra_numero} não está cadastrada. Cadastre a compra antes de importar o empenho.',
                    'compra_nao_encontrada': True,
                    'compra_numero': compra_numero,
                }, status=404)

        from datetime import date, datetime
        data_empenho = None
        if dados.get('data_empenho'):
            try:
                data_empenho = datetime.strptime(dados['data_empenho'], '%d/%m/%Y').date()
            except ValueError:
                pass

        valor_empenho = MoedaUtils.valor_to_decimal(dados.get('valor'))
        numero = dados.get('numero', '')

        empenho_existente = Empenho.objects.filter(numero=numero).first()

        if empenho_existente:
            if empenho_existente.contrato and empenho_existente.contrato_id != getattr(contrato, 'pk', None):
                return JsonResponse({
                    'success': False,
                    'error': f'O empenho {numero} já está vinculado ao contrato {empenho_existente.contrato.numero}.'
                }, status=409)

            empenho_existente.data_empenho = data_empenho
            empenho_existente.dotacao = dados.get('dotacao', '')
            empenho_existente.grupo = dados.get('grupo', '')
            empenho_existente.unidade = dados.get('unidade', '')
            empenho_existente.fonte_recurso = dados.get('fonte_recurso', '')
            empenho_existente.funcional_programatica = dados.get('funcional_programatica', '')
            empenho_existente.categoria_economica = dados.get('categoria_economica', '')
            empenho_existente.grupo_despesa = dados.get('grupo_despesa', '')
            empenho_existente.modalidade = dados.get('modalidade', '')
            empenho_existente.elemento = dados.get('elemento', '')
            empenho_existente.item = dados.get('item', '')
            empenho_existente.organizacao = organizacao
            empenho_existente.valor = valor_empenho

            if not empenho_existente.contrato and contrato:
                empenho_existente.contrato = contrato

            empenho_existente.save()
            empenho = empenho_existente
        else:
            empenho = Empenho.objects.create(
                numero=numero,
                data_empenho=data_empenho,
                dotacao=dados.get('dotacao', ''),
                grupo=dados.get('grupo', ''),
                unidade=dados.get('unidade', ''),
                fonte_recurso=dados.get('fonte_recurso', ''),
                funcional_programatica=dados.get('funcional_programatica', ''),
                categoria_economica=dados.get('categoria_economica', ''),
                grupo_despesa=dados.get('grupo_despesa', ''),
                modalidade=dados.get('modalidade', ''),
                elemento=dados.get('elemento', ''),
                item=dados.get('item', ''),
                organizacao=organizacao,
                contrato=contrato,
                valor=valor_empenho,
            )

        contrato_obj = contrato
        if not pk:
            contrato_numero = request.POST.get('numero', '').strip()
            if not contrato_numero:
                return JsonResponse({'success': False, 'error': 'Número do contrato é obrigatório.'})

            contratante = Organizacao.objects.filter(is_propria_instituicao=True).first()
            if not contratante:
                return JsonResponse({
                    'success': False,
                    'error': 'Nenhuma instituição contratante cadastrada. Cadastre uma organização como instituição própria antes de importar o empenho.'
                })

            contrato_obj = Contrato.objects.create(
                numero=contrato_numero,
                contratante=contratante,
                contratada=organizacao,
                compra=compra_obj,
                data=date.today(),
            )

            if not empenho.contrato:
                empenho.contrato = contrato_obj
                empenho.save(update_fields=['contrato'])

        return JsonResponse({
            'success': True,
            'contrato_id': contrato_obj.id if contrato_obj else None,
            'empenho': {
                'id': empenho.id,
                'numero': empenho.numero,
                'valor': str(empenho.valor) if empenho.valor else '',
                'valor_brl': empenho.valor_brl,
            },
            'compra': {
                'id': compra_obj.id,
                'numero': compra_obj.numero_compra,
                'objeto': compra_obj.objeto or '',
            } if compra_obj else None,
            'organizacao': {
                'id': organizacao.id,
                'nome': organizacao.nome,
                'cnpj': organizacao.cnpj,
                'endereco': organizacao.endereco or '',
                'cidade': organizacao.cidade or '',
                'estado': organizacao.estado or '',
                'tem_endereco': bool(organizacao.endereco and organizacao.cidade and organizacao.estado),
            },
            'representantes': {
                'tem_representantes': VinculoOrganizacao.objects.filter(
                    organizacao=organizacao
                ).exists(),
                'vinculos': list(
                    VinculoOrganizacao.objects.filter(
                        organizacao=organizacao
                    ).select_related('pessoa').values('id', 'pessoa__nome', 'cargo')
                ),
            },
        })

