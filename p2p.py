"""
p2p.py — Menu interativo do simulador de busca em rede P2P.

Trabalho 7 — Computação Distribuída — Prof. Nabor C. Mendonça.

Uso:
    python p2p.py [arquivo_de_configuracao]
"""

import sys

from network import Network
from search import search


ALGOS = ["flooding", "informed_flooding", "random_walk", "informed_random_walk"]


def ask(prompt=""):
    """input() robusto: remove espacos e um eventual BOM (\\ufeff) que o
    Windows/PowerShell injeta no inicio do stdin redirecionado."""
    return input(prompt).strip().lstrip("\ufeff\xef\xbb\xbf").strip()


def carregar(path):
    try:
        net = Network.from_file(path)
    except FileNotFoundError:
        print(f"  Arquivo nao encontrado: {path}")
        return None
    except Exception as e:
        print(f"  Erro ao ler o arquivo: {e}")
        return None

    ok, results = net.validate()
    print(f"\n  Rede carregada de '{path}': {len(net.nodes)} nos.")
    print("  --- Validacoes ---")
    for nome, passou, msg in results:
        print(f"   [{'OK ' if passou else 'X  '}] {nome}: {msg}")
    if not ok:
        print("\n  >> Rede INVALIDA. Corrija o arquivo antes de buscar.\n")
        return None
    print("  >> Rede VALIDA.\n")
    return net


def mostrar_validacoes(net):
    ok, results = net.validate()
    print("  --- Validacoes ---")
    for nome, passou, msg in results:
        print(f"   [{'OK ' if passou else 'X  '}] {nome}: {msg}")
    print(f"  >> Rede {'VALIDA' if ok else 'INVALIDA'}.\n")


def desenhar(net):
    try:
        from visualize import draw_network
    except ImportError:
        print("  Instale: pip install networkx matplotlib\n")
        return
    draw_network(net, title="Rede P2P")


def pedir_busca(net):
    print("\n  --- Nova busca ---")
    origin = ask("  No de origem (ex: n1): ")
    if origin not in net.nodes:
        print(f"  No '{origin}' nao existe.\n")
        return
    resource = ask("  Recurso a buscar (ex: r18): ")
    try:
        ttl = int(ask("  TTL (ex: 5): "))
    except ValueError:
        print("  TTL invalido.\n")
        return

    print("  Algoritmos:")
    for i, a in enumerate(ALGOS, 1):
        print(f"    {i}. {a}")
    escolha = ask("  Escolha (1-4 ou nome): ")
    if escolha.isdigit() and 1 <= int(escolha) <= 4:
        algo = ALGOS[int(escolha) - 1]
    elif escolha in ALGOS:
        algo = escolha
    else:
        print("  Algoritmo invalido.\n")
        return

    result = search(net, origin, resource, ttl, algo)
    print("\n  " + str(result).replace("\n", "\n  ") + "\n")

    ver = ask("  Animar a busca? (s/N): ").lower()
    if ver == "s":
        try:
            from visualize import animate_search
            animate_search(net, result)
        except ImportError:
            print("  Instale: pip install networkx matplotlib\n")


def rodar_benchmark(net, path):
    try:
        from benchmark import run_benchmark
    except ImportError as e:
        print(f"  Erro: {e}\n")
        return
    run_benchmark([path])


def limpar_cache(net):
    for node in net.nodes.values():
        node.cache.clear()
    print("  Cache de todos os nos foi limpo (buscas informadas reiniciadas).\n")


MENU = """
============================================
   Simulador de Busca em Rede P2P
============================================
  1. Carregar arquivo de configuracao
  2. Validar rede
  3. Desenhar a rede
  4. Buscar recurso
  5. Rodar testes comparativos (benchmark)
  6. Limpar cache (reseta buscas informadas)
  0. Sair
--------------------------------------------"""


def main():
    net = None
    path = None

    # carrega da linha de comando, se passado
    if len(sys.argv) > 1:
        path = sys.argv[1]
        net = carregar(path)

    while True:
        print(MENU)
        op = ask("  Opcao: ")

        if op == "1":
            path = ask("  Caminho do arquivo (ex: configs/rede_exemplo.txt): ")
            net = carregar(path)
        elif op == "2":
            if net:
                mostrar_validacoes(net)
            else:
                print("  Carregue uma rede primeiro (opcao 1).\n")
        elif op == "3":
            if net:
                desenhar(net)
            else:
                print("  Carregue uma rede primeiro (opcao 1).\n")
        elif op == "4":
            if net:
                pedir_busca(net)
            else:
                print("  Carregue uma rede primeiro (opcao 1).\n")
        elif op == "5":
            if net and path:
                rodar_benchmark(net, path)
            else:
                print("  Carregue uma rede primeiro (opcao 1).\n")
        elif op == "6":
            if net:
                limpar_cache(net)
            else:
                print("  Carregue uma rede primeiro (opcao 1).\n")
        elif op == "0":
            print("  Encerrando.")
            break
        else:
            print("  Opcao invalida.\n")


if __name__ == "__main__":
    main()
