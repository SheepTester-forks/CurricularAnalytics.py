"""
Term data type
"""

import math
from functools import cached_property
from io import StringIO
from typing import Any, Dict, List, NamedTuple, Optional, Set

from ..graph_algs import edge_crossings
from .course import AbstractCourse
from .curriculum import Curriculum
from .data_types import pre


class Term:
    """
    The `Term` data type is used to represent a single term within a :class:`DegreePlan`.

    Args:
        courses: `Course` data objects.

    """

    courses: List[AbstractCourse]
    "The courses associated with a term in a degree plan"
    num_courses: int
    "The number of courses in the Term"
    credit_hours: float
    "The number of credit hours associated with the term"
    metadata: Dict[str, Any]
    "Term-related metadata"

    def __init__(self, courses: List[AbstractCourse]) -> None:
        self.num_courses = len(courses)
        self.courses = courses.copy()
        self.credit_hours = sum(course.credit_hours for course in courses)
        self.metadata = {}

    def __repr__(self) -> str:
        return f"Term(courses={self.courses}, num_courses={self.num_courses}, credit_hours={self.credit_hours}, metadata={self.metadata})"


class TermMetrics(NamedTuple):
    min: float
    "max. credits in a term"
    min_term: int
    "max. credit term"
    max: float
    "min. credits in a term"
    max_term: int
    "min. credit term"
    average: float
    "avg. credits per term"
    stddev: float
    "term credit hour std. dev."


