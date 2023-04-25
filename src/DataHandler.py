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
from typing import Dict, List, Literal, Optional, Union
from src.CSVUtilities import csv_line_reader, read_all_courses, remove_empty_lines
from src.CurricularAnalytics import (
    blocking_factor,
    centrality,
    complexity,
    delay_factor,
)
from src.DataTypes.Course import Course
from src.DataTypes.Curriculum import Curriculum
from src.DataTypes.DataTypes import quarter, semester
from src.DataTypes.DegreePlan import DegreePlan
from src.DataTypes.LearningOutcome import LearningOutcome


def read_csv(raw_file_path: str):
    file_path = remove_empty_lines(raw_file_path)
    if isinstance(file_path, bool) and not file_path:
        return False
    # dict_curric_degree_type = Dict("AA"=>AA, "AS"=>AS, "AAS"=>AAS, "BA"=>BA, "BS"=>BS, ""=>BS)
    dict_curric_system = {"semester": semester, "quarter": quarter, "": semester}
    dp_name = ""
    dp_add_courses: List[Course] = []
    curric_name = ""
    curric_inst = ""
    curric_dtype = "BS"
    curric_stype = dict_curric_system["semester"]
    curric_CIP = ""
    courses_header = 1
    course_count = 0
    additional_course_start = 0
    additional_course_count = 0
    learning_outcomes_start = 0
    learning_outcomes_count = 0
    curric_learning_outcomes_start = 0
    curric_learning_outcomes_count = 0
    part_missing_term = False
    output = ""
    # Open the CSV file and read in the basic information such as the type (curric or degreeplan), institution, degree type, etc
    with open(file_path) as csv_file:
        read_line = csv_line_reader(csv_file.readline(), ",")
        courses_header += 1
        if read_line[0] == "Curriculum":
            curric_name = read_line[1]
            read_line = csv_line_reader(csv_file.readline(), ",")
            is_dp = read_line[0] == "Degree Plan"
            if is_dp:
                dp_name = read_line[1]
                read_line = csv_line_reader(csv_file.readline(), ",")
                courses_header += 1
            if read_line[0] == "Institution":
                curric_inst = read_line[1]
                read_line = csv_line_reader(csv_file.readline(), ",")
                courses_header += 1
            if read_line[0] == "Degree Type":
                curric_dtype = read_line[1]
                read_line = csv_line_reader(csv_file.readline(), ",")
                courses_header += 1
            if read_line[0] == "System Type":
                curric_stype = dict_curric_system[lowercase(read_line[1])]
                read_line = csv_line_reader(csv_file.readline(), ",")
                courses_header += 1
            if read_line[0] == "CIP":
                curric_CIP = read_line[1]
                read_line = csv_line_reader(csv_file.readline(), ",")
                courses_header += 1
            if read_line[0] == "Courses":
                courses_header += 1
            else:
                print("Could not find Courses")
                return False

        # File isn't formatted correctly, couldn't find the curriculum field in Col A Row 1
        else:
            print("Could not find a Curriculum")
            return False

        # This is the row containing Course ID, Course Name, Prefix, etc
        read_line = csv_line_reader(csv_file.readline(), ",")

        # Checks that all courses have an ID, and counts the total number of courses
        while (
            len(read_line) > 0
            and read_line[0] != "Additional Courses"
            and read_line[0] != "Course Learning Outcomes"
            and read_line[0] != "Curriculum Learning Outcomes"
            and not read_line[0].startswith("#")
        ):
            # Enforce that each course has an ID
            if len(read_line[0]) == 0:
                if not any(x != "" for x in read_line):
                    read_line = csv_line_reader(csv_file.readline(), ",")
                    continue
                print("All courses must have a Course ID (1)")
                return False

            # Enforce that each course has an associated term if the file is a degree plan
            if is_dp:
                if len(read_line) == 10:
                    raise Exception(
                        "Each Course in a Degree Plan must have an associated term."
                        + f"\nCourse with ID '{read_line[0]}' ({read_line[1]}) has no term."
                    )
                elif read_line[10] == 0:
                    raise Exception(
                        "Each Course in a Degree Plan must have an associated term."
                        + f"\nCourse with ID '{read_line[0]}' ({read_line[1]}) has no term."
                    )

            course_count += 1
            read_line = csv_line_reader(csv_file.readline(), ",")

        df_courses = DataFrame(
            CSV.File(
                file_path,
                header=courses_header,
                limit=course_count - 1,
                delim=",",
                silencewarnings=True,
            )
        )
        if nrow(df_courses) != nrow(unique(df_courses, Symbol("Course ID"))):
            print("All courses must have a unique Course ID (2)")
            return False
        if not is_dp and Symbol("Term") in names(df_courses):
            print("Curriculum cannot have term information.")
            return False
        df_all_courses = DataFrame()
        df_additional_courses = DataFrame()
        if len(read_line) > 0 and read_line[0] == "Additional Courses":
            if not is_dp:
                print("Only Degree Plan can have additional courses")
                return False
            end
            additional_course_start = courses_header + course_count + 1
            read_line = csv_line_reader(csv_file.readline(), ",")
            while (
                length(read_line) > 0
                and read_line[0] != "Course Learning Outcomes"
                and read_line[0] != "Curriculum Learning Outcomes"
                and not read_line[0].startswith("#")
            ):
                additional_course_count += 1
                read_line = csv_line_reader(csv_file.readline(), ",")
        if additional_course_count > 1:
            df_additional_courses = DataFrame(
                CSV.File(
                    file_path,
                    header=additional_course_start,
                    limit=additional_course_count - 1,
                    delim=",",
                    silencewarnings=True,
                )
            )
            df_all_courses = vcat(df_courses, df_additional_courses)
        else:
            df_all_courses = df_courses

        df_course_learning_outcomes = ""
        if len(read_line) > 0 and read_line[0] == "Course Learning Outcomes":
            learning_outcomes_start = (
                additional_course_start + additional_course_count + 1
            )
            read_line = csv_line_reader(csv_file.readline(), ",")
            while (
                len(read_line) > 0
                and not read_line[0].startswith("#")
                and read_line[0] != "Curriculum Learning Outcomes"
            ):
                learning_outcomes_count += 1
                read_line = csv_line_reader(csv_file.readline(), ",")
            if learning_outcomes_count > 1:
                df_course_learning_outcomes = DataFrame(
                    CSV.File(
                        file_path,
                        header=learning_outcomes_start,
                        limit=learning_outcomes_count - 1,
                        delim=",",
                        silencewarnings=True,
                    )
                )
        course_learning_outcomes: Dict[int, List[LearningOutcome]] = {}
        if df_course_learning_outcomes != "":
            course_learning_outcomes = generate_course_lo(df_course_learning_outcomes)
            if (
                isinstance(course_learning_outcomes, bool)
                and not course_learning_outcomes
            ):
                return False

        df_curric_learning_outcomes = ""
        if len(read_line) > 0 and read_line[0] == "Curriculum Learning Outcomes":
            curric_learning_outcomes_start = (
                learning_outcomes_start + learning_outcomes_count + 1
            )
            read_line = csv_line_reader(csv_file.readline(), ",")
            while len(read_line) > 0 and not read_line[0].startswith("#"):
                curric_learning_outcomes_count += 1
                read_line = csv_line_reader(csv_file.readline(), ",")
            if learning_outcomes_count > 1:
                df_curric_learning_outcomes = DataFrame(
                    CSV.File(
                        file_path,
                        header=curric_learning_outcomes_start,
                        limit=curric_learning_outcomes_count - 1,
                        delim=",",
                        silencewarnings=True,
                    )
                )

        curric_learning_outcomes = (
            generate_curric_lo(df_curric_learning_outcomes)
            if df_curric_learning_outcomes != ""
            else []
        )

        if is_dp:
            all_courses = read_all_courses(df_all_courses, course_learning_outcomes)
            if isinstance(all_courses, bool) and not all_courses:
                return False
            all_courses_arr = [course[1] for course in all_courses]
            additional_courses = read_courses(df_additional_courses, all_courses)
            ac_arr = []
            for course in additional_courses:
                ac_arr.append(course[1])
            curric = Curriculum(
                curric_name,
                all_courses_arr,
                learning_outcomes=curric_learning_outcomes,
                degree_type=curric_dtype,
                system_type=curric_stype,
                institution=curric_inst,
                CIP=curric_CIP,
            )
            terms = read_terms(df_all_courses, all_courses, all_courses_arr)
            # If some courses has term informations but some does not
            if isinstance(terms, tuple):
                # Add curriculum to the output tuple
                output = (
                    *terms,
                    curric,
                    dp_name,
                    ac_arr,
                )  # ... operator enumrates the terms
            else:
                degree_plan = DegreePlan(dp_name, curric, terms, ac_arr)
                output = degree_plan
        else:
            curric_courses = read_all_courses(df_courses, course_learning_outcomes)
            if isinstance(curric_courses, bool) and not curric_courses:
                return False
            curric_courses_arr = [course[1] for course in curric_courses]
            curric = Curriculum(
                curric_name,
                curric_courses_arr,
                learning_outcomes=curric_learning_outcomes,
                degree_type=curric_dtype,
                system_type=curric_stype,
                institution=curric_inst,
                CIP=curric_CIP,
            )
            output = curric
    # Current file is the temp file created by remove_empty_lines(), remove the file.
    if file_path[-8:] == "_temp.csv":
        # GC.gc() # TODO
        os.remove(file_path)
    return output


def write_csv_curriculum(
    curric: Curriculum, file_path: str, iostream: bool = False, metrics: bool = False
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
    metrics=False,
) -> None:
    # dict_curric_degree_type = Dict(AA=>"AA", AS=>"AS", AAS=>"AAS", BA=>"BA", BS=>"BS")
    dict_curric_system = {semester: "semester", quarter: "quarter"}
    # Write Curriculum Name
    if is_degree_plan:
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
    csv_file.write(urric_dtype)

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
    curric_CIP = "\nCIP," + '"' + str(curric.CIP) + '"' + ",,,,,,,,,"
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
    if is_degree_plan:
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
