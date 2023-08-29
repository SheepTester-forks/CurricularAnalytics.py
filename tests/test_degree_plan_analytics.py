from contextlib import redirect_stdout
from io import StringIO
import unittest

from curricularanalytics.types.course import Course
from curricularanalytics.types.curriculum import Curriculum
from curricularanalytics.types.data_types import co, pre, strict_co
from curricularanalytics.types.degree_plan import DegreePlan, Term
from curricularanalytics.DegreePlanAnalytics import (
    basic_metrics,
    plan_requisite_distance,
    requisite_distance,
)

r"""
6-vertex test curriculum - valid

    /---------------------*\
A --------* C    /-----* E
            /-----/      */|*
            /  |----------/ |
B-------/   D            F
    \---------------------*/

(A,C) - pre;  (A,E) -  pre; (B,E) - pre; (B,F) - pre; (D,E) - co; (F,E) - strict_co
"""

A = Course("A", 3)
B = Course("B", 1)
C = Course("C", 2)
D = Course("D", 1)
E = Course("E", 4)
F = Course("F", 1)

E.add_requisite(A, pre)
C.add_requisite(A, pre)
E.add_requisite(B, pre)
F.add_requisite(B, pre)
E.add_requisite(D, co)
E.add_requisite(F, strict_co)

curric = Curriculum("Test Curric", [A, B, C, D, E, F])
terms = [Term([A, B]), Term([C, D]), Term([E, F])]
dp = DegreePlan("Test Plan", curric, terms)


class DegreePlanAnalyticsTests(unittest.TestCase):
    def test_isvalid(self) -> None:
        self.assertTrue(dp.isvalid_degree_plan())
        dp_bad1 = DegreePlan(
            "Bad Plan 1", curric, [terms[0], terms[1]]
        )  # missing some courses
        self.assertFalse(dp_bad1.isvalid_degree_plan())
        dp_bad2 = DegreePlan(
            "Bad Plan 2", curric, [terms[1], terms[0], terms[2]]
        )  # out of order requisites
        self.assertFalse(dp_bad2.isvalid_degree_plan())

        self.assertEqual(dp.find_term(F), 2)

    def test_print_plan(self) -> None:
        "Test the output of print_plan()"
        read_pipe = StringIO()
        with redirect_stdout(read_pipe):
            dp.print_plan()
        read_pipe.seek(0)
        self.assertEqual(
            read_pipe.read().splitlines()[0:17],
            [
                "",
                "Degree Plan: Test Plan for BS in Test Curric",
                "",
                " 12 credit hours",
                " Term 1 courses:",
                " A ",
                " B ",
                "",
                "",
                " Term 2 courses:",
                " C ",
                " D ",
                "",
                "",
                " Term 3 courses:",
                " E ",
                " F ",
            ],
        )

    def test_requisite_distance(self) -> None:
        "Test requisite_distance(plan, course) and requisite_distance(plan)"
        self.assertEqual(requisite_distance(dp, A), 0)
        self.assertEqual(requisite_distance(dp, B), 0)
        self.assertEqual(requisite_distance(dp, C), 1)
        self.assertEqual(requisite_distance(dp, D), 0)
        self.assertEqual(requisite_distance(dp, E), 5)
        self.assertEqual(requisite_distance(dp, F), 2)
        self.assertEqual(
            plan_requisite_distance(
                dp,
            ),
            8,
        )

    def test_basic_metrics(self) -> None:
        "Test basic basic_metrics(plan)"
        basic_metrics(dp)
        self.assertEqual(dp.metrics.get("total credit hours"), 12)
        self.assertEqual(dp.metrics.get("avg. credits per term"), 4.0)
        self.assertEqual(dp.metrics.get("min. credits in a term"), 3)
        self.assertEqual(dp.metrics.get("max. credits in a term"), 5)
        self.assertAlmostEqual(
            dp.metrics.get("term credit hour std. dev.", -1), 0.816497, places=5
        )
        self.assertEqual(dp.metrics.get("number of terms"), 3)
        self.assertEqual(dp.metrics.get("min. credit term"), 2)
        self.assertEqual(dp.metrics.get("max. credit term"), 3)
