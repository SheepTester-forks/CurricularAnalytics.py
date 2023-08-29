from typing import Any, Dict, List, Optional


class Student:
    id: int
    "Unique ID for student"
    total_credits: int = 0
    "The total number of credit hours the student has earned"
    gpa: float = 0.0
    "The student's GPA"
    total_points: float = 0
    "The total number of points the student has earned"

    attributes: Dict[Any, Any]
    "A dictionary that can store any kind of student attribute"
    stopout: bool
    "Indicates whether the student has stopped out. (False if the student has, True if still enrolled)"
    stopsem: bool
    "The term the student stopped out."
    termcredits: int = 0
    "The number of credits the student has enrolled in for a given term."
    performance: Dict[Any, Any]
    "Stores the grades the student has made in each course."
    graduated: bool
    "Indicates wheter the student has graduated."
    gradsem: int
    "The term the student has graduated."
    termpassed: List[int]
    "An array that represents the term in which the student passed each course."

    def __init__(self, id: int, *, attributes: Optional[Dict[Any, Any]] = None) -> None:
        self.id = id
        self.performance = {}
        self.attributes = attributes or {}


def simple_students(number: int) -> List[Student]:
    "Returns an array of students"
    students: List[Student] = []
    for i in range(number):
        student = Student(i)
        student.stopout = False
        students.append(student)
    return students
