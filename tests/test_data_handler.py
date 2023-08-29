import os
import unittest

from curricularanalytics import (
    Course,
    Curriculum,
    DegreePlan,
    Term,
    co,
    pre,
    read_csv,
    semester,
    strict_co,
    write_csv,
)


class DataHandlerTests(unittest.TestCase):
    def test_curriclum_data_format(self) -> None:
        "test the data file format used for curricula"
        curric = read_csv("./tests/curriculum.csv")
        self.assertIsInstance(curric, Curriculum)
        assert isinstance(curric, Curriculum)

        self.assertEqual(curric.name, "Underwater Basket Weaving")
        self.assertEqual(curric.institution, "ACME State University")
        self.assertEqual(curric.degree_type, "AA")
        self.assertEqual(curric.system_type, semester)
        self.assertEqual(curric.cip, "445786")
        self.assertEqual(len(curric.courses), 12)
        self.assertEqual(curric.num_courses, 12)
        self.assertEqual(curric.credit_hours, 35)
        # test courses
        for course in curric.courses:
            if course.id == 1:
                self.assertEqual(course.name, "Introduction to Baskets")
                self.assertEqual(course.credit_hours, 3)
                self.assertIsInstance(course, Course)
                assert isinstance(course, Course)
                self.assertEqual(course.prefix, "BW")
                self.assertEqual(course.num, "110")
                self.assertEqual(course.institution, "ACME State University")
                self.assertEqual(course.canonical_name, "Baskets I")
                self.assertEqual(len(course.requisites), 0)
            elif course.id == 2:
                self.assertEqual(course.name, "Swimming")
                self.assertEqual(course.credit_hours, 3)
                self.assertIsInstance(course, Course)
                assert isinstance(course, Course)
                self.assertEqual(course.prefix, "PE")
                self.assertEqual(course.num, "115")
                self.assertEqual(course.institution, "ACME State University")
                self.assertEqual(course.canonical_name, "Physical Education")
                self.assertEqual(len(course.requisites), 0)
            elif course.id == 3:
                self.assertEqual(
                    course.name, "Introductory Calculus w/ Basketry Applications"
                )
                self.assertEqual(course.credit_hours, 4)
                self.assertIsInstance(course, Course)
                assert isinstance(course, Course)
                self.assertEqual(course.prefix, "MA")
                self.assertEqual(course.num, "116")
                self.assertEqual(course.institution, "ACME State University")
                self.assertEqual(course.canonical_name, "Calculus I")
                self.assertEqual(len(course.requisites), 0)
            elif course.id == 4:
                self.assertEqual(course.name, "Basic Basket Forms")
                self.assertEqual(course.credit_hours, 3)
                self.assertIsInstance(course, Course)
                assert isinstance(course, Course)
                self.assertEqual(course.prefix, "BW")
                self.assertEqual(course.num, "111")
                self.assertEqual(course.institution, "ACME State University")
                self.assertEqual(course.canonical_name, "Baskets II")
                self.assertEqual(course.requisites[1], pre)
                self.assertEqual(course.requisites[5], strict_co)
            elif course.id == 5:
                self.assertEqual(course.name, "Basic Basket Forms Lab")
                self.assertEqual(course.credit_hours, 1)
                self.assertIsInstance(course, Course)
                assert isinstance(course, Course)
                self.assertEqual(course.prefix, "BW")
                self.assertEqual(course.num, "111L")
                self.assertEqual(course.institution, "ACME State University")
                self.assertEqual(course.canonical_name, "Baskets II Laboratory")
                self.assertEqual(len(course.requisites), 0)
            elif course.id == 6:
                self.assertEqual(course.name, "Advanced Basketry")
                self.assertEqual(course.credit_hours, 3)
                self.assertIsInstance(course, Course)
                assert isinstance(course, Course)
                self.assertEqual(course.prefix, "BW")
                self.assertEqual(course.num, "201")
                self.assertEqual(course.institution, "ACME State University")
                self.assertEqual(course.canonical_name, "Baskets III")
                self.assertEqual(course.requisites[4], pre)
                self.assertEqual(course.requisites[5], pre)
                self.assertEqual(course.requisites[3], co)
            elif course.id == 7:
                self.assertEqual(course.name, "Basket Materials & Decoration")
                self.assertEqual(course.credit_hours, 3)
                self.assertIsInstance(course, Course)
                assert isinstance(course, Course)
                self.assertEqual(course.prefix, "BW")
                self.assertEqual(course.num, "214")
                self.assertEqual(course.institution, "ACME State University")
                self.assertEqual(course.canonical_name, "Basket Materials")
                self.assertEqual(course.requisites[1], pre)
            elif course.id == 8:
                self.assertEqual(course.name, "Underwater Weaving")
                self.assertEqual(course.credit_hours, 3)
                self.assertIsInstance(course, Course)
                assert isinstance(course, Course)
                self.assertEqual(course.prefix, "BW")
                self.assertEqual(course.num, "301")
                self.assertEqual(course.institution, "ACME State University")
                self.assertEqual(course.canonical_name, "Baskets IV")
                self.assertEqual(course.requisites[2], pre)
                self.assertEqual(course.requisites[7], co)
            elif course.id == 9:
                self.assertEqual(course.name, "Humanitites Elective")
                self.assertEqual(course.credit_hours, 3)
                self.assertEqual(course.institution, "ACME State University")
                self.assertEqual(len(course.requisites), 0)
            elif course.id == 10:
                self.assertEqual(course.name, "Social Sciences Elective")
                self.assertEqual(course.credit_hours, 3)
                self.assertEqual(course.institution, "ACME State University")
                self.assertEqual(len(course.requisites), 0)
            elif course.id == 11:
                self.assertEqual(course.name, "Technical Elective")
                self.assertEqual(course.credit_hours, 3)
                self.assertEqual(course.institution, "ACME State University")
                self.assertEqual(len(course.requisites), 0)
            elif course.id == 12:
                self.assertEqual(course.name, "General Elective")
                self.assertEqual(course.credit_hours, 3)
                self.assertEqual(course.institution, "ACME State University")
                self.assertEqual(len(course.requisites), 0)
        # TODO: add learning outcomes

    def test_degree_plan_data_format(self) -> None:
        "test the data file format used for degree plans"
        dp = read_csv("./tests/degree_plan.csv")
        self.assertIsInstance(dp, DegreePlan)
        assert isinstance(dp, DegreePlan)

        self.assertEqual(dp.name, "4-Term Plan")
        self.assertEqual(dp.curriculum.name, "Underwater Basket Weaving")
        self.assertEqual(dp.curriculum.institution, "ACME State University")
        self.assertEqual(dp.curriculum.degree_type, "AA")
        self.assertEqual(dp.curriculum.system_type, semester)
        self.assertEqual(dp.curriculum.cip, "445786")
        self.assertEqual(len(dp.curriculum.courses) - len(dp.additional_courses), 12)
        self.assertEqual(dp.num_terms, 4)
        self.assertEqual(dp.credit_hours, 45)
        self.assertEqual(len(dp.additional_courses), 4)
        # test courses -- same tests as in the above curriculum, but a few additional courses
        # have been added, as well as a new requisite to an existing courses.
        # test courses
        curric = dp.curriculum
        for course in curric.courses:
            if course.id == 1:
                self.assertEqual(course.name, "Introduction to Baskets")
                self.assertEqual(course.credit_hours, 3)
                self.assertIsInstance(course, Course)
                assert isinstance(course, Course)
                self.assertEqual(course.prefix, "BW")
                self.assertEqual(course.num, "110")
                self.assertEqual(course.institution, "ACME State University")
                self.assertEqual(course.canonical_name, "Baskets I")
                self.assertEqual(len(course.requisites), 0)
            elif course.id == 2:
                self.assertEqual(course.name, "Swimming")
                self.assertEqual(course.credit_hours, 3)
                self.assertIsInstance(course, Course)
                assert isinstance(course, Course)
                self.assertEqual(course.prefix, "PE")
                self.assertEqual(course.num, "115")
                self.assertEqual(course.institution, "ACME State University")
                self.assertEqual(course.canonical_name, "Physical Education")
                self.assertEqual(len(course.requisites), 0)
            elif course.id == 3:
                self.assertEqual(
                    course.name, "Introductory Calculus w/ Basketry Applications"
                )
                self.assertEqual(course.credit_hours, 4)
                self.assertIsInstance(course, Course)
                assert isinstance(course, Course)
                self.assertEqual(course.prefix, "MA")
                self.assertEqual(course.num, "116")
                self.assertEqual(course.institution, "ACME State University")
                self.assertEqual(course.canonical_name, "Calculus I")
                # this is the only difference from above tests
                self.assertEqual(course.requisites[13], pre)
            elif course.id == 4:
                self.assertEqual(course.name, "Basic Basket Forms")
                self.assertEqual(course.credit_hours, 3)
                self.assertIsInstance(course, Course)
                assert isinstance(course, Course)
                self.assertEqual(course.prefix, "BW")
                self.assertEqual(course.num, "111")
                self.assertEqual(course.institution, "ACME State University")
                self.assertEqual(course.canonical_name, "Baskets II")
                self.assertEqual(course.requisites[1], pre)
                self.assertEqual(course.requisites[5], strict_co)
            elif course.id == 5:
                self.assertEqual(course.name, "Basic Basket Forms Lab")
                self.assertEqual(course.credit_hours, 1)
                self.assertIsInstance(course, Course)
                assert isinstance(course, Course)
                self.assertEqual(course.prefix, "BW")
                self.assertEqual(course.num, "111L")
                self.assertEqual(course.institution, "ACME State University")
                self.assertEqual(course.canonical_name, "Baskets II Laboratory")
                self.assertEqual(len(course.requisites), 0)
            elif course.id == 6:
                self.assertEqual(course.name, "Advanced Basketry")
                self.assertEqual(course.credit_hours, 3)
                self.assertIsInstance(course, Course)
                assert isinstance(course, Course)
                self.assertEqual(course.prefix, "BW")
                self.assertEqual(course.num, "201")
                self.assertEqual(course.institution, "ACME State University")
                self.assertEqual(course.canonical_name, "Baskets III")
                self.assertEqual(course.requisites[4], pre)
                self.assertEqual(course.requisites[5], pre)
                self.assertEqual(course.requisites[3], co)
            elif course.id == 7:
                self.assertEqual(course.name, "Basket Materials & Decoration")
                self.assertEqual(course.credit_hours, 3)
                self.assertIsInstance(course, Course)
                assert isinstance(course, Course)
                self.assertEqual(course.prefix, "BW")
                self.assertEqual(course.num, "214")
                self.assertEqual(course.institution, "ACME State University")
                self.assertEqual(course.canonical_name, "Basket Materials")
                self.assertEqual(course.requisites[1], pre)
            elif course.id == 8:
                self.assertEqual(course.name, "Underwater Weaving")
                self.assertEqual(course.credit_hours, 3)
                self.assertIsInstance(course, Course)
                assert isinstance(course, Course)
                self.assertEqual(course.prefix, "BW")
                self.assertEqual(course.num, "301")
                self.assertEqual(course.institution, "ACME State University")
                self.assertEqual(course.canonical_name, "Baskets IV")
                self.assertEqual(course.requisites[2], pre)
                self.assertEqual(course.requisites[7], co)
            elif course.id == 9:
                self.assertEqual(course.name, "Humanitites Elective")
                self.assertEqual(course.credit_hours, 3)
                self.assertEqual(course.institution, "ACME State University")
                self.assertEqual(len(course.requisites), 0)
            elif course.id == 10:
                self.assertEqual(course.name, "Social Sciences Elective")
                self.assertEqual(course.credit_hours, 3)
                self.assertEqual(course.institution, "ACME State University")
                self.assertEqual(len(course.requisites), 0)
            elif course.id == 11:
                self.assertEqual(course.name, "Technical Elective")
                self.assertEqual(course.credit_hours, 3)
                self.assertEqual(course.institution, "ACME State University")
                self.assertEqual(len(course.requisites), 0)
            elif course.id == 12:
                self.assertEqual(course.name, "General Elective")
                self.assertEqual(course.credit_hours, 3)
                self.assertEqual(course.institution, "ACME State University")
                self.assertEqual(len(course.requisites), 0)
        # test additional courses
        for course in dp.additional_courses:
            if course.id == 13:
                self.assertEqual(
                    course.name,
                    "Precalculus w/ Basketry Applications",
                )
                self.assertEqual(course.credit_hours, 3)
                self.assertIsInstance(course, Course)
                assert isinstance(course, Course)
                self.assertEqual(course.prefix, "MA")
                self.assertEqual(course.num, "110")
                self.assertEqual(course.institution, "ACME State University")
                self.assertEqual(course.canonical_name, "Precalculus")
                self.assertEqual(course.requisites[14], pre)
            elif course.id == 14:
                self.assertEqual(course.name, "College Algebra")
                self.assertEqual(course.credit_hours, 3)
                self.assertIsInstance(course, Course)
                assert isinstance(course, Course)
                self.assertEqual(course.prefix, "MA")
                self.assertEqual(course.num, "102")
                self.assertEqual(course.institution, "ACME State University")
                self.assertEqual(course.canonical_name, "College Algebra")
                self.assertEqual(course.requisites[15], strict_co)
            elif course.id == 15:
                self.assertEqual(course.name, "College Algebra Studio")
                self.assertEqual(course.credit_hours, 1)
                self.assertIsInstance(course, Course)
                assert isinstance(course, Course)
                self.assertEqual(course.prefix, "MA")
                self.assertEqual(course.num, "102S")
                self.assertEqual(course.institution, "ACME State University")
                self.assertEqual(
                    course.canonical_name,
                    "College Algebra Recitation",
                )
                self.assertEqual(len(course.requisites), 0)
            elif course.id == 16:
                self.assertEqual(course.name, "Hemp Baskets")
                self.assertEqual(course.credit_hours, 3)
                self.assertIsInstance(course, Course)
                assert isinstance(course, Course)
                self.assertEqual(course.prefix, "BW")
                self.assertEqual(course.num, "420")
                self.assertEqual(course.institution, "ACME State University")
                self.assertEqual(
                    course.canonical_name,
                    "College Algebra Recitation",
                )
                self.assertEqual(course.requisites[6], co)
        # TODO: add learning outcomes

    def test_read_write_invariance(self) -> None:
        """
        Create a curriculum and degree plan, and test read/write invariance for both
        8-vertex test curriculum - valid

           A --------* C --------* E
                    */ |*
                    /  |
           B-------/   D --------* F

           (A,C) - pre;  (C,E) -  pre; (B,C) - pre; (D,C) - co; (C,E) - pre; (D,F) - pre
        """

        try:
            A = Course(
                "Introduction to Baskets",
                3.0,
                institution="ACME State University",
                prefix="BW",
                num="101",
                canonical_name="Baskets I",
            )
            B = Course(
                "Swimming",
                3.0,
                institution="ACME State University",
                prefix="PE",
                num="115",
                canonical_name="Physical Education",
            )
            C = Course(
                "Basic Basket Forms",
                3.0,
                institution="ACME State University",
                prefix="BW",
                num="111",
                canonical_name="Baskets I",
            )
            D = Course(
                "Basic Basket Forms Lab",
                1.0,
                institution="ACME State University",
                prefix="BW",
                num="111L",
                canonical_name="Baskets I Laboratory",
            )
            E = Course(
                "Advanced Basketry",
                3.0,
                institution="ACME State University",
                prefix="CS",
                num="300",
                canonical_name="Baskets II",
            )
            F = Course(
                "Basket Materials & Decoration",
                3.0,
                institution="ACME State University",
                prefix="BW",
                num="214",
                canonical_name="Basket Materials",
            )

            C.add_requisite(A, pre)
            C.add_requisite(B, pre)
            C.add_requisite(D, co)
            E.add_requisite(C, pre)
            F.add_requisite(D, pre)

            curric1 = Curriculum(
                "Underwater Basket Weaving",
                [A, B, C, D, E, F],
                institution="ACME State University",
                cip="445786",
            )
            # write curriculum to secondary storage
            self.assertIsNone(write_csv(curric1, "./tests/UBW-curric.csv"))
            # read from same location
            curric2 = read_csv("./tests/UBW-curric.csv")
            self.assertEqual(str(curric1), str(curric2))  # read/write invariance test

            terms = [
                Term([A, B]),
                Term([C, D]),
                Term([E, F]),
            ]

            dp1 = DegreePlan("3-term UBW plan", curric1, terms)
            # write degree plan to secondary storage
            self.assertIsNone(write_csv(dp1, "./tests/UBW-degree-plan.csv"))
            # read from same location
            dp2 = read_csv("./tests/UBW-degree-plan.csv")

            self.assertEqual(str(dp1), str(dp2))  # read/write invariance test
        finally:
            try:
                os.remove("./tests/UBW-curric.csv")
                os.remove("./tests/UBW-degree-plan.csv")
            except FileNotFoundError:
                pass
