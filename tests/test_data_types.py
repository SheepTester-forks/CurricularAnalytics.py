import unittest
from datetime import date, timedelta
from typing import List

from curricularanalytics import (
    AbstractRequirement,
    Course,
    CourseCatalog,
    CourseCollection,
    CourseRecord,
    CourseSet,
    Curriculum,
    LearningOutcome,
    RequirementSet,
    Simulation,
    Student,
    StudentRecord,
    TransferArticulation,
    co,
    course_id,
    from_grade,
    grade,
    pre,
    read_csv,
    semester,
    simple_students,
)
from tests.test_degree_plan import A, B, C, D, E, F, G, H, curric, dp


class DataTypesTests(unittest.TestCase):
    def test_course(self) -> None:
        "Test Course creation"
        self.assertEqual(A.name, "Introduction to Baskets")
        self.assertEqual(A.credit_hours, 3)
        self.assertEqual(A.prefix, "BW")
        self.assertEqual(A.num, "110")
        self.assertEqual(A.institution, "ACME State University")
        self.assertEqual(A.canonical_name, "Baskets I")

    def test_course_id(self) -> None:
        "Test course_id function"
        self.assertEqual(
            course_id(A.name, A.prefix, A.num, A.institution),
            hash(A.name + A.prefix + A.num + A.institution),
        )

    def test_add_requisite(self) -> None:
        "Test add_requisite! function"
        self.assertEqual(len(A.requisites), 0)
        self.assertEqual(len(B.requisites), 0)
        self.assertEqual(len(C.requisites), 3)
        self.assertEqual(len(D.requisites), 0)
        self.assertEqual(len(E.requisites), 1)
        self.assertEqual(len(F.requisites), 1)

    def test_delete_requisite(self) -> None:
        "Test delete_requisite! function"
        C.delete_requisite(A)
        self.assertEqual(len(C.requisites), 2)
        C.add_requisite(A, pre)

    def test_curriculum(self) -> None:
        "Test Curriciulum creation"
        self.assertEqual(curric.name, "Underwater Basket Weaving")
        self.assertEqual(curric.institution, "ACME State University")
        self.assertEqual(curric.degree_type, "BS")
        self.assertEqual(curric.system_type, semester)
        self.assertEqual(curric.cip, "445786")
        self.assertEqual(curric.num_courses, 8)
        self.assertEqual(curric.credit_hours, 22)

    def test_graph(self) -> None:
        "test the underlying graph"
        self.assertEqual(curric.graph.number_of_nodes(), 8)
        self.assertEqual(curric.graph.number_of_edges(), 5)

        lo1 = LearningOutcome(
            "Test learning outcome #1", "students will demonstrate ability to do #1", 12
        )
        lo2 = LearningOutcome(
            "Test learning outcome #1", "students will demonstrate ability to do #2", 10
        )
        lo3 = LearningOutcome(
            "Test learning outcome #1", "students will demonstrate ability to do #3", 15
        )
        lo4 = LearningOutcome(
            "Test learning outcome #1", "students will demonstrate ability to do #3", 7
        )
        lo2.add_requisite(lo1, pre)
        lo4.add_requisites([(lo2, pre), (lo3, co)])
        self.assertEqual(len(lo1.requisites), 0)
        self.assertEqual(len(lo2.requisites), 1)
        self.assertEqual(len(lo3.requisites), 0)
        self.assertEqual(len(lo4.requisites), 2)

        # test the uderlying learning outcome graph
        # @test nv(curric.graph) == 8
        # @test ne(curric.graph) == 5

        # mapped_ids = map_vertex_ids(curric)
        # self.assertEqual(curric.requisite_type(A.id, C.id), pre)
        # self.assertEqual(curric.requisite_type(D.id, C.id), co)

        self.assertEqual(curric.total_credits, 22)
        # self.assertIn(curric.course_from_id(1), [A, B, C, D, E, F, G, H])
        # self.assertIn(curric.course_from_id(2), [A, B, C, D, E, F, G, H])
        # self.assertIn(curric.course_from_id(3), [A, B, C, D, E, F, G, H])
        # self.assertIn(curric.course_from_id(4), [A, B, C, D, E, F, G, H])
        # self.assertIn(curric.course_from_id(5), [A, B, C, D, E, F, G, H])
        # self.assertIn(curric.course_from_id(6), [A, B, C, D, E, F, G, H])
        # self.assertIn(curric.course_from_id(7), [A, B, C, D, E, F, G, H])
        # self.assertIn(curric.course_from_id(8), [A, B, C, D, E, F, G, H])

        self.assertEqual(curric.course_from_id(A.id), A)
        self.assertEqual(
            curric.course(
                "BW", "110", "Introduction to Baskets", "ACME State University"
            ),
            A,
        )
        id = A.id
        curric.convert_ids()
        # this should not change the ids, since the curriculum was not created from a CSV file
        self.assertEqual(A.id, id)
        test_curric = read_csv("./tests/curriculum.csv")
        if not isinstance(test_curric, Curriculum):
            self.fail()
        test_curric.convert_ids()
        # this should change the ids
        self.assertEqual(
            test_curric.course(
                "BW", "110", "Introduction to Baskets", "ACME State University"
            ).id,
            hash("Introduction to Baskets" + "BW" + "110" + "ACME State University"),
        )

    def test_course_collection(self) -> None:
        "Test CourseCollection creation"
        CC = CourseCollection(
            "Test Course Collection",
            3,
            [A, B, C, E],
            institution="ACME State University",
        )
        self.assertEqual(CC.name, "Test Course Collection")
        self.assertEqual(CC.credit_hours, 3)
        self.assertEqual(len(CC.courses), 4)
        self.assertEqual(CC.institution, "ACME State University")

    def _course_catalog(self) -> CourseCatalog:
        return CourseCatalog(
            "Test Course Catalog",
            "ACME State University",
            courses=[A],
            catalog={B.id: B, C.id: C},
            date_range=(date(2019, 8, 1), date(2020, 7, 31)),
        )

    def test_course_catalog(self) -> None:
        "Test CourseCatalog creation"
        CCat = self._course_catalog()
        self.assertEqual(CCat.name, "Test Course Catalog")
        self.assertEqual(CCat.institution, "ACME State University")
        self.assertEqual(len(CCat.catalog), 3)

    def test_add_course(self) -> None:
        "Test add_course! functions"
        CCat = self._course_catalog()
        CCat.add_courses([D])
        self.assertEqual(len(CCat.catalog), 4)
        CCat.add_courses([E, F, G])
        self.assertEqual(len(CCat.catalog), 7)
        self.assertTrue(CCat.is_duplicate(A))
        self.assertFalse(CCat.is_duplicate(H))
        self.assertEqual((CCat.date_range[1] - CCat.date_range[0]), timedelta(365))
        self.assertEqual(A, CCat.course("BW", "110", "Introduction to Baskets"))

    def test_degree_plan(self) -> None:
        "Test DegreePlan creation, other degree plan functions tested in ./test/DegreePlanAnalytics.jl"
        self.assertEqual(dp.name, "2019 Plan")
        self.assertIs(
            dp.curriculum, curric
        )  # tests that they're the same object in memory
        self.assertEqual(dp.num_terms, 4)
        self.assertEqual(dp.credit_hours, 22)

    def test_degree_requirements(self) -> None:
        "Test DegreeRequirements data types"
        self.assertEqual(grade("A➕"), grade(from_grade(13)))
        self.assertEqual(grade("A"), grade(from_grade(12)))
        self.assertEqual(grade("A➖"), grade(from_grade(11)))
        self.assertEqual(grade("B➕"), grade(from_grade(10)))
        self.assertEqual(grade("B"), grade(from_grade(9)))
        self.assertEqual(grade("B➖"), grade(from_grade(8)))
        self.assertEqual(grade("C➕"), grade(from_grade(7)))
        self.assertEqual(grade("C"), grade(from_grade(6)))
        self.assertEqual(grade("C➖"), grade(from_grade(5)))
        self.assertEqual(grade("D➕"), grade(from_grade(4)))
        self.assertEqual(grade("D"), grade(from_grade(3)))
        self.assertEqual(grade("D➖"), grade(from_grade(2)))
        self.assertEqual(grade("P"), 0)
        self.assertEqual(grade("F"), 0)
        self.assertEqual(grade("I"), 0)
        self.assertEqual(grade("WP"), 0)
        self.assertEqual(grade("W"), 0)
        self.assertEqual(grade("WF"), 0)

        # The regex's specified will match all courses with the EGR prefix and any number
        CCat = self._course_catalog()
        CCat.add_courses([D, E, F, G])
        cs1 = CourseSet(
            "Test Course Set 1",
            3,
            [(A, grade("C")), (B, grade("D"))],
            course_catalog=CCat,
            prefix_regex=r"^\s*EGR\s*$",
            num_regex=r".*",
            double_count=True,
        )
        self.assertEqual(cs1.name, "Test Course Set 1")
        self.assertEqual(cs1.course_catalog, CCat)
        self.assertTrue(cs1.double_count)
        self.assertEqual(len(cs1.course_reqs), 3)
        # The regex's specified will match all courses with number 111 and any prefix
        cs2 = CourseSet(
            "Test Course Set 2",
            3,
            [],
            course_catalog=CCat,
            prefix_regex=r".*",
            num_regex=r"^\s*111\s*$",
        )
        self.assertFalse(
            cs2.double_count,
        )
        self.assertEqual(len(cs2.course_reqs), 1)

        req_set: List[AbstractRequirement] = [cs1, cs2]
        rs = RequirementSet("Test Requirement Set", 6, req_set)
        self.assertEqual(rs.name, "Test Requirement Set")
        self.assertEqual(rs.credit_hours, 6)
        self.assertEqual(rs.satisfy, 2)
        rs = RequirementSet("Test Requirement Set", 6, req_set, satisfy=1)
        self.assertEqual(rs.satisfy, 1)
        rs = RequirementSet("Test Requirement Set", 6, req_set, satisfy=5)
        self.assertEqual(rs.satisfy, 2)

    def test_student_record(self) -> None:
        "Test StudentRecord creation"
        cr1 = CourseRecord(A, grade("C"), "FALL 2020")
        self.assertEqual(cr1.course, A)
        self.assertEqual(cr1.grade, 6)
        cr2 = CourseRecord(B, 13, "SPRING 2020")
        self.assertEqual(cr2.grade, grade("A➕"))
        std_rec = StudentRecord("A14356", "Patti", "Furniture", "O", [cr1, cr2])
        self.assertEqual(len(std_rec.transcript), 2)

    def test_student(self) -> None:
        "Test Student creation"
        std = Student(1, attributes={"race": "other", "HS_GPA": 3.5})
        self.assertEqual(len(std.attributes), 2)
        stds = simple_students(100)
        self.assertEqual(len(stds), 100)

    def test_transfer_articulation(self) -> None:
        "Test TransferArticulation creation"
        XA = Course(
            "Baskets 101",
            3,
            institution="Tri-county Community College",
            prefix="BW",
            num="101",
            canonical_name="Baskets I",
        )
        XB = Course(
            "Fun w/ Baskets",
            3,
            institution="South Harmon Institute of Technology",
            prefix="FUN",
            num="101",
            canonical_name="Baskets I",
        )
        XCat1 = CourseCatalog(
            "Another Course Catalog",
            "Tri-county Community College",
            courses=[XA],
            date_range=(date(2019, 8, 1), date(2020, 7, 31)),
        )
        XCat2 = CourseCatalog(
            "Yet Another Course Catalog",
            "South Harmon Institute of Technology",
            courses=[XB],
            date_range=(date(2019, 8, 1), date(2020, 7, 31)),
        )
        # xfer_map = Dict((XCat.id, XA.id) => [A.id])  # this should work, but it fails
        CCat = self._course_catalog()
        # ta = TransferArticulation("Test Xfer Articulation", "ACME State University", CCat, Dict(XCat.id => XCat), xfer_map);
        ta = TransferArticulation(
            "Test Xfer Articulation", "ACME State University", CCat, {XCat1.id: XCat1}
        )
        ta.add_transfer_catalog(XCat2)
        self.assertEqual(len(ta.transfer_catalogs), 2)
        ta.add_transfer_course([A.id], XCat1.id, XA.id)
        ta.add_transfer_course([A.id], XCat2.id, XB.id)
        self.assertEqual(ta.transfer_equiv(XCat1.id, XA.id), [A.id])
        self.assertEqual(ta.transfer_equiv(XCat2.id, XB.id), [A.id])

    def test(self) -> None:
        "Test Simulation creation"
        sim_obj = Simulation(dp)
        self.assertEqual(sim_obj.degree_plan, dp)
