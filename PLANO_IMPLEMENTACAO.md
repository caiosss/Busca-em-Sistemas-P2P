# Plano de Implementação — Trabalho 7: Busca em Sistemas P2P

> Computação Distribuída — Prof. Nabor C. Mendonça
> Stack escolhida: **Python 3** · com **visualização gráfica + animação** · **menu interativo no terminal**

---

## 1. Entendimento do problema

Simular uma **rede P2P não estruturada** e implementar **4 algoritmos de busca** por recursos:

| algo | nome | ideia |
|------|------|-------|
| `flooding` | Inundação | envia query para TODOS os vizinhos, que repassam aos vizinhos deles (≈ BFS) |
| `random_walk` | Passeio aleatório | envia query para UM vizinho aleatório, que repassa para outro (≈ caminho aleatório) |
| `informed_flooding` | Inundação informada | flooding + cache: nó que já sabe a localização responde direto |
| `informed_random_walk` | Passeio aleatório informado | random walk + cache para guiar/encurtar a busca |

**Premissas do professor (importantes):**
- Um nó **não conhece** a rede inteira — só conhece **seus vizinhos imediatos** e **os recursos que ele mesmo guarda**.
- A busca verifica se um recurso existe em **algum** nó.
- **TTL** = limite de saltos; decrementa a cada salto; ao chegar a 0, a mensagem é descartada.
- A métrica principal de comparação é o **número total de mensagens trocadas** (e nº de nós envolvidos).

> Não é necessário rodar processos/sockets reais — fazemos uma **simulação determinística** sobre um grafo (o próprio professor disse que "é basicamente uma pesquisa de grafo em profundidade e em largura"). Isso facilita contar mensagens e animar.

---

## 2. Estrutura de arquivos

```
trabalho 7 nabor/
├── p2p.py            # ponto de entrada: menu interativo
├── network.py        # parser do config, classes Node/Network, validações
├── search.py         # os 4 algoritmos + contagem de mensagens (gera log de eventos)
├── visualize.py      # desenho da rede (networkx) + animação da busca (matplotlib)
├── benchmark.py      # testes comparativos -> tabelas e gráficos
├── configs/
│   ├── rede_linha.txt      # topologia em linha (pior caso p/ random walk)
│   ├── rede_estrela.txt    # topologia estrela
│   ├── rede_malha.txt      # topologia bem conectada
│   └── rede_grande.txt     # ~20-30 nós p/ ver diferença de escala
└── PLANO_IMPLEMENTACAO.md
```

**Dependências:** `networkx`, `matplotlib` (e `pandas` opcional para tabelas do benchmark).
`pip install networkx matplotlib pandas`

---

## 3. Formato do arquivo de configuração

Usaremos o formato texto do PDF (parser próprio simples):

```
num_nodes: 12
min_neighbors: 2
max_neighbors: 4
resources:
  n1: r1, r2, r3
  n2: r4, r5
  ...
edges:
  n1, n2
  n1, n3
  n2, n4
  ...
```

O parser lê em 3 seções (cabeçalho / `resources:` / `edges:`) e monta as estruturas. (Aceitar JSON também é trivial de adicionar depois, mas o formato texto já cumpre o requisito.)

---

## 4. Modelo de dados (`network.py`)

```python
class Node:
    id: str
    resources: set[str]        # recursos que ESTE nó guarda
    neighbors: set[str]        # ids dos vizinhos imediatos (só isso ele "enxerga")
    cache: dict[str, str]      # recurso_id -> id do nó onde ele JÁ SOUBE que existe
                               # (usado só pelos algoritmos informed_*)

class Network:
    nodes: dict[str, Node]
    # métodos: parse(arquivo), validate(), neighbors(id), has_resource(id, r), ...
```

---

## 5. Validações pós-leitura (Requisitos II)

Implementar e exibir o resultado de cada uma:

1. **Rede não particionada** → BFS/DFS a partir de um nó; ao final, todos os nós devem ter sido alcançados.
2. **Grau respeita limites** → para cada nó, `min_neighbors ≤ len(neighbors) ≤ max_neighbors`.
3. **Nenhum nó sem recurso** → todo nó deve ter `resources` não-vazio.
4. **Sem self-loop** → nenhuma aresta `n_x, n_x`.

Se alguma falhar, abortar a carga e mostrar mensagem clara do que está errado.

---

## 6. Os algoritmos de busca (`search.py`)

### Convenção de contagem (definir e documentar — é a "régua" de toda a comparação)
- **1 mensagem** = uma transmissão de uma query por **uma aresta** (de um nó a um vizinho).
- Quando o recurso é encontrado, conta-se também a(s) **mensagem(ns) de resposta** que informam o nó de origem (nº de saltos do caminho de volta).
- **Nós envolvidos** = conjunto de nós que receberam/processaram a query.
- Cada algoritmo retorna um objeto `SearchResult`:
  ```python
  found: bool
  located_at: str | None
  total_messages: int
  nodes_involved: set[str]
  events: list[Event]   # log p/ a animação: (origem, destino, tipo) onde tipo ∈ {query, hit, response, dropped}
  ```

