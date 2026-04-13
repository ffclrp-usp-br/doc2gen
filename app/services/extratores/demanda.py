# services/extratores/demanda.py

import re
from .base import ExtratorBase


class ExtratorDocumentoDemanda(ExtratorBase):
    tipo = 'demanda'

    def pode_processar(self, texto: str) -> bool:
        return "Documento da Demanda" in texto

    def extrair(self, texto: str) -> dict:
        try:
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
        except Exception as e:
            print(f"ERRO no extrator de demanda: {e}")
            import traceback
            traceback.print_exc()
            return {}

    def _extrair_numero_demanda(self, texto: str) -> str | None:
        # Tentar diferentes padrões
        patterns = [
            r'N[ºo°\.]?\s*(\d+)\s*-\s*Ano\s*(\d{4})',
            r'Documento\s+da\s+Demanda.*?N[ºo°\.]?\s*(\d+).*?Ano\s*(\d{4})',
            r'(\d+)\s*-\s*Ano\s*(\d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, texto, re.IGNORECASE | re.DOTALL)
            if match:
                return f"{match.group(1)}/{match.group(2)}"
        return None

    def _extrair_unidade_despesa(self, texto: str) -> str | None:
        match = re.search(r'Unidade\s+Despesa[:\s]+(.+?)(?:\n|$)', texto, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1)[:2]
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
        
        # Tentar diferentes padrões para linhas de item
        patterns = [
            r'^\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(.+)$',  # 7 números + texto
        ]
        
        for pattern in patterns:
            match = re.match(pattern, linha_principal)
            if match:
                groups = match.groups()
                if len(groups) >= 5:  # Pelo menos item, classe, material, bem, contabiliza
                    return {
                        "item": groups[0] if len(groups) > 0 else "",
                        "classe": groups[1] if len(groups) > 1 else "",
                        "codigo_material": groups[2] if len(groups) > 2 else "",
                        "codigo_compras_gov": groups[3] if len(groups) > 5 else "",
                        "codigo_contabiliza": groups[4] if len(groups) > 4 else "",
                        "codigo_bem": groups[5] if len(groups) > 3 else "",
                        "qtd": groups[6] if len(groups) > 6 else "",
                        "unidade": groups[7] if len(groups) > 7 else "",
                        "itens_despesa": self._extrair_itens_despesa_do_bloco(linhas),
                    }
        
        return None
