"""
The curriculum-based metrics in this toolbox are based upon the graph structure of a
curriculum.  Specifically, assume curriculum ``c`` consists of ``n`` courses ``\\{c_1, \\ldots, c_n\\}``,
and that there are ``m`` requisite (prerequisite or co-requsitie) relationships between these courses.
A curriculum graph ``G_c = (V,E)`` is formed by creating a vertex set ``V = \\{v_1, \\ldots, v_n\\}``
(i.e., one vertex for each course) along with an edge set ``E = \\{e_1, \\ldots, e_m\\}``, where a
directed edge from vertex ``v_i`` to ``v_j`` is in ``E`` if course ``c_i`` is a requisite for course ``c_j``.
"""

from queue import Queue
from typing import List, Optional, Tuple
from src.DataTypes.Course import Course, add_requisite
from src.DataTypes.Curriculum import Curriculum, course_from_id
from src.DataTypes.DataTypes import co, quarter, strict_co
from src.DataTypes.DegreePlan import DegreePlan

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


def isvalid_curriculum(c: Curriculum, error_msg: IOBuffer = IOBuffer()) -> bool:
    """
        isvalid_curriculum(c:Curriculum, errors:IOBuffer)

    Tests whether or not the curriculum graph ``G_c`` associated with curriculum `c` is valid, i.e.,
    whether or not it contains a requisite cycle, or requisites that cannot be satisfied.  Returns
    a boolean value, with `true` indicating the curriculum is valid, and `false` indicating it is not.

    If ``G_c`` is not valid, the `errors` buffer. To view these errors, use:

    ```julia-repl
    julia> errors = IOBuffer()
    julia> isvalid_curriculum(c, errors)
    julia> println(String(take!(errors)))
    ```

    A curriculum graph is not valid if it contains a directed cycle or unsatisfiable requisites; in this
    case it is not possible to complete the curriculum. For the case of unsatisfiable requistes, consider
    two courses ``c_1`` and ``c_2``, with ``c_1`` a prerequisite for ``c_2``. If a third course ``c_3``
    is a strict corequisite for ``c_2``, as well as a requisite for ``c_1`` (or a requisite for any course
    on a path leading to ``c_2``), then the set of requisites cannot be satisfied.
    """
    g = deepcopy(c.graph)
    validity = True
    # First check for simple cycles
    cycles = simplecycles(g)
    # Next check for cycles that could be created by strict co-requisites.
    # For every strict-corequisite in the curriculum, add another strict-corequisite between the same two vertices, but in
    # the opposite direction. If this creates any cycles of length greater than 2 in the modified graph (i.e., involving
    # more than the two courses in the strict-corequisite relationship), then the curriculum is unsatisfiable.
    for course in c.courses:
        for (k, r) in course.requisites:
            if r == strict_co:
                v_d = course_from_id(c, course.id).vertex_id[c.id]  # destination vertex
                v_s = course_from_id(c, k).vertex_id[c.id]  # source vertex
                g.add_edge(v_d, v_s)
    new_cycles = simplecycles(g)
    idx: List[int] = []
    for (i, cyc) in enumerate(new_cycles):  # remove length-2 cycles
        if len(cyc) == 2:
            idx.append(i)
    del new_cycles[idx]
    cycles = union(new_cycles, cycles)  # remove redundant cycles
    if length(cycles) != 0:
        validity = False
        if c.institution != "":
            write(error_msg, f"\n{c.institution}: ")
        write(error_msg, f" curriculum '{c.name}' has requisite cycles:\n")
        for cyc in cycles:
            write(error_msg, "(")
            for (i, v) in enumerate(cyc):
                if i != len(cyc) - 1:
                    write(error_msg, f"{c.courses[v].name}, ")
                else:
                    write(error_msg, f"{c.courses[v].name})\n")
    return validity


