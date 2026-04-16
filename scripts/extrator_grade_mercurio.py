import pdfplumber
import re
import sys
import os


# -------------------------
# EXTRAÇÃO DE TEXTO
# -------------------------
def extrair_texto(pdf_path):
    texto_completo = ""

    with pdfplumber.open(pdf_path) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if texto:
                texto_completo += texto + "\n"

    print(texto_completo)  # DEBUG (remova depois)
    return texto_completo


# -------------------------
# NÚMERO DA COMPRA
# -------------------------
def extrair_numero_compra(texto):
    match = re.search(r'Compra:\s*(\d+)\s*/\s*(\d{4})', texto, re.IGNORECASE)
    if match:
        return f"{match.group(1)}/{match.group(2)}"
    return None


# -------------------------
# SEPARAR ITENS (CORRIGIDO)
# -------------------------
def extrair_blocos_itens_compra(texto):
    linhas = texto.split("\n")

    blocos = []
    bloco_atual = []

    for linha in linhas:
        linha = linha.strip()

        # Detecta início de item
        if re.match(r'^Item\s+\d+', linha, re.IGNORECASE):
            if bloco_atual:
                blocos.append("\n".join(bloco_atual))
                bloco_atual = []

        if linha:
            bloco_atual.append(linha)

    if bloco_atual:
        blocos.append("\n".join(bloco_atual))

    return blocos


# -------------------------
# EXTRAIR COTAÇÕES (ROBUSTO)
# -------------------------
def extrair_cotacoes(bloco):
    linhas = bloco.split("\n")
    cotacoes = []

    buffer = ""

    for linha in linhas:
        linha = linha.strip()

        if not linha:
            continue

        buffer += " " + linha

        # fim de uma cotação
        if " Sim " in buffer or buffer.endswith(" Sim"):

            pattern = r'''
                (\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})?   # CNPJ opcional
                \s*
                (\d+)\s+                             # índice
                (\d{2}/\d{2}/\d{4})\s+               # data
                (.*?)\s+                             # empresa
                (\d+,\d+)\s+                         # quantidade
                ([\d\.,]+)\s+                        # valor unitário
                ([\d\.,]+)\s+                        # valor total
                Sim
            '''

            match = re.search(pattern, buffer, re.VERBOSE)

            if match:
                cotacoes.append({
                    "empresa": match.group(4).strip(),
                    "quantidade": match.group(5),
                    "valor_unitario": match.group(6),
                })

            buffer = ""

    return cotacoes


# -------------------------
# EXTRAIR DADOS DO ITEM
# -------------------------
def extrair_dados_item_compra(bloco):

    primeira_linha = bloco.split("\n")[0]

    pattern = r'''
        Item\s+(\d+)\s*\|\s*
        Lote:\s*\|\s*
        Bem:\s*(\d+)\s*\|\s*
        BEC:\s*(\d+)\s*\|\s*
        (.*?)\s*\|\s*
        Método:\s*(.*?)\s*\|\s*
        Valor\s*Prev\.:\s*([\d\.,]+)
    '''

    match = re.search(pattern, primeira_linha, re.VERBOSE)

    if match:
        item_num = match.group(1)
        bem = match.group(2)
        bec = match.group(3)
        descricao = match.group(4).strip()
        metodo = match.group(5)
        valor_prev = match.group(6)
    else:
        item_num = bem = bec = descricao = metodo = valor_prev = None

    cotacoes = extrair_cotacoes(bloco)

    return {
        "item": item_num,
        "codigo_contabiliza": bec,
        "codigo_bem": bem,
        "descricao": descricao,
        "metodo": metodo,
        "valor_previsto": valor_prev,
        "cotacoes": cotacoes
    }


# -------------------------
# EXTRAÇÃO COMPLETA
# -------------------------
def extrair_dados(pdf_path):
    texto = extrair_texto(pdf_path)

    dados = {}

    dados["numero_compra"] = extrair_numero_compra(texto)

    blocos = extrair_blocos_itens_compra(texto)

    itens = []
    for bloco in blocos:
        item = extrair_dados_item_compra(bloco)

        # evita blocos inválidos
        if any([item["codigo_contabiliza"], item["codigo_bem"], item["descricao"]]):
            itens.append(item)

    dados["itens"] = itens

    return dados


# -------------------------
# CLI
# -------------------------
def main():
    if len(sys.argv) != 2:
        print("Uso: python extrator_compra.py <arquivo.pdf>")
        sys.exit(1)

    pdf_path = sys.argv[1]

    if not os.path.exists(pdf_path):
        print(f"Erro: arquivo '{pdf_path}' não encontrado.")
        sys.exit(1)

    if not pdf_path.lower().endswith(".pdf"):
        print("Erro: o arquivo precisa ser um PDF.")
        sys.exit(1)

    try:
        dados = extrair_dados(pdf_path)
    except Exception as e:
        print(f"Erro ao processar o PDF: {e}")
        sys.exit(1)

    print("\n=== DADOS EXTRAÍDOS ===\n")

    print(f"Número da compra: {dados['numero_compra']}")

    print("\n--- ITENS ---\n")

    for i, item in enumerate(dados["itens"], start=1):
        print(f"\nITEM {i}")
        print(f"Código Contabiliza: {item['codigo_contabiliza']}")
        print(f"Código Bem: {item['codigo_bem']}")
        print(f"Descrição: {item['descricao']}")
        print(f"Valor Previsto: {item['valor_previsto']}")

        print("\n  COTAÇÕES:")
        for c in item["cotacoes"]:
            print(f"   - Empresa: {c['empresa']}")
            print(f"     Quantidade: {c['quantidade']}")
            print(f"     Valor Unitário: {c['valor_unitario']}")
            print()


if __name__ == "__main__":
    main()