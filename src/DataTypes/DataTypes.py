# file: DataTypes.jl

from enum import Enum, auto

# Enumerated types
# @enum Degree AA AS AAS BA BAAS BAH BBA BDes BE BED BFA BGS BIS BLA BLS BM BME BMS BMus BPS BRIT BS BSAS BSBA BSBE BSCE BSCH BSCP BSCS BSCYS BSE BSEd BSEE BSEV BSIE BSIS BSIT BSME BSN BSPH BSW BTAS
class System(Enum):
    semester = auto()
    quarter = auto()


class Requisite(Enum):
    pre = auto()
    co = auto()
    strict_co = auto()
    custom = auto()
    belong_to = auto()


class EdgeClass(Enum):
    tree_edge = auto()
    back_edge = auto()
    forward_edge = auto()
    cross_edge = auto()


class EdgeType(Enum):
    c_to_c = auto()
    lo_to_lo = auto()
    lo_to_c = auto()