def extraneous_requisites(c: Curriculum, print: bool = False) -> List[List[int]]:
    """
        extraneous_requisites(c:Curriculum; print=false)

    Determines whether or not a curriculum `c` contains extraneous requisites, and returns them.  Extraneous requisites
    are redundant requisites that are unnecessary in a curriculum.  For example, if a curriculum has the prerequisite
    relationships $c_1 \\rightarrow c_2 \\rightarrow c_3$ and $c_1 \\rightarrow c_3$, and $c_1$ and $c_2$ are
    *not* co-requisites, then $c_1 \\rightarrow c_3$ is redundant and therefore extraneous.
    """
    if is_cyclic(c.graph):
        error(
            "\nCurriculm graph has cycles, extraneous requisities cannot be determined."
        )
    if print == True:
        msg = IOBuffer()
    redundant_reqs: List[List[int]] = []
    g = c.graph
    que: Queue[int] = Queue()
    components = weakly_connected_components(g)
    extraneous = False
    str = ""  # create an empty string to hold messages
    for wcc in components:
        if len(wcc) > 1:  # only consider components with more than one vertex
            for u in wcc:
                nb = neighbors(g, u)
                for n in nb:
                    que.put(n)
                while not que.empty():
                    x = que.get()
                    nnb = neighbors(g, x)
                    for n in nnb:
                        que.put(n)
                    for v in neighbors(g, x):
                        if has_edge(g, u, v):  # possible redundant requsisite
                            # TODO: If this edge is a co-requisite it is an error, as it would be impossible to satsify.
                            # This needs to be checked here.
                            remove = True
                            for n in nb:  # check for co- or strict_co requisites
                                if has_path(
                                    c.graph, n, v
                                ):  # is there a path from n to v?
                                    req_type = c.courses[n].requisites[
                                        c.courses[u].id
                                    ]  # the requisite relationship between u and n
                                    if (req_type == co) or (
                                        req_type == strict_co
                                    ):  # is u a co or strict_co requisite for n?
                                        remove = False  # a co or strict_co relationshipo is involved, must keep (u, v)
                            if remove == True:
                                if (
                                    next(
                                        (
                                            x
                                            for x in redundant_reqs
                                            if x == [c.courses[u].id, c.courses[v].id]
                                        ),
                                        None,
                                    )
                                    == None
                                ):  # make sure redundant requisite wasn't previously found
                                    redundant_reqs.append(
                                        [c.courses[u].id, c.courses[v].id]
                                    )
                                    if print == True:
                                        str = (
                                            str
                                            + f"-{c.courses[v].name} has redundant requisite {c.courses[u].name}\n"
                                        )
                                extraneous = True
    if (extraneous == True) and (print == True):
        if c.institution != "":
            write(msg, f"\n{c.institution}: ")
        write(msg, f"curriculum {c.name} has extraneous requisites:\n")
        write(msg, str)
    if print == True:
        print(str(msg))
    return redundant_reqs


# Compute the blocking factor of a course
def blocking_factor(c: Curriculum, course: int) -> int:
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
    b = 0
    bf: List[int] = []  # TODO: Array{Int, 1}(undef, c.num_courses)
    for (i, v) in enumerate(vertices(c.graph)):
        bf[i] = blocking_factor(c, v)
        b += bf[i]
    c.metrics["blocking factor"] = b, bf
    return b, bf


# Compute the delay factor of a course
def delay_factor_course(c: Curriculum, course: int) -> Tuple[int, List[int]]:
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
    if "delay factor" not in c.courses[course].metrics:
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
    df = ones(c.num_courses)
    for v in vertices(g):
        for path in all_paths(g):
            for vtx in path:
                path_length = len(
                    path
                )  # path_length in terms of # of vertices, not edges
                if path_length > df[vtx]:
                    df[vtx] = path_length
    d = 0
    c.metrics["delay factor"] = 0
    for v in vertices(g):
        c.courses[v].metrics["delay factor"] = df[v]
        d += df[v]
    c.metrics["delay factor"] = d, df
    return d, df


# Compute the centrality of a course
def centrality(c: Curriculum, course: int) -> int:
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
    cent = 0
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
    cent = 0
    cf = []  # Array{Int, 1}(undef, c.num_courses)
    for (i, v) in enumerate(vertices(c.graph)):
        cf[i] = centrality(c, v)
        cent += cf[i]
    c.metrics["centrality"] = cent, cf
    return cent, cf


# Compute the complexity of a course
def complexity(c: Curriculum, course: int) -> Tuple[int, List[int]]:
    """
        complexity(c:Curriculum, course:Int)

    The **complexity** associated with course ``c_i`` in curriculum ``c`` with
    curriculum graph ``G_c = (V,E)`` is defined as:
    ```math
    h_c(v_i) = d_c(v_i) + b_c(v_i)
    ```
    i.e., as a linear combination of the course delay and blocking factors.
    """
    if "complexity" not in c.courses[course].metrics:
        complexity(c)
    return c.courses[course].metrics["complexity"]


