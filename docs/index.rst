.. currentmodule:: curricularanalytics

Curricular Analytics Toolbox
============================

`CurricularAnalytics.py <https://github.com/SheepTester-forks/CurricularAnalytics.py>`_ is a toolbox for studying, analyzing and comparing academic program curricula and their associated degree plans. The toolbox is a `Python <https://www.python.org/>`_ port of the original `CurricularAnalytics.jl <https://github.com/CurricularAnalytics/CurricularAnalytics.jl>`_. If you are migrating from the Julia version, see :ref:`migrating`.

* :ref:`install`
* :ref:`example`
* :doc:`api`
* :ref:`migrating`

Links:

* `PyPI listing <https://pypi.org/project/curricularanalytics/>`_
* `Documentation <https://sheeptester-forks.github.io/CurricularAnalytics.py/>`_
* `GitHub repo <https://github.com/SheepTester-forks/CurricularAnalytics.py>`_
* `Original Julia version <https://github.com/CurricularAnalytics/CurricularAnalytics.jl>`_

.. _install:

Installation
============

Installation is straightforward. First, install the Python programming language on your computer. To do this, `download Python <https://www.python.org/>`_, and follow the instructions for your operating system.

Next, open the command line, and then type::

   # Linux/macOS
   python3 -m pip install -U curricularanalytics

   # Windows
   py -3 -m pip install -U curricularanalytics

This will install the toolbox, along with the other Python packages needed to run it.

To load and use the toolbox, enter the following at the top of your Python code::

   from curricularanalytics import *

See :ref:`example` for a quick example showcasing some of the features in the toolbox.

.. _terminology:

Terminology
-----------

A basic understanding of the terminology associated with curricula and degree programs will greatly facilitate the use of this toolbox.

A *curriculum* for an academic program consists of the set of courses that a student must complete in order to earn the degree associated with that program. By successfully completing a course, a student should attain the learning outcomes associated with the course, while also earning the number of credit hours associated with the course. For instance, most associate degree programs require a student to earn a minimum of 60 credit hours, and most bachelor's degree programs require a student to earn a minimum of 120 credit hours.

In order to attain the learning outcomes associated with course :math:`B`, a student may first need to attain some of the learning outcomes associated with some other course, say :math:`A`. In order to capture this requirement, course :math:`A` is listed as a *prerequisite* for course :math:`B`. That is, students may not enroll in course :math:`B` unless they have successfully completed course :math:`A`.  More generally, we refer to these types of requirements as *requisites*, and we differentiate between three types:

* Prerequisite: course :math:`A` must be completed prior to attempting course :math:`B`.
* Co-requisite: course :math:`A` may be taken prior to or at the same time as attempting course :math:`B`.
* Strict co-requisite: course :math:`A` must be taken at the same time as course :math:`B`.

A *degree plan* is a term-by-term arrangement for taking all of the courses in a curriculum, layed out so as to satisfy all requisite relationships. A *term* is typically offered either in the semester (two terms/academic year) or quarter (three terms/academic year) format. It is common for schools to offer two-year degree plans for associates degrees and four-year degree plans for bachelors degrees.

There is a one-to-many relationship between a curriculum and the degree plans that satisfy the curriculum. I.e., many different degree plans can be constructed to satisfy a single curriculum. Furthermore, it is likely that some of these degree plans are better suited to the needs of particular students. In addition, it is important to note that a degree plan may contain more courses than are stipulated in a curriculum. For instance, a student may not have the background necessary to take the first math course in a curriculum, necessitating the addition of a prerequisite math class as a part of the degree plan.

.. _example:

Example
~~~~~~~

Consider the Basket Weaving curriculum, consisting of the following four courses:

* BW 101: Introduction to Baskets, 3 credits
* BW 101L: Introduction to Baskets Lab, 1 credit; strict co-requisite: BW 101
* BW 111: Basic Basket Forms, 3 credits; prerequisite: BW 101
* BW 201: Advanced Basketry, 3 credits; co-requisite: BW 111

Represent courses with :class:`Course`::

   from curricularanalytics import Course
   bw101 = Course("Introduction to Baskets", 3, prefix="BW", num="101")
   bw101l = Course("Introduction to Baskets Lab", 1, prefix="BW", num="101L")
   bw111 = Course("Basic Basket Forms", 3, prefix="BW", num="111")
   bw201 = Course("Advanced Basketry", 3, prefix="BW", num="201")

