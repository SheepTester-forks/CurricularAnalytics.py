"""
Course-related data types::

    AbstractCourse
    ├── Course
    └── CourseCollection

A requirement may involve a set of courses (CourseSet), or a set of requirements (RequirementSet), but not both.
"""

from abc import ABC, abstractmethod
from typing import (
    Any,
    Dict,
    List,
    Literal,
    Optional,
    TextIO,
    Tuple,
    TypeVar,
)

from .data_types import Requisite
from .learning_outcome import LearningOutcome

Self = TypeVar("Self", bound="AbstractCourse")

MatchCriterion = Literal["prefix", "num", "name", "canonical name", "credit hours"]


class AbstractCourse(ABC):
    """
    The :class:`AbstractCourse` data type is used to represent the notion of an abstract course that may appear in a curriculum
    or degree plan. That is, this abstract type serves as a placeholder for a course in a curriculum or degree plan,
    where the abstract course may correspond to a single course, or a set of courses, where only one of the courses in the
    set should be taken at that particular point in the curriculum or degree plan. This allows a user to specify a course
    or a collection of courses as a part part of a curriculum or degree plans. The two possible concrete subtypes of
    an :class:`AbstractCourse` are:

    * :class:`Course`: a specific course.
    * :class:`CourseCollection`: a set of courses, any of which can serve as the required course in a curriculum or degree plan.
    """

    id: int
    "Unique course id"
    vertex_id: Dict[int, int]
    """
    The vertex id of the course w/in a curriculum graph, stored as (curriculum_id, vertex_id)
    """

    name: str
    "Name of the course, e.g., Introduction to Psychology"
    credit_hours: float
    'Number of credit hours associated with course or a "typcial" course in the collection. For the purpose of analytics, variable credits are not supported'

    institution: str
    "Institution offering the course"
    college: str
    "College or school (within the institution) offering the course"
    department: str
    "Department (within the school or college) offering the course"
    canonical_name: str
    "Standard name used to denote the course in the discipline, e.g., Psychology I, or course collection, e.g., math genearl education"

    requisites: Dict[int, Requisite]
    "List of requisites, in (requisite_course id, requisite_type) format"
    learning_outcomes: List[LearningOutcome]
    "A list of learning outcomes associated with the course"
    metadata: Dict[str, Any]
    "Course-related metadata"

    @abstractmethod
    def default_id(self) -> int:
        ...

    @abstractmethod
    def copy(self: Self) -> Self:
        "create an indentical coures, but with a new course id"
        ...

    def add_requisite(
        self, requisite_course: "AbstractCourse", requisite_type: Requisite
    ) -> None:
        """
        Add course ``requisite_course`` as a requisite, of type ``requisite_type``, for this course.

        Args:
            requisite_course: Requisite course.
            requisite_type: Requisite type.

        One of the following requisite types must be specified for the ``requisite_type``:

        * :data:`pre`: a prerequisite course that must be passed before this course can be attempted.
        * :data:`co`: a co-requisite course that may be taken before or at the same time as this course.
        * :data:`strict_co`: a strict co-requisite course that must be taken at the same time as this course.
        """
        self.requisites[requisite_course.id] = requisite_type

    def add_requisites(
        self,
        requisites: List[Tuple["AbstractCourse", Requisite]],
    ) -> None:
        """
        Add a collection of requisites to this course.

        Args:
            requisites: An array of tuples of requisite courses and their respective types.

        The following requisite types may be specified for the ``requisite_type``:

        * :data:`pre`: a prerequisite course that must be passed before this course can be attempted.
        * :data:`co`: a co-requisite course that may be taken before or at the same time as this course.
        * :data:`strict_co`: a strict co-requisite course that must be taken at the same time as this course.
        """
        for requisite_course, requisite_type in requisites:
            self.add_requisite(requisite_course, requisite_type)

    def delete_requisite(
        self,
        requisite_course: "AbstractCourse",
    ) -> None:
        """
        Remove course ``requisite_course`` as a requisite for this course.

        Args:
            requisite_course: Requisite course.

        Raises:
            KeyError: If ``requisite_course`` is not an existing requisite for this course.
        """
        try:
            del self.requisites[requisite_course.id]
        except KeyError:
            raise KeyError("The requisite you are trying to delete does not exist.")

    def match(
        self,
        other: "AbstractCourse",
        match_criteria: List[MatchCriterion] = [],
    ) -> bool:
        if len(match_criteria) == 0:
            return self == other
        for criterion in match_criteria:
            if criterion == "prefix":
                if isinstance(self, Course) and isinstance(other, Course):
                    if self.prefix != other.prefix:
                        return False
            elif criterion == "num":
                if isinstance(self, Course) and isinstance(other, Course):
                    if self.num != other.num:
                        return False
            elif criterion == "name":
                if self.name != other.name:
                    return False
            elif criterion == "canonical name":
                if self.canonical_name != other.canonical_name:
                    return False
            elif criterion == "credit hours":
                if self.credit_hours != other.credit_hours:
                    return False
            else:
                raise ValueError(f"invalid match criteria: {criterion}")
        return True

    def find_match(
        self,
        course_set: List["AbstractCourse"],
        match_criteria: List[MatchCriterion] = [],
    ) -> Optional["AbstractCourse"]:
        for course in course_set:
            if self.match(course, match_criteria):
                return self
        return None