# Compute the complexity of a curriculum
def complexity(c: Curriculum) -> Tuple[int, List[int]]:
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
    course_complexity: List[float] = []  # Array{Number, 1}(undef, c.num_courses)
    curric_complexity = 0
    if "delay factor" not in c.metrics:
        delay_factor(c)
    if "blocking factor" not in c.metrics:
        blocking_factor(c)
    for v in vertices(c.graph):
        c.courses[v].metrics["complexity"] = (
            c.courses[v].metrics["delay factor"]
            + c.courses[v].metrics["blocking factor"]
        )
        if c.system_type == quarter:
            c.courses[v].metrics["complexity"] = round(
                (c.courses[v].metrics["complexity"] * 2) / 3, ndigits=1
            )
        course_complexity[v] = c.courses[v].metrics["complexity"]
        curric_complexity += course_complexity[v]
    c.metrics["complexity"] = curric_complexity, course_complexity
    return curric_complexity, course_complexity


# Find all the longest paths in a curriculum.
def longest_paths(c: Curriculum):
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
    lps: List[List[Course]] = []
    for path in longest_paths(c.graph):  # longest_paths(), GraphAlgs.jl
        c_path = courses_from_vertices(c, path)
        lps.append(c_path)
    c.metrics["longest paths"] = lps
    return lps


def compare_curricula(c1: Curriculum, c2: Curriculum) -> IOBuffer:
    """
    Compare the metrics associated with two curricula
    to print out the report, use: println(String(take!(report))), where report is the IOBuffer returned by this function
    """
    report = IOBuffer()
    if c1.metrics.keys() != c2.metrics.keys():
        error("cannot compare curricula, they do not have the same metrics")
    write(report, f"Comparing: C1 = {c1.name} and C2 = {c2.name}\n")
    for k in c1.metrics:
        write(report, f" Curricular {k}: ")
        if len(c1.metrics[k]) == 2:  # curriculum has course-level metrics
            metric1 = c1.metrics[k][0]
            metric2 = c2.metrics[k][0]
        else:
            metric1 = c1.metrics[k]
            metric2 = c2.metrics[k]
        diff = c1.metrics[k][0] - c2.metrics[k][0]
        if diff > 0:
            write(
                report,
                "C1 is %.1f units (%.0f%c) larger than C2\n"
                % (diff, 100 * diff / c2.metrics[k][1], "%"),
            )
        elif diff < 0:
            write(
                report,
                "C1 is %.1f units (%.0f%c) smaller than C2\n"
                % (-diff, 100 * (-diff) / c2.metrics[k][1], "%"),
            )
        else:
            write(report, f"C1 and C2 have the same curricular {k}\n")
        if len(c1.metrics[k]) == 2:
            write(report, "  Course-level {k}:\n")
            for (i, c) in enumerate([c1, c2]):
                maxval = max(c.metrics[k][1])
                pos = [j for (j, x) in enumerate(c.metrics[k][1]) if x == maxval]
                write(report, f"   Largest {k} value in C{i} is {maxval} for course: ")
                for p in pos:
                    write(report, f"{c.courses[p].name}  ")
                write(report, "\n")
    return report


def courses_from_vertices(
    curriculum: Curriculum, vertices: List[int], course: str = "object"
) -> List[Course]:
    """
    Create a list of courses or course names from a array of vertex IDs.
    The array returned can be (keyword arguments):
    -course data objects : object
    -the names of courses : name
    -the full names of courses (prefix, number, name) : fullname
    """
    if course == "object":
        course_list: List[Course] = []
    else:
        course_list: List[str] = []  # TODO
    for v in vertices:
        c = curriculum.courses[v]
        if course == "object":
            course_list.append(c)
        if course == "name":
            course_list.append(f"{c.name}")
        if course == "fullname":
            course_list.append(f"{c.prefix} {c.num} - {c.name}")
    return course_list


