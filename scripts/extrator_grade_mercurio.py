import pdfplumber
import re
import sys
import os
import json

# ==========================================================
# UTILIDADES
# ==========================================================
def limpar(txt):
    if not txt:
        return ""
    return re.sub(r'\s+', ' ', txt).strip()


def tem_documento(txt):
    return bool(re.search(
        r'(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})|(\d{3}\.\d{3}\.\d{3}-\d{2})',
        txt
    ))


# ==========================================================
# EXTRAÇÃO TEXTO
# ==========================================================
def extrair_texto(pdf_path):
    paginas = []

    with pdfplumber.open(pdf_path) as pdf:
        for pagina in pdf.pages:
            txt = pagina.extract_text(
                x_tolerance=2,
                y_tolerance=2
            )
            if txt:
                paginas.append(txt)

    return "\n".join(paginas)


# ==========================================================
# CABEÇALHO
# ==========================================================
def extrair_numero_compra(texto):
    m = re.search(r'Documento da Compra:\s*(\d+)\s*/\s*(\d+)', texto)
    return f"{m.group(1)}" if m else None


def extrair_numero_sei(texto):
    m = re.search(r'Processo:\s*([\d\.]+/\d{4}-\d+)', texto)
    return m.group(1) if m else None


def extrair_modalidade(texto):
    m = re.search(r'Modalidade:\s*(.+?)(?:\n|$)', texto)
    return limpar(m.group(1)) if m else None


def extrair_valor_total_previsto(texto):
    m = re.search(
        r'Valor Total Previsto[\s\S]{0,150}?(\d{1,3}(?:\.\d{3})*,\d{2})',
        texto
    )
    return m.group(1) if m else None


# ==========================================================
# DIVIDIR ITENS
# ==========================================================
def extrair_blocos_itens(texto):
    linhas = texto.split("\n")

    blocos = []
    atual = []
    iniciou = False

    for linha in linhas:

        if re.match(r'^Item\s*#\d+', linha.strip()):
            iniciou = True

            if atual:
                blocos.append("\n".join(atual))
                atual = []

        if iniciou:
            atual.append(linha)

    if atual:
        blocos.append("\n".join(atual))

    return blocos


# ==========================================================
# DESCRIÇÃO
# ==========================================================
def extrair_descricao(bloco):
    m = re.search(
        r'Material:\s*\d+\s+(.*?)\s+\d+(?:,\d+)?\s+UNIDADE',
        bloco,
        re.S
    )

    if m:
        return limpar(m.group(1))

    return ""



# ==========================================================
# NÚMERO DE DEMANDA
# Ex:
# Demanda: 202600000753 - FFCLRP - \ADM\DIR
# ==========================================================
def extrair_numero_demanda(bloco):
    m = re.search(
          r'\s*(\d{12})',
        bloco
    )

    if m:
        return limpar(m.group(0))

    return None


# ==========================================================
# CENTRO DE DESPESA
# Ex:
# Demanda: 202600000753 - FFCLRP - \ADM\DIR
# ==========================================================
def extrair_centro_despesa(bloco):
    m = re.search(
         r'Demanda:\s*\d+\s*-\s*[^-\n]+-\s*(\\.*?)(?=\s+Item de Despesa:|\n|$)',
        bloco
    )

    if m:
        return limpar(m.group(1))

    return None




# ==========================================================
# GRUPO ORÇAMENTÁRIO
# valor padrão solicitado
# ==========================================================
def extrair_grupo_orcamentario(bloco):
    return "59.000"


# ==========================================================
# PESQUISAS
# ==========================================================
def extrair_pesquisas(bloco):

    m = re.search(
        r'Contratação gov\.br:(.*?)(?:Método de Cálculo do Valor Unitário:)',
        bloco,
        re.S | re.I
    )

    if not m:
        return []

    tabela = m.group(1)

    linhas = [limpar(x) for x in tabela.split("\n") if limpar(x)]

    pesquisas = []

    for i in range(len(linhas) - 1):

        linha = linhas[i]

        if tem_documento(linha):

            fornecedor = linha
            proxima = linhas[i + 1]

            m_val = re.search(
                r'(\d{1,3}(?:\.\d{3})*,\d{2})',
                proxima
            )

            if m_val:
                pesquisas.append({
                    "fornecedor": fornecedor,
                    "valor_unitario": m_val.group(1)
                })

    # remove duplicados
    final = []
    vistos = set()

    for p in pesquisas:
        chave = (p["fornecedor"], p["valor_unitario"])

        if chave not in vistos:
            vistos.add(chave)
            final.append(p)

    return final


