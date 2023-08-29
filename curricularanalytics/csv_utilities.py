import math
from io import TextIOWrapper
from typing import Callable, Dict, List, Optional, Tuple, TypeVar, Union

import pandas as pd

from .types.course import AbstractCourse, Course
from .types.curriculum import Curriculum
from .types.data_types import Requisite, co, pre, strict_co
from .types.degree_plan import Term
from .types.learning_outcome import LearningOutcome


def remove_empty_lines(file_path: str) -> str:
    if not file_path.endswith(".csv"):
        raise ValueError("Input is not a csv file")
    temp_file: str = file_path[:-4] + "_temp.csv"
    with open(temp_file, "w") as f, open(file_path) as file:
        new_file: str = ""
        for line in file.read().splitlines():
            if line and not line.replace('"', "").startswith("#"):
                new_file = new_file + line + "\n"
        if new_file:
            new_file = new_file[:-1]
        f.write(new_file)
    return temp_file


def find_courses(courses: List[AbstractCourse], course_id: int) -> bool:
    return any(course_id == course.id for course in courses)


def _course_reqs(course: AbstractCourse, requisite: Requisite) -> str:
    reqs = ";".join(
        str(course_id)
        for course_id, req_type in course.requisites.items()
        if req_type == requisite
    )
    return f'"{reqs}"' if reqs else ""


def course_line(
    curriculum: Curriculum,
    course: AbstractCourse,
    term_id: Optional[int] = None,
    *,
    metrics: bool = False,
) -> str:
    prefix_num: str = (
        f'"{course.prefix}","{course.num}"' if isinstance(course, Course) else ","
    )
    course_line: str = f'\n{course.id},"{course.name}",{prefix_num},{_course_reqs(course, pre)},{_course_reqs(course, co)},{_course_reqs(course, strict_co)},{course.credit_hours},"{course.institution}","{course.canonical_name}"'
    if term_id is not None:
        course_line += f",{term_id}"
    if metrics:
        course_line += f"{curriculum.course_complexity(course)},{curriculum.course_blocking_factor(course)},{curriculum.course_delay_factor(course)},{curriculum.course_centrality(course)}"
    return course_line


def csv_line_reader(line: str, delimeter: str = ",") -> List[str]:
    quotes: bool = False
    result: List[str] = []
    item: str = ""
    for char in line:
        if char == '"':
            quotes = not quotes
        elif char == delimeter and not quotes:
            result.append(item)
            item = ""
        else:
            item += char
    if item:
        result.append(item)
    return result


CellType = TypeVar("CellType", str, int, float, bool)


def find_cell(
    row: "pd.Series[pd.CsvInferTypes]", header: str, type: Callable[..., CellType] = str
) -> CellType:
    if header not in row:  # I assume this means if header is not in names
        raise KeyError(f"{header} column is missing")
    cell: "pd.CsvInferTypes" = row[header]
    if isinstance(cell, float) and math.isnan(cell):
        return type()
    else:
        return type(cell)


def read_all_courses(
    df_courses: "pd.DataFrame[pd.CsvInferTypes]",
    lo_Course: Dict[int, List[LearningOutcome]] = {},
) -> Dict[int, Course]:
    course_dict: Dict[int, Course] = {}
    for _, row in df_courses.iterrows():
        c_ID: int = int(row["Course ID"])
        if c_ID in course_dict:
            raise ValueError("Course IDs must be unique")
        course_dict[c_ID] = Course(
            find_cell(row, "Course Name"),
            find_cell(row, "Credit Hours", float),
            prefix=find_cell(row, "Prefix"),
            learning_outcomes=lo_Course.get(c_ID, []),
            num=find_cell(row, "Number"),
            institution=find_cell(row, "Institution"),
            canonical_name=find_cell(row, "Canonical Name"),
            id=c_ID,
        )
    for _, row in df_courses.iterrows():
        c_ID: int = int(row["Course ID"])
        pre_reqs: str = find_cell(row, "Prerequisites")
        if pre_reqs:
            for pre_req in pre_reqs.split(";"):
                course_dict[c_ID].add_requisite(course_dict[int(pre_req)], pre)
        co_reqs: str = find_cell(row, "Corequisites")
        if co_reqs:
            for co_req in co_reqs.split(";"):
                course_dict[c_ID].add_requisite(course_dict[int(co_req)], co)
        sco_reqs: str = find_cell(row, "Strict-Corequisites")
        if sco_reqs:
            for sco_req in sco_reqs.split(";"):
                course_dict[c_ID].add_requisite(course_dict[int(sco_req)], strict_co)
    return course_dict


