# file: DegreePlanCreation.jl

from typing import List, Literal, Optional, Protocol, Union

from networkx import has_path

from .types.course import AbstractCourse, Course
from .types.curriculum import Curriculum
from .types.data_types import pre, strict_co
from .types.degree_plan import DegreePlan, Term


class CreateTerms(Protocol):
    def __call__(
        self,
        curric: Curriculum,
        additional_courses: List[AbstractCourse] = [],
        *,
        min_terms: int = 2,
        max_terms: int = 10,
        min_cpt: int = 3,
        max_cpt: int = 19,
    ) -> Union[List[Term], Literal[False]]:
        ...


def bin_filling(
    curric: Curriculum,
    additional_courses: List[AbstractCourse] = [],
    *,
    min_terms: int = 2,
    max_terms: int = 10,
    min_cpt: int = 3,
    max_cpt: int = 19,
) -> Union[List[Term], Literal[False]]:
    terms: List[Term] = []
    term_credits = 0
    term_courses: List[AbstractCourse] = []
    UC = curric.courses.copy()  # lower numbered courses will be considered first
    UC.sort(key=course_num)
    while len(UC) > 0:
        c = select_vertex(curric, term_courses, UC)
        if c != None:
            UC.remove(c)
            if term_credits + c.credit_hours <= max_cpt:
                term_courses.append(c)
                term_credits = term_credits + c.credit_hours
            else:  # exceeded max credits allowed per term
                terms.append(Term(term_courses))
                term_courses = [c]
                term_credits = c.credit_hours
            # if c serves as a strict-corequisite for other courses, include them in current term too
            for course in UC:
                for req in course.requisites.items():
                    if req[0] == c.id:
                        if req[1] == strict_co:
                            UC.remove(course)
                            term_courses.append(course)
                            term_credits = term_credits + course.credit_hours
        else:  # can't find a course to add to current term, create a new term
            if len(term_courses) > 0:
                terms.append(Term(term_courses))
            term_courses = []
            term_credits = 0
    if len(term_courses) > 0:
        terms.append(Term(term_courses))
    return terms


def create_degree_plan(
    curric: Curriculum,
    create_terms: CreateTerms = bin_filling,
    name: str = "",
    additional_courses: List[AbstractCourse] = [],
    *,
    min_terms: int = 1,
    max_terms: int = 10,
    min_cpt: int = 3,
    max_cpt: int = 19,
) -> Optional[DegreePlan]:
    terms = create_terms(
        curric,
        additional_courses,
        min_terms=min_terms,
        max_terms=max_terms,
        min_cpt=min_cpt,
        max_cpt=max_cpt,
    )
    if terms == False:
        print("Unable to create degree plan")
        return
    else:
        return DegreePlan(name, curric, terms)


def select_vertex(
    curric: Curriculum, term_courses: List[AbstractCourse], UC: List[AbstractCourse]
) -> Optional[AbstractCourse]:
    for target in UC:
        target_vertex = curric.courses.index(target)
        invariant1 = True
        for source in UC:
            if source == target:
                continue
            # target cannot be moved to AC
            if has_path(curric.graph, curric.courses.index(source), target_vertex):
                invariant1 = False  # invariant 1 violated
                break  # try a new target
        if invariant1:
            invariant2 = True
            for c in term_courses:
                if target.requisites.get(c.id) == pre:
                    invariant2 = False
                    break  # try a new target
            if invariant2:
                return target


def course_num(c: AbstractCourse) -> str:
    return c.num if isinstance(c, Course) and c.num != "" else c.name
