# ==============================
# CSV Read / Write Functionality
# ==============================

"""
    read_csv(file_path:AbstractString)

Read (i.e., deserialize) a CSV file containing either a curriculum or a degree plan, and returns a corresponding
`Curriculum` or `DegreePlan` data object.  The required format for curriculum or degree plan CSV files is
described in [File Format](@ref).

# Arguments
- `file_path:AbstractString` : the relative or absolute path to the CSV file.

# Examples:
```julia-repl
julia> c = read_csv("./mydata/UBW_curric.csv")
julia> dp = read_csv("./mydata/UBW_plan.csv")
```
"""
from io import StringIO, TextIOWrapper
import os
from typing import Dict, Hashable, List, Literal, Optional, Tuple, Union

import pandas as pd
from src.CSVUtilities import (
    course_line,
    csv_line_reader,
    find_courses,
    generate_course_lo,
    generate_curric_lo,
    read_all_courses,
    read_courses,
    read_terms,
    remove_empty_lines,
    write_learning_outcomes,
)
from src.CurricularAnalytics import (
    blocking_factor,
    centrality,
    complexity,
    delay_factor,
)
from src.DataTypes.Course import Course
from src.DataTypes.Curriculum import Curriculum
from src.DataTypes.DataTypes import quarter, semester
from src.DataTypes.DegreePlan import DegreePlan, Term
from src.DataTypes.LearningOutcome import LearningOutcome

HeaderKey = Literal[
    "Curriculum",
    "Degree Plan",
    "Institution",
    "Degree Type",
    "System Type",
    "CIP",
]
header_keys: List[HeaderKey] = [
    "Curriculum",
    "Degree Plan",
    "Institution",
    "Degree Type",
    "System Type",
    "CIP",
]

SectionKey = Literal[
    "Courses",
    "Additional Courses",
    "Course Learning Outcomes",
    "Curriculum Learning Outcomes",
]
section_keys: List[SectionKey] = [
    "Courses",
    "Additional Courses",
    "Course Learning Outcomes",
    "Curriculum Learning Outcomes",
]

# dict_curric_degree_type = Dict("AA"=>AA, "AS"=>AS, "AAS"=>AAS, "BA"=>BA, "BS"=>BS, ""=>BS)
dict_curric_system = {"semester": semester, "quarter": quarter, "": semester}


