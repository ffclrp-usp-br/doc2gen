# services/extratores/empenho.py

import typing_extensions
import re
from .base import ExtratorBase
from compras.utils.string_utils import StringUtils

class ExtratorEmpenho(ExtratorBase):

    tipo = 'empenho'

    def pode_processar(self, texto: str) -> bool:
        return 'Nota de Empenho' in texto or 'Data do Empenho' in texto

    def extrair(self, texto: str) -> dict:
        data = {}

        m = re.search(r"\b(\d{8}/\d{4})\b", texto)
        if m:
            data["numero"] = m.group(1)

        m = re.search(r"Data do Empenho:\s*(\d{2}/\d{2}/\d{4})", texto)
        if m:
            data["data_empenho"] = m.group(1)

        m = re.search(r"Dotação:\s*([0-9]+/[0-9]{4})", texto, re.MULTILINE)
        if m:
            data["dotacao"] = m.group(1)

        m = re.search(r"Grupo:\s*(.+)", texto, re.MULTILINE)
        if m:
            data["grupo"] = m.group(1).strip()

        m = re.search(r"(\d+\s*-\s*Faculdade.*?Ribeirão Preto)", texto)
        if m:
            data["unidade"] = m.group(1)

        m = re.search(r"Credor:\s*(.+)", texto)
        if m:
            data["organizacao_nome"] = m.group(1).strip()

        m = re.search(r"C\.N\.P\.J\.\s*([\d./-]+)", texto)
        if m:
            data["organizacao_cnpj"] = m.group(1)

        m = re.search(r"Fonte de Recurso:\s*(.+)", texto)
        if m:
            data["fonte_recurso"] = StringUtils.formatar_codigo_descricao(m.group(1).strip())

        m = re.search(
            r"(\d+\s*-\s*\d+\s*-\s*\d+\s*-\s*\d+\s+Ensino.*?Estaduais)",
            texto,
            re.DOTALL,
        )
        if m:
            data["funcional_programatica"] = " ".join(m.group(1).split())

        
        m = re.search(r"Categoria Econômica:\s*(.+)", texto, re.MULTILINE)
        if m:
            data["categoria_economica"] = StringUtils.formatar_codigo_descricao(m.group(1).strip())

        m = re.search(r"Grupo de Despesa:\s*(.+)", texto, re.MULTILINE)
        if m:
            data["grupo_despesa"] = StringUtils.formatar_codigo_descricao(m.group(1).strip())

        m = re.search(r"Modalidade:\s*(.+)", texto, re.MULTILINE)
        if m:
            data["modalidade"] = StringUtils.formatar_codigo_descricao(m.group(1).strip())

        m = re.search(r"Elemento:\s*(.+)", texto, re.MULTILINE)
        if m:
            data["elemento"] = StringUtils.formatar_codigo_descricao(m.group(1).strip())

        m = re.search(r"Item:\s*(.+)", texto, re.MULTILINE)
        if m:
            data["item"] = StringUtils.formatar_codigo_descricao(m.group(1).strip())

        m = re.search(r"Funcional Programática:\s*(.+)", texto, re.MULTILINE)
        if m:
            data["funcional_programatica"] = m.group(1).strip()

        
        return data