# Basic metrics for a currciulum.
def basic_metrics(curric: Curriculum) -> IOBuffer:
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
    buf = IOBuffer()
    complexity(curric), centrality(curric), longest_paths(
        curric
    )  # compute all curricular metrics
    max_bf = 0
    max_df = 0
    max_cc = 0
    max_cent = 0
    max_bf_courses: List[Course] = []
    max_df_courses: List[Course] = []
    max_cc_courses: List[Course] = []
    max_cent_courses: List[Course] = []
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
    write(buf, f"\n{curric.institution} ")
    write(buf, f"\nCurriculum: {curric.name}\n")
    write(buf, f"  credit hours = {curric.credit_hours}\n")
    write(buf, f"  number of courses = {curric.num_courses}")
    write(buf, "\n  Blocking Factor --\n")
    write(buf, f"    entire curriculum = {curric.metrics['blocking factor'][0]}\n")
    write(buf, f"    max. value = {max_bf}, ")
    write(buf, "for course(s): ")
    write_course_names(buf, max_bf_courses)
    write(buf, "\n  Centrality --\n")
    write(buf, f"    entire curriculum = {curric.metrics['centrality'][0]}\n")
    write(buf, f"    max. value = {max_cent}, ")
    write(buf, "for course(s): ")
    write_course_names(buf, max_cent_courses)
    write(buf, "\n  Delay Factor --\n")
    write(buf, f"    entire curriculum = {curric.metrics['delay factor'][0]}\n")
    write(buf, f"    max. value = {max_df}, ")
    write(buf, "for course(s): ")
    write_course_names(buf, max_df_courses)
    write(buf, "\n  Complexity --\n")
    write(buf, f"    entire curriculum = {curric.metrics['complexity'][0]}\n")
    write(buf, f"    max. value = {max_cc}, ")
    write(buf, "for course(s): ")
    write_course_names(buf, max_cc_courses)
    write(buf, "\n  Longest Path(s) --\n")
    write(
        buf,
        f"    length = {len(curric.metrics['longest paths'][0])}, number of paths = {len(curric.metrics['longest paths'])}\n    path(s):\n",
    )
    for (i, path) in enumerate(curric.metrics["longest paths"]):
        write(buf, f"    path {i} = ")
        write_course_names(buf, path, separator=" -> ")
        write(buf, "\n")
    return buf


def basic_statistics(curricula: List[Curriculum], metric_name: str) -> IOBuffer:
    buf = IOBuffer()
    # set initial values used to find min and max metric values
    total_metric = 0
    STD_metric = 0
    if metric_name in curricula[0].metrics:
        if isinstance(curricula[0].metrics[metric_name], float):
            max_metric = curricula[0].metrics[metric_name]
            min_metric = curricula[0].metrics[metric_name]
        elif isinstance(
            curricula[0].metrics[metric_name], tuple
        ):  # Tuple{Float64,Array{Number,1}}
            max_metric = curricula[0].metrics[metric_name][0]
            min_metric = curricula[0].metrics[metric_name][0]
            # metric where total curricular metric as well as course-level metrics are stored in an array
    for c in curricula:
        if metric_name not in c.metrics:
            raise Exception(
                f"metric {metric_name} does not exist in curriculum {c.name}"
            )
        basic_metrics(c)
        if isinstance(c.metrics[metric_name], float):
            value = c.metrics[metric_name]
        elif isinstance(
            c.metrics[metric_name], tuple
        ):  # Tuple{Float64,Array{Number,1}}
            value = c.metrics[metric_name][
                0
            ]  # metric where total curricular metric as well as course-level metrics are stored in an array
        total_metric += value
        if value > max_metric:
            max_metric = value
        if value < min_metric:
            min_metric = value
    avg_metric = total_metric / len(curricula)
    for c in curricula:
        if isinstance(c.metrics[metric_name], float):
            value = c.metrics[metric_name]
        elif isinstance(
            c.metrics[metric_name], tuple
        ):  # Tuple{Float64,Array{Number,1}}
            value = c.metrics[metric_name][
                0
            ]  # metric where total curricular metric as well as course-level metrics are stored in an array
        STD_metric = (value - avg_metric) ** 2
    STD_metric = math.sqrt(STD_metric / len(curricula))
    write(buf, f"\n Metric -- {metric_name}")
    write(buf, f"\n  Number of curricula = {len(curricula)}")
    write(buf, f"\n  Mean = {avg_metric}")
    write(buf, f"\n  STD = {STD_metric}")
    write(buf, f"\n  Max. = {max_metric}")
    write(buf, f"\n  Min. = {min_metric}")
    return buf


