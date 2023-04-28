# File: GraphAlgs.jl

from typing import Any, Dict, List, Literal, Protocol,  Tuple, TypeVar

import networkx as nx

from src.DataTypes.DataTypes import EdgeClass, back_edge, cross_edge, forward_edge, tree_edge

class HashComparable(Protocol):
    __hash__: ClassVar[None]  # type: ignore[assignment]
    def __lt__(self, __other: Any) -> bool: ...

T = TypeVar('T', bound=HashComparable)

# Depth-first search, returns edge classification using EdgeClass, as well as the discovery and finish time for each vertex.
def dfs(g:nx.Graph[T]) -> Tuple[Dict[nx.Edge[T], EdgeClass], Dict[T, int], Dict[T, int]]:
    """
    dfs(g)

    Perform a depth-first traversal of input graph `g`.

    # Arguments
    Required:
    - `g:AbstractGraph` : input graph.

    This function returns the classification of each edge in graph `g`, as well as the order in which vertices are
    first discovered during a depth-first search traversal, and when the processing from that vertex is completed
    during the depth-first traverlsa.  According to the vertex discovery and finish times, each edge in `g` will be
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

    ```julia-repl
    julia> edges, discover, finish = dfs(g)
    ```
    """
    time = 0
    # discover and finish times
    d = {node:0 for node in g.nodes}
    f = {node:0 for node in g.nodes}
    edge_type: Dict[nx.Edge[T], EdgeClass] = {}
    for s in g.nodes:
        if d[s] == 0:  # undiscovered
            # a closure, shares variable space w/ outer function
            def dfs_visit(s: T):
                nonlocal time, edge_type
                time += 1  # discovered
                d[s] = time
                for n in g.neighbors(s):
                    if d[n] == 0: # encounted a undiscovered vertex
                        edge_type[(s,n)] = tree_edge
                        dfs_visit(n)
                    elif f[n] == 0: # encountered a discovered but unfinished vertex
                        edge_type[(s,n)] = back_edge
                    else:  # encountered a finished vertex
                        if d[s] < d[n]:
                            edge_type[(s,n)] = forward_edge
                        else: # d[s] > d[n]
                            edge_type[(s,n)] = cross_edge
                time += 1  # finished
                f[s] =  time
            dfs_visit(s)  # call the closure
    return edge_type, d, f

# In a DFS of a DAG, sorting the vertices according to their finish times in the DFS will yeild a topological sorting of the
# DAG vertices.
def topological_sort(g:nx.DiGraph[T], sort:Literal['','descending','ascending']="") -> List[List[T]]:
    """
        topological_sort(g; <keyword arguments>)

    Perform a topoloical sort on graph `g`, returning the weakly connected components of the graph, each in topological sort order.
    If the `sort` keyword agrument is supplied, the components will be sorted according to their size, in either ascending or
    descending order.  If two or more components have the same size, the one with the smallest vertex ID in the first position of the
    topological sort will appear first.

    # Arguments
    Required:
    - `g:AbstractGraph` : input graph.

    Keyword:
    - `sort:String` : sort weakly connected components according to their size, allowable
    strings: `ascending`, `descending`.
    """
    _edges_type, _d, f = dfs(g)
    topo_order = sorted(f.keys(), reverse=True)
    wcc = [list(s) for s in nx.weakly_connected_components(g)]
    if sort == "descending":
        wcc.sort(key=lambda x: (len(x), x[0]),reverse=True) # order components by size, if same size, by lower index
    elif sort == "ascending":
        wcc.sort(key=lambda x: (len(x), x[0])) # order components by size, if same size, by lower index
    reorder: List[T] = []
    for component in wcc:
        component.sort(key=lambda x: topo_order.index(x)) # topological sort within each component
        for i in component:
            reorder.append(i)
    return wcc

# transpose of DAG
def gad(g:nx.DiGraph[T]) -> nx.DiGraph[T]:
    """
        gad(g)

    Returns the transpose of directed acyclic graph (DAG) `g`, i.e., a DAG identical to `g`, except the direction
    of all edges is reversed.  If `g` is not a DAG, and error is thrown.

    # Arguments
    Required:
    - `g:SimpleDiGraph` : input graph.
    """
    return nx.DiGraph(transpose(adjacency_matrix(g)))

