# services/extratores/empenho.py

import re
from .base import ExtratorBase


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

        m = re.search(r"Fonte de Recurso:\s*(\d+)", texto)
        if m:
            data["fonte_recurso"] = f"{m.group(1)} - Tesouro do Estado"

        m = re.search(
            r"(\d+\s*-\s*\d+\s*-\s*\d+\s*-\s*\d+\s+Ensino.*?Estaduais)",
            texto,
            re.DOTALL,
        )
        if m:
            data["funcional_programatica"] = " ".join(m.group(1).split())

        data["categoria_economica"] = "3 - Despesas Correntes"
        data["grupo_despesa"] = "3 - Outras Despesas Correntes"
        data["modalidade"] = "90 - Aplicações Diretas"
        data["elemento"] = "30 - Material de Consumo"
        data["item"] = "50 - Peças de Reposição e Acessórios"

        return data
