from io import StringIO
from typing import Any, Dict, List, Optional, Set

from networkx import DiGraph
from src.DataTypes.Course import AbstractCourse
from src.DataTypes.Curriculum import Curriculum, course_from_id
from src.DataTypes.DataTypes import pre

##############################################################
# Term data type


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
    metrics: Dict[str, Any]
    "Term-related metrics"
    metadata: Dict[str, Any]
    "Term-related metadata"

    def __init__(self, courses: List[AbstractCourse]) -> None:
        "Constructor"
        self.num_courses = len(courses)
        self.courses = []  # TODO: Array{AbstractCourse}(undef, self.num_courses)
        self.credit_hours = 0
        for i in range(self.num_courses):
            self.courses[i] = courses[i]
            self.credit_hours += courses[i].credit_hours
        self.metrics = {}
        self.metadata = {}


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
    graph: DiGraph[int]
    "Directed graph representation of pre-/co-requisite structure of the degre plan"
    terms: List[Term]
    "The terms associated with the degree plan"
    num_terms: int
    "Number of terms in the degree plan"
    credit_hours: float
    "Total number of credit hours in the degree plan"
    metrics: Dict[str, Any]
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
def isvalid_degree_plan(plan: DegreePlan, error_msg: StringIO = StringIO()) -> bool:
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
    validity = True
    # All requisite relationships are satisfied?
    #  -no backwards pointing requisites
    for i in range(1, plan.num_terms):
        for c in plan.terms[i].courses:
            for j in range(i - 1, -1, -1):  # TODO
                for k in plan.terms[j].courses:
                    for l in k.requisites:
                        if l == c.id:
                            validity = False
                            error_msg.write(
                                f"\n-Invalid requisite: {c.name} in term {i} is a requisite for {k.name} in term {j}",
                            )
    #  -requisites within the same term must be corequisites
    for i in range(plan.num_terms):
        for c in plan.terms[i].courses:
            for r in plan.terms[i].courses:
                if c == r:
                    continue
                elif (r.id) in c.requisites:
                    if c.requisites[r.id] == pre:
                        validity = False
                        error_msg.write(
                            f"\n-Invalid prerequisite: {r.name} in term {i} is a prerequisite for {c.name} in the same term",
                        )
    #  -TODO: strict co-requisites must be in the same term
    # All courses in the curriculum are in the degree plan?
    curric_classes: Set[int] = set()
    dp_classes: Set[int] = set()
    for i in plan.curriculum.courses:
        curric_classes.add(i.id)
    for i in range(plan.num_terms):
        for j in plan.terms[i].courses:
            dp_classes.add(j.id)
    if len((curric_classes - dp_classes)) > 0:
        validity = False
        for i in curric_classes - dp_classes:
            c = course_from_id(plan.curriculum, i)
            error_msg.write(f"\n-Degree plan is missing required course: {c.name}")
    # Is a course in the degree plan multiple times?
    dp_classes: Set[int] = set()
    for i in range(plan.num_terms):
        for j in plan.terms[i].courses:
            if (j.id) in dp_classes:
                validity = False
                error_msg.write(
                    f"\n-Course {j.name} is listed multiple times in degree plan",
                )
            else:
                dp_classes.add(j.id)
    return validity


def find_term(plan: DegreePlan, course: AbstractCourse) -> int:
    """
        find_term(plan:DegreePlan, course:Course)

    In degree plan `plan`, find the term in which course `course` appears.  If `course` in not in the degree plan an
    error message is provided.
    """
    for i, term in enumerate(plan.terms):
        if course in term.courses:
            return i
    raise ValueError(f"Course {course.name} is not in the degree plan")


# ugly print of degree plan
def print_plan(plan: DegreePlan) -> None:
    """
        print_plan(plan:DegreePlan)

    Ugly print out of a degree plan to the Julia console.
    """
    print(
        f"\nDegree Plan: {plan.name} for {plan.curriculum.degree_type} in {plan.curriculum.name}\n"
    )
    print(f" {plan.credit_hours} credit hours")
    for i in range(plan.num_terms):
        print(f" Term {i} courses:")
        for j in plan.terms[i].courses:
            print(f" {j.name} ")
        print("\n")
