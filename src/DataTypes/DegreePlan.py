from io import StringIO
from typing import Any, Dict, List, Set, TypedDict

import networkx as nx
from src.DataTypes.Course import AbstractCourse
from src.DataTypes.Curriculum import Curriculum
from src.DataTypes.DataTypes import pre

##############################################################
# Term data type

TermMetrics = TypedDict("TermMetrics", {})


class Term:
    """
    The `Term` data type is used to represent a single term within a `DegreePlan`. To
    instantiate a `Term` use:

        Term([c1, c2, ...])

    where c1, c2, ... are `Course` data objects
    """

    courses: List[AbstractCourse]
    "The courses associated with a term in a degree plan"
    num_courses: int
    "The number of courses in the Term"
    credit_hours: float
    "The number of credit hours associated with the term"
    metrics: TermMetrics
    "Term-related metrics"
    metadata: Dict[str, Any]
    "Term-related metadata"

    def __init__(self, courses: List[AbstractCourse]) -> None:
        "Constructor"
        self.num_courses = len(courses)
        self.courses = courses.copy()
        self.credit_hours = sum(course.credit_hours for course in courses)
        self.metrics = {}
        self.metadata = {}

    def __repr__(self) -> str:
        return f"Term(courses={self.courses}, num_courses={self.num_courses}, credit_hours={self.credit_hours}, metrics={self.metrics}, metadata={self.metadata})"


DegreePlanMetrics = TypedDict(
    "DegreePlanMetrics",
    {
        "total credit hours": float,
        "number of terms": int,
        "max. credits in a term": float,
        "max. credit term": int,
        "min. credits in a term": float,
        "min. credit term": int,
        "avg. credits per term": float,
        "term credit hour std. dev.": float,
        "requisite distance": int,
    },
    total=False,
)


