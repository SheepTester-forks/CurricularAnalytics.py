"""
The curriculum-based metrics in this toolbox are based upon the graph structure of a
curriculum.  Specifically, assume curriculum ``c`` consists of ``n`` courses ``\\{c_1, \\ldots, c_n\\}``,
and that there are ``m`` requisite (prerequisite or co-requsitie) relationships between these courses.
A curriculum graph ``G_c = (V,E)`` is formed by creating a vertex set ``V = \\{v_1, \\ldots, v_n\\}``
(i.e., one vertex for each course) along with an edge set ``E = \\{e_1, \\ldots, e_m\\}``, where a
directed edge from vertex ``v_i`` to ``v_j`` is in ``E`` if course ``c_i`` is a requisite for course ``c_j``.
"""

from io import StringIO
import math
from queue import Queue
from typing import FrozenSet, List, Literal, Optional, Tuple, Union, overload

import networkx as nx
from src.DataTypes.Course import AbstractCourse, Course
from src.DataTypes.Curriculum import (
    Curriculum,
    CurriculumMetricKey,
)
from src.DataTypes.DataTypes import System, co, quarter, semester, strict_co
from src.DataTypes.DegreePlan import DegreePlan
from src.DataTypes.LearningOutcome import LearningOutcome
from src.GraphAlgs import (
    all_paths,
    edge_crossings,
    longest_paths as longest_paths_graph,
    reachable_from,
)

# TODO:
# export AA, AAS, AS, AbstractCourse, AbstractRequirement, BA, BS, Course, CourseCollection, CourseCatalog, CourseRecord, CourseSet, Curriculum, DegreePlan,
#         EdgeClass, Enrollment, Grade, LearningOutcome, PassRate, RequirementSet, Requisite, Student, StudentRecord, Simulation, System, Term, TransferArticulation,
#         add_course!, add_lo_requisite!, add_requisite!, add_transfer_catalog, add_transfer_course, all_paths, back_edge, basic_metrics, basic_statistics,
#         bin_filling, blocking_factor, centrality, co, compare_curricula, convert_ids, complexity, course, course_from_id, course_from_vertex, course_id,
#         courses_from_vertices, create_degree_plan, cross_edge, dead_ends, delay_factor, delete_requisite!, dfs, extraneous_requisites, find_term, forward_edge,
#         gad, grade, homology, is_duplicate, isvalid_curriculum, isvalid_degree_plan, longest_path, longest_paths, merge_curricula, pass_table, passrate_table,
#         pre, print_plan, quarter, reach, reach_subgraph, reachable_from, reachable_from_subgraph, reachable_to, reachable_to_subgraph, read_csv, requisite_distance,
#         requisite_type, semester, set_passrates, set_passrate_for_course, set_passrates_from_csv, similarity, simple_students, simulate, simulation_report,
#         strict_co, topological_sort, total_credits, transfer_equiv, tree_edge, write_csv, knowledge_transfer, csv_stream

# Check if a curriculum graph has requisite cycles.

MatchCriterion = Literal["prefix", "num", "name", "canonical name", "credit hours"]


