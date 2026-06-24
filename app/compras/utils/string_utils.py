import re
import unicodedata

class StringUtils:

    @staticmethod
    def formatar_numero_demanda_compra(valor):

        if not valor or len(valor) < 5:
            return ''

        ano = valor[:4]
        numero = valor[4:].lstrip('0') or '0'

        return f"{numero}/{ano}"
    

    @staticmethod
    def extrair_elemento_despesa(valores):

        if not valores:
            return ''

        # se vier string separada por vírgula
        if isinstance(valores, str):

            valores = [
                v.strip()
                for v in valores.split(',')
                if v.strip()
            ]

        elementos = set()

        # considera apenas os 6 primeiros dígitos
        for valor in valores:

            valor_str = str(valor).strip()

            if len(valor_str) >= 6:
                elementos.add(valor_str[:6])
            else:
                elementos.add(valor_str)

        # regras de prioridade

        # 339030 prevalece sobre 449052
        if '339030' in elementos:
            elementos.discard('449052')

        # 339039 prevalece sobre 339036
        if '339039' in elementos:
            elementos.discard('339036')

        return ', '.join(sorted(elementos))
    

    @staticmethod
    def formatar_codigo_descricao(texto):
        m = re.match(r'^\s*(\d+)\s+(.*)$', texto.strip())
    
        if m:
            return f"{m.group(1)} - {m.group(2)}"
    
        return texto
    
    @staticmethod
    def sei_compacto(numero_sei):
        ''''Retorna no formato compacto: 154.00009999/2026-99 -> 9999/2026'''
        if not numero_sei:
            return None, None
        match = re.search(r'\.(\d+)/(\d{4})-', numero_sei)
        if match:
            numero = match.group(1).lstrip('0')
            ano = match.group(2)
            return f"{numero}/{ano}"
        return numero_sei
    

    @staticmethod
    def parse_sei(sei):
        """
        Extracts year and number from SEI string.
        Format: 154.00009999/2026-99
        Returns: (year, number) or (None, None)
        """
        if not sei:
            return None, None
        match = re.search(r'\.(\d+)/(\d{4})-', sei)
        if match:
            numero = match.group(1).lstrip('0')
            ano = match.group(2)
            return ano, numero
        return None, None
    

    def nome_or_nome_fantasia_organizacao(self):
        nome = self.nome_fantasia or self.nome

        # Remove acentos
        nome = unicodedata.normalize('NFKD', nome)
        nome = ''.join(c for c in nome if not unicodedata.combining(c))

        # Pega apenas a primeira palavra
        primeira_palavra = nome.strip().split()[0]

        # Mantém apenas letras
        primeira_palavra = re.sub(r'[^a-zA-Z]', '', primeira_palavra)

        return primeira_palavra
