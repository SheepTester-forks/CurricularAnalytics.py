from io import StringIO
import unittest
from src.CurricularAnalytics import (
    basic_metrics,
    blocking_factor,
    centrality,
    complexity,
    dead_ends,
    delay_factor,
    extraneous_requisites,
    isvalid_curriculum,
    similarity,
)
from src.DataHandler import read_csv

from src.DataTypes.Course import Course
from src.DataTypes.Curriculum import Curriculum
from src.DataTypes.DataTypes import co, pre, strict_co


class CurricularAnalyticsTests(unittest.TestCase):
    def test_isvalid_curriculum(self) -> None:
        """
        Curric1: 1-vertex test curriculum - invalid (a one-vertex cycle)

           A *---
           |     |
           |     |
            ------
        """

        A = Course("A", 3)
        A.add_requisite(A, pre)
        curric = Curriculum("Cycle", [A])

        # Test isvalid_curriculum()
        errors = StringIO()
        self.assertFalse(isvalid_curriculum(curric, errors))
        # @test String(take!(errors)) == "\nCurriculum Cycle contains the following requisite cycles:\n(A)\n"

    def test_create_unsatisfiable_requisites(self) -> None:
        r"""
        create unsatisfiable requisites

            (pre)
           A---* B
          * \  |* (strict_co)
             \ |
              \|
               C
        """

        a = Course("A", 3)
        b = Course("B", 3)
        c = Course("C", 3)

        b.add_requisite(a, pre)
        b.add_requisite(c, strict_co)
        a.add_requisite(c, pre)  # can be any requisite

        curric = Curriculum("Unsatisfiable", [a, b, c], sortby_ID=False)
        errors = StringIO()
        self.assertFalse(isvalid_curriculum(curric, errors))

    def test_big_unsatisfiable_curric(self):
        curric = read_csv("big_unsatisfiable_curric.csv")
        self.assertIsInstance(curric, Curriculum)
        assert isinstance(curric, Curriculum)
        self.assertFalse(isvalid_curriculum(curric))

    def test_extraneous_prerequisite(self) -> None:
        """
        Curric1: 4-vertex test curriculum - invalid (contains a extraneous prerequisite)

           A --------* C
           |        */ |*
           |*       /  |
           B ------/   D

           Course A is an extraneous prerequisite for course C
        """

        a = Course("A", 3)
        b = Course("B", 3)
        c = Course("C", 3)
        d = Course("D", 1)

        c.add_requisite(a, pre)
        c.add_requisite(b, pre)
        c.add_requisite(d, co)
        b.add_requisite(a, co)

        curric = Curriculum("Extraneous", [a, b, c, d], sortby_ID=False)
        # Test extraneous_requisites()
        self.assertEqual(len(extraneous_requisites(curric)), 1)

    def test_8_vertex_test_curriculum(self) -> None:
        """
        8-vertex test curriculum - valid

           A --------* C --------* E           G
                    */ |*
                    /  |
           B-------/   D --------* F           H

           (A,C) - pre;  (C,E) -  pre; (B,C) - pre; (D,C) - co; (C,E) - pre; (D,F) - pre
        """

        A = Course(
            "Introduction to Baskets",
            3,
            institution="ACME State University",
            prefix="BW",
            num="101",
            canonical_name="Baskets I",
        )
        B = Course(
            "Swimming",
            3,
            institution="ACME State University",
            prefix="PE",
            num="115",
            canonical_name="Physical Education",
        )
        C = Course(
            "Basic Basket Forms",
            3,
            institution="ACME State University",
            prefix="BW",
            num="111",
            canonical_name="Baskets I",
        )
        D = Course(
            "Basic Basket Forms Lab",
            1,
            institution="ACME State University",
            prefix="BW",
            num="111L",
            canonical_name="Baskets I Laboratory",
        )
        E = Course(
            "Advanced Basketry",
            3,
            institution="ACME State University",
            prefix="BW",
            num="300",
            canonical_name="Baskets II",
        )
        F = Course(
            "Basket Materials & Decoration",
            3,
            institution="ACME State University",
            prefix="BW",
            num="214",
            canonical_name="Basket Materials",
        )
        G = Course(
            "Humanitites Elective",
            3,
            institution="ACME State University",
            prefix="HU",
            num="101",
            canonical_name="Humanitites Core",
        )
        H = Course(
            "Technical Elective",
            3,
            institution="ACME State University",
            prefix="BW",
            num="3xx",
            canonical_name="Elective",
        )

        C.add_requisite(A, pre)
        C.add_requisite(B, pre)
        C.add_requisite(D, co)
        E.add_requisite(C, pre)
        F.add_requisite(D, pre)

        curric = Curriculum(
            "Underwater Basket Weaving",
            [A, B, C, D, E, F, G, H],
            institution="ACME State University",
            CIP="445786",
            sortby_ID=False,
        )

        # Test isvalid_curriculum() and extraneous_requisites()
        errors = StringIO()
        self.assertTrue(isvalid_curriculum(curric, errors))
        self.assertEqual(len(extraneous_requisites(curric)), 0)

        self.assertEqual(
            delay_factor(curric), (19.0, [3.0, 3.0, 3.0, 3.0, 3.0, 2.0, 1.0, 1.0])
        )
        self.assertEqual(blocking_factor(curric), (8, [2, 2, 1, 3, 0, 0, 0, 0]))
        self.assertEqual(centrality(curric), (9, [0, 0, 9, 0, 0, 0, 0, 0]))
        self.assertEqual(
            complexity(curric), (27.0, [5.0, 5.0, 4.0, 6.0, 3.0, 2.0, 1.0, 1.0])
        )

    def test_7_vertex_test_curriculum(self) -> None:
        """
        Curric: 7-vertex test curriculum - valid

           A --------* C --------* E
           |           |
           |*          |*
           B---------* D --------* F
                       |        /*
                       |*      /
                       G------/

           (A,B) - co; (A,C) - pre; (B,D) - pre; (C,D) -  co;
           (C,E) - pre; (D,F) - pre; (D,G) - co; (G,F) - pre
        """

        A = Course("A", 3)
        B = Course("B", 1)
        C = Course("C", 3)
        D = Course("D", 1)
        E = Course("E", 3)
        F = Course("F", 3)
        G = Course("G", 3)

        B.add_requisite(A, co)
        C.add_requisite(A, pre)
        D.add_requisite(B, pre)
        D.add_requisite(C, co)
        E.add_requisite(C, pre)
        F.add_requisite(D, pre)
        G.add_requisite(D, co)
        F.add_requisite(G, pre)

        curric = Curriculum(
            "Postmodern Basket Weaving", [A, B, C, D, E, F, G], sortby_ID=False
        )

        # Test isvalid_curriculum() and extraneous_requisites()
        errors = StringIO()
        self.assertTrue(isvalid_curriculum(curric, errors))
        self.assertEqual(len(extraneous_requisites(curric)), 0)

        # Test analytics
        self.assertEqual(
            delay_factor(curric), (33.0, [5.0, 5.0, 5.0, 5.0, 3.0, 5.0, 5.0])
        )
        self.assertEqual(blocking_factor(curric), (16, [6, 3, 4, 2, 0, 0, 1]))
        self.assertEqual(centrality(curric), (49, [0, 9, 12, 18, 0, 0, 10]))
        self.assertEqual(
            complexity(curric), (49.0, [11.0, 8.0, 9.0, 7.0, 3.0, 5.0, 6.0])
        )

    def test_delay_factor_multiple_paths(self) -> None:
        """
        Tested added to check that delay factor is computed correctly when multiple long paths of the same length pass through a given course
        """
        A = Course("A", 3)
        B = Course("B", 3)
        C = Course("C", 3)
        D = Course("D", 3)

        B.add_requisite(A, pre)
        C.add_requisite(A, pre)
        D.add_requisite(B, pre)
        D.add_requisite(C, pre)

        curric = Curriculum("Delay Factor Test", [A, B, C, D], sortby_ID=False)
        self.assertEqual(delay_factor(curric), (12.0, [3.0, 3.0, 3.0, 3.0]))


