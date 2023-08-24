"""
Curriculum data type:
The required curriculum associated with a degree program.
"""

from io import StringIO
from queue import Queue
import sys
from typing import (
    Any,
    Dict,
    FrozenSet,
    List,
    Literal,
    Optional,
    Set,
    TextIO,
    Tuple,
    TypedDict,
    Union,
    overload,
)

import networkx as nx

from curricularanalytics.DataTypes.Course import (
    AbstractCourse,
    Course,
    MatchCriterion,
    course_id,
    write_course_names,
)
from curricularanalytics.DataTypes.DataTypes import (
    System,
    belong_to,
    c_to_c,
    co,
    lo_to_c,
    lo_to_lo,
    pre,
    quarter,
    semester,
    strict_co,
)
from curricularanalytics.DataTypes.LearningOutcome import LearningOutcome
from curricularanalytics.GraphAlgs import all_paths, longest_paths, reachable_from

CurriculumMetrics = TypedDict(
    "CurriculumMetrics",
    {
        "blocking factor": Tuple[int, List[int]],
        "delay factor": Tuple[int, List[int]],
        "centrality": Tuple[int, List[int]],
        "complexity": Tuple[float, List[float]],
        "longest paths": List[List[AbstractCourse]],
        "max. blocking factor": int,
        "max. blocking factor courses": List[AbstractCourse],
        "max. centrality": int,
        "max. centrality courses": List[AbstractCourse],
        "max. delay factor": int,
        "max. delay factor courses": List[AbstractCourse],
        "max. complexity": float,
        "max. complexity courses": List[AbstractCourse],
        "dead end": Dict[FrozenSet[str], List[Course]],
    },
)
CurriculumMetricKey = Literal[
    "blocking factor",
    "delay factor",
    "centrality",
    "complexity",
]