def extraneous_requisites(c: Curriculum, *, debug: bool = False) -> List[List[int]]:
    """
        extraneous_requisites(c:Curriculum; print=false)

    Determines whether or not a curriculum `c` contains extraneous requisites, and returns them.  Extraneous requisites
    are redundant requisites that are unnecessary in a curriculum.  For example, if a curriculum has the prerequisite
    relationships $c_1 \\rightarrow c_2 \\rightarrow c_3$ and $c_1 \\rightarrow c_3$, and $c_1$ and $c_2$ are
    *not* co-requisites, then $c_1 \\rightarrow c_3$ is redundant and therefore extraneous.
    """
    try:
        nx.find_cycle(c.graph)
        raise Exception(
            "\nCurriculm graph has cycles, extraneous requisities cannot be determined."
        )
    except nx.NetworkXNoCycle:
        pass
    msg = StringIO()
    redundant_reqs: List[List[int]] = []
    g = c.graph
    que: Queue[int] = Queue()
    components = nx.weakly_connected_components(g)
    extraneous = False
    string = ""  # create an empty string to hold messages
    for wcc in components:
        if len(wcc) > 1:  # only consider components with more than one vertex
            for u in wcc:
                nb = g.neighbors(u)
                for n in nb:
                    que.put(n)
                while not que.empty():
                    x = que.get()
                    nnb = g.neighbors(x)
                    for n in nnb:
                        que.put(n)
                    for v in g.neighbors(x):
                        if g.has_edge(u, v):  # possible redundant requsisite
                            # TODO: If this edge is a co-requisite it is an error, as it would be impossible to satsify.
                            # This needs to be checked here.
                            remove: bool = True
                            for n in nb:  # check for co- or strict_co requisites
                                if nx.has_path(
                                    c.graph, n, v
                                ):  # is there a path from n to v?
                                    req_type = c.courses[n].requisites[
                                        c.courses[u].id
                                    ]  # the requisite relationship between u and n
                                    if (
                                        req_type == co or req_type == strict_co
                                    ):  # is u a co or strict_co requisite for n?
                                        remove = False  # a co or strict_co relationshipo is involved, must keep (u, v)
                            if remove:
                                if all(
                                    x != [c.courses[u].id, c.courses[v].id]
                                    for x in redundant_reqs
                                ):  # make sure redundant requisite wasn't previously found
                                    redundant_reqs.append(
                                        [c.courses[u].id, c.courses[v].id]
                                    )
                                    if debug:
                                        string += f"-{c.courses[v].name} has redundant requisite {c.courses[u].name}\n"
                                extraneous = True
    if extraneous and debug:
        if c.institution:
            msg.write(f"\n{c.institution}: ")
        msg.write(f"curriculum {c.name} has extraneous requisites:\n")
        msg.write(string)
    if debug == True:
        print(msg.getvalue())
    return redundant_reqs


# Compute the blocking factor of a course
def blocking_factor_course(c: Curriculum, course: int) -> int:
    """
        blocking_factor(c:Curriculum, course:Int)

    The **blocking factor** associated with course ``c_i`` in curriculum ``c`` with
    curriculum graph ``G_c = (V,E)`` is defined as:
    ```math
    b_c(v_i) = \\sum_{v_j \\in V} I(v_i,v_j)
    ```
    where ``I(v_i,v_j)`` is the indicator function, which is ``1`` if  ``v_i \\leadsto v_j``,
    and ``0`` otherwise. Here ``v_i \\leadsto v_j`` denotes that a directed path from vertex
    ``v_i`` to ``v_j`` exists in ``G_c``, i.e., there is a requisite pathway from course
    ``c_i`` to ``c_j`` in curriculum ``c``.
    """
    b = len(reachable_from(c.graph, course))
    c.courses[course].metrics["blocking factor"] = b
    return b


# Compute the blocking factor of a curriculum
def blocking_factor(c: Curriculum) -> Tuple[int, List[int]]:
    """
        blocking_factor(c:Curriculum)

    The **blocking factor** associated with curriculum ``c`` is defined as:
    ```math
    b(G_c) = \\sum_{v_i \\in V} b_c(v_i).
    ```
    where ``G_c = (V,E)`` is the curriculum graph associated with curriculum ``c``.
    """
    bf: List[int] = [blocking_factor_course(c, v) for v in c.graph.nodes]
    b: int = sum(bf)
    c.metrics["blocking factor"] = b, bf
    return b, bf


