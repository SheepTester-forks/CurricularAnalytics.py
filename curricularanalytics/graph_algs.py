# File: GraphAlgs.jl

from queue import Queue
from typing import Any, Dict, List, Literal, Optional, Protocol, Tuple, TypeVar

import networkx as nx

from .types.data_types import EdgeClass, back_edge, cross_edge, forward_edge, tree_edge


class HashComparable(Protocol):
    def __hash__(self) -> int:
        ...

    def __lt__(self, __other: Any) -> bool:
        ...


T = TypeVar("T", bound=HashComparable)


# Depth-first search, returns edge classification using EdgeClass, as well as the discovery and finish time for each vertex.
def dfs(
    g: "nx.Graph[T]",
) -> Tuple[Dict["nx.Edge[T]", EdgeClass], Dict[T, int], Dict[T, int]]:
    """
    Perform a depth-first traversal of input graph `g`.

    Args:
        g: Input graph.

    Returns:
        The classification of each edge in graph `g`, as well as the order in which vertices are
        first discovered during a depth-first search traversal, and when the processing from that vertex is completed
        during the depth-first traverlsa.

    According to the vertex discovery and finish times, each edge in `g` will be
    classified as one of:
    - *tree edge* : Any collection of edges in `g` that form a forest. Every vertex is either a single-vertex tree
    with respect to such a collection, or is part of some larger tree through its connection to another vertex via a
    tree edge. This collection is not unique defined on `g`.
    - *back edge* : Given a collection of tree edges, back edges are those edges that connect some descendent vertex
    in a tree to an ancestor vertex in the same tree.
    - *forward edge* : Given a collection of tree edges, forward edges are those that are incident from an ancestor
    in a tree, and incident to an descendent in the same tree.
    - *cross edge* : Given a collection of tree edges, cross edges are those that are adjacent between vertices in
    two different trees, or between vertices in two different subtrees in the same tree.

    Examples:
        >>> edges, discover, finish = dfs(g)
    """
    time = 0
    # discover and finish times
    d = {node: 0 for node in g.nodes}
    f = {node: 0 for node in g.nodes}
    edge_type: Dict["nx.Edge[T]", EdgeClass] = {}
    for s in g.nodes:
        if d[s] == 0:  # undiscovered
            # a closure, shares variable space w/ outer function
            def dfs_visit(s: T):
                nonlocal time, edge_type
                time += 1  # discovered
                d[s] = time
                for n in g.neighbors(s):
                    if d[n] == 0:  # encounted a undiscovered vertex
                        edge_type[(s, n)] = tree_edge
                        dfs_visit(n)
                    elif f[n] == 0:  # encountered a discovered but unfinished vertex
                        edge_type[(s, n)] = back_edge
                    else:  # encountered a finished vertex
                        if d[s] < d[n]:
                            edge_type[(s, n)] = forward_edge
                        else:  # d[s] > d[n]
                            edge_type[(s, n)] = cross_edge
                time += 1  # finished
                f[s] = time

            dfs_visit(s)  # call the closure
    return edge_type, d, f


# In a DFS of a DAG, sorting the vertices according to their finish times in the DFS will yeild a topological sorting of the
# DAG vertices.
def topological_sort(
    g: "nx.DiGraph[T]", *, sort: Literal["", "descending", "ascending"] = ""
) -> List[List[T]]:
    """
    Perform a topoloical sort on graph `g`.

    Args:
        g: Input graph.
        sort: Sort weakly connected components according to their size, allowable strings: `ascending`, `descending`.

    Returns:
        The weakly connected components of the graph, each in topological sort order.

        If the `sort` keyword agrument is supplied, the components will be sorted according to their size, in either ascending or
        descending order.  If two or more components have the same size, the one with the smallest vertex ID in the first position of the
        topological sort will appear first.
    """
    _edges_type, _d, f = dfs(g)
    topo_order = sorted(f.keys(), key=lambda k: f[k], reverse=True)
    wcc = [list(s) for s in nx.weakly_connected_components(g)]
    if sort == "descending":
        wcc.sort(
            key=lambda x: (-len(x), x[0])
        )  # order components by size, if same size, by lower index
    elif sort == "ascending":
        wcc.sort(
            key=lambda x: (len(x), x[0])
        )  # order components by size, if same size, by lower index
    reorder: List[T] = []
    for component in wcc:
        component.sort(
            key=lambda x: topo_order.index(x)
        )  # topological sort within each component
        for i in component:
            reorder.append(i)
    return wcc


