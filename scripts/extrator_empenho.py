import re
import sys
import os
import pdfplumber
from pathlib import Path


def extract_nota_empenho(pdf_path: str) -> dict:
    """
    Extrai informações de uma Nota de Empenho USP.
    """

    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join(
            page.extract_text() or ""
            for page in pdf.pages
        )

    data = {}

    # Número da NE
    m = re.search(r"\b(\d{8}/\d{4})\b", text)
    if m:
        data["numero"] = m.group(1)

    # Data do empenho
    m = re.search(
        r"Data do Empenho:\s*(\d{2}/\d{2}/\d{4})",
        text
    )
    if m:
        data["data_empenho"] = m.group(1)

    # Dotação
    m = re.search(
        r"Dotação:\s*([0-9]+/[0-9]{4})",
        text,
        re.MULTILINE    
    )
    if m:
        data["dotacao"] = m.group(1)

    # Grupo
    m = re.search(
        r"Grupo:\s*(.+)",
        text,
        re.MULTILINE
    )

    if m:
        data["grupo"] = m.group(1).strip()

    # Unidade
    m = re.search(
        r"(\d+\s*-\s*Faculdade.*?Ribeirão Preto)",
        text
    )
    if m:
        data["unidade"] = m.group(1)

    # Credor
    m = re.search(
        r"Credor:\s*(.+)",
        text
    )
    if m:
        data["organizacao_nome"] = m.group(1).strip()

    # CNPJ
    m = re.search(
        r"C\.N\.P\.J\.\s*([\d./-]+)",
        text
    )
    if m:
        data["organizacao_cnpj"] = m.group(1)

    # Fonte de recurso
    m = re.search(
        r"Fonte de Recurso:\s*(\d+)",
        text
    )
    if m:
        data["fonte_recurso"] = (
            f"{m.group(1)} - Tesouro do Estado"
        )

    # Funcional Programática
    m = re.search(
        r"(\d+\s*-\s*\d+\s*-\s*\d+\s*-\s*\d+\s+Ensino.*?Estaduais)",
        text,
        re.DOTALL
    )
    if m:
        data["funcional_programatica"] = (
            " ".join(m.group(1).split())
        )

    # Campos fixos do layout
    data["categoria_economica"] = (
        "3 - Despesas Correntes"
    )

    data["grupo_despesa"] = (
        "3 - Outras Despesas Correntes"
    )

    data["modalidade"] = (
        "90 - Aplicações Diretas"
    )

    data["elemento"] = (
        "30 - Material de Consumo"
    )

    data["item"] = (
        "50 - Peças de Reposição e Acessórios"
    )

    m = re.search(r'Total\s+R\$\s*([\d\.]+,\d{2})', 
        text, 
        re.IGNORECASE
    )
    if m:
        data["valor"] = m.group(1)
    

    return data


def print_result(data: dict):
    print()
    print(f"Data do Empenho: {data.get('data_empenho', '')}")
    print(f"Número: {data.get('numero', '')}")
    print()

    print(f"Dotação: {data.get('dotacao', '')}")
    print(f"Grupo: {data.get('grupo', '')}")
    print(f"Unidade: {data.get('unidade', '')}")
    print(f"Categoria Econômica: {data.get('categoria_economica', '')}")
    print(f"Grupo de Despesa: {data.get('grupo_despesa', '')}")
    print(f"Modalidade: {data.get('modalidade', '')}")
    print(f"Elemento: {data.get('elemento', '')}")
    print(f"Item: {data.get('item', '')}")
    print(
        f"Funcional Programática: "
        f"{data.get('funcional_programatica', '')}"
    )
    print(
        f"Fonte de Recurso: "
        f"{data.get('fonte_recurso', '')}"
    )

    print()
    print(
        f"Organização (nome): "
        f"{data.get('organizacao_nome', '')}"
    )
    print(
        f"Organização (CNPJ): "
        f"{data.get('organizacao_cnpj', '')}"
    )

    print(f"Valor: {data.get('valor', '')}")

if __name__ == "__main__":

    
    if len(sys.argv) != 2:
        print("Uso: python extrator_empenho.py arquivo.pdf")
        sys.exit(1)

    arquivo = sys.argv[1]

    if not os.path.exists(arquivo):
        print("Arquivo não encontrado.")
        sys.exit(1)

    resultado = extract_nota_empenho(arquivo)

    print_result(resultado)