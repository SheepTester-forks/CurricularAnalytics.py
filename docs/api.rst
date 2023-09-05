.. currentmodule:: curricularanalytics

API Reference
=============

The following section outlines the API of CurricularAnalytics.py.

Here are quick links to common classes and methods you might use:

* Data types: :class:`Course` (:meth:`~AbstractCourse.add_requisite`, :meth:`~AbstractCourse.delete_requisite`), :class:`LearningOutcome`, :class:`Curriculum` (:meth:`Curriculum.is_valid`), :class:`Term`, :class:`DegreePlan` (:meth:`DegreePlan.is_valid`, :meth:`~DegreePlan.find_term`, :meth:`~DegreePlan.print`)
* Reading/writing curricula and degree plans: :func:`write_csv`, :func:`read_csv`
* Metrics: :meth:`~Curriculum.blocking_factor`, :meth:`~Curriculum.delay_factor`, :meth:`~Curriculum.centrality`, :meth:`~Curriculum.complexity`, :meth:`Curriculum.basic_metrics`, :meth:`DegreePlan.basic_metrics`, :meth:`~DegreePlan.requisite_distance`

Courses
-------

.. autoclass:: AbstractCourse
  :members:
  :undoc-members:
.. autoclass:: Course
  :members:
  :undoc-members:
.. autoclass:: CourseCollection
  :members:
  :undoc-members:
.. autoclass:: CourseCatalog
  :members:
  :undoc-members:
.. autofunction:: course_id

Curricula
----------

To create a curriculum from a collection of courses, and their associated requisites, use:

.. autoclass:: Curriculum
  :members:
  :undoc-members:
.. autoclass:: BasicMetrics
  :members:
  :undoc-members:
.. autofunction:: basic_statistics
.. autofunction:: homology

Degree Plans
------------

To create a degree plan that satisfies the courses associated with a particular curriculum use:

.. autoclass:: DegreePlan
  :members:
  :undoc-members:

The ability to create degree plans that satsify very "goodness" criteria is described in more detail in :ref:`degreeplans`.

A sophisticated visualization capability for viewing degree plans is described in :doc:`/visualize`.

.. image:: src/BW-plan.png
  :alt: Basket Weaving degree plan

.. autoclass:: Term
  :members:
  :undoc-members:
.. autoclass:: TermMetrics
  :members:
  :undoc-members:

Data Types
----------

System
~~~~~~
.. autoclass:: System
  :members:
  :undoc-members:
.. autodata:: semester
.. autodata:: quarter

Requisite
~~~~~~~~~
.. autoclass:: Requisite
  :members:
  :undoc-members:
.. autodata:: pre
.. autodata:: co
.. autodata:: strict_co

Edge Class
~~~~~~~~~~
.. autoclass:: EdgeClass
  :members:
  :undoc-members:
.. autodata:: tree_edge
.. autodata:: back_edge
.. autodata:: forward_edge
.. autodata:: cross_edge

Reading/Writing
---------------

The ability to read/write curricula and degree plans to disk is greatly facilitated by using the functions described here.

.. autofunction:: read_csv
.. autofunction:: write_csv

.. _degreeplans:

Degree Plan Creation
--------------------
.. autofunction:: bin_filling
.. autofunction:: create_degree_plan

Degree Requirements
-------------------
.. autoclass:: Grade
  :members:
  :undoc-members:
.. autofunction:: grade
.. autofunction:: from_grade
.. autoclass:: AbstractRequirement
  :members:
  :undoc-members:
.. autoclass:: CourseSet
  :members:
  :undoc-members:
.. autoclass:: RequirementSet
  :members:
  :undoc-members:

Learning Outcomes
-----------------

Just like courses, learning outcomes can have requisite relationships between them.

.. autoclass:: LearningOutcome
  :members:
  :undoc-members:

Simulation
----------
.. autoclass:: Simulation
  :members:
  :undoc-members:

Student Record
--------------
.. autoclass:: CourseRecord
  :members:
  :undoc-members:
.. autoclass:: StudentRecord
  :members:
  :undoc-members:

Student
-------
.. autoclass:: Student
  :members:
  :undoc-members:
.. autofunction:: simple_students

Transfer Articulation
---------------------
.. autoclass:: TransferArticulation
  :members:
  :undoc-members:

Graph Algorithms
----------------

This toolbox makes use of a number of the graph algorithms provided in the `NetworkX <https://networkx.org/>`_ package.  In addition, we have implemented a number of graph algorithms that you may find useful when developing analytics around curriculum graphs.  The functions implementing these algorithms are described next.

.. autofunction:: dfs
.. autofunction:: gad
.. autofunction:: all_paths
.. autofunction:: longest_path
.. autofunction:: longest_paths
.. autofunction:: reachable_from
.. autofunction:: reachable_from_subgraph
.. autofunction:: reachable_to
.. autofunction:: reachable_to_subgraph
.. autofunction:: reach
.. autofunction:: reach_subgraph
.. autofunction:: topological_sort
