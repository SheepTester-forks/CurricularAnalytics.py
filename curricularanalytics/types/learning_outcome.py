"""
LearningOutcome data type
"""

from typing import Any, Dict, List, Tuple

from .data_types import Requisite


class LearningOutcome:
    """
    The `LearningOutcome` data type is used to associate a set of learning outcomes with
    a course or a curriculum (i.e., degree program).

    Args:
        name: The name of the learning outcome.
        description: Detailed description of the learning outcome.
        hours: Number of class (contact) hours needed to attain the learning outcome.

    Examples:
        >>> LearningOutcome("M1", "Learner will demonstrate the ability to ...", 12)
    """

    id: int
    "Unique id for the learning outcome, set when the cousrse is added to a graph"
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

    def add_requisite(
        self, requisite_lo: "LearningOutcome", requisite_type: Requisite
    ) -> None:
        """
        Add learning outcome `requisite_lo` as a requisite, of type `requisite_type`, for this learning outcome.
        """
        self.requisites[requisite_lo.id] = requisite_type

    def add_requisites(
        self,
        requisites: List[Tuple["LearningOutcome", Requisite]],
    ) -> None:
        for requisite_lo, requisite_type in requisites:
            self.add_requisite(requisite_lo, requisite_type)
