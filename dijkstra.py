from collections import defaultdict
from datetime import datetime

def build_graph(edge_list):
    graph = defaultdict(list)
    seen_edges = defaultdict(int)
    for src, dst, weight in edge_list:
        seen_edges[(src, dst, weight)] += 1
        if seen_edges[(src, dst, weight)] > 1:  # checking for duplicated edge entries
            continue
        graph[src].append((dst, weight))
        graph[dst].append((src, weight))  # remove this line of edge list is directed
    return graph


def dijkstra(graph, src, dst=None):
    nodes = []
    for n in graph:
        nodes.append(n)
        nodes += [x[0] for x in graph[n]]

    q = set(nodes)
    nodes = list(q)
    dist = dict()
    prev = dict()
    for n in nodes:
        dist[n] = float('inf')
        prev[n] = None

    dist[src] = 0

    while q:
        u = min(q, key=dist.get)
        q.remove(u)

        if dst is not None and u == dst:
            return dist[dst], prev

        for v, w in graph.get(u, ()):
            alt = dist[u] + w
            if alt < dist[v]:
                dist[v] = alt
                prev[v] = u

    print('dist: {}, prev:{} is'.format(dist, prev))
    return dist, prev


def find_path(pr, node):  # generate path list based on parent points 'prev'
    p = []
    while node is not None:
        p.append(node)
        node = pr[node]
    return p[::-1]


if __name__ == "__main__":
    edges = [
        ("A", "B", 7),
        ("A", "D", 5),
        ("B", "C", 8),
        ("B", "D", 9),
        ("B", "E", 7),
        ("C", "E", 5),
        ("D", "E", 15),
        ("D", "F", 6),
        ("E", "F", 8),
        ("E", "G", 9),
        ("F", "G", 11)
    ]

    g = build_graph(edges)

    print("=== Dijkstra ===")

    print("--- Single source, single destination ---")

    start = datetime.now()
    d, prev = dijkstra(g, "A", "G")
    path = find_path(prev, "G")
    end = datetime.now()
    elapsed = end - start
    print('elspsed time {}'.format(elapsed))
    print("A -> E: distance = {}, path = {}".format(d, path))

    # d, prev = dijkstra(g, "F", "G")
    # path = find_path(prev, "G")
    # print("F -> G: distance = {}, path = {}".format(d, path))

    # print("--- Single source, all destinations ---")
    # ds, prev = dijkstra(g, "A")
    # for k in ds:
    #     path = find_path(prev, k)
    #     print("A -> {}: distance = {}, path = {}".format(k, ds[k], path))