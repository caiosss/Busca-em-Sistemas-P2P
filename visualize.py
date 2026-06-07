"""
visualize.py — Representação gráfica da rede P2P e animação da busca.

Usa networkx (layout) + matplotlib (desenho/animação). Requisitos OPCIONAIS (IV).
"""

import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from search import EV_QUERY, EV_HIT, EV_RESPONSE, EV_DROPPED


def _build_graph(net):
    g = nx.Graph()
    for node in net.nodes.values():
        g.add_node(node.id)
        for nb in node.neighbors:
            if nb != node.id and nb in net.nodes:
                g.add_edge(node.id, nb)
    return g


def _layout(net):
    """Posições fixas (seed) para o desenho não mudar entre execuções."""
    g = _build_graph(net)
    return g, nx.spring_layout(g, seed=42)


def draw_network(net, title="Rede P2P", highlight=None):
    """Desenha a rede estática. `highlight` = conjunto de nós a destacar."""
    g, pos = _layout(net)
    highlight = highlight or set()

    labels = {n.id: f"{n.id}\n[{','.join(sorted(n.resources))}]"
              for n in net.nodes.values()}
    colors = ["#ffcc66" if nid in highlight else "#9ecae1" for nid in g.nodes()]

    plt.figure(figsize=(11, 8))
    nx.draw_networkx_edges(g, pos, edge_color="#bbbbbb", width=1.5)
    nx.draw_networkx_nodes(g, pos, node_color=colors, node_size=1600,
                           edgecolors="#08519c")
    nx.draw_networkx_labels(g, pos, labels, font_size=8)
    plt.title(title)
    plt.axis("off")
    plt.tight_layout()
    plt.show()


def animate_search(net, result, interval=900):
    """Anima, passo a passo, as mensagens trocadas durante a busca.

    Cores:
        verde  = nó de origem
        azul   = query trafegando
        laranja= resposta voltando p/ origem
        cinza  = mensagem descartada (nó já visitado / TTL)
        rosa   = nó que encontrou o recurso
    """
    g, pos = _layout(net)
    events = result.events
    if not events:
        print("(Sem mensagens para animar — recurso na origem ou nó inexistente.)")
        draw_network(net, title=f"Busca {result.algo}: {result.resource}",
                     highlight={result.origin})
        return

    fig, ax = plt.subplots(figsize=(11, 8))
    labels = {n.id: f"{n.id}\n[{','.join(sorted(n.resources))}]"
              for n in net.nodes.values()}

    color_by_type = {
        EV_QUERY: "#3182bd",
        EV_RESPONSE: "#fd8d3c",
        EV_DROPPED: "#cccccc",
        EV_HIT: "#e7298a",
    }

    def draw_frame(i):
        ax.clear()
        ax.axis("off")
        src, dst, tipo = events[i]

        # nós já tocados até aqui
        touched = {result.origin}
        for j in range(i + 1):
            s, d, t = events[j]
            touched.add(s)
            touched.add(d)

        node_colors = []
        for nid in g.nodes():
            if nid == result.located_at and result.found and i == len(events) - 1:
                node_colors.append("#e7298a")
            elif nid == result.origin:
                node_colors.append("#74c476")
            elif nid in touched:
                node_colors.append("#ffcc66")
            else:
                node_colors.append("#9ecae1")

        nx.draw_networkx_edges(g, pos, ax=ax, edge_color="#dddddd", width=1.2)
        # aresta ativa neste frame
        if src != dst and g.has_edge(src, dst):
            nx.draw_networkx_edges(g, pos, ax=ax, edgelist=[(src, dst)],
                                   edge_color=color_by_type.get(tipo, "#3182bd"),
                                   width=4.0)
        nx.draw_networkx_nodes(g, pos, ax=ax, node_color=node_colors,
                               node_size=1600, edgecolors="#08519c")
        nx.draw_networkx_labels(g, pos, labels, ax=ax, font_size=8)

        legenda = {EV_QUERY: "query", EV_RESPONSE: "resposta",
                   EV_DROPPED: "descartada", EV_HIT: "ENCONTROU"}.get(tipo, tipo)
        ax.set_title(f"{result.algo} | passo {i+1}/{len(events)} | "
                     f"{src} -> {dst} ({legenda}) | msgs={i+1}")

    anim = FuncAnimation(fig, draw_frame, frames=len(events),
                         interval=interval, repeat=False)
    plt.tight_layout()
    plt.show()
    return anim