class Curriculum:
    """
    The `Curriculum` data type is used to represent the collection of courses that must be
    be completed in order to earn a particualr degree. Thus, we use the terms *curriculum* and
    *degree program* synonymously.

    Args:
        name: The name of the curriculum.
        courses: The collection of required courses that comprise the curriculum.
        degree_type: The type of degree, e.g. BA, BBA, BSc, BEng, etc.
        institution: The name of the institution offering the curriculum.
        system_type: The type of system the institution uses, allowable
          types: `semester` (default), `quarter`.
        cip: The Classification of Instructional Programs (CIP) code for the
          curriculum. See: https://nces.ed.gov/ipeds/cipcode

    Examples:
        >>> Curriculum("Biology", courses, institution="South Harmon Tech", degree_type=AS, cip="26.0101")
        Curriculum(...)
    """

    id: int
    "Unique curriculum ID"
    name: str
    "Name of the curriculum (can be used as an identifier)"
    institution: str
    "Institution offering the curriculum"
    degree_type: str
    "Type of degree_type"
    system_type: System
    "Semester or quarter system"
    cip: str
    "CIP code associated with the curriculum"
    courses: List[AbstractCourse]
    "Array of required courses in curriculum"
    num_courses: int
    "Number of required courses in curriculum"
    credit_hours: float
    "Total number of credit hours in required curriculum"
    graph: "nx.DiGraph[int]"
    "Directed graph representation of pre-/co-requisite structure of the curriculum, note: this is a course graph"
    learning_outcomes: List[LearningOutcome]
    "A list of learning outcomes associated with the curriculum"
    learning_outcome_graph: "nx.DiGraph[int]"
    "Directed graph representatin of pre-/co-requisite structure of learning outcomes in the curriculum"
    course_learning_outcome_graph: "nx.DiGraph[int]"
    """
    Directed Int64 metagraph with Float64 weights defined by :weight (default weight 1.0)
    This is a course and learning outcome graph
    """
    metrics: CurriculumMetrics
    "Curriculum-related metrics"
    metadata: Dict[str, Any]
    "Curriculum-related metadata"

    _metric_keys: Set[CurriculumMetricKey] = {
        "blocking factor",
        "delay factor",
        "centrality",
        "complexity",
    }

    def __init__(
        self,
        name: str,
        courses: List[AbstractCourse],
        *,
        learning_outcomes: List[LearningOutcome] = [],
        degree_type: str = "BS",
        system_type: System = semester,
        institution: str = "",
        cip: str = "",
        id: int = 0,
        sortby_ID: bool = True,
        warn: bool = False,
    ) -> None:
        self.name = name
        self.degree_type = degree_type
        self.system_type = system_type
        self.institution = institution
        self.id = id or hash(self.name + self.institution + str(self.degree_type))
        self.cip = cip
        self.courses = sorted(courses, key=lambda c: c.id) if sortby_ID else courses
        self.num_courses = len(self.courses)
        self.credit_hours = self.total_credits
        self.graph = self._create_graph()
        self.metrics = {
            "blocking factor": (-1, []),
            "delay factor": (-1, []),
            "centrality": (-1, []),
            "complexity": (-1, []),
            "longest paths": [],
            "max. blocking factor": -1,
            "max. blocking factor courses": [],
            "max. centrality": -1,
            "max. centrality courses": [],
            "max. delay factor": -1,
            "max. delay factor courses": [],
            "max. complexity": -1,
            "max. complexity courses": [],
            "dead end": {},
        }
        self.metadata = {}
        self.learning_outcomes = learning_outcomes
        self.learning_outcome_graph = self._create_learning_outcome_graph()
        self.course_learning_outcome_graph = (
            self._create_course_learning_outcome_graph()
        )
        errors = StringIO()
        if warn and not self.isvalid(errors):
            print(
                "WARNING: Curriculum was created, but is invalid due to requisite cycle(s):"
            )  # TODO: yellow
            print(errors.getvalue())

    def convert_ids(self) -> "Curriculum":
        "Converts course ids, from those used in CSV file format, to the standard hashed id used by the data structures in the toolbox"
        for course in self.courses:
            old_id = course.id
            course.id = course.default_id()
            if old_id != course.id:
                for other in self.courses:
                    if old_id in other.requisites:
                        other.add_requisite(course, other.requisites[old_id])
                        del other.requisites[old_id]
        return self

    def course(
        self, prefix: str, num: str, name: str, institution: str
    ) -> AbstractCourse:
        "Compute the hash value used to create the id for a course, and return the course if it exists in the curriculum supplied as input"
        hash_val = course_id(name, prefix, num, institution)
        try:
            return next(x for x in self.courses if x.id == hash_val)
        except StopIteration:
            raise LookupError(
                f"Course: {prefix} {num}: {name} at {institution} does not exist in curriculum: {self.name}"
            )

    def course_from_id(self, id: int) -> AbstractCourse:
        "Return the course associated with a course id in a curriculum"
        for c in self.courses:
            if c.id == id:
                return c
        raise KeyError(f"The course associated with id {id} is not in the curriculum.")

    def lo_from_id(self, id: int) -> LearningOutcome:
        "Return the lo associated with a lo id in a curriculum"
        for lo in self.learning_outcomes:
            if lo.id == id:
                return lo
        raise KeyError(f"The lo associated with id {id} is not in the curriculum.")

    @property
    def total_credits(self) -> float:
        "The total number of credit hours in a curriculum"
        return sum(course.credit_hours for course in self.courses)

    def _create_graph(self) -> "nx.DiGraph[int]":
        """
        Create a curriculum directed graph from a curriculum specification.
        """
        graph: "nx.DiGraph[int]" = nx.DiGraph()
        for course in self.courses:
            graph.add_node(course.id)
            # TODO: make sure course is not alerady in the curriculum
        for course in self.courses:
            for requisite in course.requisites.keys():
                graph.add_edge(requisite, course.id)
        return graph

    def _create_course_learning_outcome_graph(self) -> "nx.DiGraph[int]":
        """
        Create a curriculum directed graph from a curriculum specification. This graph graph contains courses and learning outcomes
        of the curriculum.
        """
        graph: "nx.DiGraph[int]" = nx.DiGraph()
        for course in self.courses:
            graph.add_node(course.id)
            # TODO: make sure course is not alerady in the curriculum

        for outcome in self.learning_outcomes:
            graph.add_node(outcome.id)
            # TODO: make sure course is not alerady in the curriculum

        # Add edges among courses
        for course in self.courses:
            for requisite in course.requisites.keys():
                graph.add_edge(requisite, course.id)
                nx.set_edge_attributes(
                    graph,
                    {(requisite, course.id): {c_to_c: course.requisites[requisite]}},
                )

        # Add edges among learning_outcomes
        for outcome in self.learning_outcomes:
            for requisite in outcome.requisites:
                graph.add_edge(requisite, outcome.vertex_id[self.id])
                nx.set_edge_attributes(
                    graph, {(requisite, outcome.vertex_id[self.id]): {lo_to_lo: pre}}
                )

        # Add edges between each pair of a course and a learning outcome
        for course in self.courses:
            for outcome in course.learning_outcomes:
                graph.add_edge(outcome.id, course.id)
                nx.set_edge_attributes(
                    graph, {(outcome.id, course.id): {lo_to_c: belong_to}}
                )
        return graph

    def _create_learning_outcome_graph(self) -> "nx.DiGraph[int]":
        """
        Create a curriculum directed graph from a curriculum specification.
        """
        graph: "nx.DiGraph[int]" = nx.DiGraph()
        for i, outcome in enumerate(self.learning_outcomes):
            graph.add_node(i)
            outcome.vertex_id[self.id] = i
        for outcome in self.learning_outcomes:
            for requisite in outcome.requisites.keys():
                graph.add_edge(requisite, outcome.vertex_id[self.id])
        return graph

    # Check if a curriculum graph has requisite cycles.
    def isvalid(self, error_file: Optional[TextIO] = None) -> bool:
        """
        Tests whether or not the curriculum graph associated with the curriculum is valid, i.e.,
        whether or not it contains a requisite cycle, or requisites that cannot be satisfied.

        Returns:
            A boolean value, with `True` indicating the curriculum is valid, and `False` indicating it is not.

        If the graph is not valid, the `error_file` buffer. To view these errors, use::

            >>> errors = StringIO()
            >>> c.isvalid(errors)
            >>> print(errors.getvalue())

        A curriculum graph is not valid if it contains a directed cycle or unsatisfiable requisites; in this
        case it is not possible to complete the curriculum. For the case of unsatisfiable requistes, consider
        two courses ``c_1`` and ``c_2``, with ``c_1`` a prerequisite for ``c_2``. If a third course ``c_3``
        is a strict corequisite for ``c_2``, as well as a requisite for ``c_1`` (or a requisite for any course
        on a path leading to ``c_2``), then the set of requisites cannot be satisfied.
        """
        graph = self.graph.copy()
        # First check for simple cycles
        cycles = list(nx.simple_cycles(graph))
        # Next check for cycles that could be created by strict co-requisites.
        # For every strict-corequisite in the curriculum, add another strict-corequisite between the same two vertices, but in
        # the opposite direction. If this creates any cycles of length greater than 2 in the modified graph (i.e., involving
        # more than the two courses in the strict-corequisite relationship), then the curriculum is unsatisfiable.
        for course in self.courses:
            for req_course, req_type in course.requisites.items():
                if req_type == strict_co:
                    graph.add_edge(
                        self.course_from_id(course.id).id,  # destination vertex
                        self.course_from_id(req_course).id,  # source vertex
                    )
        new_cycles = (
            cyc for cyc in nx.simple_cycles(graph) if len(cyc) != 2
        )  # remove length-2 cycles
        cycles = set(
            tuple(cyc) for cyc in [*new_cycles, *cycles]
        )  # remove redundant cycles
        if len(cycles) != 0 and error_file:
            if self.institution != "":
                error_file.write(f"\n{self.institution}: ")
            error_file.write(f" curriculum '{self.name}' has requisite cycles:\n")
            for cyc in cycles:
                error_file.write("(")
                for i, v in enumerate(cyc):
                    name: str = self.course_from_id(v).name
                    if i != len(cyc) - 1:
                        error_file.write(f"{name}, ")
                    else:
                        error_file.write(f"{name})\n")
        return len(cycles) == 0

    def extraneous_requisites(self, *, debug: bool = False) -> Set[Tuple[int, int]]:
        """
        Determines whether or not the curriculum contains extraneous requisites, and returns them.  Extraneous requisites
        are redundant requisites that are unnecessary in a curriculum.  For example, if a curriculum has the prerequisite
        relationships ``c_1 → c_2 → c_3`` and ``c_1 → c_3``, and ``c_1`` and ``c_2`` are
        *not* co-requisites, then ``c_1 → c_3`` is redundant and therefore extraneous.
        """
        try:
            nx.find_cycle(self.graph)
            raise ValueError(
                "Curriculum graph has cycles, extraneous requisities cannot be determined."
            )
        except nx.NetworkXNoCycle:
            pass
        redundant_reqs: Set[Tuple[int, int]] = set()
        extraneous = False
        string = ""  # create an empty string to hold messages
        for component in nx.weakly_connected_components(self.graph):
            # only consider components with more than one vertex
            if len(component) <= 1:
                continue
            for u in component:
                u_neighbors = list(self.graph.neighbors(u))
                queue: Queue[int] = Queue()
                for neighbor in u_neighbors:
                    queue.put(neighbor)
                while not queue.empty():
                    x = queue.get()
                    x_neighbors = self.graph.neighbors(x)
                    for neighbor in x_neighbors:
                        queue.put(neighbor)
                    for v in self.graph.neighbors(x):
                        if not self.graph.has_edge(u, v):
                            # definitely not redundant requsisite
                            continue
                        # TODO: If this edge is a co-requisite it is an error, as it would be impossible to satsify.
                        # This needs to be checked here.
                        remove: bool = True
                        # check for co- or strict_co requisites
                        for neighbor in u_neighbors:
                            neighbor = self.course_from_id(neighbor)
                            # is there a path from n to v?
                            if nx.has_path(self.graph, neighbor, v):
                                # the requisite relationship between u and n
                                req_type = neighbor.requisites[u]
                                # is u a co or strict_co requisite for n?
                                if req_type == co or req_type == strict_co:
                                    remove = False  # a co or strict_co relationshipo is involved, must keep (u, v)
                        if remove:
                            # make sure redundant requisite wasn't previously found
                            if (u, v) not in redundant_reqs:
                                redundant_reqs.add((u, v))
                                if debug:
                                    string += f"-{self.courses[v].name} has redundant requisite {self.courses[u].name}\n"
                            extraneous = True
        if extraneous and debug:
            if self.institution:
                sys.stdout.write(f"\n{self.institution}: ")
            sys.stdout.write(f"curriculum {self.name} has extraneous requisites:\n")
            sys.stdout.write(string)
        return redundant_reqs

    # Compute the blocking factor of a course
    def blocking_factor_course(self, course: AbstractCourse) -> int:
        """
        The **blocking factor** associated with course ``c_i`` in the curriculum with
        curriculum graph ``G_c = (V,E)`` is defined as:

        .. math::

            b_c(v_i) = \\sum_{v_j \\in V} I(v_i,v_j)

        where ``I(v_i,v_j)`` is the indicator function, which is ``1`` if  ``v_i ⤳ v_j``,
        and ``0`` otherwise. Here ``v_i ⤳ v_j`` denotes that a directed path from vertex
        ``v_i`` to ``v_j`` exists in ``G_c``, i.e., there is a requisite pathway from course
        ``c_i`` to ``c_j`` in curriculum ``c``.
        """
        b = len(reachable_from(self.graph, course.id))
        course.metrics["blocking factor"] = b
        return b

    # Compute the blocking factor of a curriculum
    def blocking_factor(self) -> Tuple[int, List[int]]:
        """
        The **blocking factor** associated with the curriculum is defined as:

        .. math::

            b(G_c) = \\sum_{v_i \\in V} b_c(v_i).

        where ``G_c = (V,E)`` is the curriculum graph associated with the curriculum.
        """
        bf: List[int] = [self.blocking_factor_course(course) for course in self.courses]
        b: int = sum(bf)
        self.metrics["blocking factor"] = b, bf
        return b, bf

    # Compute the delay factor of a course
    def delay_factor_course(self, course: AbstractCourse) -> int:
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
        if course.metrics["delay factor"] == -1:
            self.delay_factor()
        return course.metrics["delay factor"]

    # Compute the delay factor of a curriculum
    def delay_factor(self) -> Tuple[int, List[int]]:
        """
            delay_factor(c:Curriculum)

        The **delay factor** associated with curriculum ``c`` is defined as:
        ```math
        d(G_c) = \\sum_{v_k \\in V} d_c(v_k).
        ```
        where ``G_c = (V,E)`` is the curriculum graph associated with curriculum ``c``.
        """
        g = self.graph
        df: Dict[int, int] = {course.id: 1 for course in self.courses}
        for path in all_paths(g):
            for vtx in path:
                path_length = len(
                    path
                )  # path_length in terms of # of vertices, not edges
                if path_length > df[vtx]:
                    df[vtx] = path_length
        for course in self.courses:
            course.metrics["delay factor"] = df[course.id]
        self.metrics["delay factor"] = sum(df.values()), list(df.values())
        return self.metrics["delay factor"]

    # Compute the centrality of a course
    def centrality_course(self, course: AbstractCourse) -> int:
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
        g = self.graph
        for path in all_paths(g):
            # conditions: path length is greater than 2, target course must be in the path, the target vertex
            # cannot be the first or last vertex in the path
            if (
                course.id in path
                and len(path) > 2
                and path[0] != course.id
                and path[-1] != course.id
            ):
                cent += len(path)
        course.metrics["centrality"] = cent
        return cent

    # Compute the total centrality of all courses in a curriculum
    def centrality(self) -> Tuple[int, List[int]]:
        """
            centrality(c:Curriculum)

        Computes the total **centrality** associated with all of the courses in curriculum ``c``,
        with curriculum graph ``G_c = (V,E)``.
        ```math
        q(c) = \\sum_{v \\in V} q(v).
        ```
        """
        cf: List[int] = [self.centrality_course(course) for course in self.courses]
        cent: int = sum(cf)
        self.metrics["centrality"] = cent, cf
        return cent, cf

    # Compute the complexity of a course
    def complexity_course(self, course: AbstractCourse) -> float:
        """
            complexity(c:Curriculum, course:Int)

        The **complexity** associated with course ``c_i`` in curriculum ``c`` with
        curriculum graph ``G_c = (V,E)`` is defined as:
        ```math
        h_c(v_i) = d_c(v_i) + b_c(v_i)
        ```
        i.e., as a linear combination of the course delay and blocking factors.
        """
        if course.metrics["complexity"] == -1:
            self.complexity()
        return course.metrics["complexity"]

    # Compute the complexity of a curriculum
    def complexity(self) -> Tuple[float, List[float]]:
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
        if self.metrics["delay factor"][0] == -1:
            self.delay_factor()
        if self.metrics["blocking factor"][0] == -1:
            self.blocking_factor()
        course_complexity: List[float] = [
            course.metrics["delay factor"] + course.metrics["blocking factor"]
            for course in self.courses
        ]
        if self.system_type == quarter:
            course_complexity = [
                round((complexity * 2) / 3, ndigits=1)
                for complexity in course_complexity
            ]
        for course, complexity in zip(self.courses, course_complexity):
            course.metrics["complexity"] = complexity
        curric_complexity: float = sum(course_complexity)
        self.metrics["complexity"] = curric_complexity, course_complexity
        return curric_complexity, course_complexity

    # Find all the longest paths in a curriculum.
    def longest_paths(self) -> List[List[AbstractCourse]]:
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
        lps: List[List[AbstractCourse]] = [
            self.courses_from_vertices(path) for path in longest_paths(self.graph)
        ]
        self.metrics["longest paths"] = lps
        return lps

    def compare_curricula(self, other: "Curriculum") -> StringIO:
        """
        Compare the metrics associated with two curricula
        to print out the report, use: println(String(take!(report))), where report is the IOBuffer returned by this function
        """
        report = StringIO()
        if self.metrics.keys() != other.metrics.keys():
            raise Exception(
                "cannot compare curricula, they do not have the same metrics"
            )
        report.write(f"Comparing: C1 = {self.name} and C2 = {other.name}\n")
        for k in Curriculum._metric_keys:
            report.write(f" Curricular {k}: ")
            metric1 = self.metrics[k][0]
            metric2 = self.metrics[k][0]
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
            for i, c in enumerate([self, other]):
                metric = c.metrics[k]
                maxval = max(metric[1])
                pos = [i for i, x in enumerate(metric[1]) if x == maxval]
                report.write(f"   Largest {k} value in C{i} is {maxval} for course: ")
                for p in pos:
                    report.write(f"{c.courses[p].name}  ")
                report.write("\n")
        return report

    @overload
    def courses_from_vertices(
        self, vertices: List[int], *, course: Literal["object"] = "object"
    ) -> List[AbstractCourse]:
        ...

    @overload
    def courses_from_vertices(
        self, vertices: List[int], *, course: Literal["name", "fullname"]
    ) -> List[str]:
        ...

    def courses_from_vertices(
        self,
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
            return [self.course_from_id(v) for v in vertices]
        else:
            course_list: List[str] = []
            for v in vertices:
                c = self.courses[v]
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
    def basic_metrics(self) -> StringIO:
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
        self.complexity()
        self.centrality()
        self.longest_paths()
        max_bf: int = 0
        max_df: int = 0
        max_cc: float = 0
        max_cent: int = 0
        max_bf_courses: List[AbstractCourse] = []
        max_df_courses: List[AbstractCourse] = []
        max_cc_courses: List[AbstractCourse] = []
        max_cent_courses: List[AbstractCourse] = []
        for c in self.courses:
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
            self.metrics["max. blocking factor"] = max_bf
            self.metrics["max. blocking factor courses"] = max_bf_courses
            self.metrics["max. centrality"] = max_cent
            self.metrics["max. centrality courses"] = max_cent_courses
            self.metrics["max. delay factor"] = max_df
            self.metrics["max. delay factor courses"] = max_df_courses
            self.metrics["max. complexity"] = max_cc
            self.metrics["max. complexity courses"] = max_cc_courses
        # write metrics to IO buffer
        buf.write(f"\n{self.institution} ")
        buf.write(f"\nCurriculum: {self.name}\n")
        buf.write(f"  credit hours = {self.credit_hours}\n")
        buf.write(f"  number of courses = {self.num_courses}")
        buf.write("\n  Blocking Factor --\n")
        buf.write(f"    entire curriculum = {self.metrics['blocking factor'][0]}\n")
        buf.write(f"    max. value = {max_bf}, ")
        buf.write("for course(s): ")
        write_course_names(buf, max_bf_courses)
        buf.write("\n  Centrality --\n")
        buf.write(f"    entire curriculum = {self.metrics['centrality'][0]}\n")
        buf.write(f"    max. value = {max_cent}, ")
        buf.write("for course(s): ")
        write_course_names(buf, max_cent_courses)
        buf.write("\n  Delay Factor --\n")
        buf.write(f"    entire curriculum = {self.metrics['delay factor'][0]}\n")
        buf.write(f"    max. value = {max_df}, ")
        buf.write("for course(s): ")
        write_course_names(buf, max_df_courses)
        buf.write("\n  Complexity --\n")
        buf.write(f"    entire curriculum = {self.metrics['complexity'][0]}\n")
        buf.write(f"    max. value = {max_cc}, ")
        buf.write("for course(s): ")
        write_course_names(buf, max_cc_courses)
        buf.write("\n  Longest Path(s) --\n")
        buf.write(
            f"    length = {len(self.metrics['longest paths'][0])}, number of paths = {len(self.metrics['longest paths'])}\n    path(s):\n",
        )
        for i, path in enumerate(self.metrics["longest paths"]):
            buf.write(f"    path {i} = ")
            write_course_names(buf, path, separator=" -> ")
            buf.write("\n")
        return buf

    def similarity(self, other: "Curriculum", *, strict: bool = True) -> float:
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
        if other.num_courses == 0:
            raise Exception(
                f"Curriculum {other.name} does not have any courses, similarity cannot be computed"
            )
        if self == other:
            return 1
        matches = 0
        if strict == True:
            for course in self.courses:
                if course in other.courses:
                    matches += 1
        else:  # strict == False
            for course in self.courses:
                for basis_course in other.courses:
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
        return matches / other.num_courses

    def merge_curricula(
        self,
        other: "Curriculum",
        name: str,
        *,
        match_criteria: List[MatchCriterion] = [],
        learning_outcomes: List[LearningOutcome] = [],
        degree_type: str = "BS",  # Julia version uses `BS`, which isn't defined anywhere
        system_type: System = semester,
        institution: str = "",
        CIP: str = "",
    ) -> "Curriculum":
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
        merged_courses = self.courses.copy()
        extra_courses: List[AbstractCourse] = []  # courses in c2 but not in c1
        for course in other.courses:
            matched = False
            for target_course in self.courses:
                if course.match(target_course, match_criteria) == True:
                    matched = True
                #    skip TODO
            if not matched:
                extra_courses.append(course)
        # patch-up requisites of extra_courses, using course ids form c1 where appropriate
        # for each extra course create an indentical coures, but with a new course id
        new_courses: List[AbstractCourse] = [c.copy() for c in extra_courses]
        for c, new_course in zip(extra_courses, new_courses):
            #    print(f"\n {c.name}: ")
            #    print(f"total requisistes = {len(c.requisites)},")
            for req in c.requisites:
                #        print(f" requisite id: {req} ")
                req_course = other.course_from_id(req)
                if req_course.find_match(merged_courses, match_criteria) != None:
                    # requisite already exists in c1
                    #            print(f" match in c1 - {course_from_id(c1, req).name} ")
                    new_course.add_requisite(req_course, c.requisites[req])
                elif req_course.find_match(extra_courses, match_criteria) != None:
                    # requisite is not in c1, but it's in c2 -- use the id of the new course created for it
                    #            print(" match in extra courses, ")
                    i = extra_courses.index(req_course)
                    #            print(f" index of match = {i} ")
                    new_course.add_requisite(new_courses[i], c.requisites[req])
                else:  # requisite is neither in c1 or 2 -- this shouldn't happen => error
                    raise Exception(f"requisite error on course: {c.name}")
        merged_courses = [*merged_courses, *new_courses]
        merged_curric = Curriculum(
            name,
            merged_courses,
            learning_outcomes=learning_outcomes,
            degree_type=degree_type,
            system_type=system_type,
            institution=institution,
            cip=CIP,
        )
        return merged_curric

    def dead_ends(
        self, prefixes: FrozenSet[str]
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
        paths = all_paths(self.graph)
        for p in paths:
            course = self.course_from_id(p[-1])
            if not isinstance(course, Course) or course.prefix == "":
                continue
            if course.prefix not in prefixes:
                if course not in dead_end_courses:
                    dead_end_courses.append(course)
        if "dead end" in self.metrics:
            if prefixes in self.metrics["dead end"]:
                self.metrics["dead end"][prefixes] = dead_end_courses
        else:
            self.metrics["dead end"] = {prefixes: dead_end_courses}
        return (prefixes, dead_end_courses)

    def __repr__(self) -> str:
        return f"Curriculum(id={self.id}, name={repr(self.name)}, institution={repr(self.institution)}, degree_type={repr(self.degree_type)}, system_type={self.system_type} cip={repr(self.cip)}, courses={self.courses}, num_courses={self.num_courses}, credit_hours={self.credit_hours}, graph={self.graph}, learning_outcomes={self.learning_outcomes}, learning_outcome_graph={self.learning_outcome_graph}, course_learning_outcome_graph={self.course_learning_outcome_graph}, metrics={self.metrics}, metadata={self.metadata})"