class Test8VertexTestCurriculum(unittest.TestCase):
    """
    8-vertex test curriculum - valid

    A --------* C --------* E G
    */ |*
    / |
    B-------/ D --------* F H

    (A,C) - pre; (C,E) - pre; (B,C) - pre; (D,C) - co; (C,E) - pre; (D,F) - pre
    """

    A = Course(
        "Introduction to Baskets",
        3,
        institution="ACME State University",
        prefix="BW",
        num="101",
        canonical_name="Baskets I",
    )
    B = Course(
        "Swimming",
        3,
        institution="ACME State University",
        prefix="PE",
        num="115",
        canonical_name="Physical Education",
    )
    C = Course(
        "Basic Basket Forms",
        3,
        institution="ACME State University",
        prefix="BW",
        num="111",
        canonical_name="Baskets I",
    )
    D = Course(
        "Basic Basket Forms Lab",
        1,
        institution="ACME State University",
        prefix="BW",
        num="111L",
        canonical_name="Baskets I Laboratory",
    )
    E = Course(
        "Advanced Basketry",
        3,
        institution="ACME State University",
        prefix="BW",
        num="300",
        canonical_name="Baskets II",
    )
    F = Course(
        "Basket Materials & Decoration",
        3,
        institution="ACME State University",
        prefix="BW",
        num="214",
        canonical_name="Basket Materials",
    )
    G = Course(
        "Humanitites Elective",
        3,
        institution="ACME State University",
        prefix="HU",
        num="101",
        canonical_name="Humanitites Core",
    )
    H = Course(
        "Technical Elective",
        3,
        institution="ACME State University",
        prefix="BW",
        num="3xx",
        canonical_name="Elective",
    )

    curric = Curriculum(
        "Underwater Basket Weaving",
        [A, B, C, D, E, F, G, H],
        institution="ACME State University",
        CIP="445786",
        sortby_ID=False,
    )

    def __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName)

        self.C.add_requisite(self.A, pre)
        self.C.add_requisite(self.B, pre)
        self.C.add_requisite(self.D, co)
        self.E.add_requisite(self.C, pre)
        self.F.add_requisite(self.D, pre)

    def test_isvalid_curriculum(self) -> None:
        errors = StringIO()
        self.assertTrue(isvalid_curriculum(self.curric, errors))

    def test_extraneous_requisites(self) -> None:
        self.assertEqual(len(extraneous_requisites(self.curric)), 0)

    def test_basic_metrics(self) -> None:
        basic_metrics(self.curric)
        self.assertEqual(self.curric.credit_hours, 22)
        self.assertEqual(self.curric.num_courses, 8)
        self.assertEqual(
            self.curric.metrics["blocking factor"], (8, [2, 2, 1, 3, 0, 0, 0, 0])
        )
        self.assertEqual(
            self.curric.metrics["delay factor"],
            (19.0, [3.0, 3.0, 3.0, 3.0, 3.0, 2.0, 1.0, 1.0]),
        )
        self.assertEqual(
            self.curric.metrics["centrality"], (9, [0, 0, 9, 0, 0, 0, 0, 0])
        )
        self.assertEqual(
            self.curric.metrics["complexity"],
            (27.0, [5.0, 5.0, 4.0, 6.0, 3.0, 2.0, 1.0, 1.0]),
        )
        self.assertEqual(self.curric.metrics["max. blocking factor"], 3)
        self.assertEqual(len(self.curric.metrics["max. blocking factor courses"]), 1)
        self.assertEqual(
            self.curric.metrics["max. blocking factor courses"][1].name,
            "Basic Basket Forms Lab",
        )
        self.assertEqual(self.curric.metrics["max. centrality"], 9)
        self.assertEqual(len(self.curric.metrics["max. centrality courses"]), 1)
        self.assertEqual(
            self.curric.metrics["max. centrality courses"][1].name, "Basic Basket Forms"
        )
        self.assertEqual(self.curric.metrics["max. delay factor"], 3.0)
        self.assertEqual(len(self.curric.metrics["max. delay factor courses"]), 5)
        self.assertEqual(
            self.curric.metrics["max. delay factor courses"][1].name,
            "Introduction to Baskets",
        )
        self.assertEqual(self.curric.metrics["max. complexity"], 6.0)
        self.assertEqual(len(self.curric.metrics["max. complexity courses"]), 1)
        self.assertEqual(
            self.curric.metrics["max. complexity courses"][1].name,
            "Basic Basket Forms Lab",
        )

    def test_similarity(self) -> None:
        curric_mod = Curriculum(
            "Underwater Basket Weaving (no elective)",
            [self.A, self.B, self.C, self.D, self.E, self.F, self.G],
            institution="ACME State University",
            CIP="445786",
            sortby_ID=False,
        )
        self.assertEqual(similarity(curric_mod, self.curric), 0.875)
        self.assertEqual(similarity(self.curric, curric_mod), 1.0)

    def dead_ends(self) -> None:
        de = dead_ends(self.curric, frozenset({"BW"}))
        self.assertEqual(de, (frozenset({"BW"}), []))
        I = Course(
            "Calculus I",
            4,
            institution="ACME State University",
            prefix="MA",
            num="110",
            canonical_name="Calculus I",
        )
        J = Course(
            "Calculus II",
            4,
            institution="ACME State University",
            prefix="MA",
            num="210",
            canonical_name="Calculus II",
        )
        J.add_requisite(I, pre)
        curric_de = Curriculum(
            "Underwater Basket Weaving (w/ Calc)",
            [self.A, self.B, self.C, self.D, self.E, self.F, self.G, self.H, I, J],
            institution="ACME State University",
            CIP="445786",
            sortby_ID=False,
        )
        de = dead_ends(curric_de, frozenset({"BW"}))
        self.assertEqual(len(de[1]), 1)
        self.assertEqual(de[1][0], J)


if __name__ == "__main__":
    unittest.main()