Add relationships between courses with the :meth:`~AbstractCourse.add_requisite` method. See :class:`Requisite` for the types of requisites available::

   from curricularanalytics import co, pre, strict_co
   bw101l.add_requisite(bw101, strict_co)
   bw111.add_requisite(bw101, pre)
   bw201.add_requisite(bw111, co)

Finally, construct a :class:`Curriculum` consisting of the courses::

   from curricularanalytics import Curriculum
   curriculum = Curriculum("Basket Weaving", [bw101, bw101, bw111, bw201])

The following degree plan completes this curriculum in two terms while satisfying all of the requisite relationships:

* Term 1: BW 101, BW 101L
* Term 2: BW 111, BW 201

This degree plan can be represented with a :class:`DegreePlan`, constructed from :class:`Term` objects::

   from curricularanalytics import DegreePlan, Term
   terms = [Term([bw101, bw101l]), Term([bw111, bw201])]
   degree_plan = DegreePlan("2-Term Plan", curriculum, terms)

A visual representation of this degree plan is as follows:

.. image:: src/BW-plan.png
   :alt: Basket Weaving degree plan

The solid arrow in this figure represents a prerequisite relationship, while the dashed arrows represent co-requisite relationships.

To save the curriculum and degree plan to a file, use :func:`write_csv`::

   from curricularanalytics import write_csv
   write_csv(curriculum, "./basket_weaving_curriculum.csv")
   write_csv(degree_plan, "./basket_weaving_plan.csv")

To load from a file, use :func:`read_csv`::

   from curricularanalytics import Curriculum, DegreePlan, read_csv
   curriculum = read_csv("./basket_weaving_curriculum.csv")
   assert isinstance(curriculum, Curriculum)
   degree_plan = read_csv("./basket_weaving_plan.csv")
   assert isinstance(degree_plan, DegreePlan)

Toolbox Overview
----------------

The toolbox represents curricula as graphs, allowing various graph-theoretic measures to be applied in order to quantify the complexity of curricula. In addition to analyzing curricular complexity, the toolbox supports the ability to visualize curricula and degree plans, to compare and contrast curricula, to create optimal degree plans for completing curricula that satisfy particular constraints, and to simulate the impact of various events on student progression through a curriculum.

Functions that can be used to read and write curricula and degree plans to/from permanent storage are described in :doc:`persistence`.
Metrics that have been developed to quantify the complexity of curricula and degree plans are described in :doc:`metrics`. Functions that can be used to study degree plans, and to create degree plans according to various constraints and optimization criteria are described in :doc:`degreeplans`.

Visualization-related functions are described in :doc:`visualize`.

.. _migrating:

Differences from Julia
~~~~~~~~~~~~~~~~~~~~~~

Some substantial API changes were made from the `original Julia package <https://github.com/CurricularAnalytics/CurricularAnalytics.jl>`_, largely to make the package more ergonomic for Python.

The most significant change is that functions associated with objects have been moved to class methods::

   # Julia
   isvalid(curriculum)
   isvalid(degree_plan)

   # Python
   curriculum.is_valid()
   degree_plan.is_valid()

If your editor provides autocomplete, this can help with discovering the methods available for each object.

There are fewer function overloads, so overloaded functions are given different names::

   # Julia
   add_requisite!([A, B, D], C, [pre, pre, co])

   # Python (note the method name and change in list structure)
   C.add_requisites([(A, pre), (B, pre), (D, co)])

   # Julia
   first_course_complexity = complexity(curriculum, 1)
   total, course_complexities = complexity(curriculum)

   # Python
   first_course_complexity = curriculum.complexity(curriculum.courses[0])
   total = curriculum.total_complexity
   course_complexities = list(map(curriculum.complexity, curriculum.courses))

The Python version for calculating curricular metrics may seem verbose, but I hope the resulting API ends up being clearer, particularly with what methods return and what arguments are expected.

Documentation contents
~~~~~~~~~~~~~~~~~~~~~~

.. toctree::
   :maxdepth: 3

   api
   persistence
   metrics
   visualize
   degreeplans
   simulating
   contributing

Indices and tables
==================

* :ref:`genindex`
* :ref:`search`
