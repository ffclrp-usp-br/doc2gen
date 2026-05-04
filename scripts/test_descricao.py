import re

def limpar(txt):
    if not txt:
        return ""
    return re.sub(r'\s+', ' ', txt).strip()

def extrair_descricao(bloco):
    m = re.search(
        r'(?:Bem:|Material:)[^\n]*\n(.*?)(?=\n\s*Demanda:|$)',
        bloco,
        re.S
    )

    if m:
        texto = limpar(m.group(1))
        if not texto:
            return ""

        # Encontrar a primeira ocorrência de vírgula ou ponto e vírgula
        m_delim = re.search(r'[,;]', texto)

        if m_delim:
            idx = m_delim.start()
            antes_delim = texto[:idx].strip()
            palavras_antes = antes_delim.split()

            if len(palavras_antes) <= 5:
                return antes_delim

        # Se não tem delimitador, ou se o delimitador está depois da 5ª palavra
        palavras = texto.split()
        return " ".join(palavras[:3])

    return ""

log1 = """Bem: 8812381 | BEC: 5186978 | Material: 340979 1 UNIDADE 1.356,14 1.356,14
COMPUTADOR, TIPO DESKTOP
Demanda: 202600032086 - FFCLRP - \ADM\DM Item de Despesa: 44905234, 449052341"""

log2 = """Bem: 8812381 | BEC: 5186978 | Material: 340979 1 UNIDADE 1.356,14 1.356,14
CADEIRA DE ESCRITORIO; GIRATORIA
Demanda: 202600032086"""

log3 = """Bem: 8812381 | BEC: 5186978 | Material: 340979 1 UNIDADE 1.356,14 1.356,14
CADEIRA DE ESCRITORIO COM RODINHAS PARA, SALA
Demanda: 202600032086"""

print(extrair_descricao(log1))
print(extrair_descricao(log2))
print(extrair_descricao(log3))