# Compute the delay factor of a course
def delay_factor_course(c: Curriculum, course: int) -> int:
    """
        delay_factor(c:Curriculum, course:Int)

    The **delay factor** associated with course ``c_k`` in curriculum ``c`` with
    curriculum graph ``G_c = (V,E)`` is the number of vertices in the longest path
    in ``G_c`` that passes through ``v_k``. If ``\\#(p)`` denotes the number of
    vertices in the directed path ``p`` in ``G_c``, then we can define the delay factor of
    course ``c_k`` as:
    ```math
    d_c(v_k) = \\max_{i,j,l,m}\\left\\{\\#(v_i  \\overset{p_l}{\\leadsto} v_k \\overset{p_m}{\\leadsto} v_j)\\right\\}
    ```
    where ``v_i \\overset{p}{\\leadsto} v_j`` denotes a directed path ``p`` in ``G_c`` from vertex
    ``v_i`` to ``v_j``.
    """
    if c.courses[course].metrics["delay factor"] == -1:
        delay_factor(c)
    return c.courses[course].metrics["delay factor"]


# Compute the delay factor of a curriculum
def delay_factor(c: Curriculum) -> Tuple[int, List[int]]:
    """
        delay_factor(c:Curriculum)

    The **delay factor** associated with curriculum ``c`` is defined as:
    ```math
    d(G_c) = \\sum_{v_k \\in V} d_c(v_k).
    ```
    where ``G_c = (V,E)`` is the curriculum graph associated with curriculum ``c``.
    """
    g = c.graph
    df: List[int] = [1] * c.num_courses
    for v in g.nodes:
        for path in all_paths(g):
            for vtx in path:
                path_length = len(
                    path
                )  # path_length in terms of # of vertices, not edges
                if path_length > df[vtx]:
                    df[vtx] = path_length
    d = 0
    for v in g.nodes:
        c.courses[v].metrics["delay factor"] = df[v]
        d += df[v]
    c.metrics["delay factor"] = d, df
    return d, df


# Compute the centrality of a course
def centrality_course(c: Curriculum, course: int) -> int:
    """
        centrality(c:Curriculum, course:Int)

    Consider a curriculum graph ``G_c = (V,E)``, and a vertex ``v_i \\in V``. Furthermore,
    consider all paths between every pair of vertices ``v_j, v_k \\in V`` that satisfy the
    following conditions:
    - ``v_i, v_j, v_k`` are distinct, i.e., ``v_i \\neq v_j, v_i \\neq v_k`` and ``v_j \\neq v_k``;
    - there is a path from ``v_j`` to ``v_k`` that includes ``v_i``, i.e., ``v_j \\leadsto v_i \\leadsto v_k``;
    - ``v_j`` has in-degree zero, i.e., ``v_j`` is a "source"; and
    - ``v_k`` has out-degree zero, i.e., ``v_k`` is a "sink".
    Let ``P_{v_i} = \\{p_1, p_2, \\ldots\\}`` denote the set of all directed paths that satisfy these
    conditions.
    Then the **centrality** of ``v_i`` is defined as
    ```math
    q(v_i) = \\sum_{l=1}^{\\left| P_{v_i} \\right|} \\#(p_l).
    ```
    where ``\\#(p)`` denotes the number of vertices in the directed path ``p`` in ``G_c``.
    """
    cent: int = 0
    g = c.graph
    for path in all_paths(g):
        # conditions: path length is greater than 2, target course must be in the path, the target vertex
        # cannot be the first or last vertex in the path
        if (
            course in path
            and len(path) > 2
            and path[0] != course
            and path[-1] != course
        ):
            cent += len(path)
    c.courses[course].metrics["centrality"] = cent
    return cent


# Compute the total centrality of all courses in a curriculum
def centrality(c: Curriculum) -> Tuple[int, List[int]]:
    """
        centrality(c:Curriculum)

    Computes the total **centrality** associated with all of the courses in curriculum ``c``,
    with curriculum graph ``G_c = (V,E)``.
    ```math
    q(c) = \\sum_{v \\in V} q(v).
    ```
    """
    cf: List[int] = [0] * c.num_courses
    for i, v in enumerate(c.graph.nodes):
        cf[i] = centrality_course(c, v)
    cent: int = sum(cf)
    c.metrics["centrality"] = cent, cf
    return cent, cf


