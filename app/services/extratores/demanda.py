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

    # -------------------------
    # EXTRAIR ITENS DE DESPESA DENTRO DO BLOCO
    # -------------------------
    def _extrair_itens_despesa_do_bloco(self, linhas):
        itens = []

        for linha in linhas:
            # Extrai códigos válidos direto, sem filtrar linha
            encontrados = re.findall(r'\b(3[3-9]\d{6}|4[4-9]\d{6})\b', linha)

            if encontrados:
                itens.extend(encontrados)

        # remove duplicados mantendo ordem
        vistos = set()
        itens_unicos = []
        for i in itens:
            if i not in vistos:
                vistos.add(i)
                itens_unicos.append(i)

        return itens_unicos



    # -------------------------
    # EXTRAIR DADOS DE UM ITEM
    # -------------------------

    def _extrair_dados_item(self, bloco: str)-> dict | None:
        linhas = bloco.split("\n")

        if not linhas:
            return None

        linha = linhas[0].strip()
        partes = re.split(r'\s+', linha)

        if len(partes) < 2:
            return None

        item = partes[0]

        # =========================
        # CLASSE CONTABILIZA (4 dígitos ou vazio)
        # =========================
        idx = 1

        if re.match(r'^\d{4}$', partes[idx]):
            classe_contabiliza = partes[idx]
            idx += 1
        else:
            classe_contabiliza = None

        # =========================
        # CAMPOS SEGUINTES (dinâmico)
        # =========================
        cod_mat = None
        cod_bem = None
        cod_contabiliza = None
        cod_compras = None
        quantidade = None
        unidade = None

        numeros = []
        textos = []

        for p in partes[idx:]:
            if re.match(r'^\d+$', p):
                numeros.append(p)
            else:
                textos.append(p)

        # =========================
        # ATRIBUIÇÃO INTELIGENTE
        # =========================

        # códigos geralmente grandes (>= 5 dígitos)
        codigos = [n for n in numeros if len(n) >= 5]

        if len(codigos) >= 1:
            cod_mat = codigos[0]
        if len(codigos) >= 2:
            cod_bem = codigos[1]
        if len(codigos) >= 3:
            cod_contabiliza = codigos[2]
        if len(codigos) >= 4:
            cod_compras = codigos[3]

        # quantidade = número pequeno (geralmente <= 4 dígitos)
        candidatos_qtd = [n for n in numeros if len(n) <= 4]

        if candidatos_qtd:
            quantidade = candidatos_qtd[-1]
        else:
            quantidade = None

        # unidade = tudo após a quantidade
        try:
            if quantidade:
                idx_qtd = partes.index(quantidade)
                unidade = " ".join(partes[idx_qtd + 1:])
            else:
                unidade = None
        except:
            unidade = None

        itens_despesa = self._extrair_itens_despesa_do_bloco(linhas)

        # =========================
        # VALIDAÇÃO OBRIGATÓRIA PARA DESCARTAR NULOS
        # =========================
        if self._vazio(cod_mat) or self._vazio(cod_bem) or self._vazio(cod_contabiliza):
            return None
            
                
        return {
            "item": item,
            "classe_contabiliza": classe_contabiliza,
            "codigo_material": cod_mat,
            "codigo_bem": cod_bem,
            "codigo_contabiliza": cod_contabiliza,
            "codigo_compras_gov": cod_compras,
            "quantidade": quantidade,
            "unidade": unidade,
            "item_despesa": itens_despesa,
        }
    
    def _vazio(self, valor):
        return valor is None or str(valor).strip() == ""

    