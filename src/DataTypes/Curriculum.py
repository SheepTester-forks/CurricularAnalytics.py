##############################################################
# Curriculum data type
# The required curriculum associated with a degree program
from io import StringIO
from typing import Any, Dict, List, Optional

from networkx import DiGraph, set_edge_attributes  # type: ignore
from src.CurricularAnalytics import isvalid_curriculum

from src.DataTypes.Course import AbstractCourse, add_requisite
from src.DataTypes.DataTypes import (
    Requisite,
    System,
    belong_to,
    c_to_c,
    lo_to_c,
    lo_to_lo,
    pre,
    semester,
)
from src.DataTypes.LearningOutcome import LearningOutcome


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
    graph: DiGraph
    "Directed graph representation of pre-/co-requisite structure of the curriculum, note: this is a course graph"
    learning_outcomes: List[LearningOutcome]
    "A list of learning outcomes associated with the curriculum"
    learning_outcome_graph: DiGraph
    "Directed graph representatin of pre-/co-requisite structure of learning outcomes in the curriculum"
    course_learning_outcome_graph: DiGraph
    """
    Directed Int64 metagraph with Float64 weights defined by :weight (default weight 1.0)
    This is a course and learning outcome graph
    """
    metrics: Dict[str, Any]
    "Curriculum-related metrics"
    metadata: Dict[str, Any]
    "Curriculum-related metadata"

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
        self.credit_hours = total_credits(self)
        self.graph = DiGraph()
        create_graph(self)
        self.metrics = {}
        self.metadata = {}
        self.learning_outcomes = learning_outcomes
        self.learning_outcome_graph = DiGraph()
        create_learning_outcome_graph(self)
        self.course_learning_outcome_graph = DiGraph()
        create_course_learning_outcome_graph(self)
        errors = StringIO()
        if not (isvalid_curriculum(self, errors)):
            print(
                "WARNING: Curriculum was created, but is invalid due to requisite cycle(s):"
            )  # TODO: yellow
            print(errors)


# TODO: update a curriculum graph if requisites have been added/removed or courses have been added/removed
# def update_curriculum(curriculum:Curriculum, courses:Array{Course}=())
#    # if courses array is empty, no new courses were added
# end


def convert_ids(curriculum: Curriculum) -> Curriculum:
    "Converts course ids, from those used in CSV file format, to the standard hashed id used by the data structures in the toolbox"
    for c1 in curriculum.courses:
        old_id = c1.id
        c1.id = hash(c1.name + c1.prefix + c1.num + c1.institution)
        if old_id != c1.id:
            for c2 in curriculum.courses:
                if old_id in (c2.requisites):
                    add_requisite(c1, c2, c2.requisites[old_id])
                    del c2.requisites[old_id]
    return curriculum


def map_vertex_ids(curriculum: Curriculum) -> Dict[int, int]:
    "Map course IDs to vertex IDs in an underlying curriculum graph."
    mapped_ids: Dict[int, int] = {}
    for c in curriculum.courses:
        mapped_ids[c.id] = c.vertex_id[curriculum.id]
    return mapped_ids


def map_lo_vertex_ids(curriculum: Curriculum) -> Dict[int, int]:
    "Map lo IDs to vertex IDs in an underlying curriculum graph."
    mapped_ids: Dict[int, int] = {}
    for lo in curriculum.learning_outcomes:
        mapped_ids[lo.id] = lo.vertex_id[curriculum.id]
    return mapped_ids


def course(
    curric: Curriculum, prefix: str, num: str, name: str, institution: str
) -> AbstractCourse:
    "Compute the hash value used to create the id for a course, and return the course if it exists in the curriculum supplied as input"
    hash_val = hash(name + prefix + num + institution)
    if hash_val in (c.id for c in curric.courses):
        return curric.courses[next(x.id == hash_val for x in curric.courses)]
    else:
        raise Exception(
            "Course: {prefix} {num}: {name} at {institution} does not exist in curriculum: {curric.name}"
        )


def course_from_id(curriculum: Curriculum, id: int) -> Optional[AbstractCourse]:
    "Return the course associated with a course id in a curriculum"
    for c in curriculum.courses:
        if c.id == id:
            return c


def lo_from_id(curriculum: Curriculum, id: int) -> Optional[LearningOutcome]:
    "Return the lo associated with a lo id in a curriculum"
    for lo in curriculum.learning_outcomes:
        if lo.id == id:
            return lo


def course_from_vertex(curriculum: Curriculum, vertex: int) -> AbstractCourse:
    "Return the course associated with a vertex id in a curriculum graph"
    return curriculum.courses[vertex]


def total_credits(curriculum: Curriculum) -> float:
    "The total number of credit hours in a curriculum"
    total_credits = 0
    for c in curriculum.courses:
        total_credits += c.credit_hours
    return total_credits


