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