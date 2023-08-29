from typing import List

from .course import Course
from .degree_requirements import Grade


class CourseRecord:
    "Course record - record of performance in a single course"
    course: Course
    "course that was attempted"
    grade: Grade
    "grade earned in the course"
    term: str
    "term course was attempted"

    def __init__(self, course: Course, grade: Grade, term: str = "") -> None:
        self.course = course
        self.grade = grade
        self.term = term


class StudentRecord:
    "Student record data type, i.e., a transcript"
    id: str
    "unique student id"
    first_name: str
    "student's first name"
    last_name: str
    "student's last name"
    middle_initial: str
    "Student's middle initial or name"
    transcript: List[CourseRecord]
    "list of student grades"
    GPA: float
    "student's GPA"

    def __init__(
        self,
        id: str,
        first_name: str,
        last_name: str,
        middle_initial: str,
        transcript: List[CourseRecord],
    ) -> None:
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.middle_initial = middle_initial
        self.transcript = transcript
