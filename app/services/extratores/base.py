# services/extratores/base.py

from abc import ABC, abstractmethod

class ExtratorBase(ABC):

    @abstractmethod
    def pode_processar(self, texto: str) -> bool:
        """Define se esse extrator é adequado para o documento"""
        pass

    @abstractmethod
    def extrair(self, texto: str) -> dict:
        """Extrai os dados do documento"""
        pass