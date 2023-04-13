##############################################################
# LearningOutcome data type
from typing import Any, Dict, List

from src.DataTypes.DataTypes import Requisite


class LearningOutcome:
    """
    The `LearningOutcome` data type is used to associate a set of learning outcomes with
    a course or a curriculum (i.e., degree program). To instantiate a `LearningOutcome` use:

        LearningOutcome(name, description, hours)

    # Arguments
    - `name:str` : the name of the learning outcome.
    - `description:str` : detailed description of the learning outcome.
    - `hours:int` : number of class (contact) hours needed to attain the learning outcome.

    # Examples:
    ```julia-repl
    julia> LearningOutcome("M1", "Learner will demonstrate the ability to ...", 12)
    ```
    """

    id: int
    "Unique id for the learning outcome, set when the cousrse is added to a graph"
    vertex_id: Dict[int, int]
    "The vertex id of the learning outcome w/in a curriculum graph, stored as (curriculum_id, vertex_id)"
    name: str
    "Name of the learning outcome"
    description: str
    "A description of the learning outcome"
    hours: int
    "number of class hours that should be devoted to the learning outcome"
    requisites: Dict[int, Requisite]
    "List of requisites, in (requisite_learning_outcome, requisite_type) format"
    affinity: Dict[int, float]
    "Affinity to other learning outcomes in (LearningOutcome ID, affinity value) format, where affinity is in the interval [0,1]."
    metrics: Dict[str, Any]
    "Learning outcome-related metrics"
    metadata: Dict[str, Any]
    "Learning outcome-related metadata"

    # Constructor
    def __init__(self, name: str, description: str, hours: int = 0) -> None:
        self.name = name
        self.description = description
        self.hours = hours
        self.id = hash(self.name + self.description)
        self.requisites = {}
        self.metrics = {}
        self.metadata = {}
        self.vertex_id = {}  # curriculum id -> vertex id


def add_lo_requisite(
    requisite_lo: LearningOutcome, lo: LearningOutcome, requisite_type: Requisite
) -> None:
    """
    add_lo_requisite!(rlo, tlo, requisite_type)
    Add learning outcome rlo as a requisite, of type requisite_type, for target learning outcome tlo
    outcome tlo.
    """
    lo.requisites[requisite_lo.id] = requisite_type


def add_lo_requisites(
    requisite_lo: List[LearningOutcome],
    lo: LearningOutcome,
    requisite_type: List[Requisite],
) -> None:
    assert len(requisite_lo) == len(requisite_type)
    for i in range(len(requisite_lo)):
        lo.requisites[requisite_lo[i].id] = requisite_type[i]
