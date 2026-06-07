# Resumo do Projeto — Busca em Redes P2P

Trabalho 7 — Computação Distribuída — Prof. Nabor C. Mendonça

Este documento explica **o que cada arquivo faz**, **onde está cada coisa** e
**em que ponto do código cada requisito do roteiro é atendido**. Serve como guia
para a equipe na hora de estudar, apresentar e demonstrar o programa.

---

## 1. Visão geral

O programa simula uma **rede P2P não estruturada** e permite buscar recursos
mantidos pelos nós usando 4 algoritmos. Premissas (conforme o professor):

- Um nó **não conhece a rede inteira** — só conhece seus **vizinhos imediatos** e
  os **recursos que ele mesmo guarda**.
- A busca descobre se um recurso existe em **algum** nó da rede.
- **TTL** limita o número de saltos; decrementa a cada salto; ao chegar a 0, a
  mensagem é descartada.
- A métrica de comparação é o **número total de mensagens trocadas** (e o número
  de nós envolvidos).

A simulação é feita sobre um **grafo** (o professor disse que "é basicamente busca
em grafo, em largura e em profundidade"). Não há sockets/processos reais — isso
facilita contar mensagens e animar a busca, sem mudar a lógica dos algoritmos.

---

## 2. O que cada arquivo faz

| Arquivo | Responsabilidade |
|---------|------------------|
| `p2p.py` | **Programa principal.** Menu interativo no terminal que amarra tudo. |
| `network.py` | Leitura do arquivo de configuração, modelo de dados (nó/rede) e as **4 validações**. |
| `search.py` | Os **4 algoritmos de busca** e a **contagem de mensagens e nós**. |
| `visualize.py` | **Desenho** da rede e **animação** da busca (requisitos opcionais). |
| `benchmark.py` | **Testes comparativos** entre os algoritmos → tabelas + gráficos PNG. |
| `configs/` | Arquivos de **topologias** de exemplo (entrada do programa). |
| `rede_invalida_exemplo.txt` | Rede com os 4 erros de propósito, para demonstrar as validações. |
| `README.md` | Instruções rápidas de instalação e uso. |
| `PLANO_IMPLEMENTACAO.md` | Plano de implementação (visão de projeto). |
| `resumo.md` | Este documento. |
| `benchmark_*.png` | Gráficos gerados pelo benchmark (entram nos slides). |

---

## 3. Detalhamento por arquivo (com linhas)

### 3.1 `network.py` — leitura, modelo e validações

- **`class Node`** (linha 11) — um peer da rede:
  - `id` — identificador (ex.: `n1`)
  - `resources` — conjunto de recursos que **este** nó guarda
  - `neighbors` — ids dos vizinhos imediatos (tudo que o nó "enxerga")
  - `cache` — `recurso -> nó` onde ele **já soube** que o recurso está (usado só
    pelas buscas informadas)
  - `has_resource()` (linha 21) — o nó tem tal recurso?
- **`class Network`** (linha 28) — a rede inteira:
  - `from_file(path)` (linha 41) — **lê o arquivo de configuração** (parser do
    formato texto: cabeçalho, seção `resources:` e seção `edges:`).
  - `_add_edge()` (linha 113) — cria aresta não-direcionada entre dois nós.
  - **`validate()`** (linha 136) — roda as **4 validações** e devolve
    `(ok, lista_de_resultados)`.
  - `_is_connected()` (linha 185) — BFS para checar se a rede está conectada.

### 3.2 `search.py` — algoritmos e contagem

- **`class SearchResult`** (linha 30) — resultado de uma busca:
  - `found`, `located_at`, `total_messages`, `nodes_involved`, `events`.
  - `_msg(src, dst, tipo)` (linha 44) — **conta 1 mensagem** e grava o evento
    para a animação.
  - `__str__()` (linha 49) — formata a saída (status, mensagens, nós).
- `_shortest_path()` (linha 66) — menor caminho (BFS) usado na resposta.
- `_send_response()` (linha 86) — conta as mensagens da **resposta voltando à
  origem** e atualiza o **cache** dos nós no caminho (é assim que a busca
  informada "aprende").
- **`flooding()`** (linha 104) — inundação (BFS). Param `informed=True` ativa o
  uso do cache → vira `informed_flooding`.
- **`random_walk()`** (linha 184) — passeio aleatório. Param `informed=True` →
  `informed_random_walk`.
- **`search()`** (linha 259) — **dispatcher**: recebe o nome do algoritmo
  (`flooding`, `informed_flooding`, `random_walk`, `informed_random_walk`) e
  chama a função certa.

### 3.3 `p2p.py` — menu interativo (programa principal)

- `ask()` (linha 19) — `input()` robusto (limpa espaços e o BOM que o Windows
  injeta no stdin redirecionado).
- `carregar()` (linha 25) — lê o arquivo, roda as validações e mostra o resultado.
- `mostrar_validacoes()` (linha 47) — exibe as 4 verificações (opção 2 do menu).
- `desenhar()` (linha 55) — desenho gráfico da rede (opção 3).
- **`pedir_busca()`** (linha 64) — pergunta `node_id`, `resource_id`, `ttl`,
  `algo`, executa a busca e imprime **mensagens + nós envolvidos** (opção 4).
- `rodar_benchmark()` (linha 101) — dispara os testes comparativos (opção 5).
- `limpar_cache()` (linha 110) — zera o cache de todos os nós (opção 6).
- `main()` (linha 130) — laço do menu.

### 3.4 `visualize.py` — desenho e animação (opcionais)

- `draw_network()` (linha 30) — desenha a rede estática (nós, recursos, arestas).
- `animate_search()` (linha 50) — **anima** a busca passo a passo a partir da
  lista `events`: ilumina a aresta de cada mensagem e colore os nós (origem,
  visitados, descartados, encontrado).

### 3.5 `benchmark.py` — testes comparativos

- `avaliar_rede()` (linha 38) — roda os 4 algoritmos sobre uma rede, com vários
  pares (origem, recurso), e calcula **médias**: mensagens, nós, % de sucesso.
- `imprimir_tabela()` (linha 82) — imprime a tabela no terminal.
- `gerar_grafico()` (linha 91) — gera os gráficos de barras (PNG).
- `run_benchmark()` (linha 118) — roda tudo para todas as topologias.

---

## 4. Mapa Requisito (roteiro) → onde está no código

### Requisitos I — formato do arquivo de entrada
- **Onde:** `network.py::Network.from_file()` (linha 41).
- Lê `num_nodes`, `min_neighbors`, `max_neighbors`, a seção `resources:` e a
  seção `edges:`. Exemplos prontos em `configs/`.

### Requisitos II — as 4 validações
Todas em `network.py::validate()` (linha 136):
1. **Rede não particionada** → via `_is_connected()` (BFS), linha 185.
2. **Grau entre min e max vizinhos** → laço comparando `len(neighbors)` com
   `min_neighbors`/`max_neighbors`.
3. **Nenhum nó sem recurso** → checa `resources` vazio.
4. **Sem aresta de um nó para ele mesmo** → procura `n.id in n.neighbors`.

Demonstração ao vivo: carregar `rede_invalida_exemplo.txt` (opção 1) → as 4
falham; carregar qualquer `configs/*.txt` → todas passam.

### Requisitos III — operação de busca
- **Parâmetros de entrada** (`node_id`, `resource_id`, `ttl`, `algo`):
  coletados em `p2p.py::pedir_busca()` (linha 64) e passados para
  `search.py::search()` (linha 259).
- **Os 4 algoritmos** (`flooding`, `informed_flooding`, `random_walk`,
  `informed_random_walk`): `search.py`, funções `flooding()` (104) e
  `random_walk()` (184), selecionados em `search()` (259).
- **Saída: total de mensagens + total de nós envolvidos**: calculados em
  `SearchResult` (`total_messages`, `nodes_involved`) e impressos por
  `SearchResult.__str__()` (linha 49), exibido na opção 4 do menu.

### Requisitos IV — opcionais (visualização)
- **Representação gráfica da rede**: `visualize.py::draw_network()` (linha 30),
  acessível pela opção 3 do menu.
- **Animação em tempo real da busca**: `visualize.py::animate_search()`
  (linha 50), oferecida ao final de cada busca (opção 4).

### Instruções item 2 / Entregável item 3 — testes comparativos
- **Onde:** `benchmark.py` (opção 5 do menu ou `python benchmark.py`).
- Compara os algoritmos em **várias topologias** (`configs/`) pelo **número de
  mensagens** (métrica exigida), além de nós envolvidos e taxa de sucesso.
- Gera as **tabelas** (terminal) e os **gráficos** `benchmark_msgs.png`,
  `benchmark_nos.png`, `benchmark_sucesso.png` para os slides.

---

## 5. Os 4 algoritmos em uma frase

| Algoritmo | Ideia | Custo esperado |
|-----------|-------|----------------|
| `flooding` | manda a query para **todos** os vizinhos (≈ BFS) | acha quase sempre, **muitas** mensagens |
| `random_walk` | manda para **um** vizinho aleatório por vez | **poucas** mensagens, pode não achar com TTL baixo |
| `informed_flooding` | flooding + **cache** de localização | reduz mensagens quando o cache "esquenta" |
| `informed_random_walk` | random walk + **cache** para se guiar | as menos mensagens em média |

O **cache** é o que diferencia as versões informadas: cada nó memoriza onde ficam
recursos que já descobriu, então buscas seguintes não precisam reinundar a rede.
Ele **persiste durante a sessão** (opção 6 do menu zera o cache para testes do zero).

---

## 6. Convenção de contagem de mensagens (a "régua" da comparação)

> Importante deixar isso explícito nos slides — é a base de toda a comparação.

- **1 mensagem** = uma query trafegando por **uma aresta** (de um nó para um vizinho).
- No flooding, mensagens enviadas a nós **já visitados contam** (é o desperdício
  característico da inundação) e são descartadas pelo receptor.
- Ao encontrar o recurso, contam-se também as mensagens de **resposta** que
  informam o nó de origem (saltos do caminho de volta).
- **Nós envolvidos** = conjunto de nós que receberam/processaram a query.

Implementação: cada envio passa por `SearchResult._msg()` (search.py, linha 44),
que incrementa `total_messages` e registra o evento.

---

## 7. Topologias de teste (`configs/`)

| Arquivo | Topologia | Para que serve |
|---------|-----------|----------------|
| `rede_exemplo.txt` | 12 nós (mista) | exemplo geral parecido com o do enunciado |
| `rede_linha.txt` | linha (path) | pior caso para random walk alcançar nós distantes |
| `rede_estrela.txt` | estrela | centro alcança todos em 1 salto |
| `rede_malha.txt` | grade 3×3 | bem conectada, muitos caminhos alternativos |
| `rede_invalida_exemplo.txt` | inválida (de propósito) | demonstrar as 4 validações |

---

## 8. Como executar

```
pip install networkx matplotlib pandas

python p2p.py configs/rede_exemplo.txt   # menu interativo (carrega e valida a rede)
python benchmark.py                       # tabelas + gráficos comparativos
```

Roteiro sugerido para a **demonstração ao vivo**:
1. `python p2p.py rede_invalida_exemplo.txt` → mostra as validações falhando.
2. `python p2p.py configs/rede_exemplo.txt` → rede válida.
3. Opção 3 → desenhar a rede.
4. Opção 4 → buscar um recurso com cada algoritmo, comparando mensagens/nós;
   animar a busca.
5. Repetir uma busca informada para mostrar o efeito do **cache** (menos mensagens
   na segunda vez); opção 6 limpa o cache.
6. Opção 5 → benchmark gerando as tabelas e os gráficos dos slides.
