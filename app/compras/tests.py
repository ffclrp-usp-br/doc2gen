from django.test import TestCase
from decimal import Decimal
from docx import Document
from .services.preenchedor_contrato import PreenchedorContratoService

class PreenchedorContratoServiceTest(TestCase):
    
    def test_formatar_moeda_brasileira(self):
        service = PreenchedorContratoService
        self.assertEqual(service.formatar_moeda_brasileira(1234.56), "R$ 1.234,56")
        self.assertEqual(service.formatar_moeda_brasileira(0), "R$ 0,00")
        self.assertEqual(service.formatar_moeda_brasileira(None), "R$ 0,00")
        self.assertEqual(service.formatar_moeda_brasileira(1000000), "R$ 1.000.000,00")

    def test_get_month_name(self):
        service = PreenchedorContratoService
        self.assertEqual(service.get_month_name(1), "janeiro")
        self.assertEqual(service.get_month_name(5), "maio")
        self.assertEqual(service.get_month_name(12), "dezembro")
        self.assertEqual(service.get_month_name(13), "")

    def test_valor_por_extenso(self):
        service = PreenchedorContratoService
        self.assertEqual(service.valor_por_extenso(Decimal("0.00")), "zero reais")
        self.assertEqual(service.valor_por_extenso(Decimal("1.00")), "um real")
        self.assertEqual(service.valor_por_extenso(Decimal("2.00")), "dois reais")
        self.assertEqual(service.valor_por_extenso(Decimal("1.50")), "um real e cinquenta centavos")
        self.assertEqual(service.valor_por_extenso(Decimal("0.05")), "cinco centavos")
        self.assertEqual(service.valor_por_extenso(Decimal("1000.00")), "mil reais")
        self.assertEqual(service.valor_por_extenso(Decimal("1234.56")), "mil, duzentos e trinta e quatro reais e cinquenta e seis centavos")
        self.assertEqual(service.valor_por_extenso(Decimal("1000000.00")), "um milhão de reais")
        self.assertEqual(service.valor_por_extenso(Decimal("2500300.40")), "dois milhões, quinhentos mil e trezentos reais e quarenta centavos")

    def test_localizar_secao(self):
        service = PreenchedorContratoService
        self.assertEqual(service.localizar_secao("REPRESENTANTE LEGAL DO CONTRATANTE:", "PREAMBULO"), "REPRESENTANTE_CONTRATANTE")
        self.assertEqual(service.localizar_secao("Seção de Dados da Contratada", "PREAMBULO"), "CONTRATADA")
        self.assertEqual(service.localizar_secao("Qualquer outro texto", "PREAMBULO"), "PREAMBULO")

    def test_substituir_texto_in_runs(self):
        service = PreenchedorContratoService
        doc = Document()
        p = doc.add_paragraph()
        p.add_run("Texto com ")
        p.add_run("[PLACEHOLDER]")
        p.add_run(" aqui.")
        
        # Test replace when fully in a run
        res = service.substituir_texto(p, "[PLACEHOLDER]", "VALOR")
        self.assertTrue(res)
        self.assertIn("Texto com VALOR aqui.", p.text)
        
        # Test when target is split across runs
        p2 = doc.add_paragraph()
        p2.add_run("Texto com [PLACE")
        p2.add_run("HOLDER] aqui.")
        res2 = service.substituir_texto(p2, "[PLACEHOLDER]", "VALOR_DIVIDIDO")
        self.assertTrue(res2)
        self.assertIn("Texto com VALOR_DIVIDIDO aqui.", p2.text)

    def test_substituir_texto_evita_loop_infinito(self):
        service = PreenchedorContratoService
        doc = Document()
        
        # Scenario 1: target == replacement
        p = doc.add_paragraph()
        p.add_run("Texto com [PLACEHOLDER]")
        res = service.substituir_texto(p, "[PLACEHOLDER]", "[PLACEHOLDER]")
        self.assertFalse(res)
        
        # Scenario 2: target in replacement
        p2 = doc.add_paragraph()
        p2.add_run("Texto com [PLACE")
        p2.add_run("HOLDER]")
        res2 = service.substituir_texto(p2, "[PLACEHOLDER]", "Novo [PLACEHOLDER] texto")
        self.assertTrue(res2)
        self.assertIn("Texto com Novo [PLACEHOLDER] texto", p2.text)
