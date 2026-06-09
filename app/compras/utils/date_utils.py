class DateUtils:


    MESES = {
        1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril",
        5: "maio", 6: "junho", 7: "julho", 8: "agosto",
        9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro"
    }

  
    @classmethod
    def get_month_name(cls, month_number):
        """Return the month name in Portuguese."""
        return cls.MESES.get(month_number, "")

    

    @classmethod
    def formatar_datas(cls, dt, formato="DD/MM/AAAA"):
        """Format datetime.date to string according to format."""
        if not dt:
            return ""
        if formato == "DD/MM/AAAA":
            return dt.strftime("%d/%m/%Y")
        elif formato == "por_extenso":
            dia = f"{dt.day:02d}"
            mes = cls.get_month_name(dt.month)
            ano = f"{dt.year}"
            return dia, mes, ano
        return str(dt)

