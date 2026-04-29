# services/extratores/factory.py

from .demanda import ExtratorDocumentoDemanda
from .compra import ExtratorDocumentoCompra

class ExtratorFactory:

    extratores = [
        ExtratorDocumentoDemanda(),
        ExtratorDocumentoCompra(),
    ]

    @classmethod
    def obter_extrator(cls, texto: str, tipo: str | None = None):
        if tipo:
            for extrator in cls.extratores:
                if getattr(extrator, 'tipo', None) == tipo:
                    return extrator
            raise ValueError(f"Tipo de extrator desconhecido: {tipo}")

        for extrator in cls.extratores:
            if extrator.pode_processar(texto):
                return extrator

        raise ValueError("Nenhum extrator compatível encontrado")