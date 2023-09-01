import unittest

import networkx as nx

from curricularanalytics import (
    all_paths,
    cross_edge,
    dfs,
    gad,
    longest_path,
    longest_paths,
    reach,
    reach_subgraph,
    reachable_from,
    reachable_from_subgraph,
    reachable_to,
    reachable_to_subgraph,
    topological_sort,
    tree_edge,
)


class GraphAlgsTests(unittest.TestCase):
    g: "nx.DiGraph[int]" = nx.DiGraph()
    "12-vertex test diagraph with 5 components"

    def __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName)

        self.g.add_nodes_from(range(1, 13))

        self.g.add_edge(2, 3)
        self.g.add_edge(2, 5)
        self.g.add_edge(2, 6)
        self.g.add_edge(4, 2)
        self.g.add_edge(6, 10)
        self.g.add_edge(7, 8)
        self.g.add_edge(7, 11)

        self.assertEqual(self.g.number_of_nodes(), 12)
        self.assertEqual(self.g.number_of_edges(), 7)

    def test_dfs(self) -> None:
        "test dfs"
        rtn = dfs(self.g)
        self.assertEqual(rtn[0][2, 5], tree_edge)
        self.assertEqual(rtn[0][2, 6], tree_edge)
        self.assertEqual(rtn[0][6, 10], tree_edge)
        self.assertEqual(rtn[0][4, 2], cross_edge)
        self.assertEqual(rtn[0][7, 8], tree_edge)
        self.assertEqual(rtn[0][7, 11], tree_edge)
        self.assertEqual(rtn[0][2, 3], tree_edge)

    def test_topological_sort(self) -> None:
        # topological sort w/ no ordering by component size
        self.assertEqual(
            topological_sort(self.g), [[1], [4, 2, 6, 10, 5, 3], [7, 11, 8], [9], [12]]
        )
        # topological sort w/ ordering by component size in descenting order
        self.assertEqual(
            topological_sort(self.g, sort="descending"),
            [[4, 2, 6, 10, 5, 3], [7, 11, 8], [1], [9], [12]],
        )
        # topological sort w/ ordering by component size in ascending order
        self.assertEqual(
            topological_sort(self.g, sort="ascending"),
            [[1], [9], [12], [7, 11, 8], [4, 2, 6, 10, 5, 3]],
        )

    def test_gad(self) -> None:
        "test gad()"
        t = gad(self.g)
        self.assertFalse(t.has_edge(2, 3))
        self.assertTrue(t.has_edge(3, 2))
        self.assertTrue(t.has_edge(5, 2))
        self.assertTrue(t.has_edge(6, 2))
        self.assertTrue(t.has_edge(2, 4))
        self.assertTrue(t.has_edge(10, 6))
        self.assertTrue(t.has_edge(8, 7))
        self.assertTrue(t.has_edge(11, 7))

    def test_reachable_from(self) -> None:
        "test reachable_from()"
        self.assertEqual(sorted(reachable_from(self.g, 2)), [3, 5, 6, 10])

    def test_reachable_from_subgraph(self) -> None:
        "test reachable_from_subgraph()"
        rg = reachable_from_subgraph(self.g, 2)
        self.assertEqual(rg.number_of_nodes(), 5)
        self.assertEqual(rg.number_of_edges(), 4)
        self.assertEqual(sorted(rg.nodes), [2, 3, 5, 6, 10])

    def test_reachable_to(self) -> None:
        "test reachable_to()"
        self.assertEqual(reachable_to(self.g, 2), [4])

    def test_reachable_to_subgraph(self) -> None:
        "test reachable_to_subgraph()"
        rt = reachable_to_subgraph(self.g, 2)
        self.assertEqual(rt.number_of_nodes(), 2)
        self.assertEqual(rt.number_of_edges(), 1)
        self.assertEqual(sorted(rt.nodes), [2, 4])

    def test_reach(self) -> None:
        "test reach()"
        self.assertEqual(sorted(reach(self.g, 2)), [3, 4, 5, 6, 10])

    def test_reach_subgraph(self) -> None:
        "test reach_subgraph()"
        r = reach_subgraph(self.g, 2)
        self.assertEqual(r.number_of_nodes(), 6)
        self.assertEqual(r.number_of_edges(), 5)
        self.assertEqual(sorted(r.nodes), [2, 3, 4, 5, 6, 10])

    def test_all_paths(self) -> None:
        "test all_paths()"
        paths = all_paths(self.g)
        self.assertEqual(len(paths), 5)
        self.assertIn([4, 2, 3], paths)
        self.assertIn([4, 2, 5], paths)
        self.assertIn([7, 8], paths)
        self.assertIn([4, 2, 6, 10], paths)
        self.assertIn([7, 11], paths)

    def test_longest(self) -> None:
        "test longest path algorithms"
        self.assertEqual(longest_path(self.g, 2), [2, 6, 10])
        self.assertEqual(longest_paths(self.g), [[4, 2, 6, 10]])
