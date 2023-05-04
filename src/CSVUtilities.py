from io import TextIOWrapper
import math
from typing import Dict, Hashable, List, Literal, Union

import pandas as pd

from src.DataTypes.Course import AbstractCourse, Course
from src.DataTypes.Curriculum import Curriculum
from src.DataTypes.DataTypes import Requisite, co, pre, strict_co
from src.DataTypes.DegreePlan import Term
from src.DataTypes.LearningOutcome import LearningOutcome


def readfile(file_path: str) -> List[str]:
    with open(file_path) as f:
        return f.readlines()


def remove_empty_lines(file_path: str) -> str:
    if not file_path.endswith(".csv"):
        raise ValueError("Input is not a csv file")
    temp_file: str = file_path[:-4] + "_temp.csv"
    file: List[str] = readfile(file_path)
    with open(temp_file, "w") as f:
        new_file: str = ""
        for line in file:
            line: str = line.replace("\r", "")
            if line and not line.replace('"', "").startswith("#"):
                line = line + "\n"
                new_file = new_file + line
        if new_file:
            new_file = new_file[:-1]
        f.write(new_file)
    return temp_file


def find_courses(courses: List[AbstractCourse], course_id: int) -> bool:
    return any(course_id == course.id for course in courses)


def _course_reqs(course: AbstractCourse, requisite: Requisite) -> str:
    reqs = ";".join(
        str(
            course_id
            for course_id, req_type in course.requisites.items()
            if req_type == requisite
        )
    )
    return f'"{reqs}"' if reqs else ""


def course_line(
    course: AbstractCourse, term_id: Union[str, int], *, metrics: bool = False
) -> str:
    prefix_num: str = (
        f'"{course.prefix}","{course.num}"' if isinstance(course, Course) else ","
    )
    c_line: str = f'\n{course.id},"{course.name}",{prefix_num},"{_course_reqs(course, pre)}","{_course_reqs(course, co)}","{_course_reqs(course, strict_co)}",{course.credit_hours},"{course.institution}","{course.canonical_name}",'
    if term_id != "":
        c_line += f"{term_id},"
    if metrics:
        # protect against missing metrics values in course
        if (
            course.metrics["complexity"] == -1
            or course.metrics["blocking factor"] == -1
            or course.metrics["delay factor"] == -1
            or course.metrics["centrality"] == -1
        ):
            raise KeyError(
                "Cannot call course_line(metrics=True) if the curriculum's courses do not have complexity, blocking factor, delay factor, and centrality values stored in their metrics dictionary."
            )
        c_line += f'{course.metrics["complexity"]},{course.metrics["blocking factor"]},{course.metrics["delay factor"]},{course.metrics["centrality"]}'
    return c_line


def csv_line_reader(line: str, delimeter: str = ",") -> List[str]:
    quotes: bool = False
    result: List[str] = []
    item: str = ""
    for ch in line:
        if ch == '"':
            quotes = not quotes
        elif ch == delimeter and not quotes:
            result.append(item)
            item = ""
        else:
            item += ch
    if item:
        result.append(item)
    return result


def find_cell(row: pd.Series[pd.CsvInferTypes], header: str) -> str:
    if header not in row:  # I assume this means if header is not in names
        raise KeyError(f"{header} column is missing")
    cell: pd.CsvInferTypes = row[header]
    if isinstance(cell, float) and math.isnan(cell):
        return ""
    else:
        return str(cell)


def read_all_courses(
    df_courses: pd.DataFrame[pd.CsvInferTypes],
    lo_Course: Dict[int, List[LearningOutcome]] = {},
) -> Dict[int, Course]:
    course_dict: Dict[int, Course] = {}
    for _, row in df_courses.iterrows():
        c_ID: int = int(row["Course ID"])
        if c_ID in course_dict:
            raise ValueError("Course IDs must be unique")
        course_dict[c_ID] = Course(
            find_cell(row, "Course Name"),
            float(row["Credit Hours"]),
            prefix=find_cell(row, "Prefix"),
            learning_outcomes=lo_Course.get(c_ID, []),
            num=find_cell(row, "Number"),
            institution=find_cell(row, "Institution"),
            canonical_name=find_cell(row, "Canonical Name"),
            id=c_ID,
        )
    for _, row in df_courses.iterrows():
        c_ID = int(row["Course ID"])
        pre_reqs = find_cell(row, "Prerequisites")
        if pre_reqs:
            for pre_req in pre_reqs.split(";"):
                course_dict[c_ID].add_requisite(course_dict[int(pre_req)], pre)
        co_reqs = find_cell(row, "Corequisites")
        if co_reqs:
            for co_req in co_reqs.split(";"):
                course_dict[c_ID].add_requisite(course_dict[int(co_req)], co)
        sco_reqs = find_cell(row, "Strict-Corequisites")
        if sco_reqs:
            for sco_req in sco_reqs.split(";"):
                course_dict[c_ID].add_requisite(course_dict[int(sco_req)], strict_co)
    return course_dict