# ==========================================================
# ITEM
# ==========================================================
def extrair_item(bloco):

    m = re.search(r'Item\s*#(\d+)', bloco)
    numero = m.group(1) if m else None

    m = re.search(r'Bem:\s*(\d+)\s*\|\s*BEC:\s*(\d+)', bloco)
    codigo_bem = m.group(1) if m else None
    codigo_bec = m.group(2) if m else None

    m = re.search(r'Material:\s*(\d+)', bloco)
    material = m.group(1) if m else None

    m = re.search(r'Item de Despesa:\s*([0-9,\s]+)', bloco)
    item_despesa = limpar(m.group(1)) if m else None

    m = re.search(
        r'(\d+(?:,\d+)?)\s+UNIDADE\s+(\d{1,3}(?:\.\d{3})*,\d{2})',
        bloco
    )

    quantidade = m.group(1) if m else None
    valor_prev = m.group(2) if m else None

    return {
        "item": numero,
        "numero_demanda": extrair_numero_demanda(bloco),  
        "codigo_bem": codigo_bem,
        "codigo_bec": codigo_bec,
        "codigo_material": material,
        "item_despesa": item_despesa,
        "centro_despesa": extrair_centro_despesa(bloco),
        "grupo_orcamentario": extrair_grupo_orcamentario(bloco),
        "descricao": extrair_descricao(bloco),
        "quantidade": quantidade,
        "valor_unitario_previsto": valor_prev,
        "pesquisas": extrair_pesquisas(bloco)
    }


# ==========================================================
# EXTRAÇÃO TOTAL
# ==========================================================
def extrair_dados(pdf_path):

    texto = extrair_texto(pdf_path)

    dados = {
        "numero_compra": extrair_numero_compra(texto),
        "numero_sei": extrair_numero_sei(texto),
        "modalidade": extrair_modalidade(texto),
        "valor_total_previsto": extrair_valor_total_previsto(texto),
        "itens": []
    }

    for bloco in extrair_blocos_itens(texto):
        item = extrair_item(bloco)

        if item["item"]:
            dados["itens"].append(item)

    return dados


# ==========================================================
# MAIN
# ==========================================================
def main():

    if len(sys.argv) != 2:
        print("Uso: python extrator.py arquivo.pdf")
        sys.exit(1)

    arquivo = sys.argv[1]

    if not os.path.exists(arquivo):
        print("Arquivo não encontrado.")
        sys.exit(1)

    dados = extrair_dados(arquivo)

    print("\n================ CABEÇALHO ================\n")
    print("Compra:", dados["numero_compra"])
    print("SEI:", dados["numero_sei"])
    print("Modalidade:", dados["modalidade"])
    print("Valor Total Previsto:", dados["valor_total_previsto"])

    print("\n================ ITENS ================\n")

    for item in dados["itens"]:

        print("ITEM", item["item"])
        print("Código Bem:", item["codigo_bem"])
        print("Código BEC:", item["codigo_bec"])
        print("Material:", item["codigo_material"])
        print("Item Despesa:", item["item_despesa"])
        print("Número de Demanda:", item["numero_demanda"])
        print("Centro de Despesa:", item["centro_despesa"])
        print("Grupo Orçamentário:", item["grupo_orcamentario"])
        print("Descrição:", item["descricao"])
        print("Quantidade:", item["quantidade"])
        print("Valor Previsto:", item["valor_unitario_previsto"])

        print("\nPESQUISAS:")

        if item["pesquisas"]:
            for p in item["pesquisas"]:
                print("Fornecedor:", p["fornecedor"])
                print("Valor:", p["valor_unitario"])
                print()
        else:
            print("Nenhuma localizada")

        print("--------------------------------------\n")

    with open("resultado_extracao.json", "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

    print("Arquivo resultado_extracao.json gerado.")


if __name__ == "__main__":
    main()