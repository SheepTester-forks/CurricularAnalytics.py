# file: DataTypes.jl

from enum import Enum, auto

__all__ = [
    "semester",
    "quarter",
    "pre",
    "co",
    "strict_co",
    "custom",
    "belong_to",
    "tree_edge",
    "back_edge",
    "forward_edge",
    "cross_edge",
    "c_to_c",
    "lo_to_lo",
    "lo_to_c",
]

# Enumerated types
# @enum Degree AA AS AAS BA BAAS BAH BBA BDes BE BED BFA BGS BIS BLA BLS BM BME BMS BMus BPS BRIT BS BSAS BSBA BSBE BSCE BSCH BSCP BSCS BSCYS BSE BSEd BSEE BSEV BSIE BSIS BSIT BSME BSN BSPH BSW BTAS


class System(Enum):
    """
    The number of terms during a typical year. Defaults to :data:`semester`.
    """

    semester = auto()
    quarter = auto()

    def __repr__(self) -> str:
        return (
            "semester"
            if self is self.semester
            else "quarter"
            if self is self.quarter
            else ""
        )


semester = System.semester
"Semester system."
quarter = System.quarter
"Quarter system. Complexity scores are scaled by 2/3 in quarter system curricula."


class Requisite(Enum):
    pre = auto()
    co = auto()
    strict_co = auto()
    custom = auto()
    belong_to = auto()

    def __repr__(self) -> str:
        return (
            "pre"
            if self is self.pre
            else "co"
            if self is self.co
            else "strict_co"
            if self is self.strict_co
            else "custom"
            if self is self.custom
            else "belong_to"
            if self is self.belong_to
            else ""
        )


pre = Requisite.pre
co = Requisite.co
strict_co = Requisite.strict_co
custom = Requisite.custom
belong_to = Requisite.belong_to


class EdgeClass(Enum):
    tree_edge = auto()
    back_edge = auto()
    forward_edge = auto()
    cross_edge = auto()

    def __repr__(self) -> str:
        return (
            "tree_edge"
            if self is self.tree_edge
            else "back_edge"
            if self is self.back_edge
            else "forward_edge"
            if self is self.forward_edge
            else "cross_edge"
            if self is self.cross_edge
            else ""
        )


tree_edge = EdgeClass.tree_edge
back_edge = EdgeClass.back_edge
forward_edge = EdgeClass.forward_edge
cross_edge = EdgeClass.cross_edge


class EdgeType(Enum):
    c_to_c = auto()
    lo_to_lo = auto()
    lo_to_c = auto()

    def __repr__(self) -> str:
        return (
            "c_to_c"
            if self is self.c_to_c
            else "lo_to_lo"
            if self is self.lo_to_lo
            else "lo_to_c"
            if self is self.lo_to_c
            else ""
        )


c_to_c = EdgeType.c_to_c
lo_to_lo = EdgeType.lo_to_lo
lo_to_c = EdgeType.lo_to_c
