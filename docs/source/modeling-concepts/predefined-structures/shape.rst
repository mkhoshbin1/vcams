.. _predefined-shape:

Geometric Shapes
================
Geometric shapes are very useful in modeling structures.
For example, composites are usually modeled with circular or spherical inclusions of a different material
and if this material is empty space, the result can be a foam.

This functionality is implemented in two parts:

1. There are individual classes that correspond to a geometrical shape.
   These take a number of parameters and contain a function that can be passed to mask_from_function (TODO)
   which is described in TODO.
2. There is also a TODO class that contains any number of different shapes,
   can have additional shapes added to it, and can return a mask when necessary.
   This is the preferred way of using the shapes.

These will be discussed in the following sections.

Classes Corresponding to Geometric Shapes
------------------------------------------
The basis for all of these classes is an `abstract base class <https://en.wikipedia.org/wiki/Abstract_type>`__
named TODO which introduces a *dim* property describing the dimensionality of the shape
and the *func* function that evaluates the shape's formula for a given coordinates.
Both of these are abstract and must be re-defined for the subclasses.
There is also the concrete TODO function that creates a mask based on the shape.

The usable classes are described in :numref:`shape-class-table`. Their respective documentations contain more information on them.

.. table:: Classes Implemented for Geometric Shapes.
   :name:  shape-class-table
   :align: center
   :widths: auto

   +--------+--------+------------------------+
   |  Name  | 2D/3D? |        Formula         |
   +========+========+========================+
   | Circle | 2D     | TODO aaaaaaaaaaaaaaaaa |
   +--------+--------+------------------------+
   | Sphere | 3D     | TODO aaaaaaaaaaaaaaaaa |
   +--------+--------+------------------------+


The ShapeArray Class
--------------------
The TODO class is the recommended way for modeling shapes.
It is defined based on the size and dimensions of a VoxelPart and can have any compatible shape added to it,
and will calculate a :ref:`Boolean Mask <boolean-masks>` upon request.

Examples TODO show this class in action.