import unittest

from curricularanalytics import (
    Course,
    Curriculum,
    bin_filling,
    create_degree_plan,
    pre,
    strict_co,
)


class DegreePlanCreationTests(unittest.TestCase):
    def test_curric_1(self) -> None:
        """
        4-course curriculum - only one possible degree plan w/ max_cpt

           A --------* B


           C --------* D

           (A,B) - pre;  (C,D) - pre
        """

        A = Course(
            "A",
            3,
            institution="ACME State",
            prefix="BW",
            num="101",
            canonical_name="Baskets I",
        )
        B = Course(
            "B",
            3,
            institution="ACME State",
            prefix="BW",
            num="201",
            canonical_name="Baskets II",
        )
        C = Course(
            "C",
            3,
            institution="ACME State",
            prefix="BW",
            num="102",
            canonical_name="Basket Apps I",
        )
        D = Course(
            "D",
            3,
            institution="ACME State",
            prefix="BW",
            num="202",
            canonical_name="Basket Apps II",
        )

        B.add_requisite(A, pre)
        D.add_requisite(C, pre)

        curric = Curriculum("Basket Weaving", [A, B, C, D], institution="ACME State")

        terms = bin_filling(curric, max_cpt=6)
        if not terms:
            self.fail()

        self.assertIn(terms[0].courses[0].name, ["A", "C"])
        self.assertIn(terms[0].courses[1].name, ["A", "C"])
        self.assertIn(terms[1].courses[0].name, ["B", "D"])
        self.assertIn(terms[1].courses[1].name, ["B", "D"])

    def test_curric_2(self) -> None:
        """
        4-course curriculum - only one possible degree plan w/ max_cpt

           A          C
           |          |
           |          |
           *          *
           B          D

           (A,B) - strict_co;  (C,D) - strict_co
        """

        A = Course(
            "A",
            3,
            institution="ACME State",
            prefix="BW",
            num="101",
            canonical_name="Baskets I",
        )
        B = Course(
            "B",
            3,
            institution="ACME State",
            prefix="BW",
            num="201",
            canonical_name="Baskets II",
        )
        C = Course(
            "C",
            3,
            institution="ACME State",
            prefix="BW",
            num="102",
            canonical_name="Basket Apps I",
        )
        D = Course(
            "D",
            3,
            institution="ACME State",
            prefix="BW",
            num="202",
            canonical_name="Basket Apps II",
        )

        B.add_requisite(A, strict_co)
        D.add_requisite(C, strict_co)

        curric = Curriculum("Basket Weaving", [A, B, C, D], institution="ACME State")

        terms = bin_filling(curric, max_cpt=6)
        if not terms:
            self.fail()

        self.assertIn(terms[0].courses[0].name, ["A", "B"])
        self.assertIn(terms[0].courses[1].name, ["A", "B"])
        self.assertIn(terms[1].courses[0].name, ["C", "D"])
        self.assertIn(terms[1].courses[1].name, ["C", "D"])

        dp = create_degree_plan(curric, max_cpt=6)
        if dp is None:
            self.fail()

        self.assertEqual(dp.curriculum.graph.number_of_nodes(), 4)
        self.assertEqual(dp.curriculum.graph.number_of_edges(), 2)
        for term in dp.terms:
            credits = 0
            for c in term.courses:
                credits += c.credit_hours
            self.assertGreaterEqual(credits, 3)
            self.assertLessEqual(credits, 6)
        self.assertIn(terms[0].courses[0].name, ["A", "B"])
        self.assertIn(terms[0].courses[1].name, ["A", "B"])
        self.assertIn(terms[1].courses[0].name, ["C", "D"])
        self.assertIn(terms[1].courses[1].name, ["C", "D"])
