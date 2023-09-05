import unittest
from contextlib import redirect_stdout
from io import StringIO

from curricularanalytics import Course, Curriculum, DegreePlan, Term, co, pre, strict_co

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
        self.assertTrue(dp.is_valid())
        dp_bad1 = DegreePlan(
            "Bad Plan 1", curric, [terms[0], terms[1]]
        )  # missing some courses
        self.assertFalse(dp_bad1.is_valid())
        dp_bad2 = DegreePlan(
            "Bad Plan 2", curric, [terms[1], terms[0], terms[2]]
        )  # out of order requisites
        self.assertFalse(dp_bad2.is_valid())

        self.assertEqual(dp.find_term(F), 2)

    def test_print_plan(self) -> None:
        "Test the output of print_plan()"
        read_pipe = StringIO()
        with redirect_stdout(read_pipe):
            dp.print()
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
        self.assertEqual(dp.requisite_distance(A), 0)
        self.assertEqual(dp.requisite_distance(B), 0)
        self.assertEqual(dp.requisite_distance(C), 1)
        self.assertEqual(dp.requisite_distance(D), 0)
        self.assertEqual(dp.requisite_distance(E), 5)
        self.assertEqual(dp.requisite_distance(F), 2)
        self.assertEqual(dp.total_requisite_distance, 8)

    def test_basic_metrics(self) -> None:
        "Test basic basic_metrics(plan)"
        self.assertEqual(dp.credit_hours, 12)
        self.assertEqual(dp.basic_metrics.average, 4.0)
        self.assertEqual(dp.basic_metrics.min, 3)
        self.assertEqual(dp.basic_metrics.max, 5)
        self.assertAlmostEqual(dp.basic_metrics.stddev, 0.816497, places=5)
        self.assertEqual(dp.num_terms, 3)
        self.assertEqual(dp.basic_metrics.min_term + 1, 2)
        self.assertEqual(dp.basic_metrics.max_term + 1, 3)
