from typing import Dict, Hashable, List, Literal, Union

import pandas as pd

from src.DataTypes.Course import Course
from src.DataTypes.DataTypes import Requisite, co, pre, strict_co
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


def _course_reqs(course: Course, requisite: Requisite) -> str:
    reqs = ";".join(
        str(
            course_id
            for course_id, req_type in course.requisites.items()
            if req_type == requisite
        )
    )
    return f'"{reqs}"' if reqs else ""


def course_line(
    course: Course, term_id: Union[str, int], *, metrics: bool = False
) -> str:
    c_line: str = f'\n{course.id},"{course.name}","{course.prefix}","{course.num}","{_course_reqs(course, pre)}","{_course_reqs(course, co)}","{_course_reqs(course, strict_co)}",{course.credit_hours},"{course.institution}","{course.canonical_name}",'
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


def find_cell(row: pd.Series[str], header: str) -> str:
    if header not in row:  # I assume this means if header is not in names
        raise Exception(f"{header} column is missing")
    # elif row[header] is None:
    #     return ""
    else:
        return row[header]


def read_all_courses(
    df_courses: pd.DataFrame[pd.CsvInferTypes],
    lo_Course: Dict[int, List[LearningOutcome]] = {},
) -> Dict[int, Course]:
    course_dict: Dict[int, Course] = {}
    for _, row in df_courses.iterrows():
        c_ID = row["Course ID"]
        c_Name = find_cell(row, "Course Name")
        c_Credit = row["Credit Hours"]
        c_Credit = float(c_Credit) if isinstance(c_Credit, str) else c_Credit
        c_Prefix = str(row[(("Prefix"))])
        c_Number = find_cell(row, ("Number"))
        # if not isinstance(c_Number, str):
        #     c_Number = str(c_Number)
        c_Inst = row[("Institution")]
        c_col_name = row[("Canonical Name")]
        learning_outcomes = lo_Course[c_ID] if c_ID in lo_Course else []
        if c_ID in course_dict:
            print("Course IDs must be unique")
            return False
        else:
            course_dict[c_ID] = Course(
                c_Name,
                c_Credit,
                prefix=c_Prefix,
                learning_outcomes=learning_outcomes,
                num=c_Number,
                institution=c_Inst,
                canonical_name=c_col_name,
                id=c_ID,
            )
    for _, row in df_courses.iterrows():
        c_ID = row["Course ID"]
        pre_reqs = row("Prerequisites")
        if pre_reqs != "":
            for pre_req in str(pre_reqs).split(";"):
                add_requisite(course_dict[parse(Int, pre_req)], course_dict[c_ID], pre)
        co_reqs = row("Corequisites")
        if co_reqs != "":
            for co_req in str(co_reqs).split(";"):
                add_requisite(course_dict[parse(Int, co_req)], course_dict[c_ID], co)
        sco_reqs = row("Strict-Corequisites")
        if sco_reqs != "":
            for sco_req in str(sco_reqs).split(";"):
                add_requisite(
                    course_dict[parse(Int, sco_req)], course_dict[c_ID], strict_co
                )
    return course_dict
