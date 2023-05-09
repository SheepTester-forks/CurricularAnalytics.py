from abc import ABC, abstractmethod
from typing import Any, Dict, List, Literal, Optional, TypeVar, TypedDict

from src.DataTypes.DataTypes import Requisite
from src.DataTypes.LearningOutcome import LearningOutcome

CourseMetrics = TypedDict(
    "CourseMetrics",
    {
        "blocking factor": int,
        "delay factor": int,
        "centrality": int,
        "complexity": float,
        "requisite distance": int,
    },
)

Self = TypeVar("Self", bound="AbstractCourse")

MatchCriterion = Literal["prefix", "num", "name", "canonical name", "credit hours"]


# Course-related data types:
#
#                               AbstractCourse
#                                /          \
#                          Course       CourseCollection
#
# A requirement may involve a set of courses (CourseSet), or a set of requirements (RequirementSet), but not both.
class AbstractCourse(ABC):
    """
    The `AbstractCourse` data type is used to represent the notion of an abstract course that may appear in a curriculum
    or degree plan. That is, this abstract type serves as a placeholder for a course in a curriculum or degree plan,
    where the abstract course may correspond to a single course, or a set of courses, where only one of the courses in the
    set should be taken at that particular point in the curriculum or degree plan. This allows a user to specify a course
    or a collection of courses as a part part of a curriculum or degree plans. The two possible concrete subtypes of
    an `AbstractCourse` are:
    - `Course` : a specific course.
    - `CourseCollection` : a set of courses, any of which can serve as the required course in a curriculum or degree plan.
    """

    id: int
    "Unique course id"

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
    metrics: CourseMetrics
    "Course-related metrics"
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
            add_requisite!(rc, tc, requisite_type)

        Add course rc as a requisite, of type requisite_type, for target course tc.

        # Arguments
        Required:
        - `rc::AbstractCourse` : requisite course.
        - `tc::AbstractCourse` : target course, i.e., course for which `rc` is a requisite.
        - `requisite_type::Requisite` : requisite type.

        # Requisite types
        One of the following requisite types must be specified for the `requisite_type`:
        - `pre` : a prerequisite course that must be passed before `tc` can be attempted.
        - `co`  : a co-requisite course that may be taken before or at the same time as `tc`.
        - `strict_co` : a strict co-requisite course that must be taken at the same time as `tc`.
        """

        self.requisites[requisite_course.id] = requisite_type

    def add_requisites(
        self,
        requisite_courses: List["AbstractCourse"],
        requisite_types: List[Requisite],
    ) -> None:
        """
            add_requisite!([rc1, rc2, ...], tc, [requisite_type1, requisite_type2, ...])

        Add a collection of requisites to target course tc.

        # Arguments
        Required:
        - `rc::Array{AbstractCourse}` : and array of requisite courses.
        - `tc::AbstractCourse` : target course, i.e., course for which `rc` is a requisite.
        - `requisite_type::Array{Requisite}` : an array of requisite types.

        # Requisite types
        The following requisite types may be specified for the `requisite_type`:
        - `pre` : a prerequisite course that must be passed before `tc` can be attempted.
        - `co`  : a co-requisite course that may be taken before or at the same time as `tc`.
        - `strict_co` : a strict co-requisite course that must be taken at the same time as `tc`.
        """

        assert len(requisite_courses) == len(requisite_types)
        for i in range(len(requisite_courses)):
            self.requisites[requisite_courses[i].id] = requisite_types[i]

    def delete_requisite(
        self,
        requisite_course: "AbstractCourse",
    ) -> None:
        """
            delete_requisite!(rc, tc)

        Remove course rc as a requisite for target course tc.  If rc is not an existing requisite for tc, an
        error is thrown.

        # Arguments
        Required:
        - `rc::AbstractCourse` : requisite course.
        - `tc::AbstractCourse` : target course, i.e., course for which `rc` is a requisite.

        """
        # if !haskey(course.requisites, requisite_course.id)
        #    error("The requisite you are trying to delete does not exist")
        # end
        del self.requisites[requisite_course.id]

    def match(
        self,
        other: "AbstractCourse",
        match_criteria: List[MatchCriterion] = [],
    ) -> bool:
        is_matched = False
        if len(match_criteria) == 0:
            return self == other
        else:
            for criterion in match_criteria:
                if criterion not in [
                    "prefix",
                    "num",
                    "name",
                    "canonical name",
                    "credit hours",
                ]:
                    raise Exception(f"invalid match criteria: {criterion}")
                elif criterion == "prefix":
                    is_matched = (
                        self.prefix == other.prefix
                        if isinstance(self, Course) and isinstance(other, Course)
                        else True
                    )
                elif criterion == "num":
                    is_matched = (
                        self.num == other.num
                        if isinstance(self, Course) and isinstance(other, Course)
                        else True
                    )
                elif criterion == "name":
                    is_matched = self.name == other.name
                elif criterion == "canonical name":
                    is_matched = self.canonical_name == other.canonical_name
                elif criterion == "credit hours":
                    is_matched = self.credit_hours == other.credit_hours
        return is_matched

    def find_match(
        self,
        course_set: List["AbstractCourse"],
        match_criteria: List[MatchCriterion] = [],
    ) -> Optional["AbstractCourse"]:
        for c in course_set:
            if self.match(c, match_criteria):
                return self
        return None


##############################################################
# Course data type
class Course(AbstractCourse):
    """
    The `Course` data type is used to represent a single course consisting of a given number
    of credit hours.  To instantiate a `Course` use:

        Course(name, credit_hours; <keyword arguments>)

    # Arguments
    Required:
    - `name:AbstractString` : the name of the course.
    - `credit_hours:int` : the number of credit hours associated with the course.
    Keyword:
    - `prefix:AbstractString` : the prefix associated with the course.
    - `num:AbstractString` : the number associated with the course.
    - `institution:AbstractString` : the name of the institution offering the course.
    - `canonical_name:AbstractString` : the common name used for the course.

    # Examples:
    ```julia-repl
    julia> Course("Calculus with Applications", 4, prefix="MA", num="112", canonical_name="Calculus I")
    ```
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
        "Constructor"
        self.name = name
        self.credit_hours = credit_hours
        self.prefix = prefix
        self.num = num
        self.institution = institution
        if id == 0:
            self.id = self.default_id()
        else:
            self.id = id
        self.college = college
        self.department = department
        self.cross_listed = cross_listed or []
        self.canonical_name = canonical_name
        self.requisites = {}
        # self.requisite_formula
        self.metrics = {
            "blocking factor": -1,
            "centrality": -1,
            "complexity": -1,
            "delay factor": -1,
            "requisite distance": -1,
        }
        self.metadata = {}
        self.learning_outcomes = learning_outcomes or []
        # curriculum id -> vertex id, note: course may be in multiple curricula
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
        return f"Course(id={self.id}, name={repr(self.name)}, credit_hours={self.credit_hours}, prefix={repr(self.prefix)}, num={repr(self.num)}, institution={self.institution}, college={repr(self.college)}, department={repr(self.department)}, cross_listed={self.cross_listed}, canonical_name={repr(self.canonical_name)}, requisites={self.requisites}, learning_outcomes={self.learning_outcomes}, metrics={self.metrics}, metadata={self.metadata}, passrate={self.passrate})"


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
        "Constructor"
        self.name = name
        self.credit_hours = credit_hours
        self.courses = courses
        self.institution = institution
        if id == 0:
            self.id = self.default_id()
        else:
            self.id = id
        self.college = college
        self.department = department
        self.canonical_name = canonical_name
        self.requisites = {}
        # self.requisite_formula
        self.metrics = {
            "blocking factor": -1,
            "centrality": -1,
            "complexity": -1,
            "delay factor": -1,
            "requisite distance": -1,
        }
        self.metadata = {}
        self.learning_outcomes = learning_outcomes or []
        self.vertex_id = {}  # curriculum id -> vertex id

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
        return f"Course(id={self.id}, courses={self.courses}, name={repr(self.name)}, credit_hours={self.credit_hours}, institution={self.institution}, college={repr(self.college)}, department={repr(self.department)}, canonical_name={repr(self.canonical_name)}, requisites={self.requisites}, learning_outcomes={self.learning_outcomes}, metrics={self.metrics}, metadata={self.metadata})"


def course_id(name: str, prefix: str, num: str, institution: str) -> int:
    return hash(name + prefix + num + institution)
