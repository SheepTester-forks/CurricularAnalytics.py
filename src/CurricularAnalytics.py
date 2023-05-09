"""
The curriculum-based metrics in this toolbox are based upon the graph structure of a
curriculum.  Specifically, assume curriculum ``c`` consists of ``n`` courses ``\\{c_1, \\ldots, c_n\\}``,
and that there are ``m`` requisite (prerequisite or co-requsitie) relationships between these courses.
A curriculum graph ``G_c = (V,E)`` is formed by creating a vertex set ``V = \\{v_1, \\ldots, v_n\\}``
(i.e., one vertex for each course) along with an edge set ``E = \\{e_1, \\ldots, e_m\\}``, where a
directed edge from vertex ``v_i`` to ``v_j`` is in ``E`` if course ``c_i`` is a requisite for course ``c_j``.
"""

import math
from io import StringIO
from typing import List

from src.DataTypes.Course import AbstractCourse, Course
from src.DataTypes.Curriculum import Curriculum, CurriculumMetricKey


def basic_statistics(
    curricula: List["Curriculum"], metric_name: CurriculumMetricKey
) -> StringIO:
    buf = StringIO()
    # set initial values used to find min and max metric values
    total_metric = 0
    STD_metric = 0
    max_metric = -math.inf
    min_metric = math.inf
    metric = curricula[0].metrics[metric_name]
    max_metric = metric[0]
    min_metric = metric[0]
    # metric where total curricular metric as well as course-level metrics are stored in an array
    for c in curricula:
        if c.metrics[metric_name][0] == -1:
            raise Exception(
                f"metric {metric_name} does not exist in curriculum {c.name}"
            )
        c.basic_metrics()
        metric = c.metrics[metric_name]
        value = metric[
            0
        ]  # metric where total curricular metric as well as course-level metrics are stored in an array
        total_metric += value
        if value > max_metric:
            max_metric = value
        if value < min_metric:
            min_metric = value
    avg_metric = total_metric / len(curricula)
    for c in curricula:
        metric = c.metrics[metric_name]
        if isinstance(metric, float):
            value = metric
        else:
            value = metric[
                0
            ]  # metric where total curricular metric as well as course-level metrics are stored in an array
        STD_metric = (value - avg_metric) ** 2
    STD_metric = math.sqrt(STD_metric / len(curricula))
    buf.write(f"\n Metric -- {metric_name}")
    buf.write(f"\n  Number of curricula = {len(curricula)}")
    buf.write(f"\n  Mean = {avg_metric}")
    buf.write(f"\n  STD = {STD_metric}")
    buf.write(f"\n  Max. = {max_metric}")
    buf.write(f"\n  Min. = {min_metric}")
    return buf


def write_course_names(
    buf: StringIO, courses: List[AbstractCourse], *, separator: str = ", "
) -> None:
    if len(courses) == 1:
        write_course_name(buf, courses[0])
    elif courses:
        for c in courses[:-1]:
            write_course_name(buf, c)
            buf.write(separator)
        write_course_name(buf, courses[-1])


def write_course_name(buf: StringIO, c: AbstractCourse) -> None:
    if isinstance(c, Course):
        if c.prefix:
            buf.write(f"{c.prefix} ")
        if c.num:
            buf.write(f"{c.num} - ")
    buf.write(f"{c.name}")  # name is a required item


def homology(curricula: List[Curriculum], *, strict: bool = False) -> List[List[float]]:
    return [[c1.similarity(c2, strict=strict) for c2 in curricula] for c1 in curricula]
