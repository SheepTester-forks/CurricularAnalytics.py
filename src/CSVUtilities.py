from typing import Dict, List, Literal, Union

import pandas as pd

from src.DataTypes.Course import Course
from src.DataTypes.DataTypes import co, pre, strict_co
from src.DataTypes.LearningOutcome import LearningOutcome


def readfile(file_path: str) -> List[str]:
    with open(file_path) as f:
        return f.readlines()


def remove_empty_lines(file_path: str) -> Union[str, Literal[False]]:
    if file_path[-4:] != ".csv":
        print("Input is not a csv file")
        return False
    temp_file = file_path[:-4] + "_temp.csv"
    file = readfile(file_path)
    with open(temp_file, "w") as f:
        new_file = ""
        for line in file:
            line = line.replace("\r", "")
            if len(line) > 0 and not line.replace('"', "").startswith("#"):
                line = line + "\n"
                new_file = new_file + line
        if len(new_file) > 0:
            new_file = new_file[:-1]
        f.write(new_file)
    return temp_file


def course_line(course: Course, term_id: Union[str, int], metrics: bool = False) -> str:
    course_ID = course.id
    course_name = course.name
    course_prefix = course.prefix
    course_num = course.num
    # course_vertex = course.vertex_id
    course_prereq = '"'
    course_coreq = '"'
    course_scoreq = '"'
    for requesite in course.requisites.items():
        if requesite[1] == pre:
            course_prereq = course_prereq + str(requesite[0]) + ";"
        elif requesite[1] == co:
            course_coreq = course_coreq + str(requesite[0]) + ";"
        elif requesite[1] == strict_co:
            course_scoreq = course_scoreq + str(requesite[0]) + ";"
    course_prereq = course_prereq[:-1]
    if len(course_prereq) > 0:
        course_prereq = course_prereq + '"'
    course_coreq = course_coreq[:-1]
    if len(course_coreq) > 0:
        course_coreq = course_coreq + '"'
    course_scoreq = course_scoreq[:-1]
    if len(course_scoreq) > 0:
        course_scoreq = course_scoreq + '"'
    course_chours = course.credit_hours
    course_inst = course.institution
    course_canName = course.canonical_name
    course_term = str(term_id) if isinstance(term_id, int) else term_id
    course_term = "" if course_term == "" else course_term + ","
    if metrics == False:
        c_line = (
            "\n"
            + str(course_ID)
            + ',"'
            + str(course_name)
            + '","'
            + str(course_prefix)
            + '","'
            + str(course_num)
            + '",'
            + str(course_prereq)
            + ","
            + str(course_coreq)
            + ","
            + str(course_scoreq)
            + ","
            + str(course_chours)
            + ',"'
            + str(course_inst)
            + '","'
            + str(course_canName)
            + '",'
            + course_term
        )
    else:
        # protect against missing metrics values in course
        if (
            ("complexity" not in course.metrics)
            or ("blocking factor" not in course.metrics)
            or ("delay factor" not in course.metrics)
            or ("centrality" not in course.metrics)
        ):
            raise Exception(
                "Cannot call course_line(;metrics=true) if the curriculum's courses do not have complexity, blocking factor, delay factor, and centrality values stored in their metrics dictionary."
            )
        complexity = course.metrics["complexity"]
        blocking_factor = course.metrics["blocking factor"]
        delay_factor = course.metrics["delay factor"]
        centrality = course.metrics["centrality"]
        c_line = (
            "\n"
            + str(course_ID)
            + ',"'
            + str(course_name)
            + '","'
            + str(course_prefix)
            + '","'
            + str(course_num)
            + '",'
            + str(course_prereq)
            + ","
            + str(course_coreq)
            + ","
            + str(course_scoreq)
            + ","
            + str(course_chours)
            + ',"'
            + str(course_inst)
            + '","'
            + str(course_canName)
            + '",'
            + course_term
            + str(complexity)
            + ","
            + str(blocking_factor)
            + ","
            + str(delay_factor)
            + ","
            + str(centrality)
        )
    return c_line


def csv_line_reader(line: str, delimeter: str = ",") -> List[str]:
    quotes = False
    result: List[str] = []
    item = ""
    for ch in line:
        if ch == '"':
            quotes = not quotes
        elif ch == delimeter and not quotes:
            result.append(item)
            item = ""
        else:
            item = item + str(ch)
    if len(item) > 0:
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
    df_courses: "pd.DataFrame[str]", lo_Course: Dict[int, List[LearningOutcome]] = {}
) -> Union[Dict[int, Course], Literal[False]]:
    course_dict: Dict[int, Course] = {}
    for _, row in df_courses.iterrows():
        c_ID = row["Course ID"]
        c_Name = find_cell(row, "Course Name")
        c_Credit = row["Credit Hours"]
        c_Credit = float(c_Credit)  # if isinstance(c_Credit, str) else c_Credit
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
    for row in DataFrames.eachrow(df_courses):
        c_ID = row[("Course ID")]
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
