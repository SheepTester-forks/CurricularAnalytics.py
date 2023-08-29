from typing import List

from .degree_plan import DegreePlan
from .student import Student


class Simulation:
    degree_plan: DegreePlan
    "The curriculum that is simulated"
    duration: int
    "The number of terms the simulation runs for"
    course_attempt_limit: int
    "The number of times that a course is allowed to take"

    num_students: int
    "The number of students in the simulation"
    enrolled_students: List[Student]
    "Array of students that are enrolled"
    graduated_students: List[Student]
    "Array of students that have graduated"
    stopout_students: List[Student]
    "Array of students who stopped out"

    reach_attempts_students: List[Student]
    "Array of students who have reached max course attempts"
    reach_attempts_rates: List[float]
    "Array of student reaching max course attemps rates"

    student_progress: List[int]
    "Indicates wheter students have passed each course"
    student_attemps: List[int]
    "Number of attemps that students have taken for each course"

    grad_rate: float
    "Graduation rate at the end of the simulation"
    term_grad_rates: List[float]
    "Array of graduation rates at the end of the simulation"
    time_to_degree: float
    "Average number of semesters it takes to graduate students"
    stopout_rate: float
    "Stopout rate at the end of the simulation"
    term_stopout_rates: List[float]
    "Array of stopout rates for each term"

    def __init__(self, degree_plan: DegreePlan) -> None:
        self.degree_plan = degree_plan
        self.enrolled_students = []
        self.graduated_students = []
        self.stopout_students = []

        # Set up degree plan
        degree_plan.metadata["stopout_model"] = {}

        # Set up courses
        for id, course in enumerate(degree_plan.curriculum.courses):
            course.metadata["id"] = id
            course.metadata["failures"] = 0
            course.metadata["enrolled"] = 0
            course.metadata["passrate"] = 0
            course.metadata["term_req"] = 0
            course.metadata["grades"] = []
            course.metadata["students"] = []
            course.metadata["model"] = {}
