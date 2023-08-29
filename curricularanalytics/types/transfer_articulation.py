from datetime import date
from typing import Any, Dict, List, Optional, Tuple

from .course_catalog import CourseCatalog


class TransferArticulation:
    "Transfer articulation map for a home (recieving transfer) institution"
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
    "Dictionary in ((transfer_catalog_id, transfer_course_id), array of home_course_ids) format"

    def __init__(
        self,
        name: str,
        institution: str,
        home_catalog: CourseCatalog,
        transfer_catalogs: Optional[Dict[int, CourseCatalog]] = None,
        transfer_map: Optional[Dict[Tuple[int, int], List[int]]] = None,
        date_range: Tuple[date, date] = (date.min, date.max),
    ) -> None:
        self.name = name
        self.institution = institution
        self.date_range = date_range
        self.transfer_catalogs = transfer_catalogs or {}
        self.home_catalog = home_catalog
        self.transfer_map = transfer_map or {}

    def add_transfer_catalog(self, transfer_catalog: CourseCatalog) -> None:
        self.transfer_catalogs[transfer_catalog.id] = transfer_catalog

    # TODO: add the ability for a transfer course to partially satifsfy a home institution course (i.e., some, but not all, course credits)
    def add_transfer_course(
        self,
        home_course_ids: List[int],
        transfer_catalog_id: int,
        transfer_course_id: int,
    ) -> None:
        "A single transfer course may articulate to more than one course at the home institution"
        self.transfer_map[transfer_catalog_id, transfer_course_id] = [*home_course_ids]

    def transfer_equiv(
        self, transfer_catalog_id: int, transfer_course_id: int
    ) -> Optional[List[int]]:
        """
        Find the course equivalency at a home institution of a course being transfered from another institution
        returns transfer equivalent course, or nothing if there is no transfer equivalency
        """
        return self.transfer_map.get((transfer_catalog_id, transfer_course_id))
