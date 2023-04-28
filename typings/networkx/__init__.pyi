from typing import (
    Any,
    Dict,
    Generic,
    Hashable,
    Iterable,
    List,
    Mapping,
    Optional,
    Set,
    Tuple,
    TypeVar,
)

Node = TypeVar("Node", bound=Hashable)
Edge = Tuple[Node, Node]

class NodeView(Mapping[Node, Any], Set[Node], Generic[Node]):
    pass

class Graph(Generic[Node]):
    nodes: NodeView[Node]
    def add_node(self, node_for_adding: Node, **attr: Dict[Hashable, Any]) -> None: ...
    def add_edge(
        self, u_of_edge: Node, v_of_edge: Node, **attr: Dict[Hashable, Any]
    ) -> None: ...
    def has_edge(self, u: Node, v: Node) -> bool: ...
    def neighbors(self, n: Node) -> Iterable[Node]: ...
    def number_of_nodes(self) -> int: ...
    def copy(self) -> DiGraph[Node]: ...
    def __getitem__(self, n: Node) -> Dict[Hashable, Any]: ...

class DiGraph(Graph[Node]):
    pass

def set_edge_attributes(
    G: DiGraph[Node],
    values: Dict[Edge[Node], Dict[Hashable, Any]],
) -> None: ...
def has_path(G: DiGraph[Node], source: Hashable, target: Hashable) -> bool: ...
def simple_cycles(G: DiGraph[Node]) -> Iterable[List[Node]]: ...
def find_cycle(G: DiGraph[Node], source: Optional[Node] = None) -> List[Edge[Node]]: ...
def weakly_connected_components(G: DiGraph[Node]) -> Iterable[Set[Node]]: ...

class NetworkXNoCycle(Exception):
    """Exception for algorithms that should return a cycle when running
    on graphs where such a cycle does not exist."""