# Compute the complexity of a course
def complexity_course(c: Curriculum, course: int) -> float:
    """
        complexity(c:Curriculum, course:Int)

    The **complexity** associated with course ``c_i`` in curriculum ``c`` with
    curriculum graph ``G_c = (V,E)`` is defined as:
    ```math
    h_c(v_i) = d_c(v_i) + b_c(v_i)
    ```
    i.e., as a linear combination of the course delay and blocking factors.
    """
    if c.courses[course].metrics["complexity"] == -1:
        complexity(c)
    return c.courses[course].metrics["complexity"]


# Compute the complexity of a curriculum
def complexity(c: Curriculum) -> Tuple[float, List[float]]:
    """
        complexity(c:Curriculum, course:Int)

    The **complexity** associated with curriculum ``c`` with  curriculum graph ``G_c = (V,E)``
    is defined as:

    ```math
    h(G_c) = \\sum_{v \\in V} \\left(d_c(v) + b_c(v)\\right).
    ```

    For the example curricula considered above, the curriculum in part (a) has an overall complexity of 15,
    while the curriculum in part (b) has an overall complexity of 17. This indicates that the curriculum
    in part (b) will be slightly more difficult to complete than the one in part (a). In particular, notice
    that course ``v_1`` in part (a) has the highest individual course complexity, but the combination of
    courses ``v_1`` and ``v_2`` in part (b), which both must be passed before a student can attempt course
    ``v_3`` in that curriculum, has a higher combined complexity.
    """
    course_complexity: List[float] = [0.0] * c.num_courses
    if c.metrics["delay factor"][0] == -1:
        delay_factor(c)
    if c.metrics["blocking factor"][0] == -1:
        blocking_factor(c)
    for v in c.graph.nodes:
        c.courses[v].metrics["complexity"] = (
            c.courses[v].metrics["delay factor"]
            + c.courses[v].metrics["blocking factor"]
        )
        if c.system_type == quarter:
            c.courses[v].metrics["complexity"] = round(
                (c.courses[v].metrics["complexity"] * 2) / 3, ndigits=1
            )
        course_complexity[v] = c.courses[v].metrics["complexity"]
    curric_complexity: float = sum(course_complexity)
    c.metrics["complexity"] = curric_complexity, course_complexity
    return curric_complexity, course_complexity


# Find all the longest paths in a curriculum.
def longest_paths(c: Curriculum) -> List[List[AbstractCourse]]:
    """
        longest_paths(c:Curriculum)

    Finds longest paths in curriculum `c`, and returns an array of course arrays, where
    each course array contains the courses in a longest path.

    # Arguments
    Required:
    - `c:Curriculum` : a valid curriculum.

    ```julia-repl
    julia> paths = longest_paths(c)
    ```
    """
    lps: List[List[AbstractCourse]] = []
    for path in longest_paths_graph(c.graph):  # longest_paths(), GraphAlgs.jl
        c_path = courses_from_vertices(c, path)
        lps.append(c_path)
    c.metrics["longest paths"] = lps
    return lps


def compare_curricula(c1: Curriculum, c2: Curriculum) -> StringIO:
    """
    Compare the metrics associated with two curricula
    to print out the report, use: println(String(take!(report))), where report is the IOBuffer returned by this function
    """
    report = StringIO()
    if c1.metrics.keys() != c2.metrics.keys():
        raise Exception("cannot compare curricula, they do not have the same metrics")
    report.write(f"Comparing: C1 = {c1.name} and C2 = {c2.name}\n")
    for k in Curriculum.metric_keys:
        report.write(f" Curricular {k}: ")
        metric1 = c1.metrics[k][0]
        metric2 = c1.metrics[k][0]
        diff = metric1 - metric2
        if diff > 0:
            report.write(
                "C1 is %.1f units (%.0f%%) larger than C2\n"
                % (diff, 100 * diff / metric2),
            )
        elif diff < 0:
            report.write(
                "C1 is %.1f units (%.0f%%) smaller than C2\n"
                % (-diff, 100 * (-diff) / metric2),
            )
        else:
            report.write(f"C1 and C2 have the same curricular {k}\n")
        report.write(f"  Course-level {k}:\n")
        for i, c in enumerate([c1, c2]):
            metric = c.metrics[k]
            maxval = max(metric[1])
            pos = [j for (j, x) in enumerate(metric[1]) if x == maxval]
            report.write(f"   Largest {k} value in C{i} is {maxval} for course: ")
            for p in pos:
                report.write(f"{c.courses[p].name}  ")
            report.write("\n")
    return report


