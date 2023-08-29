"""
DegreeRequirement data types

Data types for requirements::

    AbstractRequirement
    ├── CourseSet
    └── RequirementSet

A requirement may involve a set of courses (CourseSet), or a set of requirements (RequirementSet), but not both.
"""

__all__ = ["Grade"]

import re
from abc import ABC
from typing import List, Tuple

from .course import Course
from .course_catalog import CourseCatalog

Grade = int
"Create an integer data type called Grade"

Regex = str

_failing_grades = ["P", "F", "I", "WP", "W", "WF"]
_grade_strs = [
    "F",
    "F",
    "D➖",
    "D",
    "D➕",
    "C➖",
    "C",
    "C➕",
    "B➖",
    "B",
    "B➕",
    "A➖",
    "A",
    "A➕",
]


def grade(letter_grade: str) -> Grade:
    "function for converting a letter grade into a integer, divide by 3 to convert to 4-point GPA scale"
    if letter_grade in _failing_grades:
        return 0
    try:
        return _grade_strs.index(letter_grade)
    except ValueError:
        raise ValueError(f"letter grade {letter_grade} is not supported")


def from_grade(int_grade: Grade) -> str:
    "function for converting an integer letter grade, divide by 3 to convert to 4-point GPA scale"
    if int_grade == 0 or 2 <= int_grade <= 13:
        return _grade_strs[int_grade]
    else:
        raise ValueError("grade value {int_grade} is not supported")


class AbstractRequirement(ABC):
    """
    The `AbstractRequirement` data type is used to represent the requirements associated with an academic program. A
    reqiurement may consist of either the set of courses that can be used to satisfy the requirement, or a set of
    requirements that all must be satisfied. That is, the two possible concrete subtypes of an `AbstractRequirement`
    are:
    - `CourseSet` : a set of courses that may be used to satisfy a requirement.
    - `RequirementSet` : a set of requirements that may be used to satisfied a requirement. The requirement set may
        consist of other RequirementSets or CourseSets (these are the children of the parent `RequirementSet`).

    A valid set of requirements for a degree program is created as a tree of requirements, where all leaves in the
    tree must be `CourseSet` objects.
    """

    pass


class CourseSet(AbstractRequirement):
    """
    The `CourseSet` data type is used to represent the requirements associated with an academic program. A
    reqiurement may consist of either the set of courses that can be used to satisfy the requirement, or a set of
    requirements that all must be satisfied. That is, a  `Requirement` must be one of two types:
    - `course_set` : the set of courses that are used to satisfy the requirement are specifed in the `courses` array.
    - `requirement_set` : that set of requirements that must be satisfied are specified in the `requirements` array.

    Args:
        name: the name of the requirement.
        credit_hours: the number of credit hours associated with the requirement.
        course_reqs: the collection of courses that can be used to satisfy the requirement,
          and the minimum grade required in each.
        description (optional): A detailed description of the requirement. Default is the empty string.
        course_catalog (optional): Course catalog to draw courses from using the `prefix_regex` and `num_regex` regular
          expressions (positive matches are added to the course_reqs array). Note: both `prefix_regex` and `num_regex` must
          match in order for a course to be added the `course_reqs` array.
        prefix_regex (optional): regular expression for matching a course prefix in the course catalog. Default is `".*"`,
          i.e., match any character any number of times.
        num_regex (optional): regular expression for matching a course number in the course catalog. Default is `".*"`,
          i.e., match any character any number of times.
        min_grade (optional): The minimum letter grade that must be earned in courses satisfying the regular expressions.
        double_count (optional): Specifies whether or not each course in the course set can be used to satisfy other requirements
          that contain any of the courses in this `CourseSet`. Default = false

    Examples:
        >>> CourseSet("General Education - Mathematics", 9, courses)

        where `courses` is an array of Course-to-Grade `Pairs`, i.e., the set of courses/minimum grades that can satsfy this
        degree requirement.
    """

    id: int
    "Unique requirement id"
    name: str
    "Name of the requirement (must be unique)"
    description: str
    "Requirement description"
    credit_hours: float
    "The number of credit hours required to satisfy the requirement"
    course_reqs: List[Tuple[Course, Grade]]
    "The courses that the required credit hours may be drawn from, and the minimum grade that must be earned in each"
    course_catalog: CourseCatalog
    "Course catalog to draw courses from using the following regular expressions (positive matches are stored in course_reqs)"
    prefix_regex: Regex
    "Regular expression for matching a course prefix in the course catalog."
    num_regex: Regex
    "Regular expression for matching a course number in the course catalog, must satisfy both"
    min_grade: Grade
    "The minimum letter grade that must be earned in courses satisfying the regular expressions"
    double_count: bool
    "Each course in the course set can satisfy any other requirement that has the same course. Default = false"

    def __init__(
        self,
        name: str,
        credit_hours: float,
        course_reqs: List[Tuple[Course, Grade]] = [],
        *,
        description: str = "",
        course_catalog: CourseCatalog = CourseCatalog("", ""),
        prefix_regex: Regex = r".*",
        num_regex: Regex = r".*",
        min_grade: Grade = grade("D"),
        double_count: bool = False,
    ) -> None:
        self.name = name
        self.description = description
        self.credit_hours = credit_hours
        self.id = hash(self.name + self.description + str(self.credit_hours))
        self.course_reqs = course_reqs
        self.course_catalog = course_catalog
        self.prefix_regex = prefix_regex
        self.num_regex = num_regex
        self.double_count = double_count
        # search the supplied course catalog for courses satisfying both prefix and num regular expressions
        for c in course_catalog.catalog.values():
            if re.search(prefix_regex, c.prefix) and re.search(num_regex, c.num):
                course_reqs.append((c, min_grade))


class RequirementSet(AbstractRequirement):
    """
    The `RequirementSet` data type is used to represent a collection of requirements.

    Args:
        name: The name of the degree requirement set.
        credit_hours: The number of credit hours required in order to satisfy the requirement set.
        requirements: The course sets or requirement sets that comprise the requirement set.
        description: The description of the requirement set.
        satisfy: The number of requirements in the set that must be satisfied. Default is 0, meaning all.

    Examples
        >>> RequirementSet("General Education Core", 30, requirements)

        where `requirements` is an array of `CourseSet` and/or `RequirementSet` objects.
    """

    id: int
    "Unique requirement id (internally generated)"
    name: str
    "Name of the requirement (must be unique)"
    description: str
    "Requirement description"
    credit_hours: float
    "The number of credit hours required to satisfy the requirement"
    requirements: List[AbstractRequirement]
    "The set of requirements (course sets or requirements sets) that define this requirement"
    satisfy: int
    "The number of requirements in the set that must be satisfied.  Default is all."

    def __init__(
        self,
        name: str,
        credit_hours: float,
        requirements: List[AbstractRequirement],
        *,
        description: str = "",
        satisfy: int = 0,
    ) -> None:
        self.name = name
        self.description = description
        self.credit_hours = credit_hours
        self.id = hash(self.name + self.description + str(self.credit_hours))
        self.requirements = requirements
        if satisfy < 0:
            raise ValueError("satisfy cannot be a negative number")
        elif satisfy == 0:
            self.satisfy = len(requirements)  # satisfy all requirements
        else:
            # if trying satisfy more then the # of requirements, just satisfy all
            self.satisfy = min(satisfy, len(requirements))
