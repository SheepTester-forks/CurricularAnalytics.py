from typing import Any, Dict, List, Optional, Tuple
from src.DataTypes.CourseCatalog import CourseCatalog


class TransferArticulation:
    "Transfer articulation map for a home (recieving xfer) institution"
    name: str
    "Name of the transfer articulation data structure"
    institution: str
    "Institution receiving the transfer courses (home institution)"
    date_range: Tuple[Any, ...]
    "Range of dates over which the transfer articulation data is applicable"
    transfer_catalogs: Dict[int, CourseCatalog]
    "Dictionary of transfer institution catalogs, in (CourseCatalog id, catalog) format"
    home_catalog: CourseCatalog
    "Course catalog of recieving institution"
    transfer_map: Dict[Tuple[int, int], List[int]]
    "Dictionary in ((xfer_catalog_id, xfer_course_id), array of home_course_ids) format"

    def __init__(
        self,
        name: str,
        institution: str,
        home_catalog: CourseCatalog,
        transfer_catalogs: Dict[int, CourseCatalog] = {},
        transfer_map: Dict[Tuple[int, int], List[int]] = {},
        date_range: Tuple[Any, ...] = (),
    ) -> None:
        "Constructor"
        self.name = name
        self.institution = institution
        self.transfer_catalogs = transfer_catalogs
        self.home_catalog = home_catalog
        self.transfer_map = transfer_map


def add_transfer_catalog(
    ta: TransferArticulation, transfer_catalog: CourseCatalog
) -> None:
    ta.transfer_catalogs[transfer_catalog.id] = transfer_catalog


# A single transfer course may articulate to more than one course at the home institution
# TODO: add the ability for a transfer course to partially satifsfy a home institution course (i.e., some, but not all, course credits)
def add_transfer_course(
    ta: TransferArticulation,
    home_course_ids: List[int],
    transfer_catalog_id: int,
    transfer_course_id: int,
) -> None:
    ta.transfer_map[(transfer_catalog_id, transfer_course_id)] = []
    for id in home_course_ids:
        ta.transfer_map[(transfer_catalog_id, transfer_course_id)].append(id)


# Find the course equivalency at a home institution of a course being transfered from another institution
# returns transfer equivalent course, or nothing if there is no transfer equivalency
def transfer_equiv(
    ta: TransferArticulation, transfer_catalog_id: int, transfer_course_id: int
) -> Optional[List[int]]:
    if (transfer_catalog_id, transfer_course_id) in ta.transfer_map:
        return ta.transfer_map[(transfer_catalog_id, transfer_course_id)]
