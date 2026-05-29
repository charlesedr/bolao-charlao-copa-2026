"""Processa o Anexo C (alocação dos 3º colocados) e gera data/mapeamento_terceiros.csv.

O arquivo bruto (data/anexo_c_raw.txt) vem auto-traduzido do inglês para português,
corrompendo alguns códigos: 'UM'->A, 'EU'->I (colunas de grupos) e '3 mil'->'3K'.
Este script reverte isso e VALIDA cada linha com um invariante de bijeção:
os 8 terceiros alocados devem ser exatamente os 8 grupos que classificaram.
"""
import csv
import re
import sys
from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / "data" / "anexo_c_raw.txt"
OUT = Path(__file__).resolve().parents[1] / "data" / "mapeamento_terceiros.csv"

# Vencedores de grupo que enfrentam um 3º colocado, na ordem das colunas do anexo.
VENCEDORES = ["1A", "1B", "1D", "1E", "1G", "1I", "1K", "1L"]
REVERTER = {"UM": "A", "EU": "I"}


def main() -> int:
    if not RAW.exists():
        print(f"ERRO: salve o arquivo do anexo em {RAW}")
        return 1

    texto = RAW.read_text(encoding="utf-8", errors="ignore")
    texto = texto.replace("3 mil", "3K")  # 3K traduzido como "3 mil"

    combinacoes: dict[frozenset, dict[str, str]] = {}
    erros: list[str] = []
    linhas_ok = 0

    for linha in texto.splitlines():
        tokens = linha.split()
        if not tokens or not tokens[0].isdigit():
            continue
        num = tokens[0]
        quali: list[str] = []
        aloc: list[str] = []
        for tk in tokens[1:]:
            if re.fullmatch(r"3[A-L]", tk):
                aloc.append(tk[1:])
            else:
                g = REVERTER.get(tk, tk)
                if re.fullmatch(r"[A-L]", g):
                    quali.append(g)

        # Validações (invariante de bijeção)
        if len(quali) != 8 or len(aloc) != 8:
            erros.append(f"linha {num}: quali={len(quali)} aloc={len(aloc)} (esperado 8/8)")
            continue
        if set(quali) != set(aloc):
            erros.append(f"linha {num}: quali={sorted(quali)} != aloc={sorted(aloc)}")
            continue

        chave = frozenset(quali)
        if chave in combinacoes:
            erros.append(f"linha {num}: combinação duplicada {sorted(quali)}")
            continue
        combinacoes[chave] = dict(zip(VENCEDORES, aloc, strict=True))
        linhas_ok += 1

    print(f"Linhas válidas: {linhas_ok} (esperado 495)")
    print(f"Combinações distintas: {len(combinacoes)}")
    if erros:
        print(f"\n{len(erros)} ERROS:")
        for e in erros[:30]:
            print("  -", e)
        return 1
    if linhas_ok != 495:
        print("ERRO: número de linhas válidas diferente de 495.")
        return 1

    # Gera o CSV final
    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["combinacao", *VENCEDORES])
        for chave, aloc in sorted(combinacoes.items(), key=lambda kv: "".join(sorted(kv[0]))):
            w.writerow(["".join(sorted(chave)), *[aloc[v] for v in VENCEDORES]])

    print(f"\nOK: {OUT} gerado com {len(combinacoes)} combinações validadas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