def write_course_names(
    buf: IOBuffer, courses: List[Course], separator: str = ", "
) -> None:
    if len(courses) == 1:
        write_course_name(buf, courses[0])
    else:
        for c in courses:
            write_course_name(buf, c)
            write(buf, separator)
        write_course_name(buf, courses[-1])


def write_course_name(buf: IOBuffer, c: Course) -> None:
    if c.prefix:
        write(buf, f"{c.prefix} ")
    if c.num:
        write(buf, f"{c.num} - ")
    write(buf, f"{c.name}")  # name is a required item


def similarity(c1: Curriculum, c2: Curriculum, strict: bool = True) -> float:
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
                if (course.name != "" and basis_course.name == course.name) or (
                    course.prefix != ""
                    and basis_course.prefix == course.prefix
                    and course.num != ""
                    and basis_course.num == course.num
                ):
                    matches += 1
                    break  # only match once
    return matches / c2.num_courses


def merge_curricula(
    name: str,
    c1: Curriculum,
    c2: Curriculum,
    match_criteria: List[str] = [],
    learning_outcomes: List[LearningOutcome] = [],
    degree_type: str = BS,
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
    extra_courses: List[Course] = []  # courses in c2 but not in c1
    new_courses: List[Course] = []
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
        new_courses.append(
            Course(
                c.name,
                c.credit_hours,
                prefix=c.prefix,
                learning_outcomes=c.learning_outcomes,
                num=c.num,
                institution=c.institution,
                canonical_name=c.canonical_name,
            )
        )
    for (j, c) in enumerate(extra_courses):
        #    print(f"\n {c.name}: ")
        #    print(f"total requisistes = {len(c.requisites)},")
        for req in c.requisites:
            #        print(f" requisite id: {req} ")
            req_course = course_from_id(c2, req)
            if find_match(req_course, merged_courses, match_criteria) != None:
                # requisite already exists in c1
                #            print(f" match in c1 - {course_from_id(c1, req).name} ")
                add_requisite(req_course, new_courses[j], c.requisites[req])
            elif find_match(req_course, extra_courses, match_criteria) != None:
                # requisite is not in c1, but it's in c2 -- use the id of the new course created for it
                #            print(" match in extra courses, ")
                i = next(x for x in extra_courses if x == req_course)
                #            print(f" index of match = {i} ")
                add_requisite(new_courses[i], new_courses[j], c.requisites[req])
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


def match(course1: Course, course2: Course, match_criteria: List[str] = []) -> bool:
    is_matched = False
    if len(match_criteria) == 0:
        return course1 == course2
    else:
        for str in match_criteria:
            if str not in ["prefix", "num", "name", "canonical name", "credit hours"]:
                raise Exception(f"invalid match criteria: {str}")
            elif str == "prefix":
                if course1.prefix == course2.prefix:
                    is_matched = True
                else:
                    is_matched = False
            elif str == "num":
                if course1.num == course2.num:
                    is_matched = True
                else:
                    is_matched = False
            elif str == "name":
                if course1.name == course2.name:
                    is_matched = True
                else:
                    is_matched = False
            elif str == "canonical name":
                if course1.canonical_name == course2.canonical_name:
                    is_matched = True
                else:
                    is_matched = False
            elif str == "credit hours":
                if course1.credit_hours == course2.credit_hours:
                    is_matched = True
                else:
                    is_matched = False
    return is_matched


def find_match(
    course: Course, course_set: List[Course], match_criteria: List[str] = []
) -> Optional[Course]:
    for c in course_set:
        if match(course, c, match_criteria):
            return course
    return None


def homology(curricula: List[Curriculum], strict: bool = False) -> Matrix[float]:
    similarity_matrix: Matrix[float] = Matrix(I, len(curricula), len(curricula))  # TODO
    for i in range(len(curricula)):
        for j in range(len(curricula)):
            similarity_matrix[i, j] = similarity(
                curricula[i], curricula[j], strict=strict
            )
            similarity_matrix[j, i] = similarity(
                curricula[j], curricula[i], strict=strict
            )
    return similarity_matrix


def dead_ends(
    curric: Curriculum, prefixes: List[str]
) -> Tuple[List[str], List[Course]]:
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
        course = course_from_vertex(curric, p[-1])
        if course.prefix == "":
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
