from curricularanalytics import Course, Curriculum, DegreePlan, Term, co, pre

A = Course(
    "Introduction to Baskets",
    3,
    institution="ACME State University",
    prefix="BW",
    num="110",
    canonical_name="Baskets I",
)
B = Course(
    "Swimming",
    3,
    institution="ACME State University",
    prefix="PE",
    num="115",
    canonical_name="Physical Education",
)
C = Course(
    "Basic Basket Forms",
    3,
    institution="ACME State University",
    prefix="BW",
    num="111",
    canonical_name="Baskets I",
)
D = Course(
    "Basic Basket Forms Lab",
    1,
    institution="ACME State University",
    prefix="BW",
    num="111L",
    canonical_name="Baskets I Laboratory",
)
E = Course(
    "Advanced Basketry",
    3,
    institution="ACME State University",
    prefix="BW",
    num="300",
    canonical_name="Baskets II",
)
F = Course(
    "Basket Materials & Decoration",
    3,
    institution="ACME State University",
    prefix="BW",
    num="214",
    canonical_name="Basket Materials",
)
G = Course(
    "Humanitites Elective",
    3,
    institution="ACME State University",
    prefix="EGR",
    num="101",
    canonical_name="Humanitites Core",
)
H = Course(
    "Technical Elective",
    3,
    institution="ACME State University",
    prefix="BW",
    num="3xx",
    canonical_name="Elective",
)

E.add_requisite(C, pre)
F.add_requisite(D, pre)
C.add_requisites([(A, pre), (B, pre), (D, co)])

# add some learning outcomes for each of the courses
# Yiming add code here

curric = Curriculum(
    "Underwater Basket Weaving",
    [A, B, C, D, E, F, G, H],
    institution="ACME State University",
    cip="445786",
)


dp = DegreePlan(
    "2019 Plan",
    curric,
    [
        Term([A, B]),
        Term([C, D]),
        Term([E, F]),
        Term([G, H]),
    ],
)
