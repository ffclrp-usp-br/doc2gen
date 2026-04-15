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

    print (texto_completo)  # Para depuração, pode ser removido depois

    return texto_completo


# -------------------------
# NÚMERO DA DEMANDA
# -------------------------
def extrair_numero_demanda(texto):
    match = re.search(r'N[ºo\.]?\s*(\d+)\s*-\s*Ano\s*(\d{4})', texto, re.IGNORECASE)
    if match:
        return f"{match.group(1)}/{match.group(2)}"
    return None


# -------------------------
# UNIDADE DE DESPESA (ROBUSTO)
# -------------------------
def extrair_unidade_despesa(texto):
    match = re.search(r'Unidade\s+Despesa:\s*(\d+)', texto, re.IGNORECASE)
    if match:
        return match.group(1)
    return None


# -------------------------
# CAMPOS SIMPLES
# -------------------------
def extrair_campo(texto, label):
    pattern = rf'{label}[:\s]+(.+)'
    match = re.search(pattern, texto, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


# -------------------------
# IDENTIFICAR BLOCOS DE ITENS
# -------------------------
def extrair_blocos_itens(texto):
    linhas = texto.split("\n")
    blocos = []
    bloco_atual = []
    capturando = False

    for linha in linhas:
        # Detecta início de item (linha da tabela)
        if re.match(r'^\d+\s+\d+\s+\d+', linha):
            if bloco_atual:
                blocos.append("\n".join(bloco_atual))
                bloco_atual = []

            capturando = True

        if capturando:
            bloco_atual.append(linha)

    if bloco_atual:
        blocos.append("\n".join(bloco_atual))

    return blocos


# -------------------------
# EXTRAIR ITENS DE DESPESA DENTRO DO BLOCO
# -------------------------
def extrair_itens_despesa_do_bloco(linhas):
    itens = []

    for linha in linhas:
        # Extrai códigos válidos direto, sem filtrar linha
        encontrados = re.findall(r'\b(3[3-9]\d{6}|4[4-9]\d{6})\b', linha)

        if encontrados:
            itens.extend(encontrados)

    # remove duplicados mantendo ordem
    vistos = set()
    itens_unicos = []
    for i in itens:
        if i not in vistos:
            vistos.add(i)
            itens_unicos.append(i)

    return itens_unicos

# -------------------------
# EXTRAIR DADOS DE UM ITEM
# -------------------------

def extrair_dados_item(bloco):
    linhas = bloco.split("\n")

    if not linhas:
        return None

    linha = linhas[0].strip()
    partes = re.split(r'\s+', linha)

    if len(partes) < 2:
        return None

    item = partes[0]

    # =========================
    # CLASSE CONTABILIZA (4 dígitos ou vazio)
    # =========================
    idx = 1

    if re.match(r'^\d{4}$', partes[idx]):
        classe_contabiliza = partes[idx]
        idx += 1
    else:
        classe_contabiliza = None

    # =========================
    # CAMPOS SEGUINTES (dinâmico)
    # =========================
    cod_mat = None
    cod_bem = None
    cod_contabiliza = None
    cod_compras = None
    qtd = None
    unidade = None

    numeros = []
    textos = []

    for p in partes[idx:]:
        if re.match(r'^\d+$', p):
            numeros.append(p)
        else:
            textos.append(p)

    # =========================
    # ATRIBUIÇÃO INTELIGENTE
    # =========================

    # códigos geralmente grandes (>= 5 dígitos)
    codigos = [n for n in numeros if len(n) >= 5]

    if len(codigos) >= 1:
        cod_mat = codigos[0]
    if len(codigos) >= 2:
        cod_bem = codigos[1]
    if len(codigos) >= 3:
        cod_contabiliza = codigos[2]
    if len(codigos) >= 4:
        cod_compras = codigos[3]

    # quantidade = número pequeno (geralmente <= 4 dígitos)
    candidatos_qtd = [n for n in numeros if len(n) <= 4]

    if candidatos_qtd:
        qtd = candidatos_qtd[-1]
    else:
        qtd = None

    # unidade = tudo após a quantidade
    try:
        if qtd:
            idx_qtd = partes.index(qtd)
            unidade = " ".join(partes[idx_qtd + 1:])
        else:
            unidade = None
    except:
        unidade = None

    itens_despesa = extrair_itens_despesa_do_bloco(linhas)

    # =========================
    # VALIDAÇÃO OBRIGATÓRIA PARA DESCARTAR NULOS
    # =========================
    if vazio(cod_mat) or vazio(cod_bem) or vazio(cod_contabiliza):
        return None
        
    
    return {
        "item": item,
        "classe_contabiliza": classe_contabiliza,
        "codigo_material": cod_mat,
        "codigo_bem": cod_bem,
        "codigo_contabiliza": cod_contabiliza,
        "codigo_compras_gov": cod_compras,
        "qtd": qtd,
        "unidade": unidade,
        "item_despesa": itens_despesa
    }





# -------------------------
# EXTRAÇÃO COMPLETA
# -------------------------
def extrair_dados(pdf_path):
    texto = extrair_texto(pdf_path)

    dados = {}

    dados["numero_demanda"] = extrair_numero_demanda(texto)
    dados["unidade_despesa"] = extrair_unidade_despesa(texto)
    dados["centro_gerencial"] = extrair_campo(texto, "Centro Gerencial")
    dados["codigo_contabiliza"] = extrair_campo(texto, "Código Contabiliza")

    blocos = extrair_blocos_itens(texto)

    itens = []
    for bloco in blocos:
        item = extrair_dados_item(bloco)
        if item:
            itens.append(item)

    dados["itens"] = itens

    return dados


def vazio(valor):
    return valor is None or str(valor).strip() == ""



# -------------------------
# CLI
# -------------------------
def main():
    if len(sys.argv) != 2:
        print("Uso: python extrator.py <arquivo.pdf>")
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

    for chave, valor in dados.items():
        if chave != "itens":
            print(f"{chave}: {valor}")

    print("\n--- ITENS ---\n")
    for item in dados["itens"]:
        print(item)


if __name__ == "__main__":
    main()