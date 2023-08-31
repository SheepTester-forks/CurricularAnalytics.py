.. currentmodule:: curricularanalytics

API Reference
=============

The following section outlines the API of CurricularAnalytics.py.

Course Catalog
--------------
.. autoclass:: CourseCatalog
  :members:

Course
------
.. autoclass:: AbstractCourse
  :members:
.. autoclass:: Course
  :members:
.. autoclass:: CourseCollection
  :members:
.. autofunction:: course_id

Curriculum
----------
.. autoclass:: BasicMetrics
  :members:
.. autoclass:: Curriculum
  :members:
.. autofunction:: basic_statistics
.. autofunction:: homology

Data Types
----------

System
~~~~~~
.. autoclass:: System
  :members:
.. autodata:: semester
.. autodata:: quarter

Requisite
~~~~~~~~~
.. autoclass:: Requisite
  :members:
.. autodata:: pre
.. autodata:: co
.. autodata:: strict_co

Edge Class
~~~~~~~~~
.. autoclass:: EdgeClass
  :members:
.. autodata:: tree_edge
.. autodata:: back_edge
.. autodata:: forward_edge
.. autodata:: cross_edge

Degree Plan
-----------
.. autoclass:: Term
  :members:
.. autoclass:: TermMetrics
  :members:
.. autoclass:: DegreePlan
  :members:

Degree Requirements
-------------------
.. autoclass:: Grade
  :members:
.. autofunction:: grade
.. autofunction:: from_grade
.. autoclass:: AbstractRequirement
  :members:
.. autoclass:: CourseSet
  :members:
.. autoclass:: RequirementSet
  :members:

Learning Outcome
----------------
.. autoclass:: LearningOutcome
  :members:

Simulation
----------
.. autoclass:: Simulation
  :members:

Student Record
--------------
.. autoclass:: CourseRecord
  :members:
.. autoclass:: StudentRecord
  :members:

Student
-------
.. autoclass:: Student
  :members:
.. autofunction:: simple_students

Transfer Articulation
---------------------
.. autoclass:: TransferArticulation
  :members:

Data Handler
------------
.. autofunction:: read_csv
.. autofunction:: write_csv

Degree Plan Creation
--------------------
.. autofunction:: bin_filling
.. autofunction:: create_degree_plan
