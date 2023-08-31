.. currentmodule:: curricularanalytics

API Reference
=============

The following section outlines the API of CurricularAnalytics.py.

Course Catalog
--------------
.. attributetable:: CourseCatalog
.. autoclass:: CourseCatalog
  :members:
Course
------
.. attributetable:: AbstractCourse
.. autoclass:: AbstractCourse
  :members:
.. attributetable:: Course
.. autoclass:: Course
  :members:
.. attributetable:: CourseCollection
.. autoclass:: CourseCollection
  :members:
.. autofunction:: course_id
Curriculum
----------
.. attributetable:: BasicMetrics
.. autoclass:: BasicMetrics
  :members:
.. attributetable:: Curriculum
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
.. autodata:: custom
.. autodata:: belong_to
EdgeClass
~~~~~~~~~
.. autoclass:: EdgeClass
  :members:
.. autodata:: tree_edge
.. autodata:: back_edge
.. autodata:: forward_edge
.. autodata:: cross_edge
EdgeType
~~~~~~~~
.. autoclass:: EdgeType
  :members:
.. autodata:: c_to_c
.. autodata:: lo_to_lo
.. autodata:: lo_to_c
Degree Plan
~~~~~~~~~~~
.. attributetable:: Term
.. autoclass:: Term
  :members:
.. attributetable:: TermMetrics
.. autoclass:: TermMetrics
  :members:
.. attributetable:: DegreePlan
.. autoclass:: DegreePlan
  :members:
Degree Requirements
~~~~~~~~~~~~~~~~~~~
.. attributetable:: Grade
.. autoclass:: Grade
  :members:
.. autofunction:: grade
.. autofunction:: from_grade
.. attributetable:: AbstractRequirement
.. autoclass:: AbstractRequirement
  :members:
.. attributetable:: CourseSet
.. autoclass:: CourseSet
  :members:
.. attributetable:: RequirementSet
.. autoclass:: RequirementSet
  :members:
Learning Outcome
----------------
.. attributetable:: LearningOutcome
.. autoclass:: LearningOutcome
  :members:
Simulation
----------
.. attributetable:: Simulation
.. autoclass:: Simulation
  :members:
Student Record
--------------
.. attributetable:: CourseRecord
.. autoclass:: CourseRecord
  :members:
.. attributetable:: StudentRecord
.. autoclass:: StudentRecord
  :members:
Student
-------
.. attributetable:: Student
.. autoclass:: Student
  :members:
.. autofunction:: simple_students
Transfer Articulation
---------------------
.. attributetable:: TransferArticulation
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
Graph Algorithms
----------------
.. autofunction:: all_paths
.. autofunction:: dfs
.. autofunction:: gad
.. autofunction:: longest_path
.. autofunction:: longest_paths
.. autofunction:: reach
.. autofunction:: reach_subgraph
.. autofunction:: reachable_from
.. autofunction:: reachable_from_subgraph
.. autofunction:: reachable_to
.. autofunction:: reachable_to_subgraph
.. autofunction:: topological_sort
