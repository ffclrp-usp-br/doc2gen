import re

bloco = """Item #1
Bem: 12345
Demanda: 202600032086 - FFCLRP - \ADM\DM Item de Despesa: 44905234, 449052341
Descricao"""

def limpar(txt): return txt.strip()

match = re.search(r'Demanda:\s*\d+\s*-\s*[^-\n]+-\s*(\\.*?)(?=\s+Item de Despesa:|\n|$)', bloco, re.IGNORECASE)
if match:
    print(limpar(match.group(1)))
else:
    print("No match")