# transpose of DAG
def gad(g: "nx.DiGraph[T]") -> "nx.DiGraph[T]":
    """
    Args:
        g: Input graph.

    Returns:
        The transpose of directed acyclic graph (DAG) `g`, i.e., a DAG identical to `g`, except the direction
        of all edges is reversed.  If `g` is not a DAG, an error is thrown.
    """
    return g.reverse()


# The set of all vertices in the graph reachable from vertex s
def reachable_from(g: "nx.Graph[T]", s: T, vlist: Optional[List[T]] = None) -> List[T]:
    """
    Args:
        g: Acylic input graph.
        s: Index of the source vertex in `g`.

    Returns:
        The set of all vertices in `g` that are reachable from vertex `s`.
    """
    if vlist is None:
        vlist = []
    for v in g.neighbors(s):
        if v not in vlist:
            vlist.append(v)
        reachable_from(g, v, vlist)
    return vlist


# The subgraph induced by vertex s and the vertices reachable from vertex s
def reachable_from_subgraph(g: "nx.Graph[T]", s: T) -> "nx.Graph[T]":
    """
    Returns:
        The subgraph induced by `s` in `g` (i.e., a graph object consisting of vertex
        `s` and all vertices reachable from vertex `s` in`g`), as well as a vector mapping the vertex
        IDs in the subgraph to their IDs in the orginal graph `g`.

    Examples:
        >>> sg, vmap = reachable_from_subgraph(g, s)
    """
    vertices: List[T] = reachable_from(g, s)
    vertices.append(s)  # add the source vertex to the reachable set
    return g.subgraph(vertices)


# The set of all vertices in the graph that can reach vertex s
def reachable_to(g: "nx.DiGraph[T]", t: T) -> List[T]:
    """
    Args:
        g: Acylic input graph.
        t: Index of the target vertex in `g`.

    Returns:
        The set of all vertices in `g` that can reach target vertex `t` through any path.
    """
    return reachable_from(gad(g), t)  # vertices reachable from s in the transpose graph


# The subgraph induced by vertex s and the vertices that can reach s
def reachable_to_subgraph(g: "nx.DiGraph[T]", s: T) -> "nx.DiGraph[T]":
    """
    Args:
        g: Acylic graph.
        t: Index of the target vertex in `g`.

    Returns:
        A subgraph in `g` consisting of vertex `t` and all vertices that can reach
        vertex `t` in`g`, as well as a vector mapping the vertex IDs in the subgraph to their IDs
        in the orginal graph `g`.

    Examples:
        >>> sg, vmap = reachable_to(g, t)
    """
    vertices = reachable_to(g, s)
    vertices.append(s)  # add the source vertex to the reachable set
    return g.subgraph(vertices)


# The set of all vertices reachable to and reachable from vertex s
def reach(g: "nx.DiGraph[T]", v: T) -> List[T]:
    """
    Args:
        g: Acylic graph.
        v: Index of a vertex in `g`.

    Returns:
        The reach of vertex `v` in `g`, ie., the set of all vertices in `g` that can
        reach vertex `v` and can be reached from `v`.
    """
    return [*reachable_to(g, v), *reachable_from(g, v)]


# Subgraph induced by the reach of a vertex
def reach_subgraph(g: "nx.DiGraph[T]", v: T) -> "nx.DiGraph[T]":
    """
    Args:
        g: Acylic graph.
        v: Index of a vertex in `g`.

    Returns:
        A subgraph in `g` consisting of vertex `v ` and all vertices that can reach `v`, as
        well as all vertices that `v` can reach.  In addition, a vector is returned that maps the
        vertex IDs in the subgraph to their IDs in the orginal graph `g`.

    Examples:
        >>> sg, vmap = reachable_to(g, v)
    """
    vertices = reach(g, v)
    vertices.append(v)  # add the source vertex to the reachable set
    return g.subgraph(vertices)