### 6.1 `flooding` (BFS por níveis)
- Origem confere se tem o recurso (achou → 0 msgs).
- Propaga em ondas; cada nó repassa a query a todos os vizinhos, decrementando TTL.
- Para terminar e evitar loops infinitos: cada nó processa a query **uma vez** por busca (marca como visto). Uma query reenviada a um nó já visitado ainda **conta como mensagem** (foi transmitida), mas é **descartada** (`dropped`) sem reencaminhar — esse é exatamente o "desperdício" do flooding que queremos medir.
- Para quando: recurso encontrado, TTL zera, ou não há mais nós novos.

### 6.2 `random_walk`
- Origem escolhe **1 vizinho aleatório** e envia a query (1 msg).
- Esse nó confere; se não tem e TTL>0, escolhe **outro vizinho aleatório** (evitando voltar imediatamente pelo mesmo de onde veio, quando possível) e repassa.
- Continua até achar ou TTL zerar. Custo ≈ nº de saltos.
- Como é aleatório, no benchmark rodaremos **várias vezes e tiramos a média**.

### 6.3 `informed_flooding`
- Igual ao flooding, **mas com cache**:
  - Antes/durante a busca, se o nó atual tem no `cache` a localização do recurso, ele **responde imediatamente** (rota direta) em vez de continuar inundando → menos mensagens.
  - À medida que respostas trafegam, os nós **aprendem** (atualizam o cache) onde ficam os recursos. Buscas **futuras** ficam mais rápidas (o cache persiste durante a sessão).

### 6.4 `informed_random_walk`
- Igual ao random walk, mas em cada nó: se o `cache` conhece a localização, encaminha **na direção do vizinho** que leva ao recurso (ou responde direto), em vez de escolher 100% aleatório.

> O **cache** é o que separa as versões "informadas". Ele persiste entre buscas dentro da mesma sessão do menu (com opção de "limpar cache" para refazer testes do zero).

---

## 7. Visualização e animação (`visualize.py`)

- **Desenho estático**: `networkx` + `matplotlib`. Layout fixo (`spring_layout` com seed) para a posição dos nós não mudar entre execuções. Rótulos com id do nó e seus recursos.
- **Animação da busca**: usar o `events` retornado pela busca + `matplotlib.animation.FuncAnimation`:
  - nó de origem destacado (ex.: verde),
  - a cada frame, ilumina a aresta da mensagem e "acende" o nó que recebeu a query,
  - mensagem `dropped` em cinza/tracejado, `hit` (achou) em destaque, `response` no caminho de volta.
- Cores por tipo de evento para ficar didático na **demo ao vivo**.

---

## 8. Menu interativo (`p2p.py`)

```
=== Rede P2P — Busca de Recursos ===
1. Carregar arquivo de configuração
2. Validar rede
3. Desenhar a rede
4. Buscar recurso  (pergunta: node_id, resource_id, ttl, algo)
       -> imprime: encontrado? onde? total de mensagens, nós envolvidos
       -> opção de ver a animação da busca
5. Rodar testes comparativos (benchmark) -> gera tabelas/gráficos
6. Limpar cache (reseta buscas informadas)
0. Sair
```

A opção 4 imprime o resultado no formato pedido pelo Requisito III (total de mensagens + total de nós envolvidos).

---

## 9. Testes comparativos (`benchmark.py`) — Requisito Instruções item 2 + Entregável item 3

- Para **cada topologia** em `configs/` e **cada algoritmo**:
  - rodar buscas variando origem/recurso/TTL (random walk: média de N repetições),
  - registrar: **nº de mensagens**, **p95 de mensagens**, **nº de nós envolvidos**, **p95 de nós envolvidos**, **taxa de sucesso**.
- Gerar:
  - **tabela** comparativa (pandas → texto/CSV),
  - **gráficos de barras** (mensagens médias e p95 por algoritmo × topologia; nós médios e p95; taxa de sucesso).
- Esses gráficos vão direto para os slides do entregável.

**Hipóteses esperadas (para discutir nos slides):** flooding acha rápido mas gera MUITAS mensagens; random walk gera poucas mensagens mas pode demorar/falhar com TTL baixo; as versões informadas reduzem mensagens conforme o cache "esquenta".

---

## 10. Ordem de implementação sugerida

1. `network.py`: parser + classes + 4 validações. ✔ testar com um config pequeno.
2. `search.py`: `flooding` (mais simples de validar) + contagem de mensagens.
3. `search.py`: `random_walk`.
4. `search.py`: cache → `informed_flooding` e `informed_random_walk`.
5. `p2p.py`: menu amarrando tudo (itens 1–4 e 6).
6. `visualize.py`: desenho estático → animação.
7. `benchmark.py`: tabelas + gráficos; criar 3–4 configs de topologias diferentes.
8. Rodar tudo, conferir números, preparar a demo.

---

## 11. Mapa Requisito → onde é atendido

| Requisito (PDF) | Onde |
|---|---|
| Ler config e montar a rede | `network.py` (parser) |
| 4 validações | `network.py::validate()` + menu opção 2 |
| Busca com node_id/resource_id/ttl/algo | `search.py` + menu opção 4 |
| Informar total de mensagens e nós | `SearchResult` + impressão na opção 4 |
| 4 algoritmos (flooding/informed/random/informed) | `search.py` |
| Testes comparativos (mensagens) | `benchmark.py` |
| (Opcional) representação gráfica | `visualize.py` desenho |
| (Opcional) animação em tempo real | `visualize.py` animação |