# The set of all vertices in the graph reachable from vertex s
def reachable_from(g:nx.Graph[T], s:T, vlist: List[T] = []) -> List[T]:
    """
        reachable_from(g, s)

    Returns the the set of all vertices in `g` that are reachable from vertex `s`.

    # Arguments
    Required:
    - `g:AbstractGraph` : acylic input graph.
    - `s:Int` : index of the source vertex in `g`.
    """
    for v in g.neighbors(s):
        if v not in vlist:  # v is not in vlist
            vlist.append(v)
        reachable_from(g, v, vlist)
    return vlist

# The subgraph induced by vertex s and the vertices reachable from vertex s
def reachable_from_subgraph(g:nx.DiGraph[T], s:T) -> Tuple[nx.DiGraph[T], Dict[T, T]]:
    """
        reachable_from_subgraph(g, s)

    Returns the subgraph induced by `s` in `g` (i.e., a graph object consisting of vertex
    `s` and all vertices reachable from vertex `s` in`g`), as well as a vector mapping the vertex
    IDs in the subgraph to their IDs in the orginal graph `g`.

    ```julia-rep
        sg, vmap = reachable_from_subgraph(g, s)
    ````
    """
    vertices: List[T] = reachable_from(g, s)
    vertices.append(s)  # add the source vertex to the reachable set
    return induced_subgraph(g, vertices)

# The set of all vertices in the graph that can reach vertex s
def reachable_to(g:nx.DiGraph[T], t:T) -> List[T]:
    """
        reachable_to(g, t)

    Returns the set of all vertices in `g` that can reach target vertex `t` through any path.

    # Arguments
    Required:
    - `g:AbstractGraph` : acylic input graph.
    - `t:Int` : index of the target vertex in `g`.
    """
    return reachable_from(gad(g), t)  # vertices reachable from s in the transpose graph

# The subgraph induced by vertex s and the vertices that can reach s
"""
    reachable_to_subgraph(g, t)

Returns a subgraph in `g` consisting of vertex `t` and all vertices that can reach
vertex `t` in`g`, as well as a vector mapping the vertex IDs in the subgraph to their IDs
in the orginal graph `g`.

# Arguments
Required:
- `g:AbstractGraph` : acylic graph.
- `t:Int` : index of the target vertex in `g`.

```julia-rep
    sg, vmap = reachable_to(g, t)
````
"""
function reachable_to_subgraph(g:AbstractGraph{T}, s:Int) where T
    vertices = reachable_to(g, s)
    push!(vertices, s)  # add the source vertex to the reachable set
    induced_subgraph(g, vertices)
end

# The set of all vertices reachable to and reachable from vertex s
"""
    reach(g, v)

Returns the reach of vertex `v` in `g`, ie., the set of all vertices in `g` that can
reach vertex `v` and can be reached from `v`.

# Arguments
Required:
- `g:AbstractGraph` : acylic graph.
- `v:Int` : index of a vertex in `g`.
"""
function reach(g:AbstractGraph{T}, v:Int) where T
    union(reachable_to(g, v), reachable_from(g, v))
end

# Subgraph induced by the reach of a vertex
"""
    reach_subgraph(g, v)

Returns a subgraph in `g` consisting of vertex `v ` and all vertices that can reach `v`, as
well as all vertices that `v` can reach.  In addition, a vector is returned that maps the
vertex IDs in the subgraph to their IDs in the orginal graph `g`.

# Arguments
Required:
- `g:AbstractGraph` : acylic graph.
- `v:Int` : index of a vertex in `g`.

```julia-rep
    sg, vmap = reachable_to(g, v)
````
"""
function reach_subgraph(g:AbstractGraph{T}, v:Int) where T
    vertices = reach(g, v)
    push!(vertices, v)  # add the source vertex to the reachable set
    induced_subgraph(g, vertices)
end

