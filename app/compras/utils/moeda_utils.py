from decimal import Decimal

class MoedaUtils:

    @staticmethod
    def valor_por_extenso(valor: Decimal) -> str:
        """Converte um valor decimal em reais por extenso em português."""
        if not valor:
            return "zero reais"
            
        reais = int(valor)
        centavos = int(round((valor - reais) * 100))
        
        def converter_grupo(n):
            units = ["", "um", "dois", "três", "quatro", "cinco", "seis", "sete", "oito", "nove"]
            teens = ["dez", "onze", "doze", "treze", "quatorze", "quinze", "dezesseis", "dezessete", "dezoito", "dezenove"]
            tens = ["", "dez", "vinte", "trinta", "quarenta", "cinquenta", "sessenta", "setenta", "oitenta", "noventa"]
            hundreds = ["", "cento", "duzentos", "trezentos", "quatrocentos", "quinhentos", "seiscentos", "setecentos", "oitocentos", "novecentos"]
            
            if n == 100:
                return "cem"
            
            h = n // 100
            t = (n % 100) // 10
            u = n % 10
            
            parts = []
            if h > 0:
                parts.append(hundreds[h])
            if t == 1:
                parts.append(teens[u])
            else:
                if t > 0:
                    parts.append(tens[t])
                if u > 0:
                    parts.append(units[u])
                    
            return " e ".join(parts)

        def converter_inteiro(n):
            if n < 1000:
                return converter_grupo(n)
            
            if n < 1000000:
                thousands = n // 1000
                rest = n % 1000
                t_str = "mil" if thousands == 1 else f"{converter_grupo(thousands)} mil"
                if rest == 0:
                    return t_str
                if rest < 100 or rest % 100 == 0:
                    return f"{t_str} e {converter_grupo(rest)}"
                return f"{t_str}, {converter_grupo(rest)}"
                
            # Millions
            millions = n // 1000000
            rest = n % 1000000
            m_str = "um milhão" if millions == 1 else f"{converter_grupo(millions)} milhões"
            if rest == 0:
                return m_str
            if rest < 100 or (rest < 1000 and rest % 100 == 0) or (rest >= 1000 and rest % 1000 == 0):
                return f"{m_str} e {converter_inteiro(rest)}"
            return f"{m_str}, {converter_inteiro(rest)}"

        part_reais = ""
        if reais > 0:
            if reais == 1:
                part_reais = "um real"
            else:
                suffix = " de reais" if reais >= 1000000 and reais % 1000000 == 0 else " reais"
                part_reais = f"{converter_inteiro(reais)}{suffix}"
                
        part_centavos = ""
        if centavos > 0:
            if centavos == 1:
                part_centavos = "um centavo"
            else:
                part_centavos = f"{converter_inteiro(centavos)} centavos"
                
        if part_reais and part_centavos:
            return f"{part_reais} e {part_centavos}"
        elif part_reais:
            return part_reais
        elif part_centavos:
            return part_centavos
        else:
            return "zero reais"



    @staticmethod
    def formatar_moeda_brasileira(valor):
        """Format a decimal/float to Brazilian currency string (R$ X.XXX,XX)."""
        if valor is None:
            return "R$ 0,00"
        try:
            return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except (ValueError, TypeError):
            return "R$ 0,00"