def read_courses(
    df_courses: "pd.DataFrame[pd.CsvInferTypes]", all_courses: Dict[int, Course]
) -> Dict[int, Course]:
    course_dict: Dict[int, Course] = {}
    for _, row in df_courses.iterrows():
        c_ID: int = int(row["Course ID"])
        course_dict[c_ID] = all_courses[c_ID]
    return course_dict


def read_terms(
    df_courses: "pd.DataFrame[pd.CsvInferTypes]",
    course_dict: Dict[int, Course],
    course_arr: List[Course],
) -> Union[List[Term], Tuple[List[Term], List[Course], List[Course]]]:
    terms: Dict[int, List[Course]] = {}
    have_term: List[Course] = []
    not_have_term: List[Course] = []
    for _, row in df_courses.iterrows():
        c_ID = int(find_cell(row, "Course ID"))
        term_ID: int = find_cell(row, "Term", int)
        for course in course_arr:
            if course_dict[c_ID].id == course.id:  # This could be simplified with logic
                if term_ID != 0:  # operations rather than four if statemnts
                    have_term.append(course)
                    terms.setdefault(term_ID, []).append(course)
                else:
                    not_have_term.append(course)
                break
    terms_arr: List[Term] = [
        Term(list(terms[term]) if term in terms else [])
        for term in range(1, len(terms) + 1)  # Term IDs are 1-indexed
    ]
    if not_have_term:
        return terms_arr, have_term, not_have_term
    else:
        return terms_arr


def generate_course_lo(
    df_learning_outcomes: "pd.DataFrame[pd.CsvInferTypes]",
) -> Dict[int, List[LearningOutcome]]:
    lo_dict: Dict[int, LearningOutcome] = {}
    for _, row in df_learning_outcomes.iterrows():
        lo_ID: int = int(row["Learning Outcome ID"])
        if lo_ID in lo_dict:
            raise ValueError("Learning Outcome ID must be unique")
        lo_dict[lo_ID] = LearningOutcome(
            find_cell(row, "Learning Outcome"),
            find_cell(row, "Description"),
            find_cell(row, "Hours", int),
        )
    for _, row in df_learning_outcomes.iterrows():
        lo_ID: int = int(row["Learning Outcome ID"])
        reqs: str = find_cell(row, "Requisites")
        if reqs:
            for req in reqs.split(";"):
                # adds all requisite courses for the learning outcome as prerequisites
                lo_dict[lo_ID].add_requisite(lo_dict[int(req)], pre)
    lo_Course: Dict[int, List[LearningOutcome]] = {}
    for _, row in df_learning_outcomes.iterrows():
        c_ID: int = int(row["Course ID"])
        lo_ID: int = int(row["Learning Outcome ID"])
        lo_Course.setdefault(c_ID, []).append(lo_dict[lo_ID])
    return lo_Course


def generate_curric_lo(
    df_curric_lo: "pd.DataFrame[pd.CsvInferTypes]",
) -> List[LearningOutcome]:
    learning_outcomes: List[LearningOutcome] = []
    for _, row in df_curric_lo.iterrows():
        lo_name: str = find_cell(row, "Learning Outcome")
        lo_description: str = find_cell(row, "Description")
        learning_outcomes.append(LearningOutcome(lo_name, lo_description, 0))
    return learning_outcomes


def gather_learning_outcomes(curric: Curriculum) -> Dict[int, List[LearningOutcome]]:
    all_course_lo: Dict[int, List[LearningOutcome]] = {}
    for course in curric.courses:
        if course.learning_outcomes:
            all_course_lo[course.id] = course.learning_outcomes
    return all_course_lo


def write_learning_outcomes(
    curric: Curriculum,
    csv_file: TextIOWrapper,
    all_course_lo: Dict[int, List[LearningOutcome]],
) -> None:
    if all_course_lo:
        csv_file.write("\nCourse Learning Outcomes,,,,,,,,,,")
        csv_file.write(
            "\nCourse ID,Learning Outcome ID,Learning Outcome,Description,Requisites,Hours,,,,,"
        )
        for course_ID, lo_arr in all_course_lo.items():
            for lo in lo_arr:
                lo_prereq: str = ";".join(
                    str(requesite) for requesite in lo.requisites.keys()
                )
                if lo_prereq:
                    lo_prereq = f'"{lo_prereq}"'
                csv_file.write(
                    f'\n{course_ID},{lo.id},"{lo.name}","{lo.description}",{lo_prereq},{lo.hours},,,,,'
                )
    if curric.learning_outcomes:
        csv_file.write("\nCurriculum Learning Outcomes,,,,,,,,,,")
        csv_file.write("\nLearning Outcome,Description,,,,,,,,,")
        for lo in curric.learning_outcomes:
            csv_file.write(f'\n"{lo.name}","{lo.description}",,,,,,,,,')
