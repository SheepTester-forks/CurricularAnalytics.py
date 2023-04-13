from typing import Any, Dict, List, Tuple
from src.DataTypes.Course import Course

##############################################################
# Course Catalog data type
# Stores the collection of courses available at an institution


class CourseCatalog:
    id: int
    "Unique course catalog ID"
    name: str
    "Name of the course catalog"
    institution: str
    "Institution offering the courses in the catalog"
    date_range: Tuple[Any, ...]  # TODO
    "range of dates the catalog is applicable over"
    catalog: Dict[int, Course]
    "dictionary of courses in (course_id, course) format"

    # Constructor
    def __init__(
        self,
        name: str,
        institution: str,
        courses: List[Course] = [],
        catalog: Dict[int, Course] = {},
        date_range: Tuple[Any, ...] = (),
        id: int = 0,
    ) -> None:
        self.name = name
        self.institution = institution
        self.catalog = catalog
        self.date_range = date_range
        self.id = hash(self.name + self.institution)
        if len(courses) > 0:
            add_courses(self, courses)


# add a course to a course catalog, if the course is already in the catalog, it is not added again
def add_course(cc: CourseCatalog, course: Course) -> None:
    if not is_duplicate(cc, course):
        cc.catalog[course.id] = course


def add_courses(cc: CourseCatalog, courses: List[Course]) -> None:
    for course in courses:
        add_course(cc, course)


def is_duplicate(cc: CourseCatalog, course: Course) -> bool:
    return course.id in (cc.catalog)


# Return a course in a course catalog
def course(cc: CourseCatalog, prefix: str, num: str, name: str) -> Course:
    hash_val = hash(name + prefix + num + cc.institution)
    if hash_val in (cc.catalog):
        return cc.catalog[hash_val]
    else:
        raise Exception(
            f"Course: {prefix} {num}: {name} at {cc.institution} does not exist in catalog: {cc.name}"
        )