def read_csv(
    raw_file_path: str,
) -> Union[
    Curriculum,
    DegreePlan,
    Tuple[List[Term], List[Course], List[Course], Curriculum, str, List[Course]],
]:
    file_path = remove_empty_lines(raw_file_path)
    header_fields: Dict[HeaderKey, str] = {}
    rows_read: int = 0
    frames: Dict[SectionKey, pd.DataFrame[pd.CsvInferTypes]] = {}
    # Open the CSV file and read in the basic information such as the type (curric or degreeplan), institution, degree type, etc
    with open(file_path) as csv_file:

        def readline() -> List[str]:
            nonlocal rows_read
            rows_read += 1
            return csv_line_reader(csv_file.readline(), ",")

        key, value, *_ = readline()
        while key in header_keys:
            header_fields[key] = value
            key, value, *_ = readline()

        # File isn't formatted correctly, couldn't find the curriculum field in Col A Row 1
        if "Curriculum" not in header_fields:
            raise ValueError("Could not find a Curriculum")

        is_dp = "Degree Plan" in header_fields

        while key in section_keys:
            if key == "Additional Courses":
                if not is_dp:
                    raise ValueError("Only Degree Plan can have additional courses")

            # This is the row containing Course ID, Course Name, Prefix, etc
            read_line: List[str] = readline()
            skip_rows: int = rows_read

            # Checks that all courses have an ID, and counts the total number of courses
            while (
                len(read_line) > 0
                and key not in section_keys
                and not read_line[0].startswith("#")
            ):
                if key == "Courses":
                    # Enforce that each course has an ID
                    if not read_line[0]:
                        if all(x == "" for x in read_line):
                            read_line = readline()
                            continue
                        raise ValueError("All courses must have a Course ID (1)")

                    # Enforce that each course has an associated term if the file is a degree plan
                    if is_dp:
                        if len(read_line) == 10 or not read_line[10]:
                            raise ValueError(
                                "Each Course in a Degree Plan must have an associated term."
                                + f"\nCourse with ID '{read_line[0]}' ({read_line[1]}) has no term."
                            )

                read_line = readline()

            frames[key] = pd.read_csv(
                file_path, header=skip_rows, nrows=rows_read - skip_rows, delimiter=","
            )
            if key == "Courses":
                if frames[key].shape[0] != frames[key].nunique()["Course ID"]:
                    raise ValueError("All courses must have a unique Course ID (2)")
                if not is_dp and "Term" in frames[key].columns:
                    raise ValueError("Curriculum cannot have term information.")

            key = read_line[0]

    # Current file is the temp file created by remove_empty_lines(), remove the file.
    if file_path[-8:] == "_temp.csv":
        os.remove(file_path)

    if "Courses" not in frames:
        raise ValueError("Could not find Courses")
    df_all_courses: pd.DataFrame[pd.CsvInferTypes] = (
        pd.concat(
            [frames["Courses"], frames["Additional Courses"]],
        )
        if "Additional Courses" in frames
        else frames["Courses"]
    )
    course_learning_outcomes: Dict[int, List[LearningOutcome]] = (
        generate_course_lo(frames["Course Learning Outcomes"])
        if "Course Learning Outcomes" in frames
        else {}
    )
    curric_learning_outcomes: List[LearningOutcome] = (
        generate_curric_lo(frames["Curriculum Learning Outcomes"])
        if "Curriculum Learning Outcomes" in frames
        else []
    )

    if is_dp:
        all_courses = read_all_courses(df_all_courses, course_learning_outcomes)
        additional_courses = read_courses(
            frames["Additional Courses"] or pd.DataFrame(), all_courses
        )
        curric = Curriculum(
            header_fields["Curriculum"],
            list(all_courses.values()),
            learning_outcomes=curric_learning_outcomes,
            degree_type=header_fields["Degree Type"],
            system_type=dict_curric_system[header_fields["System Type"].lower()],
            institution=header_fields["Institution"],
            CIP=header_fields["CIP"],
        )
        terms = read_terms(df_all_courses, all_courses, list(all_courses.values()))
        # If some courses has term informations but some does not
        if isinstance(terms, tuple):
            # Add curriculum to the output tuple
            return (
                *terms,  # * operator enumrates the terms
                curric,
                header_fields["Degree Plan"],
                list(additional_courses.values()),
            )
        else:
            degree_plan = DegreePlan(
                header_fields["Degree Plan"],
                curric,
                terms,
                list(additional_courses.values()),
            )
            return degree_plan
    else:
        curric_courses = read_all_courses(frames["Courses"], course_learning_outcomes)
        curric = Curriculum(
            header_fields["Curriculum"],
            list(curric_courses.values()),
            learning_outcomes=curric_learning_outcomes,
            degree_type=header_fields["Degree Type"],
            system_type=dict_curric_system[header_fields["System Type"].lower()],
            institution=header_fields["Institution"],
            CIP=header_fields["CIP"],
        )
        return curric


def write_csv_curriculum(
    curric: Curriculum, file_path: str, *, iostream: bool = False, metrics: bool = False
) -> Union[StringIO, Literal[True]]:
    """
        write_csv(c:Curriculum, file_path:AbstractString)

    Write (i.e., serialize) a `Curriculum` data object to disk as a CSV file. To read
    (i.e., deserialize) a curriculum CSV file, use the corresponding `read_csv` function.
    The file format used to store curricula is described in [File Format](@ref).

    # Arguments
    - `c:Curriculum` : the `Curriculum` data object to be serialized.
    - `file_path:AbstractString` : the absolute or relative path where the CSV file will be stored.

    # Examples:
    ```julia-repl
    julia> write_csv(c, "./mydata/UBW_curric.csv")
    ```
    """
    if iostream == True:
        csv_file = StringIO()
        write_csv_content(csv_file, curric, False, metrics=metrics)
        return csv_file
    else:
        with open(file_path, "w") as csv_file:
            write_csv_content(csv_file, curric, False, metrics=metrics)
        return True


# TODO - Reduce duplicated code between this and the curriculum version of the function
"""
    write_csv(dp:DegreePlan, file_path:AbstractString)

Write (i.e., serialize) a `DegreePlan` data object to disk as a CSV file. To read
(i.e., deserialize) a degree plan CSV file, use the corresponding `read_csv` function.
The file format used to store degree plans is described in [File Format](@ref).

# Arguments
- `dp:DegreePlan` : the `DegreePlan` data object to be serialized.
- `file_path:AbstractString` : the absolute or relative path where the CSV file will be stored.

# Examples:
```julia-repl
julia> write_csv(dp, "./mydata/UBW_plan.csv")
```
"""


def write_csv_degree_plan(
    original_plan: DegreePlan,
    file_path: str,
    iostream: bool = False,
    metrics: bool = False,
) -> Optional[Literal[True]]:
    if iostream:
        csv_file = StringIO()  # TODO: I think it's supposed to return this
        write_csv_content(csv_file, original_plan, True, metrics=metrics)
    else:
        with open(file_path, "w") as csv_file:
            write_csv_content(csv_file, original_plan, True, metrics=metrics)
        return True


