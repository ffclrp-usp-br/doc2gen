class StringUtils:

    @staticmethod
    def formatar_numero_demanda(valor):

        if not valor or len(valor) < 5:
            return ''

        ano = valor[:4]
        numero = valor[4:].lstrip('0') or '0'

        return f"{numero}/{ano}"