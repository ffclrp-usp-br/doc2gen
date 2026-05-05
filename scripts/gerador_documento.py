from docxtpl import DocxTemplate

doc = DocxTemplate("/home/marcelo/SEI/CONFERENCIA_PREGAO_14133-2021.docx")

context = {
    "numero_sei": "154.00002026/2026-85",
    "numero_compra": "3224/2026",
    "valor_total_estimado": "R$ 108.343,95",
    "objeto": "Aquisição de eletrodomésticos",
    "modalidade": "Pregão Eletrônico",
    "nome_agente_contratacao": "Regina",
    
}

doc.render(context)
doc.save("/home/marcelo/SEI/CONFERENCIA_PREGAO_14133-2021_gerado.docx")