##############################################################
# Degree Plan data type
class DegreePlan:
    """
    The `DegreePlan` data type is used to represent the collection of courses that must be
    be completed in order to earn a particualr degree.

    Args:
        name: The name of the degree plan.
        curriculum: The curriculum the degree plan must satisfy.
        terms: The arrangement of terms associated with the degree plan.
        additional_courses: Additional courses in the degree plan that are not
          a part of the curriculum. E.g., a prerequisite math class to the first required math
          class in the curriculum.

    Examples:
        >>> DegreePlan("Biology 4-year Degree Plan", curriculum, terms)
        DegreePlan(...)
    """

    name: str
    "Name of the degree plan"
    curriculum: Curriculum
    "Curriculum the degree plan satisfies"
    additional_courses: List[AbstractCourse]
    "Additional (non-required) courses added to the degree plan, e.g., these may be preparatory courses"
    terms: List[Term]
    "The terms associated with the degree plan"
    num_terms: int
    "Number of terms in the degree plan"
    credit_hours: float
    "Total number of credit hours in the degree plan"
    metadata: Dict[str, Any]
    "Dergee Plan-related metadata"

    def __init__(
        self,
        name: str,
        curriculum: Curriculum,
        terms: List[Term],
        additional_courses: List[AbstractCourse] = [],
    ) -> None:
        self.name = name
        self.curriculum = curriculum
        self.num_terms = len(terms)
        self.terms = terms.copy()
        self.credit_hours = sum(term.credit_hours for term in terms)
        self.additional_courses = additional_courses.copy()
        self.metadata = {}

    # Check if a degree plan is valid.
    def is_valid(self, errors: Optional[StringIO] = None) -> bool:
        """
        Tests whether or not the degree plan `plan` is valid.

        Returns:
            A boolean value, with `True` indicating the degree plan is valid,
            and `False` indicating it is not.

        Examples:
            If `plan` is not valid, the reason(s) why are written to the `error_msg` buffer. To view these
            reasons, use:

            >>> errors = StringIO()
            >>> plan.is_valid(errors)
            False
            >>> print(errors.getvalue())
            ...

        There are three reasons why a curriculum graph might not be valid:

        - Requisites not satsified: A prerequisite for a course occurs in a later term than the course itself.
        - Incomplete plan: There are course in the curriculum not included in the degree plan.
        - Redundant plan: The same course appears in the degree plan multiple times.
        """
        validity: bool = True
        # All requisite relationships are satisfied?
        #  -no backwards pointing requisites
        for i, term1 in enumerate(self.terms):
            for course1 in term1.courses:
                for j, term2 in enumerate(self.terms[0:i]):
                    for course2 in term2.courses:
                        for l in course2.requisites:
                            if l == course1.id:
                                if errors:
                                    validity = False
                                    errors.write(
                                        f"\n-Invalid requisite: {course1.name} in term {i + 1} is a requisite for {course2.name} in term {j + 1}",
                                    )
                                else:
                                    return False
        #  -requisites within the same term must be corequisites
        for i, term in enumerate(self.terms):
            for course in term.courses:
                for r in term.courses:
                    if course == r:
                        continue
                    if r.id in course.requisites and course.requisites[r.id] == pre:
                        if errors:
                            validity = False
                            errors.write(
                                f"\n-Invalid prerequisite: {r.name} in term {i + 1} is a prerequisite for {course.name} in the same term",
                            )
                        else:
                            return False
        #  -TODO: strict co-requisites must be in the same term
        # All courses in the curriculum are in the degree plan?
        curric_classes: Set[int] = set()
        dp_classes: Set[int] = set()
        for course in self.curriculum.courses:
            curric_classes.add(course.id)
        for term in self.terms:
            for course1 in term.courses:
                dp_classes.add(course1.id)
        if curric_classes - dp_classes:
            if errors:
                validity = False
                for i in curric_classes - dp_classes:
                    course: AbstractCourse = self.curriculum.course_from_id(i)
                    errors.write(
                        f"\n-Degree self is missing required course: {course.name}"
                    )
            else:
                return False
        # Is a course in the degree plan multiple times?
        dp_classes: Set[int] = set()
        for term in self.terms:
            for course in term.courses:
                if course.id in dp_classes:
                    if errors:
                        validity = False
                        errors.write(
                            f"\n-Course {course.name} is listed multiple times in degree plan",
                        )
                    else:
                        return False
                dp_classes.add(course.id)
        return validity

    def knowledge_transfer(self) -> List[float]:
        """
        Determine the number of requisites crossing the "cut" in a degree plan that occurs between each term.

        Returns:
            A list of crossing values between the courses in the first term and the remainder of the degree plan,
            between the courses in the first two terms in the degree plan, and the remainder of the degree plan, etc.
            The length of the list returned will be one less than the number of terms in the degree plan.
        """
        ec_terms: List[float] = []
        s: List[int] = []
        for term in self.terms:
            sum = 0
            for c in term.courses:
                s.append(c.id)
            sum += edge_crossings(self.curriculum.graph, s)
            ec_terms.append(sum)
        del ec_terms[-1]
        return ec_terms  # the last value will always be zero, so remove it

    def find_term(self, course: AbstractCourse) -> int:
        """
        In degree plan `plan`, find the term in which course `course` appears.  If `course` in not in the degree plan an
        error message is provided.
        """
        for i, term in enumerate(self.terms):
            if course in term.courses:
                return i
        raise ValueError(f"Course {course.name} is not in the degree plan")

    # ugly print of degree plan
    def print(self) -> None:
        """
        Ugly print out of a degree plan to the console.
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

    # Basic metrics for a degree plan, based soley on credits
    @cached_property
    def basic_metrics(self) -> TermMetrics:
        r"""
        Compute the basic metrics associated with degree plan `plan`. The basic
        metrics are primarily concerned with how credits hours are distributed across the terms in a plan.

        The basic metrics computed include:

        * max. credits in a term: The maximum number of credit hours in any one term in the degree plan.
        * min. credits in a term: The minimum number of credit hours in any one term in the degree plan.
        * max. credit term: The earliest term in the degree plan that has the maximum number of credit hours (0-indexed).
        * min. credit term: The earliest term in the degree plan that has the minimum number of credit hours (0-indexed).
        * avg. credits per term: The average number of credit hours per term in the degree plan, :math:`\overline{ch}`.
        * term credit hour std. dev.: The standard deviation of credit hours across all terms :math:`\sigma`.  If :math:`ch_i` denotes the number
        of credit hours in term :math:`i`, then

        .. math::
            \sigma = \sqrt{\sum_{i=1}^m {(ch_i - \overline{ch})^2 \over m}}
        """
        min_credits: float = self.credit_hours
        max_credits: float = 0
        min_term: int = 0
        max_term: int = 0
        variance: float = 0
        average = self.credit_hours / self.num_terms
        for i, term in enumerate(self.terms):
            if term.credit_hours > max_credits:
                max_credits = term.credit_hours
                max_term = i
            if term.credit_hours < min_credits:
                min_credits = term.credit_hours
                min_term = i
            variance = variance + (term.credit_hours - average) ** 2
        return TermMetrics(
            min_credits,
            min_term,
            max_credits,
            max_term,
            average,
            math.sqrt(variance / self.num_terms),
        )

    def basic_metrics_to_buffer(self) -> StringIO:
        r"""
        Compute the basic metrics associated with degree plan `plan`, and return an IO buffer containing these metrics.

        The basic metrics computed include:

        * number of terms : The total number of terms (semesters or quarters) in the degree plan, ``m``.
        * total credit hours : The total number of credit hours in the degree plan.
        * max. credits in a term : The maximum number of credit hours in any one term in the degree plan.
        * min. credits in a term : The minimum number of credit hours in any one term in the degree plan.
        * max. credit term : The earliest term in the degree plan that has the maximum number of credit hours (1-indexed).
        * min. credit term : The earliest term in the degree plan that has the minimum number of credit hours (1-indexed).
        * avg. credits per term: The average number of credit hours per term in the degree plan, :math:`\overline{ch}`.
        * term credit hour std. dev.: The standard deviation of credit hours across all terms :math:`\sigma`.  If :math:`ch_i` denotes the number
        of credit hours in term :math:`i`, then

        .. math::
            \sigma = \sqrt{\sum_{i=1}^m {(ch_i - \overline{ch})^2 \over m}}

        Examples:
            To view the basic degree plan metrics associated with degree plan `plan` in the Julia console use:

            >>> metrics = plan.basic_metrics_to_buffer()
            >>> print(metrics.getvalue())
        """
        (
            min_credits,
            min_term,
            max_credits,
            max_term,
            average,
            stddev,
        ) = self.basic_metrics
        buffer = StringIO()
        buffer.write(
            f"\nCurriculum: {self.curriculum.name}\nDegree Plan: {self.name}\n"
        )
        buffer.write(f"  total credit hours = {self.credit_hours}\n")
        buffer.write(f"  number of terms = {self.num_terms}\n")
        buffer.write(
            f"  max. credits in a term = {max_credits}, in term {max_term+1}\n"
        )
        buffer.write(
            f"  min. credits in a term = {min_credits}, in term {min_term+1}\n"
        )
        buffer.write(
            f"  avg. credits per term = {average}, with std. dev. = {stddev}\n",
        )
        return buffer

    # Degree plan metrics based upon the distance between requsites and the classes that require them.
    def requisite_distance(self, course: AbstractCourse) -> int:
        r"""
        For a target course `course`, this function computes the total distance in the degree plan between `course` and
        all of its requisite courses.

        Args:
            course: The target course.

        The distance between a target course and one of its requisites is given by the number of terms that separate the target
        course from that particular requisite in the degree plan. To compute the requisite distance, we sum this distance over all
        requisites. That is, if write let :math:`T_j^p` denote the term in degree plan :math:`p` that course :math:`c_j` appears in, then for a
        degree plan with underlying curriculum graph :math:`G_c = (V,E)`, the requisite distance for course :math:`c_j` in degree plan :math:`p`,
        denoted :math:`rd_{v_j}^p`, is:

        .. math::
            rd_{v_j}^p = \sum_{\{i | (v_i, v_j) \in E\}} (T_j - T_i).

        In general, it is desirable for a course and its requisites to appear as close together as possible in a degree plan.
        """
        return sum(
            (
                self.find_term(course)
                - self.find_term(self.curriculum.course_from_id(req))
            )
            for req in course.requisites
        )

    @cached_property
    def total_requisite_distance(self) -> int:
        r"""
        The total distance between all courses in the degree plan, and
        the requisites for those courses.

        The distance between a course a requisite is given by the number of terms that separate the course from
        its requisite in the degree plan.  If :math:`rd_{v_i}^p` denotes the requisite distance between course
        :math:`c_i` and its requisites in degree plan :math:`p`, then the total requisite distance for a degree plan,
        denoted :math:`rd^p`, is given by:

        .. math::
            rd^p = \sum_{v_i \in V} = rd_{v_i}^p

        In general, it is desirable for a course and its requisites to appear as close together as possible in a degree plan.
        Thus, a degree plan that minimizes these distances is desirable.
        """
        return sum(
            self.requisite_distance(course) for course in self.curriculum.courses
        )

    def __repr__(self) -> str:
        return f"DegreePlan(name={repr(self.name)}, curriculum={self.curriculum}, additional_courses={self.additional_courses}, terms={self.terms}, num_terms={self.num_terms}, credit_hours={self.credit_hours}, metadata={self.metadata})"