# find all paths in a graph
"""
    all_paths(g)

 Enumerate all of the unique paths in acyclic graph `g`, where a path in this case must include a
 source vertex (a vertex with in-degree zero) and a different sink vertex (a vertex with out-degree
 zero).  I.e., a path is this case must contain at least two vertices.  This function returns
 an array of these paths, where each path consists of an array of vertex IDs.

 # Arguments
Required:
- `g:AbstractGraph` : acylic graph.

```julia-repl
julia> paths = all_paths(g)
```
"""
function all_paths(g:AbstractGraph{T}) where T
    # check that g is acyclic
    if is_cyclic(g)
        error("all_paths(): input graph has cycles")
    end
    que = Queue{Array}()
    paths = Array[]
    sinks = Int[]
    for v in vertices(g)
        if (length(outneighbors(g,v)) == 0) && (length(inneighbors(g,v)) > 0) # consider only sink vertices with a non-zero in-degree
            push!(sinks, v)
        end
    end
    for v in sinks
        enqueue!(que, [v])
        while !isempty(que) # work backwards from sink v to all sources reachable to v in BFS fashion
            x = dequeue!(que) # grab a path from the queue
            for (i, u) in enumerate(inneighbors(g, x[1]))  # consider the in-neighbors at the beginning of the current path
                if i == 1 # first neighbor, build onto exising path
                    insert!(x, 1, u)  # prepend vertex u to array x
                    # if reached a source vertex, done with the path; otherwise, put it back in queue
                    length(inneighbors(g, u)) == 0 ? push!(paths, x) : enqueue!(que, x)
                else # not first neighbor, create a copy of the path
                    y = copy(x)
                    y[1] = u  # overwrite first element in array
                    length(inneighbors(g, u)) == 0 ? push!(paths, y) : enqueue!(que, y)
                end
            end
        end
    end
    return paths
end

# The longest path from vertx s to any other vertex in a DAG G (not necessarily unique).
# Note: in a DAG G, longest paths in G = shortest paths in -G
"""
    longest_path(g, s)

The longest path from vertx s to any other vertex in a acyclic graph `g`.  The longest path
is not necessarily unique, i.e., there can be more than one longest path between two vertices.

 # Arguments
Required:
- `g:AbstractGraph` : acylic graph.
- `s:Int` : index of the source vertex in `g`.

```julia-repl
julia> path = longest_paths(g, s)
```
"""
function longest_path(g:AbstractGraph{T}, s:Int) where T
    if is_cyclic(g)
        error("longest_path(): input graph has cycles")
    end
    lp = Array{Edge}[]
    max = 0
    # shortest path from s to all vertices in -G
    for path in enumerate_paths(dijkstra_shortest_paths(g, s, -weights(g)))
        if length(path) > max
            lp = path
            max = length(path)
        end
    end
    return lp
end

# Find all of the longest paths in an acyclic graph.
"""
    longest_paths(g)

Finds the set of longest paths in `g`, and returns an array of vertex arrays, where each vertex
array contains the vertices in a longest path.

 # Arguments
Required:
- `g:AbstractGraph` : acylic graph.

```julia-repl
julia> paths = longest_paths(g)
```
"""
function longest_paths(g:AbstractGraph{T}) where T
    if is_cyclic(g)
        error("longest_paths(): input graph has cycles")
    end
    lps = Array[]
    max = 0
    paths = all_paths(g)
    for path in paths  # find length of longest path
        length(path) > max ? max = length(path) : nothing
    end
    for path in paths
        length(path) == max ? push!(lps, path) : nothing
    end
    return lps
end

# determine the number of edges crossing a graph cut, where s is the set of vertices on one side of the cut,
# and the other side are the remanining vertices in g.
"""
    edge_crossing(g, s)

Given a graph ``g=(V,E)``,and a set of vertices ``s \\subseteq V``, determine the number of edges
crossing the cut determined by the partition ``(s,V-s)``.

 # Arguments
Required:
- `g:AbstractGraph` : acylic graph.
- `s:Array{Int}` : array of vertex indicies.

```julia-repl
julia> cut_size = edge_crossing(g, s)
```
"""
function edge_crossings(g:AbstractGraph{T}, s:Array{Int,1}) where T
    total = 0
    d = convert(Array{Int,1}, vertices(g)) # collect the graph vertex ids in a integer array
    filter!(x->x ∉ s, d)  # remove the vertex ids in s from d
    for v in s
        total += edge_crossings(g, v, d)
    end
    return total
end

# find number of crossing from a single vertex to all vertices in some vertex set d
function edge_crossings(g:AbstractGraph{T}, s:Int, d:Array{Int,1}) where T
    total = 0
    for v in d
        has_edge(g, s, v) ? total += 1 : nothing
    end
    return total
end