def write_csv_content(
    csv_file: TextIOWrapper,
    program: Union[Curriculum, DegreePlan],
    is_degree_plan: bool,
    *,
    metrics: bool = False,
) -> None:
    # dict_curric_degree_type = Dict(AA=>"AA", AS=>"AS", AAS=>"AAS", BA=>"BA", BS=>"BS")
    dict_curric_system = {semester: "semester", quarter: "quarter"}
    curric: Curriculum
    # Write Curriculum Name
    if isinstance(program, DegreePlan):
        # Grab a copy of the curriculum
        curric = program.curriculum
        curric_name = "Curriculum," + '"' + str(curric.name) + '"' + ",,,,,,,,,"
    else:
        curric = program
        curric_name = "Curriculum," + str(curric.name) + ",,,,,,,,,"
    csv_file.write(curric_name)

    # Write Degree Plan Name
    if is_degree_plan:
        dp_name = "\nDegree Plan," + '"' + str(program.name) + '"' + ",,,,,,,,,"
        csv_file.write(dp_name)

    # Write Institution Name
    curric_ins = "\nInstitution," + '"' + str(curric.institution) + '"' + ",,,,,,,,,"
    csv_file.write(curric_ins)

    # Write Degree Type
    curric_dtype = "\nDegree Type," + '"' + str(curric.degree_type) + '"' + ",,,,,,,,,"
    csv_file.write(curric_dtype)

    # Write System Type (Semester or Quarter)
    curric_stype = (
        "\nSystem Type,"
        + '"'
        + str(dict_curric_system[curric.system_type])
        + '"'
        + ",,,,,,,,,"
    )
    csv_file.write(curric_stype)

    # Write CIP Code
    curric_CIP = "\nCIP," + '"' + str(curric.cip) + '"' + ",,,,,,,,,"
    csv_file.write(curric_CIP)

    # Define course header
    if is_degree_plan:
        if metrics:
            course_header = "\nCourse ID,Course Name,Prefix,Number,Prerequisites,Corequisites,Strict-Corequisites,Credit Hours,Institution,Canonical Name,Term,Complexity,Blocking,Delay,Centrality"
        else:
            # 11 cols for degree plans (including term)
            course_header = "\nCourse ID,Course Name,Prefix,Number,Prerequisites,Corequisites,Strict-Corequisites,Credit Hours,Institution,Canonical Name,Term"
    else:
        if metrics:
            course_header = "\nCourse ID,Course Name,Prefix,Number,Prerequisites,Corequisites,Strict-Corequisites,Credit Hours,Institution,Canonical Name,Complexity,Blocking,Delay,Centrality"
        else:
            # 10 cols for curricula (no term)
            course_header = "\nCourse ID,Course Name,Prefix,Number,Prerequisites,Corequisites,Strict-Corequisites,Credit Hours,Institution,Canonical Name"
    csv_file.write("\nCourses,,,,,,,,,,")
    csv_file.write(course_header)

    # Define dict to store all course learning outcomes
    all_course_lo: Dict[int, List[LearningOutcome]] = {}

    # if metrics is true ensure that all values are present before writing courses
    if metrics:
        complexity(curric)
        blocking_factor(curric)
        delay_factor(curric)
        centrality(curric)

    # write courses (and additional courses for degree plan)
    if isinstance(program, DegreePlan):
        # Iterate through each term and each course in the term and write them to the degree plan
        for term_id, term in enumerate(program.terms):
            for course in term.courses:
                if not hasattr(program, "additional_courses") or not find_courses(
                    program.additional_courses, course.id
                ):
                    csv_file.write(course_line(course, term_id, metrics=metrics))
        # Check if the original plan has additional courses defined
        if not hasattr(program, "additional_courses"):
            # Write the additional courses section of the CSV
            csv_file.write("\nAdditional Courses,,,,,,,,,,")
            csv_file.write(course_header)
            # Iterate through each term
            for term_id, term in enumerate(program.terms):
                # Iterate through each course in the current term
                for course in term.courses:
                    # Check if the current course is an additional course, if so, write it here
                    if find_courses(program.additional_courses, course.id):
                        csv_file.write(course_line(course, term_id, metrics=metrics))
                    # Check if the current course has learning outcomes, if so store them
                    if len(course.learning_outcomes) > 0:
                        all_course_lo[course.id] = course.learning_outcomes
    else:
        # Iterate through each course in the curriculum
        for course in curric.courses:
            # Write the current course to the CSV
            csv_file.write(course_line(course, "", metrics=metrics))
            # Check if the course has learning outcomes, if it does store them
            if len(course.learning_outcomes) > 0:
                all_course_lo[course.id] = course.learning_outcomes

    # Write course and curriculum learning outcomes, if any
    write_learning_outcomes(curric, csv_file, all_course_lo)
