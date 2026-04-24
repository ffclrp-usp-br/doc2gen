from .base import ExtratorBase
import re


class ExtratorDocumentoGrade(ExtratorBase):
    tipo = 'grade'

    # -------------------------
    # IDENTIFICA O DOCUMENTO
    # -------------------------
    def pode_processar(self, texto: str) -> bool:
        return "Documento de Compra" in texto or "Compra:" in texto

    # -------------------------
    # EXTRAÇÃO PRINCIPAL
    # -------------------------
    def extrair(self, texto: str) -> dict:
        dados = {
            "tipo": "grade",
            "numero_compra": self._extrair_numero_grade(texto),
            "numero_sei": self._extrair_numero_sei(texto),
            "objeto": self._extrair_campo(texto, "Objeto"),
            "modalidade": self._extrair_campo(texto, "Modalidade"),
            "tipo_compra": self._extrair_tipo_grade(texto),
            "itens": [],
        }

        blocos = self._extrair_blocos_itens(texto)

        for bloco in blocos:
            item = self._extrair_item(bloco)
            if item and any([item.get("bec"), item.get("bem"), item.get("descricao"), item.get("cotacoes")]):
                dados["itens"].append(item)

        return dados

    # =========================
    # MÉTODOS INTERNOS
    # =========================

    def _extrair_numero_grade(self, texto):
        match = re.search(r'Compra[:\s]*(\d+)\s*/\s*(\d{4})', texto, re.IGNORECASE)
        if match:
            return f"{match.group(1)}/{match.group(2)}"
        return None

    def _extrair_numero_sei(self, texto):
        match = re.search(r'Número\s+SEI[:\s]*([\d\.]+/\d{4}-\d{2})', texto, re.IGNORECASE)
        if match:
            return match.group(1)
        return None

    def _extrair_campo(self, texto, label):
        match = re.search(rf'{re.escape(label)}[:\s]+(.+)', texto, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None

    def _extrair_tipo_grade(self, texto):
        match = re.search(r'Tipo(?:\s+de\s+compra)?[:\s]+(.+)', texto, re.IGNORECASE)
        if match:
            tipo = match.group(1).strip().upper()
            if 'FORNECIMENTO' in tipo:
                return 'FORNECIMENTO'
            elif 'SERVIÇO' in texto or 'SERVICO' in tipo:
                return 'SERVIÇO'
        return None

    # -------------------------
    # SEPARAR ITENS
    # -------------------------
    def _extrair_blocos_itens(self, texto):
        linhas = texto.splitlines()

        blocos = []
        bloco_atual = []

        for linha in linhas:
            linha = linha.strip()
            if re.match(r'^Item\s+\d+', linha, re.IGNORECASE):
                if bloco_atual:
                    blocos.append("\n".join(bloco_atual))
                    bloco_atual = []
            if linha:
                bloco_atual.append(linha)

        if bloco_atual:
            blocos.append("\n".join(bloco_atual))

        return blocos

    # -------------------------
    # EXTRAIR ITEM
    # -------------------------
    def _extrair_item(self, bloco):
        pattern = r'''
            Item\s+(\d+)\s*\|\s*
            (?:Lote:\s*\|\s*)?
            Bem:\s*(\d+)\s*\|\s*
            BEC:\s*(\d+)\s*\|\s*
            (.*?)\s*\|\s*
            Método:\s*(.*?)\s*\|\s*
            Valor\s*Prev\.\s*:\s*([\d\.,]+)
        '''

        match = re.search(pattern, bloco, re.VERBOSE | re.DOTALL)
        if match:
            item_num = match.group(1)
            bem = match.group(2)
            bec = match.group(3)
            descricao = match.group(4).strip()
            metodo = match.group(5).strip()
            valor_prev = match.group(6).strip()
        else:
            item_num = self._extrair_numero_do_item(bloco)
            bem = self._extrair_campo_do_bloco(bloco, r'Bem:\s*(\d+)')
            bec = self._extrair_campo_do_bloco(bloco, r'BEC:\s*(\d+)')
            descricao = self._extrair_campo_do_bloco(
                bloco,
                r'Bem:\s*\d+\s*\|\s*BEC:\s*\d+\s*\|\s*(.*?)\s*(?:\||$)'
            )
            metodo = self._extrair_campo_do_bloco(bloco, r'Método:\s*(.*?)(?:\||$)')
            valor_prev = self._extrair_campo_do_bloco(bloco, r'Valor\s*Prev\.\s*:\s*([\d\.,]+)')

        return {
            "item": item_num,
            "codigo_contabiliza": bec,
            "codigo_bem": bem,
            "descricao": descricao,
            "metodo": metodo,
            "valor_previsto": valor_prev,
            "cotacoes": self._extrair_cotacoes(bloco)
        }

    def _extrair_numero_do_item(self, bloco):
        match = re.search(r'Item\s+(\d+)', bloco, re.IGNORECASE)
        return match.group(1) if match else None

    def _extrair_campo_do_bloco(self, bloco, pattern):
        match = re.search(pattern, bloco, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else None

    # -------------------------
    # EXTRAIR COTAÇÕES
    # -------------------------
    def _extrair_cotacoes(self, bloco):
        linhas = [l.strip() for l in bloco.split("\n") if l.strip()]
        cotacoes = []

        indices = []

        # localizar início de cada cotação
        for i, linha in enumerate(linhas):
            if re.match(r'^\d+\s+\d{2}/\d{2}/\d{4}', linha):
                indices.append(i)

        # processar cada bloco individual
        for n in range(len(indices)):
            ini = indices[n]

            if n < len(indices) - 1:
                fim = indices[n + 1]
            else:
                fim = len(linhas)

            bloco_cot = linhas[ini:fim]

            cot = self._processar_cotacao(bloco_cot)
            if cot:
                cotacoes.append(cot)

        return cotacoes
        


    def _processar_cotacao(self, linhas):
        texto = " ".join(linhas)

        # pega todos valores monetários
        nums = re.findall(r'\d{1,3}(?:\.\d{3})*,\d{2}', texto)

        if len(nums) < 3:
            return None

        quantidade = nums[-3]
        valor_unitario = nums[-2]

        # remove prefixo índice + data
        texto = re.sub(r'^\d+\s+\d{2}/\d{2}/\d{4}\s+', '', texto)

        # nome vai até CNPJ/CPF ou validade
        cortes = [
            r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}',
            r'\d{3}\.\d{3}\.\d{3}-\d{2}',
            r'60 dias',
            quantidade
        ]

        posicoes = []

        for c in cortes:
            m = re.search(c, texto)
            if m:
                posicoes.append(m.start())

        if posicoes:
            empresa = texto[:min(posicoes)]
        else:
            empresa = texto

        empresa = re.sub(r'\s+', ' ', empresa).strip()

        return {
            "empresa": empresa,
            "quantidade": quantidade,
            "valor_unitario": valor_unitario
        }