##############################################################
# Course data type
class Course(AbstractCourse):
    """
    The :class:`Course` data type is used to represent a single course consisting of a given number
    of credit hours.

    Args:
        name: The name of the course.
        credit_hours: The number of credit hours associated with the course.
        prefix: The prefix associated with the course.
        num: The number associated with the course.
        institution: The name of the institution offering the course.
        canonical_name: The common name used for the course.

    Examples:
        >>> Course("Calculus with Applications", 4, prefix="MA", num="112", canonical_name="Calculus I")
        Course(...)
    """

    prefix: str
    "Typcially a department prefix, e.g., PSY"
    num: str
    "Course number, e.g., 101, or 302L"
    cross_listed: List["Course"]
    'courses that are cross-listed with the course (same as "also offered as")'

    passrate: float
    "Percentage of students that pass the course"

    def __init__(
        self,
        name: str,
        credit_hours: float,
        *,
        prefix: str = "",
        learning_outcomes: Optional[List[LearningOutcome]] = None,
        num: str = "",
        institution: str = "",
        college: str = "",
        department: str = "",
        cross_listed: Optional[List["Course"]] = None,
        canonical_name: str = "",
        id: int = 0,
        passrate: float = 0.5,
    ) -> None:
        self.name = name
        self.credit_hours = credit_hours
        self.prefix = prefix
        self.num = num
        self.institution = institution
        self.id = id or self.default_id()
        self.college = college
        self.department = department
        self.cross_listed = cross_listed or []
        self.canonical_name = canonical_name
        self.requisites = {}
        self.metadata = {}
        self.learning_outcomes = learning_outcomes or []
        self.vertex_id = {}

        self.passrate = passrate

    def default_id(self) -> int:
        return course_id(self.name, self.prefix, self.num, self.institution)

    def copy(self) -> "Course":
        return Course(
            self.name,
            self.credit_hours,
            prefix=self.prefix,
            learning_outcomes=self.learning_outcomes,
            num=self.num,
            institution=self.institution,
            canonical_name=self.canonical_name,
        )

    def __repr__(self) -> str:
        return f"Course(id={self.id}, vertex_id={self.vertex_id} name={repr(self.name)}, credit_hours={self.credit_hours}, prefix={repr(self.prefix)}, num={repr(self.num)}, institution={self.institution}, college={repr(self.college)}, department={repr(self.department)}, cross_listed={self.cross_listed}, canonical_name={repr(self.canonical_name)}, requisites={self.requisites}, learning_outcomes={self.learning_outcomes}, metadata={self.metadata}, passrate={self.passrate})"


class CourseCollection(AbstractCourse):
    courses: List[Course]
    "Courses associated with the collection"

    def __init__(
        self,
        name: str,
        credit_hours: float,
        courses: List[Course],
        *,
        learning_outcomes: Optional[List[LearningOutcome]] = None,
        institution: str = "",
        college: str = "",
        department: str = "",
        canonical_name: str = "",
        id: int = 0,
    ) -> None:
        self.name = name
        self.credit_hours = credit_hours
        self.courses = courses
        self.institution = institution
        self.id = id or self.default_id()
        self.college = college
        self.department = department
        self.canonical_name = canonical_name
        self.requisites = {}
        self.metadata = {}
        self.learning_outcomes = learning_outcomes or []
        self.vertex_id = {}

    def default_id(self) -> int:
        return hash(self.name + self.institution + str(len(self.courses)))

    def copy(self) -> "CourseCollection":
        return CourseCollection(
            self.name,
            self.credit_hours,
            courses=[course.copy() for course in self.courses],
            learning_outcomes=self.learning_outcomes,
            institution=self.institution,
            canonical_name=self.canonical_name,
        )

    def __repr__(self) -> str:
        return f"Course(id={self.id}, vertex_id={self.vertex_id} courses={self.courses}, name={repr(self.name)}, credit_hours={self.credit_hours}, institution={self.institution}, college={repr(self.college)}, department={repr(self.department)}, canonical_name={repr(self.canonical_name)}, requisites={self.requisites}, learning_outcomes={self.learning_outcomes}, metadata={self.metadata})"


def course_id(name: str, prefix: str, num: str, institution: str) -> int:
    return hash(name + prefix + num + institution)


def _write_course_name(file: TextIO, c: AbstractCourse) -> None:
    if isinstance(c, Course):
        if c.prefix:
            file.write(f"{c.prefix} ")
        if c.num:
            file.write(f"{c.num} - ")
    file.write(c.name)


def write_course_names(
    file: TextIO, courses: List[AbstractCourse], *, separator: str = ", "
) -> None:
    if courses:
        for c in courses[:-1]:
            _write_course_name(file, c)
            file.write(separator)
        _write_course_name(file, courses[-1])
