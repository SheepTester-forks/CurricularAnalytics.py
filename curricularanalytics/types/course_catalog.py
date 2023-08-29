"""
Course Catalog data type:
Stores the collection of courses available at an institution.
"""

from datetime import date
from typing import Dict, List, Tuple

from .course import Course, course_id


class CourseCatalog:
    id: int
    "Unique course catalog ID"
    name: str
    "Name of the course catalog"
    institution: str
    "Institution offering the courses in the catalog"
    date_range: Tuple[date, date]
    "range of dates the catalog is applicable over"
    catalog: Dict[int, Course]
    "dictionary of courses in (course_id, course) format"

    # Constructor
    def __init__(
        self,
        name: str,
        institution: str,
        *,
        courses: List[Course] = [],
        catalog: Dict[int, Course] = {},
        date_range: Tuple[date, date] = (date.min, date.max),
    ) -> None:
        self.name = name
        self.institution = institution
        self.catalog = catalog
        self.date_range = date_range
        self.id = hash(self.name + self.institution)
        self.add_courses(courses)

    def add_course(self, course: Course) -> None:
        "add a course to a course catalog, if the course is already in the catalog, it is not added again"
        if not self.is_duplicate(course):
            self.catalog[course.id] = course

    def add_courses(self, courses: List[Course]) -> None:
        for course in courses:
            self.add_course(course)

    def is_duplicate(self, course: Course) -> bool:
        return course.id in self.catalog

    def course(self, prefix: str, num: str, name: str) -> Course:
        "Return a course in a course catalog"
        hash_val = course_id(name, prefix, num, self.institution)
        if hash_val in self.catalog:
            return self.catalog[hash_val]
        else:
            raise LookupError(
                f"Course: {prefix} {num}: {name} at {self.institution} does not exist in catalog: {self.name}"
            )
