"""
CSV Read / Write Functionality
"""

import os
from collections import defaultdict
from io import StringIO, TextIOWrapper
from typing import Dict, List, Literal, Optional, Tuple, Union, overload

import pandas as pd

from .csv_utilities import (
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
from .types.course import Course
from .types.curriculum import Curriculum
from .types.data_types import quarter, semester
from .types.degree_plan import DegreePlan, Term
from .types.learning_outcome import LearningOutcome

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
    """
    Read (i.e., deserialize) a CSV file containing either a curriculum or a degree plan, and returns a corresponding
    :class:`Curriculum` or :class:`DegreePlan` data object. The required format for curriculum or degree plan CSV files is
    described in :ref:`persistence`.

    Args:
        file_path: The relative or absolute path to the CSV file.

    Examples:
        >>> c = read_csv("./mydata/UBW_curric.csv")
        >>> assert isinstance(c, Curriculum)
        >>> dp = read_csv("./mydata/UBW_plan.csv")
        >>> assert isinstance(dp, DegreePlan)
    """
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
            skip_rows: int = rows_read
            read_line: List[str] = readline()

            # Checks that all courses have an ID, and counts the total number of courses
            while (
                read_line
                and read_line[0] not in section_keys
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
                file_path,
                header=skip_rows,
                nrows=rows_read - 2 - skip_rows,
                delimiter=",",
                dtype=defaultdict(
                    lambda: str,
                    {
                        "Course ID": int,
                        "Credit Hours": float,
                        "Term": int,
                        "Complexity": float,
                        "Blocking": int,
                        "Delay": int,
                        "Centrality": int,
                        "Learning Outcome ID": int,
                        "Hours": int,
                    },
                ),
            )
            if key == "Courses":
                if frames[key].shape[0] != frames[key].nunique()["Course ID"]:
                    raise ValueError("All courses must have a unique Course ID (2)")
                if not is_dp and "Term" in frames[key].columns:
                    raise ValueError("Curriculum cannot have term information.")

            key = read_line[0] if read_line else ""

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
            frames["Additional Courses"]
            if "Additional Courses" in frames
            else pd.DataFrame(),
            all_courses,
        )
        curric = Curriculum(
            header_fields["Curriculum"],
            list(all_courses.values()),
            learning_outcomes=curric_learning_outcomes,
            degree_type=header_fields["Degree Type"],
            system_type=dict_curric_system[header_fields["System Type"].lower()],
            institution=header_fields["Institution"],
            cip=header_fields["CIP"],
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
            return DegreePlan(
                header_fields["Degree Plan"],
                curric,
                terms,
                list(additional_courses.values()),
            )
    else:
        return Curriculum(
            header_fields["Curriculum"],
            list(
                read_all_courses(frames["Courses"], course_learning_outcomes).values()
            ),
            learning_outcomes=curric_learning_outcomes,
            degree_type=header_fields["Degree Type"],
            system_type=dict_curric_system[header_fields["System Type"].lower()],
            institution=header_fields["Institution"],
            cip=header_fields["CIP"],
        )


@overload
def write_csv(
    program: Union[Curriculum, DegreePlan],
    *,
    metrics: bool = False,
) -> StringIO:
    ...


@overload
def write_csv(
    program: Union[Curriculum, DegreePlan],
    file_path: str,
    *,
    metrics: bool = False,
) -> None:
    ...


def write_csv(
    program: Union[Curriculum, DegreePlan],
    file_path: Optional[str] = None,
    *,
    metrics: bool = False,
) -> Optional[StringIO]:
    """
    Write (i.e., serialize) a :class:`Curriculum` or :class:`DegreePlan` data object to disk as a CSV file. To read
    (i.e., deserialize) a curriculum CSV file, use the corresponding :func:`read_csv` function.
    The file format used to store curricula is described in :ref:`persistence`.

    Args:
        c: The :class:`Curriculum` or :class:`DegreePlan` data object to be serialized.
        file_path: The absolute or relative path where the CSV file will be stored. If omitted, the file will be written to a `StringIO` and returned.
        metrics: Whether to include curriculum metrics for each course in Complexity, Blocking, Delay, Centrality columns.

    Examples:
        >>> write_csv(c, "./mydata/UBW_curric.csv")
        >>> write_csv(dp, "./mydata/UBW_plan.csv")
    """
    if file_path is None:
        csv_file = StringIO()
        write_csv_content(csv_file, program, metrics=metrics)
        return csv_file
    else:
        with open(file_path, "w") as csv_file:
            write_csv_content(csv_file, program, metrics=metrics)


def write_csv_content(
    csv_file: TextIOWrapper,
    program: Union[Curriculum, DegreePlan],
    *,
    metrics: bool = False,
) -> None:
    # dict_curric_degree_type = Dict(AA=>"AA", AS=>"AS", AAS=>"AAS", BA=>"BA", BS=>"BS")
    dict_curric_system = {semester: "semester", quarter: "quarter"}
    # Grab a copy of the curriculum
    curric: Curriculum = (
        program.curriculum if isinstance(program, DegreePlan) else program
    )
    # Write Curriculum Name
    csv_file.write(f'Curriculum,"{curric.name}",,,,,,,,,')

    # Write Degree Plan Name
    if isinstance(program, DegreePlan):
        csv_file.write(f'\nDegree Plan,"{program.name}",,,,,,,,,')

    # Write Institution Name
    csv_file.write(f'\nInstitution,"{curric.institution}",,,,,,,,,')

    # Write Degree Type
    csv_file.write(f'\nDegree Type,"{curric.degree_type}",,,,,,,,,')

    # Write System Type (Semester or Quarter)
    csv_file.write(f'\nSystem Type,"{dict_curric_system[curric.system_type]}",,,,,,,,,')

    # Write CIP Code
    csv_file.write(f'\nCIP,"{curric.cip}",,,,,,,,,')

    # Define course header
    # 10 cols for curricula (no term)
    csv_file.write("\nCourses,,,,,,,,,,")
    course_header = "\nCourse ID,Course Name,Prefix,Number,Prerequisites,Corequisites,Strict-Corequisites,Credit Hours,Institution,Canonical Name"
    if isinstance(program, DegreePlan):
        # 11 cols for degree plans (including term)
        course_header += ",Term"
    if metrics:
        course_header += ",Complexity,Blocking,Delay,Centrality"
    csv_file.write(course_header)

    # Define dict to store all course learning outcomes
    all_course_lo: Dict[int, List[LearningOutcome]] = {}

    # write courses (and additional courses for degree plan)
    if isinstance(program, DegreePlan):
        # Iterate through each term and each course in the term and write them to the degree plan
        for term_id, term in enumerate(program.terms, 1):
            for course in term.courses:
                if not find_courses(program.additional_courses, course.id):
                    csv_file.write(
                        course_line(curric, course, term_id, metrics=metrics)
                    )
        # Write the additional courses section of the CSV
        csv_file.write("\nAdditional Courses,,,,,,,,,,")
        csv_file.write(course_header)
        # Iterate through each term
        for term_id, term in enumerate(program.terms, 1):
            # Iterate through each course in the current term
            for course in term.courses:
                # Check if the current course is an additional course, if so, write it here
                if find_courses(program.additional_courses, course.id):
                    csv_file.write(
                        course_line(curric, course, term_id, metrics=metrics)
                    )
                # Check if the current course has learning outcomes, if so store them
                if course.learning_outcomes:
                    all_course_lo[course.id] = course.learning_outcomes
    else:
        # Iterate through each course in the curriculum
        for course in curric.courses:
            # Write the current course to the CSV
            csv_file.write(course_line(curric, course, metrics=metrics))
            # Check if the course has learning outcomes, if it does store them
            if course.learning_outcomes:
                all_course_lo[course.id] = course.learning_outcomes

    # Write course and curriculum learning outcomes, if any
    write_learning_outcomes(curric, csv_file, all_course_lo)
