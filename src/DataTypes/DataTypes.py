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
    semester = auto()
    quarter = auto()


semester = System.semester
quarter = System.quarter


class Requisite(Enum):
    pre = auto()
    co = auto()
    strict_co = auto()
    custom = auto()
    belong_to = auto()


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


tree_edge = EdgeClass.tree_edge
back_edge = EdgeClass.back_edge
forward_edge = EdgeClass.forward_edge
cross_edge = EdgeClass.cross_edge


class EdgeType(Enum):
    c_to_c = auto()
    lo_to_lo = auto()
    lo_to_c = auto()


c_to_c = EdgeType.c_to_c
lo_to_lo = EdgeType.lo_to_lo
lo_to_c = EdgeType.lo_to_c
