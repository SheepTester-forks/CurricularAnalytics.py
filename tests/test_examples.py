from io import StringIO
import unittest
from typing import List

from curricularanalytics import (
    AbstractCourse,
    Course,
    Curriculum,
    DegreePlan,
    Term,
    pre,
)
from curricularanalytics.data_handler import read_csv
from curricularanalytics.types.data_types import co, strict_co


class ExampleTests(unittest.TestCase):
    maxDiff = None

    def test_example_1(self):
        """
        Curriculum assoicated with curricula c1, page 9, Heileman, G. L., Slim, A., Hickman, M.,  and Abdallah, C. T. (2018).
        Curricular Analytics: A Framework for Quantifying the Impact of Curricular Reforms and Pedagogical Innovations
        https://arxiv.org/pdf/1811.09676.pdf
        """
        # create the courses
        c: List[AbstractCourse] = [
            Course("Index 0 course (ignored)", 0),
            # term 1
            Course("Calculus 1", 3, prefix="MATH ", num="1011"),
            # term 2
            Course("Physics I: Mechanics & Heat", 3, prefix="PHYS", num="1112"),
            Course("Calculus 2", 3, prefix="MATH", num="1920"),
            # term 3
            Course("Circuits 1", 3, prefix="EE", num="2200"),
        ]

        # term 1
        c[2].add_requisite(c[1], pre)
        c[3].add_requisite(c[1], pre)

        # term 2
        c[4].add_requisite(c[2], pre)

        curric = Curriculum("Example Curricula c1", c[1:], sort_by_id=False)

        self.assertTrue(curric.is_valid())
        self.assertEqual(curric.total_delay_factor, 11.0)
        self.assertEqual(
            list(map(curric.delay_factor, curric.courses)), [3.0, 3.0, 2.0, 3.0]
        )
        self.assertEqual(curric.total_blocking_factor, 4)
        self.assertEqual(
            list(map(curric.blocking_factor, curric.courses)), [3, 1, 0, 0]
        )
        self.assertEqual(curric.total_centrality, 3)
        self.assertEqual(list(map(curric.centrality, curric.courses)), [0, 3, 0, 0])
        self.assertEqual(curric.total_complexity, 15.0)
        self.assertEqual(
            list(map(curric.complexity, curric.courses)), [6.0, 4.0, 2.0, 3.0]
        )

        terms = [
            Term([c[1]]),
            Term([c[2], c[3]]),
            Term([c[4]]),
        ]

        dp = DegreePlan("Example Curricula c1", curric, terms)

        self.assertTrue(dp.is_valid())
        self.assertEqual(dp.credit_hours, 12)
        self.assertEqual(dp.basic_metrics.average, 4.0)
        self.assertEqual(dp.basic_metrics.min, 3)
        self.assertAlmostEqual(dp.basic_metrics.stddev, 1.4142135623730951, places=5)
        self.assertEqual(dp.num_terms, 3)
        self.assertEqual(dp.basic_metrics.max, 6)
        self.assertEqual(dp.basic_metrics.min_term + 1, 1)
        self.assertEqual(dp.basic_metrics.max_term + 1, 2)

    def test_example_2(self):
        """
        Curriculum assoicated with curricula c2, page 9, Heileman, G. L., Slim, A., Hickman, M.,  and Abdallah, C. T. (2018).
        Curricular Analytics: A Framework for Quantifying the Impact of Curricular Reforms and Pedagogical Innovations
        https://arxiv.org/pdf/1811.09676.pdf
        """
        # create the courses
        c: List[AbstractCourse] = [
            Course("Index 0 course (ignored)", 0),
            Course("Calculus 1", 3, prefix="MATH ", num="1011"),
            Course("Physics I: Mechanics & Heat", 3, prefix="PHYS", num="1112"),
            # term 2
            Course("Calculus 2", 3, prefix="MATH", num="1920"),
            # term 3
            Course("Circuits 1", 3, prefix="EE", num="2200"),
        ]
        # test
        # term 2
        c[3].add_requisite(c[1], pre)
        c[3].add_requisite(c[2], pre)

        # term 3
        c[4].add_requisite(c[3], pre)

        curric = Curriculum("Example Curricula C2", c[1:], sort_by_id=False)

        self.assertTrue(curric.is_valid())
        self.assertEqual(curric.total_delay_factor, 12.0)
        self.assertEqual(
            list(map(curric.delay_factor, curric.courses)), [3.0, 3.0, 3.0, 3.0]
        )
        self.assertEqual(curric.total_blocking_factor, 5)
        self.assertEqual(
            list(map(curric.blocking_factor, curric.courses)), [2, 2, 1, 0]
        )
        self.assertEqual(curric.total_centrality, 6)
        self.assertEqual(list(map(curric.centrality, curric.courses)), [0, 0, 6, 0])
        self.assertEqual(curric.total_complexity, 17.0)
        self.assertEqual(
            list(map(curric.complexity, curric.courses)), [5.0, 5.0, 4.0, 3.0]
        )

        terms = [
            Term([c[1], c[2]]),
            Term([c[3]]),
            Term([c[4]]),
        ]

        dp = DegreePlan("Example Curricula c2", curric, terms)

        self.assertTrue(dp.is_valid())
        self.assertEqual(dp.credit_hours, 12)
        self.assertEqual(dp.basic_metrics.average, 4.0)
        self.assertEqual(dp.basic_metrics.min, 3)
        self.assertAlmostEqual(dp.basic_metrics.stddev, 1.4142135623730951, places=5)
        self.assertEqual(dp.num_terms, 3)
        self.assertEqual(dp.basic_metrics.max, 6)
        self.assertEqual(dp.basic_metrics.min_term + 1, 2)
        self.assertEqual(dp.basic_metrics.max_term + 1, 1)

    def test_example_ece_ua(self):
        """
        This is an example curriculum in ECE Department at UA.
        """
        # create the courses
        c: List[AbstractCourse] = [
            Course("Index 0 course (ignored)", 0),
            Course(
                "Computer Programming for Engineering Applications",
                3,
                prefix="ECE ",
                num="175",
            ),
            Course("Elements of Electrical Engineering", 3, prefix="ECE", num="207"),
            Course("Basic Circuits", 3, prefix="ECE", num="220"),
            Course("Digital Logic", 3, prefix="ECE", num="274A"),
            Course(
                "Computer Programming for Engineering Applications II",
                3,
                prefix="ECE",
                num="275",
            ),
            Course("Design of Electronic Circuits", 3, prefix="ECE", num="304A"),
            Course(
                "Applications of Engineering Mathematics", 3, prefix="ECE", num="310"
            ),
            Course("Circuit Theory", 3, prefix="ECE", num="320A"),
            Course("Computational Techniques", 3, prefix="ECE", num="330B"),
            Course("Introduction to Communications", 3, prefix="ECE", num="340A"),
            Course("Electronic Circuits", 3, prefix="ECE", num="351C"),
            Course("Device Electronics", 3, prefix="ECE", num="352"),
            Course(
                "Fundamentals of Computer Organization", 3, prefix="ECE", num="369A"
            ),
            Course("Microprocessor Organization", 3, prefix="ECE", num="372A"),
            Course("Object-Oriented Software Design", 3, prefix="ECE", num="373"),
            Course("Introductory Electromagnetics", 3, prefix="ECE", num="381A"),
            Course("Digital VLSI Systems Design", 3, prefix="ECE", num="407"),
            Course(
                "Numeric Modeling of Physics & Biological Systems",
                3,
                prefix="ECE",
                num="411",
            ),
            # Course("Web Development and the Internet of Things", 3, prefix = "ECE", num = "413"),
            Course("Photovoltaic Solar Energy Systems", 3, prefix="ECE", num="414A"),
            Course("Digital Signal Processing", 3, prefix="ECE", num="429"),
            Course(
                "Electrical and Optical Properties of Materials",
                3,
                prefix="ECE",
                num="434",
            ),
            Course("Digital Communications Systems", 3, prefix="ECE", num="435A"),
            Course("Automatic Control", 3, prefix="ECE", num="441A"),
            Course("Digital Control Systems", 3, prefix="ECE", num="442"),
            Course("Optoelectronics", 3, prefix="ECE", num="456"),
            Course(
                "Fundamentals of Optics for Electrical Engineers",
                3,
                prefix="ECE",
                num="459",
            ),
            Course("Computer Architecture and Design", 3, prefix="ECE", num="462"),
            Course("Knowledge-System Engineering", 3, prefix="ECE", num="466"),
            # Course("Fundamentals of Information and Network Security", 3, prefix = "ECE", num = "471"),
            # Course("Design, Modeling, and Simulation for High Technology Systems in Medicine", 3, prefix = "ECE", num = "472"),
            Course("Computer-Aided Logic Design", 3, prefix="ECE", num="474A"),
            Course("Fundamentals of Computer Networks", 3, prefix="ECE", num="478"),
            Course("Principles of Artificial Intelligence", 3, prefix="ECE", num="479"),
            Course("Antenna Theory and Design", 3, prefix="ECE", num="484"),
            Course(
                "Microwave Engineering I: Passive Circuit Design",
                3,
                prefix="ECE",
                num="486",
            ),
            Course(
                "Microwave Engineering II: Active Circuit Design",
                3,
                prefix="ECE",
                num="488",
            ),
        ]

        # Add requisites for each course if specified
        c[5].add_requisite(c[1], pre)
        c[6].add_requisite(c[11], pre)
        c[7].add_requisite(c[5], pre)
        c[7].add_requisite(c[3], pre)  # or c[7].add_requisite(c[2],pre)
        c[8].add_requisite(c[3], pre)
        c[9].add_requisite(c[1], pre)
        c[10].add_requisite(c[8], pre)
        c[11].add_requisite(c[8], pre)
        c[12].add_requisite(c[11], pre)
        c[13].add_requisite(c[1], pre)
        c[13].add_requisite(c[4], pre)
        c[14].add_requisite(c[2], pre)  # or c[14].add_requisite(c[3],pre)
        c[14].add_requisite(c[4], pre)
        c[14].add_requisite(c[5], pre)
        c[15].add_requisite(c[5], pre)
        c[16].add_requisite(c[3], pre)
        c[17].add_requisite(c[4], pre)
        c[17].add_requisite(c[11], pre)
        c[20].add_requisite(c[10], pre)
        c[22].add_requisite(c[10], pre)
        c[22].add_requisite(c[7], pre)
        c[23].add_requisite(c[10], pre)
        c[24].add_requisite(c[8], pre)
        c[25].add_requisite(c[12], pre)
        c[25].add_requisite(c[16], pre)
        c[26].add_requisite(c[16], pre)
        c[27].add_requisite(c[13], pre)
        c[29].add_requisite(c[4], pre)
        c[29].add_requisite(c[5], pre)
        c[30].add_requisite(c[5], pre)
        c[30].add_requisite(c[7], pre)
        c[31].add_requisite(c[15], pre)
        c[32].add_requisite(c[16], pre)
        c[33].add_requisite(c[16], pre)
        c[34].add_requisite(c[33], pre)

        # Create curriculum based on previous courses and learning_outcomes
        curric = Curriculum(
            "Example ECE Department at UA ",
            c[1:],
            sort_by_id=False,
        )

        self.assertTrue(curric.is_valid())
        self.assertEqual(curric.total_delay_factor, 117.0)
        self.assertEqual(
            list(map(curric.delay_factor, curric.courses)),
            [
                4.0,
                2.0,
                5.0,
                3.0,
                4.0,
                4.0,
                4.0,
                5.0,
                2.0,
                4.0,
                5.0,
                5.0,
                3.0,
                3.0,
                4.0,
                4.0,
                4.0,
                1.0,
                1.0,
                4.0,
                1.0,
                4.0,
                4.0,
                3.0,
                5.0,
                3.0,
                3.0,
                1.0,
                3.0,
                4.0,
                4.0,
                3.0,
                4.0,
                4.0,
            ],
        )
        self.assertEqual(curric.total_blocking_factor, 70)
        self.assertEqual(
            list(map(curric.blocking_factor, curric.courses)),
            [
                11,
                1,
                18,
                5,
                7,
                0,
                2,
                10,
                0,
                3,
                4,
                1,
                1,
                0,
                1,
                5,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                1,
                0,
            ],
        )
        self.assertEqual(curric.total_centrality, 120)
        self.assertEqual(
            list(map(curric.centrality, curric.courses)),
            [
                0,
                0,
                0,
                0,
                21,
                0,
                14,
                28,
                0,
                12,
                13,
                5,
                6,
                0,
                4,
                13,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                4,
                0,
            ],
        )
        self.assertEqual(curric.total_complexity, 187.0)
        self.assertEqual(
            list(map(curric.complexity, curric.courses)),
            [
                15.0,
                3.0,
                23.0,
                8.0,
                11.0,
                4.0,
                6.0,
                15.0,
                2.0,
                7.0,
                9.0,
                6.0,
                4.0,
                3.0,
                5.0,
                9.0,
                4.0,
                1.0,
                1.0,
                4.0,
                1.0,
                4.0,
                4.0,
                3.0,
                5.0,
                3.0,
                3.0,
                1.0,
                3.0,
                4.0,
                4.0,
                3.0,
                5.0,
                4.0,
            ],
        )

        terms = [
            Term([c[1]]),
            Term([c[2], c[3]]),
            Term([c[4]]),
        ]
        dp = DegreePlan("Example ECE Department at UA", curric, terms)

        self.assertEqual(dp.credit_hours, 12)
        self.assertEqual(dp.basic_metrics.average, 4.0)
        self.assertEqual(dp.basic_metrics.min, 3)
        self.assertAlmostEqual(dp.basic_metrics.stddev, 1.4142135623730951, places=5)
        self.assertEqual(dp.num_terms, 3)
        self.assertEqual(dp.basic_metrics.max, 6)
        self.assertEqual(dp.basic_metrics.min_term + 1, 1)
        self.assertEqual(dp.basic_metrics.max_term + 1, 2)

    def test_cornell_ee(self):
        """
        Curriculum assoicated with the Cornell University EE program in 2018
        """
        # create the courses
        c: List[AbstractCourse] = [
            Course("Index 0 course (ignored)", 0),
            # term 1
            Course("Engineering Gen. Chemistry", 3, prefix="CHEM ", num="2090"),
            Course("Calculus for Engineers", 3, prefix="MATH", num="1910"),
            Course("Engineering Distribution", 3, prefix="ENGRI", num="1xxx"),
            Course("1st Yr Writing Seminar", 3),
            Course("PE", 3),
            # term 2
            Course("Physics I: Mechanics & Heat", 3, prefix="PHYS", num="1112"),
            Course("Multivariable Calc. for Engineers", 3, prefix="MATH", num="1920"),
            Course("Intro. to Computing", 3, prefix="CS", num="111x"),
            Course("1st Yr Writing Seminar", 3),
            Course("PE", 3),
            # term 3
            Course("Physics II: Electromagnetism", 3, prefix="PHYS", num="2213"),
            Course("Diff. Eqs. for Engineers", 3, prefix="MATH", num="2930"),
            Course("Intro. to Circuits", 3, prefix="ECE/ENGRD", num="2100"),
            Course("Digital Logic & Computer Org.", 3, prefix="ECE/ENGRD", num="2300"),
            Course("Liberal Studies", 3),
            # term 4
            Course(
                "Physics III: Oscillations, Waves, and Quantum Physics",
                3,
                prefix="PHYS",
                num="2214",
            ),
            Course("Linear Algebra for Engineers", 3, prefix="MATH", num="2940"),
            Course("Engineering Distribution", 3, prefix="ENGRD", num="2xxx"),
            Course("Signals and Information", 3, prefix="ECE/ENGRD", num="2200/2220"),
            Course("Liberal Studies", 3),
            # term 5
            Course("ECE Foundations", 3),
            Course("Elective", 3),
            Course("Outside Tech. Elective", 3),
            Course("Intelligent Physical Systems", 3, prefix="ECE", num="3400"),
            Course("Liberal Studies", 3),
            # term 6
            Course("ECE Foundations", 3),
            Course("ECE Foundations", 3),
            Course("Outside Tech. Elective", 3),
            Course("Elective", 3),
            Course("Liberal Studies", 3),
            # term 7
            Course("ECE Elective (CDE)", 3),
            Course("ECE Elective", 3),
            Course("Outside Tech. Elective", 3),
            Course("Liberal Studies", 3),
            # term 8
            Course("ECE Elective", 3),
            Course("ECE Elective", 3),
            Course("ECE Elective", 3),
            Course("Liberal Studies", 3),
        ]

        # term 1
        c[6].add_requisite(c[2], pre)
        c[7].add_requisite(c[2], pre)
        # term 2
        c[11].add_requisite(c[6], pre)
        c[11].add_requisite(c[7], pre)
        c[12].add_requisite(c[7], pre)
        c[17].add_requisite(c[7], pre)
        c[14].add_requisite(c[8], pre)
        c[23].add_requisite(c[8], pre)
        # term 3
        c[18].add_requisite(c[11], pre)
        c[13].add_requisite(c[11], co)
        c[16].add_requisite(c[12], co)
        c[13].add_requisite(c[12], co)
        c[19].add_requisite(c[12], pre)
        c[24].add_requisite(c[13], pre)
        c[24].add_requisite(c[14], pre)
        # term 4
        c[19].add_requisite(c[17], co)
        c[24].add_requisite(c[19], pre)

        curric = Curriculum("Cornell University EE Program", c[1:], sort_by_id=False)

        self.assertTrue(curric.is_valid())
        self.assertEqual(curric.total_delay_factor, 85.0)
        self.assertEqual(
            list(map(curric.delay_factor, curric.courses)),
            [
                1.0,
                5.0,
                1.0,
                1.0,
                1.0,
                5.0,
                5.0,
                3.0,
                1.0,
                1.0,
                5.0,
                5.0,
                5.0,
                3.0,
                1.0,
                4.0,
                5.0,
                4.0,
                5.0,
                1.0,
                1.0,
                1.0,
                2.0,
                5.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
            ],
        )
        self.assertEqual(curric.total_blocking_factor, 37)
        self.assertEqual(
            list(map(curric.blocking_factor, curric.courses)),
            [
                0,
                10,
                0,
                0,
                0,
                4,
                8,
                3,
                0,
                0,
                3,
                4,
                1,
                1,
                0,
                0,
                2,
                0,
                1,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
            ],
        )
        self.assertEqual(curric.total_centrality, 102)
        self.assertEqual(
            list(map(curric.centrality, curric.courses)),
            [
                0,
                0,
                0,
                0,
                0,
                9,
                28,
                0,
                0,
                0,
                18,
                14,
                15,
                3,
                0,
                0,
                5,
                0,
                10,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
            ],
        )
        self.assertEqual(curric.total_complexity, 122.0)
        self.assertEqual(
            list(map(curric.complexity, curric.courses)),
            [
                1.0,
                15.0,
                1.0,
                1.0,
                1.0,
                9.0,
                13.0,
                6.0,
                1.0,
                1.0,
                8.0,
                9.0,
                6.0,
                4.0,
                1.0,
                4.0,
                7.0,
                4.0,
                6.0,
                1.0,
                1.0,
                1.0,
                2.0,
                5.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
            ],
        )

        terms = [
            Term([c[1], c[2], c[3], c[4], c[5]]),
            Term([c[6], c[7], c[8], c[9], c[10]]),
            Term([c[11], c[12], c[13], c[14], c[15]]),
            Term([c[16], c[17], c[18], c[19], c[20]]),
            Term([c[21], c[22], c[23], c[24], c[25]]),
            Term([c[26], c[27], c[28], c[29], c[30]]),
            Term([c[31], c[32], c[33], c[34]]),
            Term([c[35], c[36], c[37], c[38]]),
        ]

        dp = DegreePlan("Cornell University EE Program 4-year Plan", curric, terms)

        self.assertEqual(dp.credit_hours, 114)
        self.assertEqual(dp.basic_metrics.average, 14.25)
        self.assertEqual(dp.basic_metrics.min, 12)
        self.assertAlmostEqual(dp.basic_metrics.stddev, 1.299038105676658, places=5)
        self.assertEqual(dp.num_terms, 8)
        self.assertEqual(dp.basic_metrics.max, 15)
        self.assertEqual(dp.basic_metrics.min_term + 1, 7)
        self.assertEqual(dp.basic_metrics.max_term + 1, 1)

    def _assert_uh_ee_dp(self, dp: DegreePlan):
        self.assertEqual(dp.credit_hours, 129)
        self.assertEqual(dp.basic_metrics.average, 16.125)
        self.assertEqual(dp.basic_metrics.min, 15)
        self.assertAlmostEqual(dp.basic_metrics.stddev, 0.5994789404140899, places=5)
        self.assertEqual(dp.num_terms, 8)
        self.assertEqual(dp.basic_metrics.max, 17)
        self.assertEqual(dp.basic_metrics.min_term + 1, 1)
        self.assertEqual(dp.basic_metrics.max_term + 1, 2)

    def test_uh_ee(self):
        """
        Curriculum assoicated with the University of Houston EE program in 2018
        Note: curriculum was created in 2016-17 and was still used in 2018
        """
        # create the courses
        c: List[AbstractCourse] = [
            Course("Index 0 course (ignored)", 0),
            # term 1
            Course("The US to 1877", 3, prefix="HIST", num="1377"),
            Course("First Year Writing I", 3, prefix="ENGL", num="1303"),
            Course("Intro to Engr.", 1, prefix="ENGI", num="1100"),
            Course("Calculus I", 4, prefix="MATH", num="1431"),
            Course("Fund. of Chemistry", 3, prefix="CHEM", num="1331"),
            Course("Fund. of Chemistry Lab", 1, prefix="CHEM", num="1111"),
            # term 2
            Course("US Since 1877", 3, prefix="HIST", num="1378"),
            Course("First Year Writing II", 3, prefix="ENGL", num="1304"),
            Course("Computing & Prob. Solving", 3, prefix="ENGI", num="1331"),
            Course("Calculus II", 4, prefix="MATH", num="1432"),
            Course("University Physics I", 3, prefix="PHYS", num="1321"),
            Course("Physics Lab I", 1, prefix="PHYS", num="1121"),
            # term 3
            Course("US and TX Constitutions & Politics", 3, prefix="POLS", num="1336"),
            Course("Engineering Math", 3, prefix="MATH", num="3321"),
            Course("Circuit Analysis I", 3, prefix="ECE", num="2201"),
            Course("Calculus III", 3, prefix="MATH", num="2433"),
            Course("University Physics II", 3, prefix="PHYS", num="1322"),
            Course("Physics Lab II", 1, prefix="PHYS", num="1122"),
            # term 4
            Course("Technical Communication", 3, prefix="ENGI", num="2304"),
            Course("Programming Apps in ECE", 3, prefix="ECE", num="3331"),
            Course("Circuits Lab", 1, prefix="ECE", num="2100"),
            Course("Circuit Analysis II", 3, prefix="ECE", num="2202"),
            Course("Signals & Systems Analysis", 3, prefix="ECE", num="3337"),
            Course("Microprocessors", 3, prefix="ECE", num="3436"),
            # term 5
            Course("Creative Arts Core", 3),
            Course("Electronics Lab", 1, prefix="ECE", num="3155"),
            Course("Electronics", 3, prefix="ECE", num="3355"),
            Course("Concentration Elective", 3),
            Course("Applied EM Waves", 3, prefix="ECE", num="3317"),
            Course("ECE Elective", 3),
            # term 6
            Course(
                "US Gov: Congress, President and Courts", 3, prefix="POLS", num="1337"
            ),
            Course("Engineering Statistics", 3, prefix="INDE", num="2333"),
            Course("Elective Lab", 1),
            Course("Concentration Elective", 3),
            Course("Numerical Methods", 3, prefix="ECE", num="3340"),
            Course("ECE Elective", 3),
            # term 7
            Course("Microeconomic Principles", 3, prefix="ECON", num="2304"),
            Course("ECE Design I", 3, prefix="ECE", num="4335"),
            Course("Elective Lab", 1),
            Course("Concentration Elective", 3),
            Course("Concentration Elective", 3),
            Course("Tecnical Elective", 3),
            # term 8
            Course("Lang., Phil. & Culture Core", 3),
            Course("ECE Design II", 3, prefix="ECE", num="4336"),
            Course("Elective Lab", 1),
            Course("Concentration Elective", 3),
            Course("Concentration Elective", 3),
            Course("Concentration Elective", 3),
            Course("Elective Lab", 1),
        ]

        # term 1
        c[8].add_requisite(c[2], pre)
        c[9].add_requisite(c[3], pre)
        c[3].add_requisite(c[4], co)
        c[9].add_requisite(c[4], pre)
        c[10].add_requisite(c[4], pre)
        c[6].add_requisite(c[5], co)
        # term 2
        c[19].add_requisite(c[8], pre)
        c[32].add_requisite(c[9], pre)
        c[15].add_requisite(c[9], pre)
        c[14].add_requisite(c[10], pre)
        c[32].add_requisite(c[10], pre)
        c[16].add_requisite(c[10], pre)
        c[11].add_requisite(c[10], co)
        c[17].add_requisite(c[11], pre)
        c[12].add_requisite(c[11], co)
        # term 3
        c[20].add_requisite(c[14], pre)
        c[15].add_requisite(c[14], co)
        c[19].add_requisite(c[15], pre)
        c[20].add_requisite(c[15], pre)
        c[22].add_requisite(c[15], pre)
        c[15].add_requisite(c[16], co)
        c[17].add_requisite(c[16], co)
        c[15].add_requisite(c[17], co)
        c[18].add_requisite(c[17], co)
        c[15].add_requisite(c[18], co)
        c[21].add_requisite(c[18], pre)
        # term 4
        c[26].add_requisite(c[19], pre)
        c[35].add_requisite(c[20], pre)
        c[24].add_requisite(c[20], co)
        c[24].add_requisite(c[21], co)
        c[26].add_requisite(c[21], pre)
        c[21].add_requisite(c[22], co)
        c[23].add_requisite(c[22], co)
        c[27].add_requisite(c[23], pre)
        c[29].add_requisite(c[23], pre)
        c[38].add_requisite(c[24], pre)
        # term 5
        c[38].add_requisite(c[26], pre)
        c[27].add_requisite(c[26], strict_co)
        c[38].add_requisite(c[27], pre)
        c[38].add_requisite(c[29], pre)
        # term 6
        c[38].add_requisite(c[32], pre)
        c[38].add_requisite(c[35], pre)
        # term 7
        c[38].add_requisite(c[37], co)
        c[44].add_requisite(c[38], pre)

        curric = Curriculum("University of Houston EE Program", c[1:], sort_by_id=False)

        self.assertTrue(curric.is_valid())
        self.assertEqual(curric.total_delay_factor, 301.0)
        self.assertEqual(
            list(map(curric.delay_factor, curric.courses)),
            [
                1.0,
                7.0,
                10.0,
                12.0,
                2.0,
                2.0,
                1.0,
                7.0,
                10.0,
                12.0,
                12.0,
                4.0,
                1.0,
                10.0,
                12.0,
                12.0,
                12.0,
                12.0,
                11.0,
                10.0,
                12.0,
                12.0,
                11.0,
                11.0,
                1.0,
                12.0,
                12.0,
                1.0,
                11.0,
                1.0,
                1.0,
                6.0,
                1.0,
                1.0,
                10.0,
                1.0,
                3.0,
                12.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                12.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
            ],
        )
        self.assertEqual(curric.total_blocking_factor, 208)
        self.assertEqual(
            list(map(curric.blocking_factor, curric.courses)),
            [
                0,
                6,
                15,
                23,
                1,
                0,
                0,
                5,
                14,
                20,
                16,
                0,
                0,
                13,
                12,
                15,
                14,
                13,
                4,
                4,
                5,
                8,
                4,
                2,
                0,
                3,
                2,
                0,
                2,
                0,
                0,
                2,
                0,
                0,
                2,
                0,
                2,
                1,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
            ],
        )
        self.assertEqual(curric.total_centrality, 5717)
        self.assertEqual(
            list(map(curric.centrality, curric.courses)),
            [
                0,
                0,
                85,
                0,
                0,
                0,
                0,
                13,
                160,
                607,
                217,
                0,
                0,
                93,
                677,
                292,
                426,
                250,
                159,
                152,
                295,
                393,
                154,
                171,
                0,
                359,
                266,
                0,
                77,
                0,
                0,
                16,
                0,
                0,
                76,
                0,
                0,
                779,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
            ],
        )
        self.assertEqual(curric.total_complexity, 509.0)
        self.assertEqual(
            list(map(curric.complexity, curric.courses)),
            [
                1.0,
                13.0,
                25.0,
                35.0,
                3.0,
                2.0,
                1.0,
                12.0,
                24.0,
                32.0,
                28.0,
                4.0,
                1.0,
                23.0,
                24.0,
                27.0,
                26.0,
                25.0,
                15.0,
                14.0,
                17.0,
                20.0,
                15.0,
                13.0,
                1.0,
                15.0,
                14.0,
                1.0,
                13.0,
                1.0,
                1.0,
                8.0,
                1.0,
                1.0,
                12.0,
                1.0,
                5.0,
                13.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                12.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
            ],
        )

        terms = [
            Term([c[1], c[2], c[3], c[4], c[5], c[6]]),
            Term([c[7], c[8], c[9], c[10], c[11], c[12]]),
            Term([c[13], c[14], c[15], c[16], c[17], c[18]]),
            Term([c[19], c[20], c[21], c[22], c[23], c[24]]),
            Term([c[25], c[26], c[27], c[28], c[29], c[30]]),
            Term([c[31], c[32], c[33], c[34], c[35], c[36]]),
            Term([c[37], c[38], c[39], c[40], c[41], c[42]]),
            Term([c[43], c[44], c[45], c[46], c[47], c[48], c[49]]),
        ]

        dp = DegreePlan("University of Houston EE Program 4-year Plan", curric, terms)
        errors = StringIO()
        valid = dp.is_valid(errors)
        self.assertEqual(
            errors.getvalue(),
            "\n".join(
                [
                    "",
                    "-Course Concentration Elective is listed multiple times in degree plan",
                    "-Course ECE Elective is listed multiple times in degree plan",
                    "-Course Elective Lab is listed multiple times in degree plan",
                    "-Course Concentration Elective is listed multiple times in degree plan",
                    "-Course Concentration Elective is listed multiple times in degree plan",
                    "-Course Elective Lab is listed multiple times in degree plan",
                    "-Course Concentration Elective is listed multiple times in degree plan",
                    "-Course Concentration Elective is listed multiple times in degree plan",
                    "-Course Concentration Elective is listed multiple times in degree plan",
                    "-Course Elective Lab is listed multiple times in degree plan",
                ]
            ),
        )
        self.assertFalse(valid)
        self._assert_uh_ee_dp(dp)

    def test_uh_ee_csv(self):
        dp = read_csv("./examples/UH_EE_plan.csv")
        assert isinstance(dp, DegreePlan)
        errors = StringIO()
        valid = dp.is_valid(errors)
        self.assertEqual(errors.getvalue(), "")
        self.assertTrue(valid)
        self._assert_uh_ee_dp(dp)

    def _assert_uky_ee(self, curric: Curriculum, dp: DegreePlan):
        self.assertTrue(curric.is_valid())
        self.assertEqual(curric.total_delay_factor, 150.0)
        self.assertEqual(
            set(map(curric.delay_factor, curric.courses)),
            {
                1.0,
                3.0,
                7.0,
                3.0,
                2.0,
                8.0,
                3.0,
                2.0,
                8.0,
                2.0,
                1.0,
                8.0,
                8.0,
                8.0,
                8.0,
                3.0,
                6.0,
                8.0,
                3.0,
                2.0,
                1.0,
                8.0,
                8.0,
                1.0,
                8.0,
                4.0,
                1.0,
                8.0,
                1.0,
                1.0,
                1.0,
                1.0,
                2.0,
                1.0,
                1.0,
                1.0,
                1.0,
                2.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
            },
        )
        self.assertEqual(curric.total_blocking_factor, 81)
        self.assertEqual(
            set(map(curric.blocking_factor, curric.courses)),
            {
                0,
                3,
                10,
                0,
                1,
                15,
                0,
                0,
                11,
                1,
                0,
                10,
                7,
                6,
                5,
                1,
                5,
                4,
                0,
                1,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                1,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
            },
        )
        self.assertEqual(curric.total_centrality, 727)
        self.assertEqual(
            set(map(curric.centrality, curric.courses)),
            {
                0,
                0,
                62,
                0,
                0,
                0,
                0,
                0,
                102,
                0,
                0,
                102,
                121,
                60,
                112,
                3,
                29,
                136,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
            },
        )
        self.assertEqual(curric.total_complexity, 231.0)
        self.assertEqual(
            set(map(curric.complexity, curric.courses)),
            {
                1.0,
                6.0,
                17.0,
                3.0,
                3.0,
                23.0,
                3.0,
                2.0,
                19.0,
                3.0,
                1.0,
                18.0,
                15.0,
                14.0,
                13.0,
                4.0,
                11.0,
                12.0,
                3.0,
                3.0,
                1.0,
                8.0,
                8.0,
                1.0,
                8.0,
                4.0,
                1.0,
                8.0,
                1.0,
                1.0,
                1.0,
                1.0,
                3.0,
                1.0,
                1.0,
                1.0,
                1.0,
                2.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
            },
        )

        self.assertTrue(dp.is_valid())
        self.assertEqual(dp.credit_hours, 131)
        self.assertEqual(dp.basic_metrics.average, 16.375)
        self.assertEqual(dp.basic_metrics.min, 15)
        self.assertAlmostEqual(dp.basic_metrics.stddev, 1.2183492931011204, places=5)
        self.assertEqual(dp.num_terms, 8)
        self.assertEqual(dp.basic_metrics.max, 18)
        self.assertEqual(dp.basic_metrics.min_term + 1, 1)
        self.assertEqual(dp.basic_metrics.max_term + 1, 4)

    def test_uky_ee_curric(self):
        """
        Curriculum assoicated with the University of Univ. of Kentucky EE program in 2018
        Revised OCT272018
        course requisties can be found at: http://www.uky.edu/registrar/2018-2019-courses
        """
        # create the courses
        c: List[AbstractCourse] = [
            Course("Index 0 course (ignored)", 0),
            # term 1
            Course("Engineering Exploration I", 1, prefix="EGR", num="101"),
            Course("Fundamentals of Engineering Computing", 2, prefix="EGR", num="102"),
            Course("General University Physics", 4, prefix="PHY", num="231"),
            Course("General University Physics Lab", 1, prefix="PHY", num="241"),
            Course("Composition and Communication I", 3, prefix="CIS/WRD", num="110"),
            Course("Calculus I", 4, prefix="MA", num="113"),
            # term 2
            Course("Engineering Exploration II", 2, prefix="EGR", num="103"),
            Course("Composition and Communication II", 3, prefix="CIS/WRD", num="111"),
            Course("Calculus II", 4, prefix="MA", num="114"),
            Course("General College Chemistry I", 4, prefix="CHE", num="105"),
            Course("UK Core - Social Sciences", 3),
            # term 3
            Course("Calculus III", 4, prefix="MA", num="213"),
            Course("General University Physics", 4, prefix="PHY", num="232"),
            Course("General University Physics Lab", 1, prefix="PHY", num="242"),
            Course("Circuits I", 4, prefix="EE", num="211"),
            Course("Digital Logic Design", 4, prefix="EE", num="282"),
            # term 4
            Course("Calculus IV", 3, prefix="MA", num="214"),
            Course("AC Circuits", 4, prefix="EE", num="223"),
            Course("Intro. to Embedded Systems", 4, prefix="EE", num="287"),
            Course(
                "Intro. to Program Design Abstraction and Problem Solving",
                4,
                prefix="CS",
                num="215",
            ),
            Course("UK Core - Humanities", 3),
            # term 5
            Course("Electromechanics", 3, prefix="EE", num="415G"),
            Course("Signals & Systems", 3, prefix="EE", num="421G"),
            Course("Elective EE Laboratory 1", 2),
            Course("Intro. to Electronics", 3, prefix="EE", num="461G"),
            Course("Introductory Probability", 3, prefix="MA", num="320"),
            Course("Technical Elective 1", 3),
            # term 6
            Course(
                "Intro. to Engineering Electromagnetics", 4, prefix="EE", num="468G"
            ),
            Course("Elective EE Laboratory 2", 2),
            Course("Engineering/Science Elective 1", 3),
            Course("Technical Elective 2", 3),
            Course("UK Core - Citizenship - USA", 3),
            # term 7
            Course("EE Capstone Design", 3, prefix="EE", num="490"),
            Course("EE Technical Elective 1", 3),
            Course("EE Technical Elective 2", 3),
            Course("Math/Statistics Elective", 3),
            Course("UK Core - Global Dynamics", 3),
            # term 8
            Course("EE Capstone Design", 3, prefix="EE", num="491"),
            Course("EE Technical Elective 3", 3),
            Course("EE Technical Elective 4", 3),
            Course("Supportive Elective", 3),
            Course("Engineering/Science Elective 2", 3),
            Course("UK Core - Statistical Inferential Reasoning", 3),
        ]

        # term 1
        c[7].add_requisite(c[2], pre)
        c[16].add_requisite(c[2], pre)
        # c[6].add_requisite(c[2],co)  # not correct
        # c[20].add_requisite(c[2],pre)  # redundant
        # c[3].add_requisite(c[2],co)  # not correct
        c[7].add_requisite(c[3], co)  # added
        c[13].add_requisite(c[3], pre)
        c[4].add_requisite(c[3], co)  # was wrong direction, flipped
        c[8].add_requisite(c[5], pre)
        c[3].add_requisite(c[6], co)  # was wrong direction, flipped
        c[7].add_requisite(c[6], co)  # added, a required edge being removed by viz
        c[9].add_requisite(c[6], pre)

        # term 2
        c[12].add_requisite(c[9], pre)
        # c[15].add_requisite(c[9],pre)  # redundant
        c[7].add_requisite(c[10], co)  # added

        # term 3
        # c[13].add_requisite(c[3],pre)  # already specified above
        c[13].add_requisite(c[12], co)
        c[17].add_requisite(c[12], pre)
        c[26].add_requisite(c[12], pre)
        c[28].add_requisite(
            c[12], pre
        )  # required edge correctly removed by viz, but not caught by isvalid_curric()
        c[14].add_requisite(c[13], co)
        c[15].add_requisite(c[13], co)
        c[22].add_requisite(c[13], pre)  # required edge being removed by viz
        c[15].add_requisite(c[14], co)
        # c[18].add_requisite(c[14],pre)  # not correct
        c[18].add_requisite(c[15], pre)  # added
        c[19].add_requisite(c[16], pre)

        # term 4
        c[18].add_requisite(c[17], co)
        c[23].add_requisite(c[17], pre)  # required edge being removed by viz
        c[22].add_requisite(c[18], pre)
        c[23].add_requisite(c[18], pre)
        c[25].add_requisite(c[18], pre)
        c[28].add_requisite(c[18], pre)
        c[19].add_requisite(c[20], co)  # was wrong direction, flipped

        # term 5

        # term 6

        # term 7
        c[38].add_requisite(c[33], pre)

        curric = Curriculum(
            "University of Kentucky EE Program", c[1:], sort_by_id=False
        )

        terms = [
            Term([c[1], c[2], c[3], c[4], c[5], c[6]]),
            Term([c[7], c[8], c[9], c[10], c[11]]),
            Term([c[12], c[13], c[14], c[15], c[16]]),
            Term([c[17], c[18], c[19], c[20], c[21]]),
            Term([c[22], c[23], c[24], c[25], c[26], c[27]]),
            Term([c[28], c[29], c[30], c[31], c[32]]),
            Term([c[33], c[34], c[35], c[36], c[37]]),
            Term([c[38], c[39], c[40], c[41], c[42], c[43]]),
        ]

        dp = DegreePlan("University of Kentucky EE Program 4-year Plan", curric, terms)

        self._assert_uky_ee(curric, dp)

    def test_uky_ee_csv(self):
        curric = read_csv("./examples/UKY_EE_curric.csv")
        assert isinstance(curric, Curriculum)
        dp = read_csv("./examples/UKY_EE_plan.csv")
        assert isinstance(dp, DegreePlan)
        self._assert_uky_ee(curric, dp)
