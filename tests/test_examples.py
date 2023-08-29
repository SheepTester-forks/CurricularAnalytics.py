from typing import List
import unittest

from curricularanalytics import Course, pre
from curricularanalytics.types.course import AbstractCourse
from curricularanalytics.types.curriculum import Curriculum
from curricularanalytics.types.degree_plan import DegreePlan, Term


class ExampleTests(unittest.TestCase):
    def test_example_1(self):
        """
        Curriculum assoicated with curricula c1, page 9, Heileman, G. L., Slim, A., Hickman, M.,  and Abdallah, C. T. (2018).
        Curricular Analytics: A Framework for Quantifying the Impact of Curricular Reforms and Pedagogical Innovations
        https://arxiv.org/pdf/1811.09676.pdf
        """
        # create the courses
        c: List[AbstractCourse] = [
            # term 1
            Course("Calculus 1", 3, prefix="MATH ", num="1011"),
            # term 2
            Course("Physics I: Mechanics & Heat", 3, prefix="PHYS", num="1112"),
            Course("Calculus 2", 3, prefix="MATH", num="1920"),
            # term 3
            Course("Circuits 1", 3, prefix="EE", num="2200"),
        ]

        # term 1
        c[1].add_requisite(c[2], pre)
        c[1].add_requisite(c[3], pre)

        # term 2
        c[2].add_requisite(c[4], pre)

        curric = Curriculum("Example Curricula c1", c)
        self.assertTrue(curric.is_valid())
        self.assertEqual(curric.delay_factor[0], 11.0)
        self.assertEqual(list(curric.delay_factor[1].values()), [3.0, 2.0, 3.0, 3.0])
        self.assertEqual(curric.blocking_factor[0], 4)
        self.assertEqual(list(curric.blocking_factor[1].values()), [1, 0, 0, 3])
        self.assertEqual(curric.centrality[0], 3)
        self.assertEqual(list(curric.centrality[1].values()), [3, 0, 0, 0])
        self.assertEqual(curric.complexity[0], 15.0)
        self.assertEqual(list(curric.complexity[1].values()), [4.0, 2.0, 3.0, 6.0])

        terms = [
            Term([c[1]]),
            Term([c[2], c[3]]),
            Term([c[4]]),
        ]

        dp = DegreePlan("Example Curricula c1", curric, terms)

        self.assertEqual(dp.credit_hours, 12)
        self.assertEqual(dp.basic_metrics.average, 4.0)
        self.assertEqual(dp.basic_metrics.min, 3)
        self.assertAlmostEqual(dp.basic_metrics.stddev, 1.4142135623730951, places=5)
        self.assertEqual(dp.num_terms, 3)
        self.assertEqual(dp.basic_metrics.max, 6)
        self.assertEqual(dp.basic_metrics.min_term, 1)
        self.assertEqual(dp.basic_metrics.max_term, 2)
