# services/extratores/demanda.py

import re
from .base import ExtratorBase


class ExtratorDocumentoDemanda(ExtratorBase):
    tipo = 'demanda'

    def pode_processar(self, texto: str) -> bool:
        return "Documento da Demanda" in texto

    def extrair(self, texto: str) -> dict:

        print ("\n\n999999999%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% extraindo em demanda .... ")
        print(texto);
        print ("999999999%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% extraindo em demanda ....\n\n ")
        
        dados = {
            "tipo": "demanda",
            "numero_demanda": self._extrair_numero_demanda(texto),
            "unidade_despesa": self._extrair_unidade_despesa(texto),
            "centro_gerencial": self._extrair_campo(texto, "Centro Gerencial"),
            "codigo_contabiliza": self._extrair_campo(texto, "Código Contabiliza"),
            "itens": [],
        }

        blocos = self._extrair_blocos_itens(texto)
        for bloco in blocos:
            item = self._extrair_dados_item(bloco)
            if item:
                dados["itens"].append(item)

        return dados

    def _extrair_numero_demanda(self, texto: str) -> str | None:
        match = re.search(r'N[ºo\.]?\s*(\d+)\s*-\s*Ano\s*(\d{4})', texto, re.IGNORECASE)
        if match:
            return f"{match.group(1)}/{match.group(2)}"
        return None

    def _extrair_unidade_despesa(self, texto: str) -> str | None:
        match = re.search(r'Unidade\s+Despesa[:\s]+(\d+)', texto, re.IGNORECASE)
        if match:
            return match.group(1)
        return None

    def _extrair_campo(self, texto: str, label: str) -> str | None:
        pattern = rf'{re.escape(label)}[:\s]+(.+)'
        match = re.search(pattern, texto, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None

    def _extrair_blocos_itens(self, texto: str) -> list[str]:
        linhas = texto.splitlines()
        blocos = []
        bloco_atual = []
        capturando = False

        for linha in linhas:
            if re.match(r'^\s*\d+\s+\d+\s+\d+', linha):
                if bloco_atual:
                    blocos.append("\n".join(bloco_atual))
                    bloco_atual = []
                capturando = True

            if capturando:
                bloco_atual.append(linha)

        if bloco_atual:
            blocos.append("\n".join(bloco_atual))

        return blocos

    def _extrair_itens_despesa_do_bloco(self, linhas: list[str]) -> list[str]:
        itens = []
        capturar = False

        for linha in linhas:
            if re.search(r'Item\s+Despesa', linha, re.IGNORECASE):
                capturar = True
                continue

            if capturar:
                if re.search(r'(Observa|Total|Valor|Item\s+\d+)', linha, re.IGNORECASE):
                    break

                if re.search(r'\d+,\d+', linha):
                    continue

                encontrados = re.findall(r'\b\d{8}\b', linha)
                for encontrado in encontrados:
                    if encontrado not in itens:
                        itens.append(encontrado)

        return itens

    def _extrair_dados_item(self, bloco: str) -> dict | None:
        linhas = bloco.splitlines()
        if not linhas:
            return None

        linha_principal = linhas[0].strip()
        pattern = r'^\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(.+)$'
        match = re.match(pattern, linha_principal)
        if not match:
            return None

        return {
            "item": match.group(1),
            "classe": match.group(2),
            "contabiliza": match.group(3),
            "cod_mat": match.group(4),
            "cod_bem": match.group(5),
            "qtd": match.group(6),
            "unidade": match.group(7).strip(),
            "itens_despesa": self._extrair_itens_despesa_do_bloco(linhas),
        }
