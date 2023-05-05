##############################################################
# Curriculum data type
# The required curriculum associated with a degree program
from io import StringIO
from typing import Any, Dict, FrozenSet, List, Literal, Set, Tuple, TypedDict

import networkx as nx

from src.DataTypes.Course import AbstractCourse, Course, course_id
from src.DataTypes.DataTypes import (
    Requisite,
    System,
    belong_to,
    c_to_c,
    lo_to_c,
    lo_to_lo,
    pre,
    semester,
    strict_co,
)
from src.DataTypes.LearningOutcome import LearningOutcome

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
    *degree program* synonymously. To instantiate a `Curriculum` use:

        Curriculum(name, courses; <keyword arguments>)

    # Arguments
    Required:
    - `name:str` : the name of the curriculum.
    - `courses:Array{Course}` : the collection of required courses that comprise the curriculum.
    Keyword:
    - `degree_type:str` : the type of degree, e.g. BA, BBA, BSc, BEng, etc.
    - `institution:str` : the name of the institution offering the curriculum.
    - `system_type:System` : the type of system the institution uses, allowable
        types: `semester` (default), `quarter`.
    - `CIP:str` : the Classification of Instructional Programs (CIP) code for the
        curriculum.  See: `https://nces.ed.gov/ipeds/cipcode`

    # Examples:
    ```julia-repl
    julia> Curriculum("Biology", courses, institution="South Harmon Tech", degree_type=AS, CIP="26.0101")
    ```
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

    metric_keys: Set[CurriculumMetricKey] = {
        "blocking factor",
        "delay factor",
        "centrality",
        "complexity",
    }

    def __init__(
        self,
        name: str,
        courses: List[AbstractCourse],
        learning_outcomes: List[LearningOutcome] = [],
        degree_type: str = "BS",
        system_type: System = semester,
        institution: str = "",
        CIP: str = "",
        id: int = 0,
        sortby_ID: bool = True,
    ) -> None:
        "Constructor"
        self.name = name
        self.degree_type = degree_type
        self.system_type = system_type
        self.institution = institution
        if id == 0:
            self.id = hash(self.name + self.institution + str(self.degree_type))
        else:
            self.id = id
        self.cip = CIP
        if sortby_ID:
            self.courses = sorted(courses, key=lambda c: c.id)
        else:
            self.courses = courses
        self.num_courses = len(self.courses)
        self.credit_hours = self.total_credits()
        self.graph = nx.DiGraph()
        self.create_graph()
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
        self.learning_outcome_graph = nx.DiGraph()
        self.create_learning_outcome_graph()
        self.course_learning_outcome_graph = nx.DiGraph()
        self.create_course_learning_outcome_graph()
        errors = StringIO()
        if not self.isvalid(errors):
            print(
                "WARNING: Curriculum was created, but is invalid due to requisite cycle(s):"
            )  # TODO: yellow
            print(errors)

    # TODO: update a curriculum graph if requisites have been added/removed or courses have been added/removed
    # def update_curriculum(curriculum:Curriculum, courses:Array{Course}=())
    #    # if courses array is empty, no new courses were added
    # end

    def convert_ids(self) -> "Curriculum":
        "Converts course ids, from those used in CSV file format, to the standard hashed id used by the data structures in the toolbox"
        for c1 in self.courses:
            old_id = c1.id
            c1.id = c1.default_id()
            if old_id != c1.id:
                for c2 in self.courses:
                    if old_id in (c2.requisites):
                        c2.add_requisite(c1, c2.requisites[old_id])
                        del c2.requisites[old_id]
        return self

    def map_vertex_ids(self) -> Dict[int, int]:
        "Map course IDs to vertex IDs in an underlying curriculum graph."
        mapped_ids: Dict[int, int] = {}
        for c in self.courses:
            mapped_ids[c.id] = c.vertex_id[self.id]
        return mapped_ids

    def map_lo_vertex_ids(self) -> Dict[int, int]:
        "Map lo IDs to vertex IDs in an underlying curriculum graph."
        mapped_ids: Dict[int, int] = {}
        for lo in self.learning_outcomes:
            mapped_ids[lo.id] = lo.vertex_id[self.id]
        return mapped_ids

    def course(
        self, prefix: str, num: str, name: str, institution: str
    ) -> AbstractCourse:
        "Compute the hash value used to create the id for a course, and return the course if it exists in the curriculum supplied as input"
        hash_val = course_id(name, prefix, num, institution)
        if hash_val in (c.id for c in self.courses):
            return self.courses[next(x.id == hash_val for x in self.courses)]
        else:
            raise Exception(
                f"Course: {prefix} {num}: {name} at {institution} does not exist in curriculum: {self.name}"
            )

    def course_from_id(self, id: int) -> AbstractCourse:
        "Return the course associated with a course id in a curriculum"
        for c in self.courses:
            if c.id == id:
                return c
        raise ValueError(
            f"The course associated with id {id} is not in the curriculum."
        )

    def lo_from_id(self, id: int) -> LearningOutcome:
        "Return the lo associated with a lo id in a curriculum"
        for lo in self.learning_outcomes:
            if lo.id == id:
                return lo
        raise ValueError(f"The lo associated with id {id} is not in the curriculum.")

    def course_from_vertex(self, vertex: int) -> AbstractCourse:
        "Return the course associated with a vertex id in a curriculum graph"
        return self.courses[vertex]

    def total_credits(self) -> float:
        "The total number of credit hours in a curriculum"
        total_credits = 0
        for c in self.courses:
            total_credits += c.credit_hours
        return total_credits

    def create_graph(self) -> None:
        """
            create_graph!(c:Curriculum)

        Create a curriculum directed graph from a curriculum specification. The graph is stored as a
        LightGraph.jl implemenation within the Curriculum data object.
        """
        for i, c in enumerate(self.courses):
            self.graph.add_node(i)
            c.vertex_id[self.id] = i  # The vertex id of a course w/in the curriculum
            # Graphs.jl orders graph vertices sequentially
            # TODO: make sure course is not alerady in the curriculum
        mapped_vertex_ids = self.map_vertex_ids()
        for c in self.courses:
            for r in c.requisites:
                self.graph.add_edge(mapped_vertex_ids[r], c.vertex_id[self.id])

    def create_course_learning_outcome_graph(self) -> None:
        """
            create_course_learning_outcome_graph!(c:Curriculum)

        Create a curriculum directed graph from a curriculum specification. This graph graph contains courses and learning outcomes
        of the curriculum. The graph is stored as a LightGraph.jl implemenation within the Curriculum data object.


        """
        len_courses = len(self.courses)
        # len_learning_outcomes = len(self.learning_outcomes)

        for i, c in enumerate(self.courses):
            self.course_learning_outcome_graph.add_node(i)
            c.vertex_id[self.id] = i  # The vertex id of a course w/in the curriculum
            # Graphs.jl orders graph vertices sequentially
            # TODO: make sure course is not alerady in the curriculum

        for j, lo in enumerate(self.learning_outcomes):
            self.course_learning_outcome_graph.add_node(j)
            lo.vertex_id[self.id] = (
                len_courses + j
            )  # The vertex id of a learning outcome w/in the curriculum
            # Graphs.jl orders graph vertices sequentially
            # TODO: make sure course is not alerady in the curriculum

        mapped_vertex_ids = self.map_vertex_ids()
        mapped_lo_vertex_ids = self.map_lo_vertex_ids()

        # Add edges among courses
        for c in self.courses:
            for r in c.requisites:
                self.course_learning_outcome_graph.add_edge(
                    mapped_vertex_ids[r], c.vertex_id[self.id]
                )
                nx.set_edge_attributes(
                    self.course_learning_outcome_graph,
                    {
                        (mapped_vertex_ids[r], c.vertex_id[self.id]): {
                            c_to_c: c.requisites[r]
                        }
                    },
                )

        # Add edges among learning_outcomes
        for lo in self.learning_outcomes:
            for r in lo.requisites:
                self.course_learning_outcome_graph.add_edge(
                    mapped_lo_vertex_ids[r],
                    lo.vertex_id[self.id],
                )
                nx.set_edge_attributes(
                    self.course_learning_outcome_graph,
                    {(mapped_lo_vertex_ids[r], lo.vertex_id[self.id]): {lo_to_lo: pre}},
                )

        # Add edges between each pair of a course and a learning outcome
        for c in self.courses:
            for lo in c.learning_outcomes:
                self.course_learning_outcome_graph.add_edge(
                    mapped_lo_vertex_ids[lo.id],
                    c.vertex_id[self.id],
                )
                nx.set_edge_attributes(
                    self.course_learning_outcome_graph,
                    {
                        (mapped_lo_vertex_ids[lo.id], c.vertex_id[self.id]): {
                            lo_to_c: belong_to
                        }
                    },
                )

    def create_learning_outcome_graph(self) -> None:
        """
            create_learning_outcome_graph!(c:Curriculum)

        Create a curriculum directed graph from a curriculum specification. The graph is stored as a
        LightGraph.jl implemenation within the Curriculum data object.
        """
        for i, lo in enumerate(self.learning_outcomes):
            self.learning_outcome_graph.add_node(i)
            lo.vertex_id[self.id] = i  # The vertex id of a course w/in the curriculum
            # Graphs.jl orders graph vertices sequentially
            # TODO: make sure course is not alerady in the curriculum
        mapped_vertex_ids = self.map_lo_vertex_ids()
        for lo in self.learning_outcomes:
            for r in lo.requisites:
                self.learning_outcome_graph.add_edge(
                    mapped_vertex_ids[r], lo.vertex_id[self.id]
                )

    # find requisite type from vertex ids in a curriculum graph
    def requisite_type(self, src_course_id: int, dst_course_id: int) -> Requisite:
        src = 0
        dst = 0
        for c in self.courses:
            if c.vertex_id[self.id] == src_course_id:
                src = c
            elif c.vertex_id[self.id] == dst_course_id:
                dst = c
        if (src == 0 or dst == 0) or src.id not in dst.requisites:
            raise Exception(
                f"edge ({src_course_id}, {dst_course_id}) does not exist in curriculum graph"
            )
        else:
            return dst.requisites[src.id]

    def isvalid(self, error_msg: StringIO = StringIO()) -> bool:
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
        g = self.graph.copy()
        validity = True
        # First check for simple cycles
        cycles = nx.simple_cycles(g)
        # Next check for cycles that could be created by strict co-requisites.
        # For every strict-corequisite in the curriculum, add another strict-corequisite between the same two vertices, but in
        # the opposite direction. If this creates any cycles of length greater than 2 in the modified graph (i.e., involving
        # more than the two courses in the strict-corequisite relationship), then the curriculum is unsatisfiable.
        for course in self.courses:
            for k, r in course.requisites.items():
                if r == strict_co:
                    v_d = self.course_from_id(course.id).vertex_id[
                        self.id
                    ]  # destination vertex
                    v_s = self.course_from_id(k).vertex_id[self.id]  # source vertex
                    g.add_edge(v_d, v_s)
        new_cycles = nx.simple_cycles(g)
        new_cycles = [
            cyc for cyc in new_cycles if len(cyc) != 2
        ]  # remove length-2 cycles
        cycles = set(
            tuple(cyc) for cyc in [*new_cycles, *cycles]
        )  # remove redundant cycles
        if len(cycles) != 0:
            validity = False
            if self.institution != "":
                error_msg.write(f"\n{self.institution}: ")
            error_msg.write(f" curriculum '{self.name}' has requisite cycles:\n")
            for cyc in cycles:
                error_msg.write("(")
                for i, v in enumerate(cyc):
                    if i != len(cyc) - 1:
                        error_msg.write(f"{self.courses[v].name}, ")
                    else:
                        error_msg.write(f"{self.courses[v].name})\n")
        return validity
