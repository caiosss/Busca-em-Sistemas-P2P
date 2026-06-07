"""
search.py — Algoritmos de busca por recursos na rede P2P.

Implementa os 4 algoritmos exigidos:
    flooding              — inundação (BFS)
    random_walk           — passeio aleatório
    informed_flooding     — inundação com cache
    informed_random_walk  — passeio aleatório com cache

Convenção de contagem (a "régua" da comparação):
    - 1 mensagem  = uma query trafegando por uma aresta (de um nó para um vizinho).
    - Mensagens enviadas a nós já visitados (no flooding) CONTAM — é o desperdício
      característico da inundação que o trabalho quer medir; o nó apenas as descarta.
    - Quando o recurso é encontrado, contam-se também as mensagens de RESPOSTA que
      informam o nó de origem (nº de saltos do caminho de volta).
    - nodes_involved = conjunto de nós que receberam/processaram a query.
"""

import random
from collections import deque


# Tipos de evento usados na animação
EV_QUERY = "query"        # query trafegando por uma aresta
EV_HIT = "hit"            # nó encontrou o recurso
EV_RESPONSE = "response"  # resposta voltando para a origem
EV_DROPPED = "dropped"    # mensagem descartada (nó já visitado / TTL zerou)


class SearchResult:
    """Resultado de uma operação de busca."""

    def __init__(self, algo, origin, resource, ttl):
        self.algo = algo
        self.origin = origin
        self.resource = resource
        self.ttl = ttl
        self.found = False
        self.located_at = None
        self.total_messages = 0
        self.nodes_involved = set()
        self.events = []  # lista de (origem, destino, tipo) para a animação

    def _msg(self, src, dst, tipo):
        """Registra uma mensagem (conta + grava evento)."""
        self.total_messages += 1
        self.events.append((src, dst, tipo))

    def __str__(self):
        status = (f"ENCONTRADO em '{self.located_at}'" if self.found
                  else "NAO ENCONTRADO")
        return (
            f"Algoritmo......: {self.algo}\n"
            f"Origem.........: {self.origin}\n"
            f"Recurso........: {self.resource}  (TTL={self.ttl})\n"
            f"Status.........: {status}\n"
            f"Mensagens......: {self.total_messages}\n"
            f"Nos envolvidos.: {len(self.nodes_involved)}  {sorted(self.nodes_involved)}"
        )


# ====================================================================== #
# Função auxiliar: caminho mais curto (para contabilizar a resposta e
# atualizar caches das buscas informadas)
# ====================================================================== #
def _shortest_path(net, src, dst):
    """BFS simples no grafo. Retorna lista de nós de src a dst (inclusive) ou None."""
    if src == dst:
        return [src]
    visited = {src}
    queue = deque([[src]])
    while queue:
        path = queue.popleft()
        last = path[-1]
        for nb in sorted(net.nodes[last].neighbors):
            if nb == last or nb not in net.nodes or nb in visited:
                continue
            visited.add(nb)
            new_path = path + [nb]
            if nb == dst:
                return new_path
            queue.append(new_path)
    return None


def _send_response(net, result, found_node):
    """Conta as mensagens de resposta voltando da localização até a origem
    e atualiza o cache dos nós do caminho (busca informada aprende a localização)."""
    path = _shortest_path(net, result.origin, found_node)
    if not path:
        return
    # resposta percorre o caminho de volta (found_node -> ... -> origem)
    back = list(reversed(path))
    for i in range(len(back) - 1):
        src, dst = back[i], back[i + 1]
        result._msg(src, dst, EV_RESPONSE)
        # cada nó no caminho de volta aprende onde está o recurso
        net.nodes[dst].cache[result.resource] = found_node