@overload
def courses_from_vertices(
    curriculum: Curriculum, vertices: List[int], *, course: Literal["object"] = "object"
) -> List[AbstractCourse]:
    ...


@overload
def courses_from_vertices(
    curriculum: Curriculum, vertices: List[int], *, course: Literal["name", "fullname"]
) -> List[str]:
    ...


def courses_from_vertices(
    curriculum: Curriculum,
    vertices: List[int],
    *,
    course: Literal["object", "name", "fullname"] = "object",
) -> Union[List[AbstractCourse], List[str]]:
    """
    Create a list of courses or course names from a array of vertex IDs.
    The array returned can be (keyword arguments):
    -course data objects : object
    -the names of courses : name
    -the full names of courses (prefix, number, name) : fullname
    """
    if course == "object":
        return [curriculum.courses[v] for v in vertices]
    else:
        course_list: List[str] = []
        for v in vertices:
            c = curriculum.courses[v]
            if course == "name":
                course_list.append(f"{c.name}")
            if course == "fullname":
                course_list.append(
                    f"{c.prefix} {c.num} - {c.name}"
                    if isinstance(c, Course)
                    else c.name
                )
        return course_list


# Basic metrics for a currciulum.
def basic_metrics(curric: Curriculum) -> StringIO:
    """
        basic_metrics(c:Curriculum)

    Compute the basic metrics associated with curriculum `c`, and return an IO buffer containing these metrics.  The basic
    metrics are also stored in the `metrics` dictionary associated with the curriculum.

    The basic metrics computed include:

    - number of credit hours : The total number of credit hours in the curriculum.
    - number of courses : The total courses in the curriculum.
    - blocking factor : The blocking factor of the entire curriculum, and of each course in the curriculum.
    - centrality : The centrality measure associated with the entire curriculum, and of each course in the curriculum.
    - delay factor : The delay factor of the entire curriculum, and of each course in the curriculum.
    - curricular complexity : The curricular complexity of the entire curriculum, and of each course in the curriculum.

    Complete descriptions of these metrics are provided above.

    ```julia-repl
    julia> metrics = basic_metrics(curriculum)
    julia> println(String(take!(metrics)))
    julia> # The metrics are also stored in a dictonary that can be accessed as follows
    julia> curriculum.metrics
    ```
    """
    buf = StringIO()
    # compute all curricular metrics
    complexity(curric)
    centrality(curric)
    longest_paths(curric)
    max_bf: int = 0
    max_df: int = 0
    max_cc: float = 0
    max_cent: int = 0
    max_bf_courses: List[AbstractCourse] = []
    max_df_courses: List[AbstractCourse] = []
    max_cc_courses: List[AbstractCourse] = []
    max_cent_courses: List[AbstractCourse] = []
    for c in curric.courses:
        if c.metrics["blocking factor"] == max_bf:
            max_bf_courses.append(c)
        elif c.metrics["blocking factor"] > max_bf:
            max_bf = c.metrics["blocking factor"]
            max_bf_courses = []
            max_bf_courses.append(c)
        if c.metrics["delay factor"] == max_df:
            max_df_courses.append(c)
        elif c.metrics["delay factor"] > max_df:
            max_df = c.metrics["delay factor"]
            max_df_courses = []
            max_df_courses.append(c)
        if c.metrics["complexity"] == max_cc:
            max_cc_courses.append(c)
        elif c.metrics["complexity"] > max_cc:
            max_cc = c.metrics["complexity"]
            max_cc_courses = []
            max_cc_courses.append(c)
        if c.metrics["centrality"] == max_cent:
            max_cent_courses.append(c)
        elif c.metrics["centrality"] > max_cent:
            max_cent = c.metrics["centrality"]
            max_cent_courses = []
            max_cent_courses.append(c)
        curric.metrics["max. blocking factor"] = max_bf
        curric.metrics["max. blocking factor courses"] = max_bf_courses
        curric.metrics["max. centrality"] = max_cent
        curric.metrics["max. centrality courses"] = max_cent_courses
        curric.metrics["max. delay factor"] = max_df
        curric.metrics["max. delay factor courses"] = max_df_courses
        curric.metrics["max. complexity"] = max_cc
        curric.metrics["max. complexity courses"] = max_cc_courses
    # write metrics to IO buffer
    buf.write(f"\n{curric.institution} ")
    buf.write(f"\nCurriculum: {curric.name}\n")
    buf.write(f"  credit hours = {curric.credit_hours}\n")
    buf.write(f"  number of courses = {curric.num_courses}")
    buf.write("\n  Blocking Factor --\n")
    buf.write(f"    entire curriculum = {curric.metrics['blocking factor'][0]}\n")
    buf.write(f"    max. value = {max_bf}, ")
    buf.write("for course(s): ")
    write_course_names(buf, max_bf_courses)
    buf.write("\n  Centrality --\n")
    buf.write(f"    entire curriculum = {curric.metrics['centrality'][0]}\n")
    buf.write(f"    max. value = {max_cent}, ")
    buf.write("for course(s): ")
    write_course_names(buf, max_cent_courses)
    buf.write("\n  Delay Factor --\n")
    buf.write(f"    entire curriculum = {curric.metrics['delay factor'][0]}\n")
    buf.write(f"    max. value = {max_df}, ")
    buf.write("for course(s): ")
    write_course_names(buf, max_df_courses)
    buf.write("\n  Complexity --\n")
    buf.write(f"    entire curriculum = {curric.metrics['complexity'][0]}\n")
    buf.write(f"    max. value = {max_cc}, ")
    buf.write("for course(s): ")
    write_course_names(buf, max_cc_courses)
    buf.write("\n  Longest Path(s) --\n")
    buf.write(
        f"    length = {len(curric.metrics['longest paths'][0])}, number of paths = {len(curric.metrics['longest paths'])}\n    path(s):\n",
    )
    for i, path in enumerate(curric.metrics["longest paths"]):
        buf.write(f"    path {i} = ")
        write_course_names(buf, path, separator=" -> ")
        buf.write("\n")
    return buf


