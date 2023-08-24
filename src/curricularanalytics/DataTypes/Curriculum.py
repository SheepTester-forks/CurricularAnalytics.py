"""
Curriculum data type:
The required curriculum associated with a degree program.

The curriculum-based metrics in this toolbox are based upon the graph structure of a
curriculum.  Specifically, assume curriculum ``c`` consists of ``n`` courses ``\\{c_1, \\ldots, c_n\\}``,
and that there are ``m`` requisite (prerequisite or co-requsitie) relationships between these courses.
A curriculum graph ``G_c = (V,E)`` is formed by creating a vertex set ``V = \\{v_1, \\ldots, v_n\\}``
(i.e., one vertex for each course) along with an edge set ``E = \\{e_1, \\ldots, e_m\\}``, where a
directed edge from vertex ``v_i`` to ``v_j`` is in ``E`` if course ``c_i`` is a requisite for course ``c_j``.
"""

from functools import cached_property
from io import StringIO
import math
from queue import Queue
import sys
from typing import (
    Any,
    Dict,
    FrozenSet,
    List,
    Literal,
    NamedTuple,
    Optional,
    Set,
    TextIO,
    Tuple,
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


class BasicMetrics(NamedTuple):
    max_blocking_factor: int
    max_blocking_factor_courses: List[AbstractCourse]
    max_delay_factor: int
    max_delay_factor_courses: List[AbstractCourse]
    max_centrality: int
    max_centrality_courses: List[AbstractCourse]
    max_complexity: float
    max_complexity_courses: List[AbstractCourse]


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
    metadata: Dict[str, Any]
    "Curriculum-related metadata"

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
        self.metadata = {}
        self.learning_outcomes = learning_outcomes
        self.learning_outcome_graph = self._create_learning_outcome_graph()
        self.course_learning_outcome_graph = (
            self._create_course_learning_outcome_graph()
        )
        if warn:
            errors = StringIO()
            if not self.isvalid(errors):
                # TODO: yellow text
                print(
                    "WARNING: Curriculum was created, but is invalid due to requisite cycle(s):"
                )
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
            return next(course for course in self.courses if course.id == hash_val)
        except StopIteration:
            raise LookupError(
                f"Course: {prefix} {num}: {name} at {institution} does not exist in curriculum: {self.name}"
            )

    def course_from_id(self, id: int) -> AbstractCourse:
        "Return the course associated with a course id in a curriculum"
        for course in self.courses:
            if course.id == id:
                return course
        raise KeyError(f"The course associated with id {id} is not in the curriculum.")

    def lo_from_id(self, id: int) -> LearningOutcome:
        "Return the lo associated with a lo id in a curriculum"
        for outcome in self.learning_outcomes:
            if outcome.id == id:
                return outcome
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
        two courses :math:`c_1` and :math:`c_2`, with :math:`c_1` a prerequisite for :math:`c_2`. If a third course :math:`c_3`
        is a strict corequisite for :math:`c_2`, as well as a requisite for :math:`c_1` (or a requisite for any course
        on a path leading to :math:`c_2`), then the set of requisites cannot be satisfied.
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
        r"""
        Determines whether or not the curriculum contains extraneous requisites, and returns them.  Extraneous requisites
        are redundant requisites that are unnecessary in a curriculum.  For example, if a curriculum has the prerequisite
        relationships :math:`c_1 \rightarrow c_2 \rightarrow c_3` and :math:`c_1 \rightarrow c_3`, and :math:`c_1` and :math:`c_2` are
        *not* co-requisites, then :math:`c_1 \rightarrow c_3` is redundant and therefore extraneous.
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
                            # is there a path from n to v?
                            if nx.has_path(self.graph, neighbor, v):
                                # the requisite relationship between u and n
                                req_type = self.course_from_id(neighbor).requisites[u]
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
    def course_blocking_factor(self, course: AbstractCourse) -> int:
        r"""
        The **blocking factor** associated with course :math:`c_i` in the curriculum with
        curriculum graph :math:`G_c = (V,E)` is defined as:

        .. math::

            b_c(v_i) = \sum_{v_j \in V} I(v_i,v_j)

        where :math:`I(v_i,v_j)` is the indicator function, which is :math:`1` if  :math:`v_i \leadsto v_j`,
        and :math:`0` otherwise. Here :math:`v_i \leadsto v_j` denotes that a directed path from vertex
        :math:`v_i` to :math:`v_j` exists in :math:`G_c`, i.e., there is a requisite pathway from course
        :math:`c_i` to :math:`c_j` in curriculum :math:`c`.
        """
        return self.blocking_factor[1][course.id]

    # Compute the blocking factor of a curriculum
    @cached_property
    def blocking_factor(self) -> Tuple[int, Dict[int, int]]:
        r"""
        The **blocking factor** associated with the curriculum is defined as:

        .. math::

            b(G_c) = \sum_{v_i \in V} b_c(v_i).

        where :math:`G_c = (V,E)` is the curriculum graph associated with the curriculum.
        """
        blocking_factors: Dict[int, int] = {
            course.id: len(reachable_from(self.graph, course.id))
            for course in self.courses
        }
        return sum(blocking_factors.values()), blocking_factors

    # Compute the delay factor of a course
    def course_delay_factor(self, course: AbstractCourse) -> int:
        r"""
            delay_factor(c:Curriculum, course:Int)

        The **delay factor** associated with course :math:`c_k` in curriculum :math:`c` with
        curriculum graph :math:`G_c = (V,E)` is the number of vertices in the longest path
        in :math:`G_c` that passes through :math:`v_k`. If :math:`\#(p)` denotes the number of
        vertices in the directed path :math:`p` in :math:`G_c`, then we can define the delay factor of
        course :math:`c_k` as:

        .. math::

            d_c(v_k) = \max_{i,j,l,m}\left\{\#(v_i  \overset{p_l}{\leadsto} v_k \overset{p_m}{\leadsto} v_j)\right\}

        where :math:`v_i \overset{p}{\leadsto} v_j` denotes a directed path :math:`p` in :math:`G_c` from vertex
        :math:`v_i` to :math:`v_j`.
        """
        return self.delay_factor[1][course.id]

    # Compute the delay factor of a curriculum
    @cached_property
    def delay_factor(self) -> Tuple[int, Dict[int, int]]:
        r"""
        The **delay factor** associated with the curriculum is defined as:

        .. math::

            d(G_c) = \sum_{v_k \in V} d_c(v_k).

        where ``G_c = (V,E)`` is the curriculum graph associated with the curriculum.
        """
        delay_factors: Dict[int, int] = {course.id: 1 for course in self.courses}
        for path in all_paths(self.graph):
            for vertex in path:
                # path_length in terms of # of vertices, not edges
                delay_factors[vertex] = max(delay_factors[vertex], len(path))
        return sum(delay_factors.values()), delay_factors

    # Compute the centrality of a course
    def course_centrality(self, course: AbstractCourse) -> int:
        r"""
        Consider a curriculum graph :math:`G_c = (V,E)`, and a vertex :math:`v_i \in V`. Furthermore,
        consider all paths between every pair of vertices :math:`v_j, v_k \in V` that satisfy the
        following conditions:
        - :math:`v_i, v_j, v_k` are distinct, i.e., :math:`v_i \neq v_j, v_i \neq v_k` and :math:`v_j \neq v_k`;
        - there is a path from :math:`v_j` to :math:`v_k` that includes :math:`v_i`, i.e., :math:`v_j \leadsto v_i \leadsto v_k`;
        - :math:`v_j` has in-degree zero, i.e., :math:`v_j` is a "source"; and
        - :math:`v_k` has out-degree zero, i.e., :math:`v_k` is a "sink".
        Let :math:`P_{v_i} = \{p_1, p_2, \ldots\}` denote the set of all directed paths that satisfy these
        conditions.
        Then the **centrality** of :math:`v_i` is defined as

        .. math::

            q(v_i) = \sum_{l=1}^{\left| P_{v_i} \right|} \#(p_l).

        where :math:`\#(p)` denotes the number of vertices in the directed path :math:`p` in :math:`G_c`.
        """
        return self.centrality[1][course.id]

    # Compute the total centrality of all courses in a curriculum
    @cached_property
    def centrality(self) -> Tuple[int, Dict[int, int]]:
        r"""
        Computes the total **centrality** associated with all of the courses in the curriculum,
        with curriculum graph :math:`G_c = (V,E)`.

        .. math::

            q(c) = \sum_{v \in V} q(v).
        """
        centralities: Dict[int, int] = {
            course.id: sum(
                len(path)
                for path in all_paths(self.graph)
                # conditions: path length is greater than 2, target course must be in the path, the target vertex
                # cannot be the first or last vertex in the path
                if (
                    course.id in path
                    and len(path) > 2
                    and path[0] != course.id
                    and path[-1] != course.id
                )
            )
            for course in self.courses
        }
        return sum(centralities.values()), centralities

    # Compute the complexity of a course
    def course_complexity(self, course: AbstractCourse) -> float:
        """
        The **complexity** associated with course :math`c_i` in the curriculum with
        curriculum graph :math`G_c = (V,E)` is defined as:

        .. math::

            h_c(v_i) = d_c(v_i) + b_c(v_i)

        i.e., as a linear combination of the course delay and blocking factors.
        """
        return self.complexity[1][course.id]

    # Compute the complexity of a curriculum
    @cached_property
    def complexity(self) -> Tuple[float, Dict[int, float]]:
        r"""
            complexity(c:Curriculum, course:Int)

        The **complexity** associated with curriculum ``c`` with  curriculum graph ``G_c = (V,E)``
        is defined as:

        ```math
        h(G_c) = \sum_{v \in V} \left(d_c(v) + b_c(v)\right).
        ```

        For the example curricula considered above, the curriculum in part (a) has an overall complexity of 15,
        while the curriculum in part (b) has an overall complexity of 17. This indicates that the curriculum
        in part (b) will be slightly more difficult to complete than the one in part (a). In particular, notice
        that course ``v_1`` in part (a) has the highest individual course complexity, but the combination of
        courses ``v_1`` and ``v_2`` in part (b), which both must be passed before a student can attempt course
        ``v_3`` in that curriculum, has a higher combined complexity.
        """
        course_complexity: Dict[int, float] = {
            course.id: self.course_delay_factor(course)
            + self.course_blocking_factor(course)
            for course in self.courses
        }
        if self.system_type == quarter:
            course_complexity = {
                course_id: round((complexity * 2) / 3, ndigits=1)
                for course_id, complexity in course_complexity.items()
            }
        return sum(course_complexity.values()), course_complexity

    # Find all the longest paths in a curriculum.
    @cached_property
    def longest_paths(self) -> List[List[AbstractCourse]]:
        """
        Finds longest paths in the curriculum, and returns an array of course arrays, where
        each course array contains the courses in a longest path.
        """
        return [self.courses_from_ids(path) for path in longest_paths(self.graph)]

    def compare(self, other: "Curriculum") -> StringIO:
        """
        Compare the metrics associated with two curricula.

        Returns:
            A `StringIO`. To print out the report, use: ``print(report.getvalue())``
        """
        report = StringIO()
        report.write(f"Comparing: C1 = {self.name} and C2 = {other.name}\n")
        metrics = {
            "blocking factor": (self.blocking_factor, other.blocking_factor),
            "delay factor": (self.delay_factor, other.delay_factor),
            "centrality": (self.centrality, other.centrality),
            "complexity": (self.complexity, other.complexity),
        }
        for metric_name, (metric1, metric2) in metrics.items():
            report.write(f" Curricular {metric_name}: ")
            diff = metric1[0] - metric2[0]
            if diff > 0:
                report.write(
                    "C1 is %.1f units (%.0f%%) larger than C2\n"
                    % (diff, 100 * diff / metric2[0]),
                )
            elif diff < 0:
                report.write(
                    "C1 is %.1f units (%.0f%%) smaller than C2\n"
                    % (-diff, 100 * (-diff) / metric2[0]),
                )
            else:
                report.write(f"C1 and C2 have the same curricular {metric_name}\n")

            report.write(f"  Course-level {metric_name}:\n")
            maxval = max(metric1[1])
            report.write(
                f"   Largest {metric_name} value in C1 is {maxval} for course: "
            )
            for course in self.courses:
                if metric1[1][course.id] == maxval:
                    report.write(f"{course.name}  ")
            report.write("\n")
            maxval = max(metric2[1])
            report.write(
                f"   Largest {metric_name} value in C2 is {maxval} for course: "
            )
            for course in other.courses:
                if metric2[1][course.id] == maxval:
                    report.write(f"{course.name}  ")
            report.write("\n")
        return report

    @overload
    def courses_from_ids(
        self, ids: List[int], *, type: Literal["object"] = "object"
    ) -> List[AbstractCourse]:
        ...

    @overload
    def courses_from_ids(
        self, ids: List[int], *, type: Literal["name", "fullname"]
    ) -> List[str]:
        ...

    def courses_from_ids(
        self,
        ids: List[int],
        *,
        type: Literal["object", "name", "fullname"] = "object",
    ) -> Union[List[AbstractCourse], List[str]]:
        """
        Create a list of courses or course names from an array of course IDs.

        Returns:
            - course data objects if ``type="object"``
            - the names of courses if ``type="name"``
            - the full names of courses ``{prefix} {num} - {name}`` if ``type="fullname"``
        """
        if type == "object":
            return [self.course_from_id(id) for id in ids]
        else:
            return [
                f"{course.prefix} {course.num} - {course.name}"
                if type == "fullname" and isinstance(course, Course)
                else course.name
                for course in self.courses
                if course.id in ids
            ]

    # Basic metrics for a currciulum.
    @cached_property
    def basic_metrics(self) -> BasicMetrics:
        """
        Compute the basic metrics associated with the curriculum `c`.

        The basic metrics computed include:

        - blocking factor: The blocking factor of the entire curriculum, and of each course in the curriculum.
        - centrality: The centrality measure associated with the entire curriculum, and of each course in the curriculum.
        - delay factor: The delay factor of the entire curriculum, and of each course in the curriculum.
        - curricular complexity: The curricular complexity of the entire curriculum, and of each course in the curriculum.

        Complete descriptions of these metrics are provided above.
        """
        # compute all curricular metrics
        max_blocking_factor: int = max(self.blocking_factor[1].values())
        max_delay_factor: int = max(self.delay_factor[1].values())
        max_centrality: int = max(self.centrality[1].values())
        max_complexity: float = max(self.complexity[1].values())
        return BasicMetrics(
            max_blocking_factor,
            [
                course
                for course in self.courses
                if self.blocking_factor[1][course.id] == max_blocking_factor
            ],
            max_delay_factor,
            [
                course
                for course in self.courses
                if self.delay_factor[1][course.id] == max_delay_factor
            ],
            max_centrality,
            [
                course
                for course in self.courses
                if self.centrality[1][course.id] == max_centrality
            ],
            max_complexity,
            [
                course
                for course in self.courses
                if self.complexity[1][course.id] == max_complexity
            ],
        )

    def basic_metrics_to_buffer(self) -> StringIO:
        """
        Return an IO buffer containing the basic metrics associated with curriculum.

        The basic metrics computed include:

        - number of credit hours: The total number of credit hours in the curriculum.
        - number of courses: The total courses in the curriculum.
        - blocking factor: The blocking factor of the entire curriculum, and of each course in the curriculum.
        - centrality: The centrality measure associated with the entire curriculum, and of each course in the curriculum.
        - delay factor: The delay factor of the entire curriculum, and of each course in the curriculum.
        - curricular complexity: The curricular complexity of the entire curriculum, and of each course in the curriculum.

        Complete descriptions of these metrics are provided above.

        Example:
            >>> metrics = curriculum.basic_metrics_to_buffer()
            >>> print(metrics.getvalue())
        ```
        """
        buffer = StringIO()
        # write metrics to IO buffer
        buffer.write(f"\n{self.institution} ")
        buffer.write(f"\nCurriculum: {self.name}\n")
        buffer.write(f"  credit hours = {self.credit_hours}\n")
        buffer.write(f"  number of courses = {self.num_courses}")
        buffer.write("\n  Blocking Factor --\n")
        buffer.write(f"    entire curriculum = {self.blocking_factor[0]}\n")
        buffer.write(f"    max. value = {self.basic_metrics.max_blocking_factor}, ")
        buffer.write("for course(s): ")
        write_course_names(buffer, self.basic_metrics.max_blocking_factor_courses)
        buffer.write("\n  Centrality --\n")
        buffer.write(f"    entire curriculum = {self.centrality[0]}\n")
        buffer.write(f"    max. value = {self.basic_metrics.max_centrality}, ")
        buffer.write("for course(s): ")
        write_course_names(buffer, self.basic_metrics.max_centrality_courses)
        buffer.write("\n  Delay Factor --\n")
        buffer.write(f"    entire curriculum = {self.delay_factor[0]}\n")
        buffer.write(f"    max. value = {self.basic_metrics.max_delay_factor}, ")
        buffer.write("for course(s): ")
        write_course_names(buffer, self.basic_metrics.max_delay_factor_courses)
        buffer.write("\n  Complexity --\n")
        buffer.write(f"    entire curriculum = {self.complexity[0]}\n")
        buffer.write(f"    max. value = {self.basic_metrics.max_complexity}, ")
        buffer.write("for course(s): ")
        write_course_names(buffer, self.basic_metrics.max_complexity_courses)
        buffer.write("\n  Longest Path(s) --\n")
        buffer.write(
            f"    length = {len(self.longest_paths[0])}, number of paths = {len(self.longest_paths)}\n    path(s):\n",
        )
        for i, path in enumerate(self.longest_paths, 1):
            buffer.write(f"    path {i} = ")
            write_course_names(buffer, path, separator=" -> ")
            buffer.write("\n")
        return buffer

    def similarity(self, basis: "Curriculum", *, strict: bool = True) -> float:
        """
        Compute how similar curriculum ``c1`` is to curriculum ``c2``.  The similarity metric is computed by comparing how many courses in
        ``c1`` are also in ``c2``, divided by the total number of courses in ``c2``.  Thus, for two curricula, this metric is not symmetric. A
        similarity value of ``1`` indicates that ``c1`` and ``c2`` are identical, whil a value of ``0`` means that none of the courses in ``c1``
        are in ``c2``.

        Args:
            basis: The curriculum serving as the basis for comparison.
            strict: If true (default), two courses are considered the same if every field in the two courses are the same; if false,
              two courses are considered the same if they have the same course name, or if they have the same course prefix and number.
        """
        if basis.num_courses == 0:
            raise ValueError(
                f"Curriculum {basis.name} does not have any courses, similarity cannot be computed"
            )
        if self == basis:
            return 1
        matches = 0
        for course in self.courses:
            if strict:
                if course in basis.courses:
                    matches += 1
            else:
                for basis_course in basis.courses:
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
        return matches / basis.num_courses

    def merge(
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
        Merge the two curricula ``c1`` and ``c2`` supplied as input into a single curriculum based on the match criteria applied
        to the courses in the two curricula.  All courses in curriculum ``c1`` will appear in the merged curriculum.  If a course in
        curriculum ``c2`` matches a course in curriculum ``c1``, that course serves as a matched course in the merged curriculum.
        If there is no match for a course in curriculum ``c2`` to the set of courses in curriculum ``c1``, course ``c2`` is added
        to the set of courses in the merged curriculum.

        Args:
            other: The other curriculum.
            match_criteria (optional): List of course items that must match, if no match critera are supplied, the
              courses must be identical (at the level of memory allocation).

        Allowable match criteria include:
        - `prefix`: the course prefixes must be identical.
        - `num`: the course numbers must be indentical.
        - `name`: the course names must be identical.
        - `canonical name`: the course canonical names must be identical.
        - `credit hours`: the course credit hours must be indentical.
        """
        merged_courses = self.courses.copy()
        extra_courses: List[AbstractCourse] = []
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
        new_courses: List[AbstractCourse] = [course.copy() for course in extra_courses]
        for course, new_course in zip(extra_courses, new_courses):
            #    print(f"\n {c.name}: ")
            #    print(f"total requisistes = {len(c.requisites)},")
            for req in course.requisites.keys():
                #        print(f" requisite id: {req} ")
                req_course = other.course_from_id(req)
                if req_course.find_match(merged_courses, match_criteria) != None:
                    # requisite already exists in c1
                    #            print(f" match in c1 - {course_from_id(c1, req).name} ")
                    new_course.add_requisite(req_course, course.requisites[req])
                elif req_course.find_match(extra_courses, match_criteria) != None:
                    # requisite is not in c1, but it's in c2 -- use the id of the new course created for it
                    #            print(" match in extra courses, ")
                    i = extra_courses.index(req_course)
                    #            print(f" index of match = {i} ")
                    new_course.add_requisite(new_courses[i], course.requisites[req])
                else:  # requisite is neither in c1 or 2 -- this shouldn't happen => error
                    raise Exception(f"requisite error on course: {course.name}")
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
        Finds all courses in the curriculum that appear at the end of a path (i.e., sink vertices).  If a course does not have a prefix, it is excluded from
        the analysis.

        Args:
            prefixes: An array of course prefix strings.

        Returns:
            Those courses that do not have one of the course prefixes listed in the `prefixes` array

        Examples:
            For instance, the following will find all courses in `curric` that appear at the end of any course path in the curriculum,
            and do *not* have `BIO` as a prefix.  One might consider these courses "dead ends," as their course outcomes are not used by any
            major-specific course, i.e., by any course with the prefix `BIO`.

            >>> curric.dead_ends(frozenset({"BIO"}))
        """
        dead_end_courses: List[Course] = []
        paths = all_paths(self.graph)
        for path in paths:
            course = self.course_from_id(path[-1])
            if not isinstance(course, Course) or course.prefix == "":
                continue
            if course.prefix not in prefixes:
                if course not in dead_end_courses:
                    dead_end_courses.append(course)
        return prefixes, dead_end_courses

    def __repr__(self) -> str:
        return f"Curriculum(id={self.id}, name={repr(self.name)}, institution={repr(self.institution)}, degree_type={repr(self.degree_type)}, system_type={self.system_type} cip={repr(self.cip)}, courses={self.courses}, num_courses={self.num_courses}, credit_hours={self.credit_hours}, graph={self.graph}, learning_outcomes={self.learning_outcomes}, learning_outcome_graph={self.learning_outcome_graph}, course_learning_outcome_graph={self.course_learning_outcome_graph}, metadata={self.metadata})"


def basic_statistics(metric_name: str, metrics: List[float]) -> StringIO:
    buffer = StringIO()
    # set initial values used to find min and max metric values
    total_metric = 0
    STD_metric = 0
    max_metric = -math.inf
    min_metric = math.inf
    max_metric = metrics[0]
    min_metric = metrics[0]
    # metric where total curricular metric as well as course-level metrics are stored in an array
    for value in metrics:
        # metric where total curricular metric as well as course-level metrics are stored in an array
        total_metric += value
        if value > max_metric:
            max_metric = value
        if value < min_metric:
            min_metric = value
    avg_metric = total_metric / len(metrics)
    for value in metrics:
        STD_metric = (value - avg_metric) ** 2
    STD_metric = math.sqrt(STD_metric / len(metrics))
    buffer.write(f"\n Metric -- {metric_name}")
    buffer.write(f"\n  Number of curricula = {len(metrics)}")
    buffer.write(f"\n  Mean = {avg_metric}")
    buffer.write(f"\n  STD = {STD_metric}")
    buffer.write(f"\n  Max. = {max_metric}")
    buffer.write(f"\n  Min. = {min_metric}")
    return buffer


def homology(curricula: List[Curriculum], *, strict: bool = False) -> List[List[float]]:
    return [[c1.similarity(c2, strict=strict) for c2 in curricula] for c1 in curricula]
