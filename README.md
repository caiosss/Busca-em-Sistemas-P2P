# Simulador de Busca em Rede P2P

Trabalho 7 — Computação Distribuída — Prof. Nabor C. Mendonça

Simula uma rede P2P não estruturada e implementa 4 algoritmos de busca por
recursos: **flooding**, **informed_flooding**, **random_walk** e
**informed_random_walk**.

## Requisitos

```
pip install networkx matplotlib pandas
```

(Só `networkx` e `matplotlib` são realmente necessários; `pandas` é opcional.)

## Arquivos

| arquivo | função |
|---------|--------|
| `p2p.py` | menu interativo (programa principal) |
| `network.py` | leitura do config, modelo de dados e as 4 validações |
| `search.py` | os 4 algoritmos de busca + contagem de mensagens |
| `visualize.py` | desenho da rede e animação da busca |
| `benchmark.py` | testes comparativos → tabelas e gráficos PNG |
| `configs/` | topologias de exemplo (exemplo, linha, estrela, malha) |

## Como executar

### Menu interativo

```
python p2p.py                          # abre o menu sem rede carregada
python p2p.py configs/rede_exemplo.txt # já carrega e valida uma rede
```

Opções do menu:
1. Carregar arquivo de configuração
2. Validar rede
3. Desenhar a rede (janela gráfica)
4. Buscar recurso (pede nó de origem, recurso, TTL e algoritmo)
5. Rodar testes comparativos (benchmark)
6. Limpar cache (reinicia as buscas informadas)
0. Sair

Na opção 4, ao final é exibido o **número total de mensagens** e o **número
total de nós envolvidos** (Requisito III), com opção de **animar** a busca.

### Benchmark direto

```
python benchmark.py                       # todas as topologias em configs/
python benchmark.py configs/rede_malha.txt
```

Gera `benchmark_msgs.png`, `benchmark_msgs_p95.png`, `benchmark_nos.png`,
`benchmark_nos_p95.png` e `benchmark_sucesso.png`.

## Formato do arquivo de configuração

```
num_nodes: 12
min_neighbors: 2
max_neighbors: 4
resources:
  n1: r1, r2, r3
  n2: r4, r5
edges:
  n1, n2
  n1, n3
```

## Validações (Requisitos II)

O carregamento tambem confere se `num_nodes` bate com a quantidade de nos
definidos no arquivo. Em seguida, executa as 4 verificacoes pedidas no PDF:

1. Rede não pode estar particionada (deve haver caminho entre quaisquer 2 nós).
2. Grau de cada nó dentro de `[min_neighbors, max_neighbors]`.
3. Nenhum nó sem recurso.
4. Nenhuma aresta de um nó para ele mesmo.

## Convenção de contagem de mensagens

- **1 mensagem** = uma query trafegando por uma aresta (nó → vizinho).
- No flooding, mensagens enviadas a nós já visitados **contam** (é o desperdício
  característico da inundação) e são descartadas pelo nó receptor.
- Ao encontrar o recurso, contam-se também as mensagens de **resposta** que
  informam o nó de origem (saltos do caminho de volta).
- **Nós envolvidos** = nós que receberam/processaram a query.

## Algoritmos

- **flooding** — repassa a query a todos os vizinhos (≈ BFS). Acha quase sempre,
  mas gera muitas mensagens.
- **random_walk** — repassa a query a um vizinho aleatório por vez. Poucas
  mensagens, mas pode não achar com TTL baixo.
- **informed_flooding / informed_random_walk** — versões com **cache**: cada nó
  guarda a localização de recursos que já aprendeu; buscas seguintes ficam mais
  rápidas. O cache persiste durante a sessão (use a opção 6 para limpá-lo).
