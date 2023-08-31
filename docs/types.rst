.. currentmodule:: curricularanalytics

CurricularAnalytics.jl Data Types
=================================

This section describes the basic data types associated with the CurricularAnalytics.jl toolbox. These are used to construct courses (with associated learning outcomes), curricula and degree plans.

Courses
-------

.. autoclass:: Course
  :members:

Just like courses, learning outcomes can have requisite relationships between them.

Learning Outcomes
-----------------

.. autoclass:: LearningOutcome
  :members:

Curricula
---------

To create a curriculum from a collection of courses, and their associated requisites, use:

.. autoclass:: Curriculum
  :members:

Terms
-----

.. autoclass:: Term
  :members:

Degree Plans
------------

To create a degree plan that satisfies the courses associated with a particular curriculum use:

.. autoclass:: DegreePlan
  :members:

The ability to create degree plans that satsify very "goodness" criteria is described in more detail in :ref:`degreeplans`.

A sophisticated visualization capability for viewing degree plans is described in :ref:`visualize`.

.. image:: src/BW-plan.png
  :alt: Basket Weaving degree plan
