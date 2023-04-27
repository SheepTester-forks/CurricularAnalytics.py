from typing import Any, Dict, Generic, Hashable, Tuple, TypeVar, Union

Node = TypeVar("Node", bound=Hashable)
Edge = Tuple[Node, Node]

class DiGraph(Generic[Node]):
    def add_node(self, node_for_adding: Node, **attr: Dict[Hashable, Any]) -> None: ...
    def add_edge(
        self, u_of_edge: Node, v_of_edge: Node, **attr: Dict[Hashable, Any]
    ) -> None: ...
    def __getitem__(self, n: Node) -> Dict[Hashable, Any]: ...

def has_path(G: DiGraph[Node], source: Hashable, target: Hashable) -> bool: ...
def set_edge_attributes(
    G: DiGraph[Node],
    values: Dict[Union[Node, Edge[Node]], Dict[Hashable, Any]],
) -> None: ...