def create_graph(curriculum: Curriculum) -> None:
    """
        create_graph!(c:Curriculum)

    Create a curriculum directed graph from a curriculum specification. The graph is stored as a
    LightGraph.jl implemenation within the Curriculum data object.
    """
    for i, c in enumerate(curriculum.courses):
        curriculum.graph.add_node(i)  # type: ignore
        c.vertex_id[curriculum.id] = i  # The vertex id of a course w/in the curriculum
        # Graphs.jl orders graph vertices sequentially
        # TODO: make sure course is not alerady in the curriculum
    mapped_vertex_ids = map_vertex_ids(curriculum)
    for c in curriculum.courses:
        for r in c.requisites:
            curriculum.graph.add_edge(mapped_vertex_ids[r], c.vertex_id[curriculum.id])  # type: ignore


def create_course_learning_outcome_graph(curriculum: Curriculum) -> None:
    """
        create_course_learning_outcome_graph!(c:Curriculum)

    Create a curriculum directed graph from a curriculum specification. This graph graph contains courses and learning outcomes
    of the curriculum. The graph is stored as a LightGraph.jl implemenation within the Curriculum data object.


    """
    len_courses = len(curriculum.courses)
    # len_learning_outcomes = len(curriculum.learning_outcomes)

    for i, c in enumerate(curriculum.courses):
        curriculum.course_learning_outcome_graph.add_node(i)  # type: ignore
        c.vertex_id[curriculum.id] = i  # The vertex id of a course w/in the curriculum
        # Graphs.jl orders graph vertices sequentially
        # TODO: make sure course is not alerady in the curriculum

    for j, lo in enumerate(curriculum.learning_outcomes):
        curriculum.course_learning_outcome_graph.add_node(j)  # type: ignore
        lo.vertex_id[curriculum.id] = (
            len_courses + j
        )  # The vertex id of a learning outcome w/in the curriculum
        # Graphs.jl orders graph vertices sequentially
        # TODO: make sure course is not alerady in the curriculum

    mapped_vertex_ids = map_vertex_ids(curriculum)
    mapped_lo_vertex_ids = map_lo_vertex_ids(curriculum)

    # Add edges among courses
    for c in curriculum.courses:
        for r in c.requisites:
            curriculum.course_learning_outcome_graph.add_edge(mapped_vertex_ids[r], c.vertex_id[curriculum.id])  # type: ignore
            set_edge_attributes(
                curriculum.course_learning_outcome_graph,
                {
                    (mapped_vertex_ids[r], c.vertex_id[curriculum.id]): {
                        c_to_c: c.requisites[r]
                    }
                },
            )

    # Add edges among learning_outcomes
    for lo in curriculum.learning_outcomes:
        for r in lo.requisites:
            curriculum.course_learning_outcome_graph.add_edge(  # type: ignore
                mapped_lo_vertex_ids[r],
                lo.vertex_id[curriculum.id],
            )
            set_edge_attributes(
                curriculum.course_learning_outcome_graph,
                {
                    (mapped_lo_vertex_ids[r], lo.vertex_id[curriculum.id]): {
                        lo_to_lo: pre
                    }
                },
            )

    # Add edges between each pair of a course and a learning outcome
    for c in curriculum.courses:
        for lo in c.learning_outcomes:
            curriculum.course_learning_outcome_graph.add_edge(  # type: ignore
                mapped_lo_vertex_ids[lo.id],
                c.vertex_id[curriculum.id],
            )
            set_edge_attributes(
                curriculum.course_learning_outcome_graph,
                {
                    (mapped_lo_vertex_ids[lo.id], c.vertex_id[curriculum.id]): {
                        lo_to_c: belong_to
                    }
                },
            )


def create_learning_outcome_graph(curriculum: Curriculum) -> None:
    """
        create_learning_outcome_graph!(c:Curriculum)

    Create a curriculum directed graph from a curriculum specification. The graph is stored as a
    LightGraph.jl implemenation within the Curriculum data object.
    """
    for i, lo in enumerate(curriculum.learning_outcomes):
        curriculum.learning_outcome_graph.add_node(i)  # type: ignore
        lo.vertex_id[curriculum.id] = i  # The vertex id of a course w/in the curriculum
        # Graphs.jl orders graph vertices sequentially
        # TODO: make sure course is not alerady in the curriculum
    mapped_vertex_ids = map_lo_vertex_ids(curriculum)
    for lo in curriculum.learning_outcomes:
        for r in lo.requisites:
            curriculum.learning_outcome_graph.add_edge(mapped_vertex_ids[r], lo.vertex_id[curriculum.id])  # type: ignore


# find requisite type from vertex ids in a curriculum graph
def requisite_type(
    curriculum: Curriculum, src_course_id: int, dst_course_id: int
) -> Requisite:
    src = 0
    dst = 0
    for c in curriculum.courses:
        if c.vertex_id[curriculum.id] == src_course_id:
            src = c
        elif c.vertex_id[curriculum.id] == dst_course_id:
            dst = c
    if (src == 0 or dst == 0) or src.id not in dst.requisites:
        raise Exception(
            f"edge ({src_course_id}, {dst_course_id}) does not exist in curriculum graph"
        )
    else:
        return dst.requisites[src.id]