def basic_statistics(
    curricula: List[Curriculum], metric_name: CurriculumMetricKey
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
        basic_metrics(c)
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


def similarity(c1: Curriculum, c2: Curriculum, *, strict: bool = True) -> float:
    """
        similarity(c1, c2; strict)

    Compute how similar curriculum `c1` is to curriculum `c2`.  The similarity metric is computed by comparing how many courses in
    `c1` are also in `c2`, divided by the total number of courses in `c2`.  Thus, for two curricula, this metric is not symmetric. A
    similarity value of `1` indicates that `c1` and `c2` are identical, whil a value of `0` means that none of the courses in `c1`
    are in `c2`.

    # Arguments
    Required:
    - `c1:Curriculum` : the target curriculum.
    - `c2:Curriculum` : the curriculum serving as the basis for comparison.

    Keyword:
    - `strict:Bool` : if true (default), two courses are considered the same if every field in the two courses are the same; if false,
    two courses are conisdred the same if they have the same course name, or if they have the same course prefix and number.

    ```julia-repl
    julia> similarity(curric1, curric2)
    ```
    """
    if c2.num_courses == 0:
        raise Exception(
            f"Curriculum {c2.name} does not have any courses, similarity cannot be computed"
        )
    if c1 == c2:
        return 1
    matches = 0
    if strict == True:
        for course in c1.courses:
            if course in c2.courses:
                matches += 1
    else:  # strict == False
        for course in c1.courses:
            for basis_course in c2.courses:
                if (
                    (course.name != "" and basis_course.name == course.name)
                    or isinstance(course, Course)
                    and isinstance(basis_course, Course)
                    and (
                        course.prefix != ""
                        and basis_course.prefix == course.prefix
                        and course.num != ""
                        and basis_course.num == course.num
                    )
                ):
                    matches += 1
                    break  # only match once
    return matches / c2.num_courses


def merge_curricula(
    name: str,
    c1: Curriculum,
    c2: Curriculum,
    *,
    match_criteria: List[
        Literal["prefix", "num", "name", "canonical name", "credit hours"]
    ] = [],
    learning_outcomes: List[LearningOutcome] = [],
    degree_type: str = "BS",  # Julia version uses `BS`, which isn't defined anywhere
    system_type: System = semester,
    institution: str = "",
    CIP: str = "",
) -> Curriculum:
    """
        merge_curricula(c1, c2; match_criteria)

    Merge the two curricula `c1` and `c2` supplied as input into a single curriculum based on the match criteria applied
    to the courses in the two curricula.  All courses in curriculum `c1` will appear in the merged curriculum.  If a course in
    curriculum `c2` matches a course in curriculum `c1`, that course serves as a matched course in the merged curriculum.
    If there is no match for a course in curriculum `c2` to the set of courses in curriculum `c1`, course `c2` is added
    to the set of courses in the merged curriculum.

    # Arguments
    Required:
    - `c1:Curriculum` : first curriculum.
    - `c2:Curriculum` : second curriculum.

    Optional:
    - `match_criteria:Array{String}` : list of course items that must match, if no match critera are supplied, the
    courses must be identical (at the level of memory allocation). Allowable match criteria include:
        - `prefix` : the course prefixes must be identical.
        - `num` : the course numbers must be indentical.
        - `name` : the course names must be identical.
        - `canonical name` : the course canonical names must be identical.
        - `credit hours` : the course credit hours must be indentical.

    """
    merged_courses = (c1.courses).copy()
    extra_courses: List[AbstractCourse] = []  # courses in c2 but not in c1
    new_courses: List[AbstractCourse] = []
    for course in c2.courses:
        matched = False
        for target_course in c1.courses:
            if match(course, target_course, match_criteria) == True:
                matched = True
            #    skip TODO
        if not matched:
            extra_courses.append(course)
    # patch-up requisites of extra_courses, using course ids form c1 where appropriate
    for c in extra_courses:
        # for each extra course create an indentical coures, but with a new course id
        new_courses.append(c.copy())
    for j, c in enumerate(extra_courses):
        #    print(f"\n {c.name}: ")
        #    print(f"total requisistes = {len(c.requisites)},")
        for req in c.requisites:
            #        print(f" requisite id: {req} ")
            req_course = c2.course_from_id(req)
            if find_match(req_course, merged_courses, match_criteria) != None:
                # requisite already exists in c1
                #            print(f" match in c1 - {course_from_id(c1, req).name} ")
                new_courses[j].add_requisite(req_course, c.requisites[req])
            elif find_match(req_course, extra_courses, match_criteria) != None:
                # requisite is not in c1, but it's in c2 -- use the id of the new course created for it
                #            print(" match in extra courses, ")
                i = next(i for i, x in enumerate(extra_courses) if x == req_course)
                #            print(f" index of match = {i} ")
                new_courses[j].add_requisite(new_courses[i], c.requisites[req])
            else:  # requisite is neither in c1 or 2 -- this shouldn't happen => error
                raise Exception(f"requisite error on course: {c.name}")
    merged_courses = [*merged_courses, *new_courses]
    merged_curric = Curriculum(
        name,
        merged_courses,
        learning_outcomes=learning_outcomes,
        degree_type=degree_type,
        institution=institution,
        CIP=CIP,
    )
    return merged_curric


def match(
    course1: AbstractCourse,
    course2: AbstractCourse,
    match_criteria: List[MatchCriterion] = [],
) -> bool:
    is_matched = False
    if len(match_criteria) == 0:
        return course1 == course2
    else:
        for criterion in match_criteria:
            if criterion not in [
                "prefix",
                "num",
                "name",
                "canonical name",
                "credit hours",
            ]:
                raise Exception(f"invalid match criteria: {criterion}")
            elif criterion == "prefix":
                is_matched = (
                    course1.prefix == course2.prefix
                    if isinstance(course1, Course) and isinstance(course2, Course)
                    else True
                )
            elif criterion == "num":
                is_matched = (
                    course1.num == course2.num
                    if isinstance(course1, Course) and isinstance(course2, Course)
                    else True
                )
            elif criterion == "name":
                is_matched = course1.name == course2.name
            elif criterion == "canonical name":
                is_matched = course1.canonical_name == course2.canonical_name
            elif criterion == "credit hours":
                is_matched = course1.credit_hours == course2.credit_hours
    return is_matched


def find_match(
    course: AbstractCourse,
    course_set: List[AbstractCourse],
    match_criteria: List[MatchCriterion] = [],
) -> Optional[AbstractCourse]:
    for c in course_set:
        if match(course, c, match_criteria):
            return course
    return None


def homology(curricula: List[Curriculum], *, strict: bool = False) -> List[List[float]]:
    return [
        [
            similarity(curricula[i], curricula[j], strict=strict)
            for j in range(len(curricula))
        ]
        for i in range(len(curricula))
    ]


def dead_ends(
    curric: Curriculum, prefixes: FrozenSet[str]
) -> Tuple[FrozenSet[str], List[Course]]:
    """
        dead_ends(curric, prefixes)

    Finds all courses in curriculum `curric` that appear at the end of a path (i.e., sink vertices), and returns those courses that
    do not have one of the course prefixes listed in the `prefixes` array.  If a course does not have a prefix, it is excluded from
    the analysis.

    # Arguments
    - `c:Curriculum` : the target curriculum.
    - `prefixes:Array{String,1}` : an array of course prefix strings.

    For instance, the following will find all courses in `curric` that appear at the end of any course path in the curriculum,
    and do *not* have `BIO` as a prefix.  One might consider these courses "dead ends," as their course outcomes are not used by any
    major-specific course, i.e., by any course with the prefix `BIO`.

    ```julia-repl
    julia> dead_ends(curric, ["BIO"])
    ```
    """
    dead_end_courses: List[Course] = []
    paths = all_paths(curric.graph)
    for p in paths:
        course = curric.course_from_vertex(p[-1])
        if not isinstance(course, Course) or course.prefix == "":
            continue
        if course.prefix not in prefixes:
            if course not in dead_end_courses:
                dead_end_courses.append(course)
    if "dead end" in curric.metrics:
        if prefixes in curric.metrics["dead end"]:
            curric.metrics["dead end"][prefixes] = dead_end_courses
    else:
        curric.metrics["dead end"] = {prefixes: dead_end_courses}
    return (prefixes, dead_end_courses)


def knowledge_transfer(dp: DegreePlan) -> List[float]:
    """
        knowledge_transfer(dp)

    Determine the number of requisites crossing the "cut" in a degree plan that occurs between each term.

    # Arguments
    - `dp:DegreePlan` : the degree to analyze.

    Returns an array of crossing values between the courses in the first term and the remainder of the degree plan,
    between the courses in the first two terms in the degree plan, and the remainder of the degree plan, etc.
    The number of values returned will be one less than the number of terms in the degree plan.

    ```julia-repl
    julia> knowledge_transfer(dp)
    ```
    """
    ec_terms: List[float] = []
    s: List[int] = []
    for term in dp.terms:
        sum = 0
        for c in term.courses:
            s.append(c.vertex_id[dp.curriculum.id])
        sum += edge_crossings(dp.curriculum.graph, s)
        ec_terms.append(sum)
    del ec_terms[-1]
    return ec_terms  # the last value will always be zero, so remove it
