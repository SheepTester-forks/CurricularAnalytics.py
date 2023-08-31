Creating Degree Plans
=====================

As mentioned previously, many different degree plans can be created for a given curriculum.  A *curriculum* is a collection of courses containing requisite relationships between them (see :ref:`terminology`), while a *degree plan* adds a temporal element to a curriculum.  Specifically, a degree plan orders the courses in a curriculum into a collection of successive *terms*: Term 1, Term 2, etc., where a term is considered an academic period (e.g., semester or quarter).  Thus, students following a particular degree plan are expected to complete all of the courses in the first term during the first semester, all of the courses in the second term during the second semester, etc.  The important concept is that if a student completes their degree plan they will earn the degree associated with the curriculum.

Given that we can create many different degree plans for a curriculum, we are interested in finding those plans that best suit the needs and backgrounds of particular students.  For instance, a transfer student with existing college credits will require a different degree plan than a new student who has no prior college credit.  Similarly, a student may not have the background necessary to take the first math course in a curriculum, necessitating the addition of a prerequisite math class as a part of that student's degree plan, etc.

Below we describe a number of different techniques for creating degree plans.  In :ref:`basic-degree-plans` we describe some simple techniques that can be used to create degree plans that are minimally feasible (feasible degree plans are defined below).

.. _basic-degree-plans:

Basic Degree Plans
------------------

In order to be considered *minimally feasible*, a degree plan $P$ for a curriculum $C$ must satisfy two conditions:

1. Every course in the curriculum :math:`C` must appear in one and only one term in the degree plan :math:`P`.  (Note: :math:`P` may contain courses that are not in :math:`C`.)
2. The requisite relationships between the courses in :math:`P` must be respected across the terms in :math:`P`.  That is, if course ``a`` is a prerequisite for course ``b`` in the curriculum, then course ``a`` must appear in the degree plan :math:`P` in an earlier term than course ``b``.
