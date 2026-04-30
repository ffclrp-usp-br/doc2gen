from .base import ExtratorBase
import re


class ExtratorDocumentoCompra(ExtratorBase):
    tipo = 'grade'

    # -------------------------
    # IDENTIFICA O DOCUMENTO
    # -------------------------
    def pode_processar(self, texto: str) -> bool:
        return "Documento de Compra" in texto or "Material:" in texto

    # -------------------------
    # EXTRAÇÃO PRINCIPAL
    # -------------------------
    def extrair(self, texto: str) -> dict:
        dados = {
            "tipo": "grade",
            "numero_compra": self._extrair_numero_compra(texto),
            "numero_sei": self._extrair_numero_sei(texto),
            "modalidade": self._extrair_modalidade(texto),
            "valor_total_previsto": self._extrair_valor_total_previsto(texto),
            "itens": [],
        }

        blocos = self._extrair_blocos_itens(texto)

        for bloco in blocos:
            item = self._extrair_item(bloco)
            if item and item.get("item"):
                dados["itens"].append(item)

        return dados

    # =========================
    # MÉTODOS - CABEÇALHO
    # =========================

    def _extrair_numero_compra(self, texto):
        """Extrai número da compra em formato XXXXX / XXXX ou 12 dígitos contínuos"""
        # Tenta primeiro o padrão antigo: "Documento da Compra: 12345 / 2026"
        match = re.search(
            r'Documento\s+da\s+Compra[:\s]*(\d+)\s*/\s*(\d+)',
            texto,
            re.IGNORECASE
        )
        if match:
            return f"{match.group(1)}"
        
        # Tenta o novo padrão: 12 dígitos contínuos
        match = re.search(
            r'(?:Documento\s+da\s+Compra[:\s]*)?(\d{12})',
            texto,
            re.IGNORECASE
        )
        if match:
            return match.group(1)
        
        return None

    def _extrair_numero_sei(self, texto):
        """Extrai número SEI/Processo"""
        match = re.search(
            r'Processo[:\s]*([\d\.]+/\d{4}-\d+)',
            texto,
            re.IGNORECASE
        )
        return match.group(1) if match else None

    def _extrair_modalidade(self, texto):
        """Extrai modalidade da compra"""
        match = re.search(
            r'Modalidade[:\s]*(.+?)(?:\n|$)',
            texto,
            re.IGNORECASE
        )
        if match:
            return match.group(1).strip()
        return None

    def _extrair_valor_total_previsto(self, texto):
        """Extrai valor total previsto"""
        match = re.search(
            r'Valor\s+Total\s+Previsto[\s\S]{0,150}?(\d{1,3}(?:\.\d{3})*,\d{2})',
            texto,
            re.IGNORECASE
        )
        return match.group(1) if match else None

    # -------------------------
    # MÉTODOS - SEPARAR ITENS
    # -------------------------

    def _extrair_blocos_itens(self, texto):
        """Divide o texto em blocos de itens"""
        linhas = texto.split("\n")
        blocos = []
        bloco_atual = []
        iniciou = False

        for linha in linhas:
            if re.match(r'^Item\s*#\d+', linha.strip()):
                iniciou = True
                if bloco_atual:
                    blocos.append("\n".join(bloco_atual))
                    bloco_atual = []

            if iniciou:
                bloco_atual.append(linha)

        if bloco_atual:
            blocos.append("\n".join(bloco_atual))

        return blocos

    # -------------------------
    # MÉTODOS - EXTRAIR ITEM
    # -------------------------

    def _extrair_item(self, bloco):
        """Extrai dados completos de um item"""
        return {
            "item": self._extrair_numero_do_item(bloco),
            "codigo_bem": self._extrair_campo_do_bloco(bloco, r'Bem:\s*(\d+)'),
            "codigo_bec": self._extrair_campo_do_bloco(bloco, r'BEC:\s*(\d+)'),
            "codigo_contabiliza": self._extrair_campo_do_bloco(bloco, r'BEC:\s*(\d+)'),
            "codigo_material": self._extrair_campo_do_bloco(bloco, r'Material:\s*(\d+)'),
            "item_despesa": self._extrair_item_despesa(bloco),
            "descricao": self._extrair_descricao(bloco),
            "quantidade": self._extrair_quantidade(bloco),
            "valor_unitario_previsto": self._extrair_valor_unitario_previsto(bloco),
            "cotacoes": self._extrair_cotacoes(bloco),
        }

    def _extrair_numero_do_item(self, bloco):
        """Extrai número do item"""
        match = re.search(r'Item\s*#(\d+)', bloco)
        return match.group(1) if match else None

    def _extrair_campo_do_bloco(self, bloco, pattern):
        """Extrai campo usando regex do bloco"""
        match = re.search(pattern, bloco, re.IGNORECASE)
        return match.group(1).strip() if match else None

    def _extrair_item_despesa(self, bloco):
        """Extrai item de despesa"""
        match = re.search(
            r'Item\s+de\s+Despesa[:\s]*([0-9,\s]+)',
            bloco,
            re.IGNORECASE
        )
        if match:
            return self._limpar(match.group(1))
        return None

    def _extrair_descricao(self, bloco):
        """Extrai descrição do material"""
        match = re.search(
            r'Material:\s*\d+\s+(.*?)\s+\d+(?:,\d+)?\s+UNIDADE',
            bloco,
            re.DOTALL
        )
        if match:
            return self._limpar(match.group(1))
        return ""

    def _extrair_quantidade(self, bloco):
        """Extrai quantidade"""
        match = re.search(
            r'(\d+(?:,\d+)?)\s+UNIDADE\s+(\d{1,3}(?:\.\d{3})*,\d{2})',
            bloco
        )
        return match.group(1) if match else None

    def _extrair_valor_unitario_previsto(self, bloco):
        """Extrai valor unitário previsto"""
        match = re.search(
            r'(\d+(?:,\d+)?)\s+UNIDADE\s+(\d{1,3}(?:\.\d{3})*,\d{2})',
            bloco
        )
        return match.group(2) if match else None

    # -------------------------
    # MÉTODOS - EXTRAIR COTAÇÕES
    # -------------------------

    def _extrair_cotacoes(self, bloco):
        """Extrai cotações (pesquisas) de fornecedores do item"""
        # pega somente a tabela entre os dois textos
        match = re.search(
            r'Contratação\s+gov\.br:(.*?)(?:Método\s+de\s+Cálculo|$)',
            bloco,
            re.IGNORECASE | re.DOTALL
        )

        if not match:
            return []

        tabela = match.group(1)
        linhas = [
            self._limpar(x)
            for x in tabela.split("\n")
            if self._limpar(x)
        ]

        cotacoes = []

        for i in range(len(linhas) - 1):
            linha = linhas[i]

            # fornecedor = linha com CPF/CNPJ
            if self._tem_documento(linha):
                empresa = linha
                proxima = linhas[i + 1]

                # valor está normalmente na próxima linha
                match_val = re.search(
                    r'(\d{1,3}(?:\.\d{3})*,\d{2})',
                    proxima
                )

                if match_val:
                    cotacoes.append({
                        "empresa": empresa,
                        "valor_unitario": match_val.group(1)
                    })

        # remove duplicados
        final = []
        vistos = set()

        for c in cotacoes:
            chave = (c["empresa"], c["valor_unitario"])
            if chave not in vistos:
                vistos.add(chave)
                final.append(c)

        return final

    # -------------------------
    # MÉTODOS UTILITÁRIOS
    # -------------------------

    def _limpar(self, txt):
        """Remove espaços múltiplos e normaliza texto"""
        if not txt:
            return ""
        return re.sub(r'\s+', ' ', txt).strip()

    def _tem_documento(self, txt):
        """Verifica se texto contém CPF ou CNPJ"""
        return bool(re.search(
            r'(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})|(\d{3}\.\d{3}\.\d{3}-\d{2})',
            txt
        ))
