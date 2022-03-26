.. _predefined-shape:

Geometric Shapes
================
Geometric shapes are very useful in modeling structures.
For example, composites are usually modeled with circular or spherical inclusions of a different material
and if this material is empty space, the result can be a porous structure (a foam).

This functionality is implemented in two parts:

1. There are individual classes that correspond to a geometrical shape.
   These take a number of parameters and contain a function
   that can be passed to the :func:`~vcams.mask.function.mask_from_function` function
   to create a Boolean mask.
2. There is also the :class:`~vcams.mask.shape.ShapeArray` class
   that can contain any number of different shapes,
   can have additional shapes added to it, and can return a mask when necessary.
   This is the preferred way of using the shapes.

These will be discussed in the following sections.

Classes Corresponding to Geometric Shapes
------------------------------------------
The basis for all of these classes is an `abstract base class <https://en.wikipedia.org/wiki/Abstract_type>`__
named :class:`~vcams.mask.shape.BaseShape` which introduces
an abstract property named :attr:`~vcams.mask.shape.BaseShape.dim`
describing the dimensionality of the shape
and the :meth:`~vcams.mask.shape.BaseShape.func` abstract method
that evaluates the shape's formula for a given coordinates.
Both of these must be re-defined for the subclasses.
There is also the concrete :meth:`~vcams.mask.shape.BaseShape.calculate_mask` method
that creates a mask based on the shape.

Currently, the following geometric shapes have been implemented.
Their respective documentations contain more information on them:

+ The 2D :class:`Circle <vcams.mask.shape.Circle>`.
+ The 3D :class:`Sphere <vcams.mask.shape.Sphere>`.

:doc:`Example C-3 </examples/example-c3>` demonstrates use of
these classes for creating a single shape in the model.

The ShapeArray Class
--------------------
The :class:`~vcams.mask.shape.ShapeArray` class is the recommended way for modeling shapes.
It is defined based on the size and dimensions of a VoxelPart
and can have any compatible shape added to it.
The criteria for compatibility is that the shape must be
a subclass of :class:`~vcams.mask.shape.BaseShape`
and must have the same dimensionality as the ShapeArray object.
The ShapeArray object has a :attr:`~vcams.mask.shape.ShapeArray.mask` property
that is guaranteed to always return return an up-to-date :ref:`Boolean mask <boolean-masks>`.

:doc:`Example C-4 </examples/example-c4>` shows this class in action.