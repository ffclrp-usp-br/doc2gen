    # services/parser_service.py

import pdfplumber
from .extratores.factory import ExtratorFactory


class ParserService:

    @staticmethod
    def extrair_texto(pdf_file):
        texto = ""

        with pdfplumber.open(pdf_file) as pdf:
            for pagina in pdf.pages:
                t = pagina.extract_text()
                if t:
                    texto += t + "\n"

        return texto

    @classmethod
    def processar_pdf(cls, pdf_file, tipo=None):
        try:
            texto = cls.extrair_texto(pdf_file)
            print(f"Texto extraído: {texto[:500]}...")  # Debug primeiros 500 chars
            extrator = ExtratorFactory.obter_extrator(texto, tipo=tipo)
            return extrator.extrair(texto)
        except Exception as e:
            print(f"Erro no processamento do PDF: {e}")
            return {}