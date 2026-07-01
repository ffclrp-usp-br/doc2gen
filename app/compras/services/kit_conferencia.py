import os
import re
import io
import zipfile
from ..models import Compra, ModeloDocumento
from .excel_conferencia import ExcelConferenciaService
from compras.utils.string_utils import StringUtils

class KitConferenciaService:

    @staticmethod
    def generate_kit(compra_id):
        compra = Compra.objects.prefetch_related('demandas__itens').get(pk=compra_id)
        modalidade_upper = (compra.modalidade or "").upper()

        # 1. Buscar todos os modelos oficiais para esta modalidade
        modelos = ModeloDocumento.objects.filter(modalidade=compra.modalidade)

        # 2. Filtrar TR e CONTRATO pelo tipo da compra
        modelos_filtrados = []
        for modelo in modelos:
            if modelo.categoria in (ModeloDocumento.Categoria.TR, ModeloDocumento.Categoria.CONTRATO):
                if modelo.tipo and modelo.tipo != compra.tipo:
                    continue
            modelos_filtrados.append(modelo)

        # 3. Gerar ZIP
        zip_io = io.BytesIO()
        with zipfile.ZipFile(zip_io, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Adicionar todos os modelos oficiais como arquivos estáticos
            for modelo in modelos_filtrados:
                if modelo.arquivo and os.path.exists(modelo.arquivo.path):
                    zip_file.write(modelo.arquivo.path, os.path.basename(modelo.arquivo.path))

            # Adicionar XLSX (gerado dinamicamente)
            try:
                xlsx_io = ExcelConferenciaService.generate_excel(compra.id)
                if xlsx_io:
                    zip_file.writestr("CONFERENCIA_LICITACAO_MODELO.xlsx", xlsx_io.getvalue())
            except Exception as e:
                print(f"Erro ao gerar planilha Excel: {e}")

        zip_io.seek(0)

        # 4. Gerar nome do arquivo
        ano_sei, num_sei = StringUtils.parse_sei(compra.numero_sei)
        if ano_sei and num_sei:
            if 'PREGÃO' in modalidade_upper or 'PREGAO' in modalidade_upper:
                zip_filename = f"Pregão {ano_sei}--SEI {num_sei} - {compra.objeto}.zip"
            else:
                zip_filename = f"{ano_sei} - SEI {num_sei} - {compra.objeto}.zip"
        else:
            clean_objeto = re.sub(r'[^\w\s-]', '', compra.objeto)[:50]
            zip_filename = f"KIT_CONFERENCIA_{compra.numero_compra.replace('/', '_')}_{clean_objeto}.zip"

        return zip_io, zip_filename
