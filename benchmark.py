"""
benchmark.py — Testes comparativos entre os algoritmos de busca.

Compara flooding, informed_flooding, random_walk e informed_random_walk em
diferentes topologias, medindo:
    - numero medio de mensagens trocadas
    - p95 de mensagens trocadas
    - numero medio de nos envolvidos
    - p95 de nos envolvidos
    - taxa de sucesso

Gera uma tabela no terminal e graficos de barras (salvos em PNG).

Uso:
    python benchmark.py                      # usa todos os configs/*.txt
    python benchmark.py configs/rede_x.txt   # usa arquivos especificos
"""

import os
import sys
import glob
import random

from network import Network
from search import search

ALGOS = ["flooding", "informed_flooding", "random_walk", "informed_random_walk"]
REPETICOES = 30   # repete buscas aleatorias p/ tirar media (algoritmos com random)
SEED = 123


def _percentil(valores, pct):
    """Calcula percentil com interpolacao linear, sem depender de numpy."""
    if not valores:
        return 0.0
    ordenados = sorted(valores)
    if len(ordenados) == 1:
        return float(ordenados[0])

    pos = (len(ordenados) - 1) * (pct / 100.0)
    baixo = int(pos)
    alto = min(baixo + 1, len(ordenados) - 1)
    if baixo == alto:
        return float(ordenados[baixo])

    peso_alto = pos - baixo
    peso_baixo = 1.0 - peso_alto
    return ordenados[baixo] * peso_baixo + ordenados[alto] * peso_alto


def _todos_recursos(net):
    res = {}
    for node in net.nodes.values():
        for r in node.resources:
            res[r] = node.id
    return res


def avaliar_rede(path, ttl=None):
    """Roda todos os algoritmos sobre uma rede e devolve metricas medias por algoritmo."""
    net = Network.from_file(path)
    ok, _ = net.validate()
    if not ok:
        print(f"  [pulando] rede invalida: {path}")
        return None

    if ttl is None:
        ttl = len(net.nodes)  # TTL generoso = nº de nós (garante alcance no flooding)

    recursos = _todos_recursos(net)
    nodes = list(net.nodes.keys())
    rng = random.Random(SEED)

    # pares (origem, recurso) de teste — amostra fixa para todos os algoritmos
    pares = []
    amostra_rng = random.Random(SEED)
    todos_recursos = list(recursos.keys())
    for _ in range(REPETICOES):
        origem = amostra_rng.choice(nodes)
        recurso = amostra_rng.choice(todos_recursos)
        pares.append((origem, recurso))

    metricas = {}
    for algo in ALGOS:
        msgs_amostras = []
        nos_amostras = []
        sucessos = 0
        # cache das buscas informadas e' reiniciado por algoritmo para medir do zero
        for node in net.nodes.values():
            node.cache.clear()
        for origem, recurso in pares:
            r = search(net, origem, recurso, ttl, algo, rng=rng)
            msgs_amostras.append(r.total_messages)
            nos_amostras.append(len(r.nodes_involved))
            sucessos += 1 if r.found else 0
        n = len(pares)
        metricas[algo] = {
            "msgs": sum(msgs_amostras) / n,
            "msgs_p95": _percentil(msgs_amostras, 95),
            "nos": sum(nos_amostras) / n,
            "nos_p95": _percentil(nos_amostras, 95),
            "sucesso": 100.0 * sucessos / n,
        }
    return net, metricas


def imprimir_tabela(nome_rede, metricas):
    print(f"\n  === {nome_rede} ===")
    print(f"  {'Algoritmo':<22}{'Msgs(med)':>11}{'Msgs(p95)':>11}{'Nos(med)':>11}{'Nos(p95)':>11}{'Sucesso%':>11}")
    print("  " + "-" * 77)
    for algo in ALGOS:
        m = metricas[algo]
        print(
            f"  {algo:<22}"
            f"{m['msgs']:>11.1f}{m['msgs_p95']:>11.1f}"
            f"{m['nos']:>11.1f}{m['nos_p95']:>11.1f}"
            f"{m['sucesso']:>11.1f}"
        )


def gerar_grafico(resultados, metrica="msgs", ylabel="Mensagens (media)",
                  fname="benchmark_msgs.png"):
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("  (matplotlib nao instalado — graficos pulados)")
        return

    redes = list(resultados.keys())
    x = range(len(redes))
    largura = 0.2

    plt.figure(figsize=(11, 6))
    for i, algo in enumerate(ALGOS):
        valores = [resultados[rede][algo][metrica] for rede in redes]
        plt.bar([p + i * largura for p in x], valores, width=largura, label=algo)

    plt.xticks([p + 1.5 * largura for p in x], redes, rotation=15)
    plt.ylabel(ylabel)
    plt.title(f"Comparacao de algoritmos de busca P2P — {ylabel}")
    plt.legend()
    plt.tight_layout()
    plt.savefig(fname, dpi=120)
    plt.close()
    print(f"  Grafico salvo: {fname}")


def run_benchmark(paths):
    resultados = {}
    for path in paths:
        out = avaliar_rede(path)
        if out is None:
            continue
        _, metricas = out
        nome = os.path.splitext(os.path.basename(path))[0]
        resultados[nome] = metricas
        imprimir_tabela(nome, metricas)

    if resultados:
        print()
        gerar_grafico(resultados, "msgs", "Mensagens (media)", "benchmark_msgs.png")
        gerar_grafico(resultados, "msgs_p95", "Mensagens (p95)", "benchmark_msgs_p95.png")
        gerar_grafico(resultados, "nos", "Nos envolvidos (media)", "benchmark_nos.png")
        gerar_grafico(resultados, "nos_p95", "Nos envolvidos (p95)", "benchmark_nos_p95.png")
        gerar_grafico(resultados, "sucesso", "Taxa de sucesso (%)", "benchmark_sucesso.png")
    return resultados


def main():
    if len(sys.argv) > 1:
        paths = sys.argv[1:]
    else:
        paths = sorted(glob.glob(os.path.join("configs", "*.txt")))
    if not paths:
        print("  Nenhum arquivo de configuracao encontrado em configs/")
        return
    run_benchmark(paths)


if __name__ == "__main__":
    main()