# find all paths in a graph
def all_paths(g: "nx.DiGraph[T]") -> List[List[T]]:
    """
    Enumerate all of the unique paths in acyclic graph `g`, where a path in this case must include a
    source vertex (a vertex with in-degree zero) and a different sink vertex (a vertex with out-degree
    zero).  I.e., a path is this case must contain at least two vertices.

    Args:
        g: Acylic graph.

    Returns:
        An array of these paths, where each path consists of an array of vertex IDs.
    """
    # check that g is acyclic
    try:
        nx.find_cycle(g)
        raise Exception("all_paths(): input graph has cycles")
    except nx.NetworkXNoCycle:
        pass
    que: Queue[List[T]] = Queue()
    paths: List[List[T]] = []
    sinks: List[T] = []
    for v in g.nodes:
        if (g.out_degree(v) == 0) and (
            g.in_degree(v) > 0
        ):  # consider only sink vertices with a non-zero in-degree
            sinks.append(v)
    for v in sinks:
        que.put([v])
        # work backwards from sink v to all sources reachable to v in BFS fashion
        while not que.empty():
            x = que.get()  # grab a path from the queue
            # consider the in-neighbors at the beginning of the current path
            for i, edge in enumerate(g.in_edges(x[0])):
                u, _ = edge
                if i == 0:  # first neighbor, build onto exising path
                    x.insert(0, u)  # prepend vertex u to array x
                    # if reached a source vertex, done with the path; otherwise, put it back in queue
                    if g.in_degree(u) == 0:
                        paths.append(x)
                    else:
                        que.put(x)
                else:  # not first neighbor, create a copy of the path
                    y = x.copy()
                    y[0] = u  # overwrite first element in array
                    if g.in_degree(u) == 0:
                        paths.append(y)
                    else:
                        que.put(y)
    return paths


# The longest path from vertx s to any other vertex in a DAG G (not necessarily unique).
# Note: in a DAG G, longest paths in G = shortest paths in -G
def longest_path(g: "nx.Graph[T]", s: T) -> List[T]:
    """
    The longest path from vertex `s` to any other vertex in a acyclic graph `g`. The longest path
    is not necessarily unique, i.e., there can be more than one longest path between two vertices.

    Args:
        g: Acylic graph.
        s: Index of the source vertex in `g`.
    """
    try:
        nx.find_cycle(g)
        raise Exception("longest_path(): input graph has cycles")
    except nx.NetworkXNoCycle:
        pass
    lp: List[T] = []
    max = 0
    # shortest path from s to all vertices in -G
    for path in nx.shortest_path(g, s).values():
        if len(path) > max:
            lp = path
            max = len(path)
    return lp


# Find all of the longest paths in an acyclic graph.
def longest_paths(g: "nx.DiGraph[T]") -> List[List[T]]:
    """
    Finds the set of longest paths in `g`.

    Args:
        g: Acylic graph.

    Returns:
        An array of vertex arrays, where each vertex
        array contains the vertices in a longest path.
    """
    try:
        nx.find_cycle(g)
        raise Exception("longest_paths(): input graph has cycles")
    except nx.NetworkXNoCycle:
        pass
    lps: List[List[T]] = []
    max = 0
    paths = all_paths(g)
    for path in paths:  # find length of longest path
        if len(path) > max:
            max = len(path)
    for path in paths:
        if len(path) == max:
            lps.append(path)
    return lps


# determine the number of edges crossing a graph cut, where s is the set of vertices on one side of the cut,
# and the other side are the remanining vertices in g.
def edge_crossings(g: "nx.Graph[T]", s: List[T]) -> int:
    """
    Given a graph ``g=(V,E)``,and a set of vertices ``s \\subseteq V``, determine the number of edges
    crossing the cut determined by the partition ``(s,V-s)``.

    Args:
        g: Acylic graph.
        s: Array of vertex indicies.

    Returns:
        The cut size.
    """
    total = 0
    d = [
        x for x in g.nodes if x not in s
    ]  # collect the graph vertex ids in a integer array,remove the vertex ids in s from d
    for v in s:
        total += edge_crossings_vertex(g, v, d)
    return total


def edge_crossings_vertex(g: "nx.Graph[T]", s: T, d: List[T]) -> int:
    """
    Find the number of crossings from a single vertex to all vertices in some vertex set d.
    """
    total = 0
    for v in d:
        if g.has_edge(s, v):
            total += 1
    return total
