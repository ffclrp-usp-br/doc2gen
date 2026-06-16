class DateUtils:


    MESES = {
        1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril",
        5: "maio", 6: "junho", 7: "julho", 8: "agosto",
        9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro"
    }

  
    @classmethod
    def get_nome_mes(cls, month_number):
        """Return the month name in Portuguese."""
        return cls.MESES.get(month_number, "")

    

    @staticmethod
    def to_dmy(dt):
        """
        Retorna a data no formato DD/MM/AAAA.
        """
        if not dt:
            return ""

        return dt.strftime("%d/%m/%Y")


    @classmethod
    def data_por_extenso(cls, dt):
        """
        Retorna dia, mês por extenso e ano.
        
        Exemplo:
        ('15', 'junho', '2026')
        """
        if not dt:
            return "", "", ""

        dia = f"{dt.day:02d}"
        mes = cls.get_nome_mes(dt.month)
        ano = str(dt.year)

        return dia, mes, ano