def read_courses(
    df_courses: pd.DataFrame[pd.CsvInferTypes], all_courses: Dict[int, Course]
) -> Dict[int, Course]:
    course_dict: Dict[int, Course] = {}
    for _, row in df_courses.iterrows():
        c_ID: int = int(row["Course ID"])
        course_dict[c_ID] = all_courses[c_ID]
    return course_dict


def read_terms(
    df_courses: pd.DataFrame[pd.CsvInferTypes],
    course_dict: Dict[int, Course],
    course_arr: List[Course],
):
    terms: Dict[int, List[Course]] = {}
    have_term: List[Course] = []
    not_have_term: List[Course] = []
    for _, row in df_courses.iterrows():
        c_ID = int(find_cell(row, "Course ID"))
        term_ID = int(find_cell(row, "Term") or -1)
        for course in course_arr:
            if course_dict[c_ID].id == course.id:  # This could be simplified with logic
                if term_ID != -1:  # operations rather than four if statemnts
                    have_term.append(course)
                    if term_ID in terms:
                        terms[term_ID].append(course)
                    else:
                        terms[term_ID] = [course]
                else:
                    not_have_term.append(course)
                break
    terms_arr = [
        Term(terms[term].copy() if term in terms else [])
        for term in range(1, len(terms) + 1)
    ]
    if not_have_term:
        return terms_arr, have_term, not_have_term
    else:
        return terms_arr


def generate_course_lo(
    df_learning_outcomes: pd.DataFrame[pd.CsvInferTypes],
) -> Dict[int, List[LearningOutcome]]:
    lo_dict: Dict[int, LearningOutcome] = {}
    for _, row in df_learning_outcomes.iterrows():
        lo_ID = int(row["Learning Outcome ID"])
        if lo_ID in lo_dict:
            raise ValueError("Learning Outcome ID must be unique")
        lo_dict[lo_ID] = LearningOutcome(
            find_cell(row, "Learning Outcome"),
            find_cell(row, "Description"),
            int(row["Hours"]),
        )
    for _, row in df_learning_outcomes.iterrows():
        lo_ID = int(row["Learning Outcome ID"])
        reqs = find_cell(row, "Requisites")
        if reqs:
            for req in reqs:
                # adds all requisite courses for the learning outcome as prerequisites
                lo_dict[lo_ID].add_lo_requisite(lo_dict[req], pre)
    lo_Course: Dict[int, List[LearningOutcome]] = {}
    for _, row in df_learning_outcomes.iterrows():
        c_ID = find_cell(row, "Course ID")
        lo_ID = find_cell(row, "Learning Outcome ID")
        if c_ID in lo_Course:
            lo_Course[c_ID].append(lo_dict[lo_ID])
        else:
            lo_Course[c_ID] = [lo_dict[lo_ID]]
    return lo_Course


def generate_curric_lo(
    df_curric_lo: pd.DataFrame[pd.CsvInferTypes],
) -> List[LearningOutcome]:
    learning_outcomes: List[LearningOutcome] = []
    for _, row in df_curric_lo.iterrows():
        lo_name = find_cell(row, "Learning Outcome")
        lo_description = find_cell(row, "Description")
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
                lo_ID = lo.id
                lo_name = lo.name
                lo_desc = lo.description
                lo_prereq = '"'
                for requesite in lo.requisites.keys():
                    lo_prereq = lo_prereq + str(requesite) + ";"
                lo_prereq = lo_prereq[:-1]
                if lo_prereq:
                    lo_prereq = lo_prereq + '"'
                lo_hours = lo.hours
                lo_line = (
                    "\n"
                    + str(course_ID)
                    + ","
                    + str(lo_ID)
                    + ',"'
                    + str(lo_name)
                    + '","'
                    + str(lo_desc)
                    + '","'
                    + str(lo_prereq)
                    + '",'
                    + str(lo_hours)
                    + ",,,,,"
                )
                csv_file.write(lo_line)
    if curric.learning_outcomes:
        csv_file.write("\nCurriculum Learning Outcomes,,,,,,,,,,")
        csv_file.write("\nLearning Outcome,Description,,,,,,,,,")
        for lo in curric.learning_outcomes:
            lo_name = lo.name
            lo_desc = lo.description
            lo_line = '\n"' + str(lo_name) + '","' + str(lo_desc) + '",,,,,,,,,'
            csv_file.write(lo_line)
