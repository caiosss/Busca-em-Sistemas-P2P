"""
network.py — Leitura do arquivo de configuração, modelo de dados da rede P2P
e validações exigidas no Trabalho 7.

Cada nó conhece apenas seus vizinhos imediatos e os recursos que ele mesmo guarda.
"""

from collections import deque


class Node:
    """Um nó (peer) da rede P2P."""

    def __init__(self, node_id):
        self.id = node_id
        self.resources = set()      # recursos que ESTE nó guarda
        self.neighbors = set()      # ids dos vizinhos imediatos (tudo que ele "enxerga")
        self.cache = {}             # recurso_id -> id do nó onde ele JÁ SOUBE que existe
                                    # (usado apenas pelas buscas informed_*)

    def has_resource(self, resource_id):
        return resource_id in self.resources

    def __repr__(self):
        return f"Node({self.id}, recursos={sorted(self.resources)}, vizinhos={sorted(self.neighbors)})"


class Network:
    """Rede P2P não estruturada: coleção de nós + arestas (grafo não-direcionado)."""

    def __init__(self):
        self.num_nodes = 0
        self.min_neighbors = 0
        self.max_neighbors = 0
        self.nodes = {}             # id -> Node

    # ------------------------------------------------------------------ #
    # Leitura do arquivo de configuração
    # ------------------------------------------------------------------ #
    @classmethod
    def from_file(cls, path):
        """Lê o arquivo de configuração no formato texto do enunciado.

        Formato esperado:
            num_nodes: 12
            min_neighbors: 2
            max_neighbors: 4
            resources:
              n1: r1, r2, r3
              n2: r4, r5
            edges:
              n1, n2
              n1, n3
        """
        net = cls()
        section = None  # None | "resources" | "edges"

        with open(path, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue

                low = line.lower()

                # Cabeçalho
                if low.startswith("num_nodes:"):
                    net.num_nodes = int(line.split(":", 1)[1].strip())
                    continue
                if low.startswith("min_neighbors:"):
                    net.min_neighbors = int(line.split(":", 1)[1].strip())
                    continue
                if low.startswith("max_neighbors:"):
                    net.max_neighbors = int(line.split(":", 1)[1].strip())
                    continue

                # Início das seções
                if low == "resources:":
                    section = "resources"
                    continue
                if low == "edges:":
                    section = "edges"
                    continue

                # Conteúdo das seções
                if section == "resources":
                    # formato: n1: r1, r2, r3
                    node_id, _, res_part = line.partition(":")
                    node_id = node_id.strip()
                    node = net._get_or_create(node_id)
                    for r in res_part.split(","):
                        r = r.strip()
                        if r:
                            node.resources.add(r)

                elif section == "edges":
                    # formato: n1, n2
                    parts = [p.strip() for p in line.split(",") if p.strip()]
                    if len(parts) == 2:
                        a, b = parts
                        net._add_edge(a, b)

        return net

    # ------------------------------------------------------------------ #
    # Helpers de construção
    # ------------------------------------------------------------------ #
    def _get_or_create(self, node_id):
        if node_id not in self.nodes:
            self.nodes[node_id] = Node(node_id)
        return self.nodes[node_id]

    def _add_edge(self, a, b):
        na = self._get_or_create(a)
        nb = self._get_or_create(b)
        if a != b:  # self-loops são tratados na validação; aqui só evitamos quebrar o set
            na.neighbors.add(b)
            nb.neighbors.add(a)
        else:
            # registramos a aresta inválida para a validação detectar
            na.neighbors.add(a)

    # ------------------------------------------------------------------ #
    # Acesso conveniente
    # ------------------------------------------------------------------ #
    def get(self, node_id):
        return self.nodes.get(node_id)

    def neighbors(self, node_id):
        node = self.nodes.get(node_id)
        return sorted(node.neighbors) if node else []

    # ------------------------------------------------------------------ #
    # Validações (Requisitos II do enunciado)
    # ------------------------------------------------------------------ #
    def validate(self):
        """Roda as 4 validações. Retorna (ok, lista_de_mensagens)."""
        results = []
        ok = True

        # 4. Não pode haver aresta de um nó para ele mesmo (checa primeiro,
        #    pois afeta a contagem de vizinhos)
        self_loops = [n.id for n in self.nodes.values() if n.id in n.neighbors]
        if self_loops:
            ok = False
            results.append(("Sem self-loops", False,
                            f"Nós com aresta para si mesmos: {self_loops}"))
        else:
            results.append(("Sem self-loops", True, "Nenhuma aresta de um nó para ele mesmo."))

        # 1. Rede não pode estar particionada
        connected, missing = self._is_connected()
        if connected:
            results.append(("Rede conectada", True, "Existe caminho entre quaisquer dois nós."))
        else:
            ok = False
            results.append(("Rede conectada", False,
                            f"Rede particionada — nós inalcançáveis a partir do início: {missing}"))

        # 2. Grau (nº de vizinhos) dentro de [min_neighbors, max_neighbors]
        grau_problemas = []
        for n in self.nodes.values():
            grau = len(n.neighbors - {n.id})  # ignora self-loop na contagem
            if grau < self.min_neighbors or grau > self.max_neighbors:
                grau_problemas.append(f"{n.id}={grau}")
        if grau_problemas:
            ok = False
            results.append(("Limites de vizinhos", False,
                            f"Fora de [{self.min_neighbors}, {self.max_neighbors}]: {grau_problemas}"))
        else:
            results.append(("Limites de vizinhos", True,
                            f"Todos os nós entre {self.min_neighbors} e {self.max_neighbors} vizinhos."))

        # 3. Não pode haver nó sem recurso
        sem_recurso = [n.id for n in self.nodes.values() if not n.resources]
        if sem_recurso:
            ok = False
            results.append(("Todos com recursos", False,
                            f"Nós sem nenhum recurso: {sem_recurso}"))
        else:
            results.append(("Todos com recursos", True, "Todos os nós possuem ao menos um recurso."))

        return ok, results

    def _is_connected(self):
        """BFS a partir de um nó qualquer; retorna (conectada?, nós_não_alcançados)."""
        if not self.nodes:
            return True, []
        start = next(iter(self.nodes))
        visited = {start}
        queue = deque([start])
        while queue:
            cur = queue.popleft()
            for nb in self.nodes[cur].neighbors:
                if nb != cur and nb not in visited and nb in self.nodes:
                    visited.add(nb)
                    queue.append(nb)
        missing = sorted(set(self.nodes) - visited)
        return len(missing) == 0, missing

    # ------------------------------------------------------------------ #
    def __repr__(self):
        return (f"Network(num_nodes={self.num_nodes}, "
                f"min={self.min_neighbors}, max={self.max_neighbors}, "
                f"nós={sorted(self.nodes)})")