# ====================================================================== #
# 1. FLOODING (inundação — BFS)
# ====================================================================== #
def flooding(net, origin, resource, ttl, informed=False):
    """Inundação: cada nó repassa a query a todos os vizinhos até achar ou TTL zerar.

    Se informed=True, um nó cujo cache conhece a localização responde direto.
    """
    algo = "informed_flooding" if informed else "flooding"
    result = SearchResult(algo, origin, resource, ttl)
    if origin not in net.nodes:
        return result

    result.nodes_involved.add(origin)

    # Origem confere a si mesma (não custa mensagem)
    if net.nodes[origin].has_resource(resource):
        result.found = True
        result.located_at = origin
        return result

    # Busca informada: origem já sabe pelo cache?
    if informed and resource in net.nodes[origin].cache:
        loc = net.nodes[origin].cache[resource]
        if loc in net.nodes and net.nodes[loc].has_resource(resource):
            result.found = True
            result.located_at = loc
            _send_response(net, result, loc)
            return result

    visited = {origin}              # nós que já receberam a query
    frontier = [origin]             # nós que vão repassar nesta onda
    remaining = ttl

    while frontier and remaining > 0 and not result.found:
        next_frontier = []
        for node_id in frontier:
            for nb in sorted(net.nodes[node_id].neighbors):
                if nb == node_id or nb not in net.nodes:
                    continue

                if nb in visited:
                    # mensagem é enviada mas descartada (desperdício do flooding)
                    result._msg(node_id, nb, EV_DROPPED)
                    continue

                # query trafega para o vizinho
                result._msg(node_id, nb, EV_QUERY)
                visited.add(nb)
                result.nodes_involved.add(nb)

                node_nb = net.nodes[nb]
                # vizinho tem o recurso?
                if node_nb.has_resource(resource):
                    result.events.append((nb, nb, EV_HIT))
                    result.found = True
                    result.located_at = nb
                    _send_response(net, result, nb)
                    break
                # busca informada: vizinho sabe pelo cache?
                if informed and resource in node_nb.cache:
                    loc = node_nb.cache[resource]
                    if loc in net.nodes and net.nodes[loc].has_resource(resource):
                        result.events.append((nb, nb, EV_HIT))
                        result.found = True
                        result.located_at = loc
                        _send_response(net, result, loc)
                        break

                next_frontier.append(nb)

            if result.found:
                break

        frontier = next_frontier
        remaining -= 1

    return result


# ====================================================================== #
# 2. RANDOM WALK (passeio aleatório)
# ====================================================================== #
def random_walk(net, origin, resource, ttl, informed=False, rng=None):
    """Passeio aleatório: a cada passo encaminha a query para UM vizinho.

    Sem cache: vizinho escolhido aleatoriamente (evitando voltar pelo mesmo nó).
    Com cache (informed=True): se o nó conhece a localização, encaminha na direção
    do vizinho que leva ao recurso.
    """
    algo = "informed_random_walk" if informed else "random_walk"
    result = SearchResult(algo, origin, resource, ttl)
    if origin not in net.nodes:
        return result
    rng = rng or random

    result.nodes_involved.add(origin)

    # Origem confere a si mesma
    if net.nodes[origin].has_resource(resource):
        result.found = True
        result.located_at = origin
        return result

    current = origin
    previous = None
    remaining = ttl

    while remaining > 0:
        node = net.nodes[current]

        # busca informada: o nó atual sabe a localização pelo cache?
        if informed and resource in node.cache:
            loc = node.cache[resource]
            if loc in net.nodes and net.nodes[loc].has_resource(resource):
                result.found = True
                result.located_at = loc
                _send_response(net, result, loc)
                return result

        vizinhos = [nb for nb in node.neighbors if nb != current and nb in net.nodes]
        if not vizinhos:
            break

        # escolha do próximo nó
        proximo = None
        if informed:
            # se algum vizinho está marcado no cache como caminho p/ o recurso, prioriza
            for nb in vizinhos:
                if net.nodes[nb].cache.get(resource) or net.nodes[nb].has_resource(resource):
                    proximo = nb
                    break
        if proximo is None:
            # evita voltar imediatamente pelo nó de onde veio, se houver alternativa
            opcoes = [nb for nb in vizinhos if nb != previous] or vizinhos
            proximo = rng.choice(opcoes)

        # query trafega para o próximo nó
        result._msg(current, proximo, EV_QUERY)
        result.nodes_involved.add(proximo)
        remaining -= 1

        node_prox = net.nodes[proximo]
        if node_prox.has_resource(resource):
            result.events.append((proximo, proximo, EV_HIT))
            result.found = True
            result.located_at = proximo
            _send_response(net, result, proximo)
            return result

        previous, current = current, proximo

    return result


# ====================================================================== #
# Dispatcher: seleciona o algoritmo pelo nome usado no enunciado
# ====================================================================== #
def search(net, origin, resource, ttl, algo, rng=None):
    algo = algo.strip().lower()
    if algo == "flooding":
        return flooding(net, origin, resource, ttl, informed=False)
    if algo == "informed_flooding":
        return flooding(net, origin, resource, ttl, informed=True)
    if algo == "random_walk":
        return random_walk(net, origin, resource, ttl, informed=False, rng=rng)
    if algo == "informed_random_walk":
        return random_walk(net, origin, resource, ttl, informed=True, rng=rng)
    raise ValueError(f"Algoritmo desconhecido: {algo!r}. "
                     "Use flooding, informed_flooding, random_walk ou informed_random_walk.")