##############################################################
# Degree Plan data type
class DegreePlan:
    """
    The `DegreePlan` data type is used to represent the collection of courses that must be
    be completed in order to earn a particualr degree.  To instantiate a `Curriculum` use:

        DegreePlan(name, curriculum, terms, additional_courses)

    # Arguments
    - `name:str` : the name of the degree plan.
    - `curriculum:Curriculum` : the curriculum the degree plan must satisfy.
    - `terms:Array{Term}` : the arrangement of terms associated with the degree plan.
    - `additional_courses:Array{Course}` : additional courses in the degree plan that are not
    a part of the curriculum. E.g., a prerequisite math class to the first required math
    class in the curriculum.

    # Examples:
    ```julia-repl
    julia> DegreePlan("Biology 4-year Degree Plan", curriculum, terms)
    ```
    """

    name: str
    "Name of the degree plan"
    curriculum: Curriculum
    "Curriculum the degree plan satisfies"
    additional_courses: List[AbstractCourse]
    "Additional (non-required) courses added to the degree plan, e.g., these may be preparatory courses"
    # graph: "nx.DiGraph[int]"
    # "Directed graph representation of pre-/co-requisite structure of the degre plan"
    terms: List[Term]
    "The terms associated with the degree plan"
    num_terms: int
    "Number of terms in the degree plan"
    credit_hours: float
    "Total number of credit hours in the degree plan"
    metrics: DegreePlanMetrics
    "Dergee Plan-related metrics"
    metadata: Dict[str, Any]
    "Dergee Plan-related metadata"

    def __init__(
        self,
        name: str,
        curriculum: Curriculum,
        terms: List[Term],
        additional_courses: List[AbstractCourse] = [],
    ) -> None:
        "Constructor"
        self.name = name
        self.curriculum = curriculum
        self.num_terms = len(terms)
        self.terms = terms.copy()
        self.credit_hours = sum(term.credit_hours for term in terms)
        self.additional_courses = additional_courses.copy()
        self.metrics = {}
        self.metadata = {}

    # Check if a degree plan is valid.
    # Print error_msg using println(str(take!(error_msg))), where error_msg is the buffer returned by this function
    def isvalid_degree_plan(self, error_msg: StringIO = StringIO()) -> bool:
        """
            isvalid_degree_plan(plan:DegreePlan, errors:IOBuffer)

        Tests whether or not the degree plan `plan` is valid.  Returns a boolean value, with `true` indicating the
        degree plan is valid, and `false` indicating it is not.

        If `plan` is not valid, the reason(s) why are written to the `errors` buffer. To view these
        reasons, use:

        ```julia-repl
        julia> errors = IOBuffer()
        julia> isvalid_degree_plan(plan, errors)
        julia> println(str(take!(errors)))
        ```

        There are two reasons why a curriculum graph might not be valid:

        - Requisites not satsified : A prerequisite for a course occurs in a later term than the course itself.
        - Incomplete plan : There are course in the curriculum not included in the degree plan.
        - Redundant plan : The same course appears in the degree plan multiple times.

        """
        validity: bool = True
        # All requisite relationships are satisfied?
        #  -no backwards pointing requisites
        for i, term1 in enumerate(self.terms):
            for c in term1.courses:
                for j, term2 in enumerate(self.terms[0:i]):
                    for k in term2.courses:
                        for l in k.requisites:
                            if l == c.id:
                                validity = False
                                error_msg.write(
                                    f"\n-Invalid requisite: {c.name} in term {i + 1} is a requisite for {k.name} in term {j + 1}",
                                )
        #  -requisites within the same term must be corequisites
        for i, term in enumerate(self.terms):
            for c in term.courses:
                for r in term.courses:
                    if c == r:
                        continue
                    if r.id in c.requisites and c.requisites[r.id] == pre:
                        validity = False
                        error_msg.write(
                            f"\n-Invalid prerequisite: {r.name} in term {i + 1} is a prerequisite for {c.name} in the same term",
                        )
        #  -TODO: strict co-requisites must be in the same term
        # All courses in the curriculum are in the degree plan?
        curric_classes: Set[int] = set()
        dp_classes: Set[int] = set()
        for c in self.curriculum.courses:
            curric_classes.add(c.id)
        for term in self.terms:
            for c in term.courses:
                dp_classes.add(c.id)
        if curric_classes - dp_classes:
            validity = False
            for i in curric_classes - dp_classes:
                c: AbstractCourse = self.curriculum.course_from_id(i)
                error_msg.write(f"\n-Degree self is missing required course: {c.name}")
        # Is a course in the degree plan multiple times?
        dp_classes: Set[int] = set()
        for term in self.terms:
            for c in term.courses:
                if c.id in dp_classes:
                    validity = False
                    error_msg.write(
                        f"\n-Course {c.name} is listed multiple times in degree plan",
                    )
                else:
                    dp_classes.add(c.id)
        return validity

    def find_term(self, course: AbstractCourse) -> int:
        """
            find_term(plan:DegreePlan, course:Course)

        In degree plan `plan`, find the term in which course `course` appears.  If `course` in not in the degree plan an
        error message is provided.
        """
        for i, term in enumerate(self.terms):
            if course in term.courses:
                return i
        raise ValueError(f"Course {course.name} is not in the degree plan")

    # ugly print of degree plan
    def print_plan(self) -> None:
        """
            print_plan(plan:DegreePlan)

        Ugly print out of a degree plan to the Julia console.
        """
        print(
            f"\nDegree Plan: {self.name} for {self.curriculum.degree_type} in {self.curriculum.name}\n"
        )
        print(f" {self.credit_hours} credit hours")
        for i, term in enumerate(self.terms):
            print(f" Term {i+1} courses:")
            for c in term.courses:
                print(f" {c.name} ")
            print("\n")

    def __repr__(self) -> str:
        return f"DegreePlan(name={repr(self.name)}, curriculum={self.curriculum}, additional_courses={self.additional_courses}, terms={self.terms}, num_terms={self.num_terms}, credit_hours={self.credit_hours},metrics={self.metrics}, metadata={self.metadata})"
